from plone.app.caching.interfaces import _
from plone.app.caching.operations.utils import cachedResponse
from plone.app.caching.operations.utils import cacheInRAM
from plone.app.caching.operations.utils import cacheStop
from plone.app.caching.operations.utils import doNotCache
from plone.app.caching.operations.utils import fetchFromRAMCache
from plone.app.caching.operations.utils import getContext
from plone.app.caching.operations.utils import getETagAnnotation
from plone.app.caching.operations.utils import getLastModifiedAnnotation
from plone.app.caching.operations.utils import isModified
from plone.app.caching.operations.utils import notModified
from plone.app.caching.operations.utils import parseDateTime
from plone.app.caching.operations.utils import setCacheHeaders
from plone.app.caching.operations.utils import visibleToRole
from plone.caching.interfaces import ICachingOperation
from plone.caching.interfaces import ICachingOperationType
from plone.caching.utils import lookupOptions
from zope.component import adapter
from zope.component import getMultiAdapter
from zope.interface import implementer
from zope.interface import Interface
from zope.interface import provider
from zope.publisher.interfaces.http import IHTTPRequest

import datetime
import random
import time


@implementer(ICachingOperation)
@provider(ICachingOperationType)
@adapter(Interface, Interface)
class BaseCaching:
    """A generic caching operation class that can do pretty much all the usual
    caching operations based on options settings. For UI simplicity, it might
    be easier to subclass this in your custom operations to set a few default
    operations.

    Generic options (Default value for each is None):

    ``maxage``
        is the maximum age of the cached item, in seconds..

    ``smaxage``
        is the maximum age of the cached item in proxies, in seconds.

    ``etags''
        is a list of etag components to use when constructing an etag.

    ``lastModified``
        is a boolean indicating whether to set a Last-Modified header
        and turn on 304 responses.

    ``ramCache``
        is a boolean indicating whether to turn on RAM caching for this item.
        Etags are only required if the URL is not specific enough to ensure
        uniqueness.

    ``vary``
        is a string to add as a Vary header value in the response.
    """

    title = _("Generic caching")
    description = _(
        "Through this operation, all standard caching functions "
        "can be performed via various combinations of the optional "
        "parameter settings. For most cases, it's probably easier "
        "to use one of the other simpler operations (Strong caching, "
        "Moderate caching, Weak caching, or No caching)."
    )
    prefix = "plone.app.caching.baseCaching"
    options = (
        "maxage",
        "smaxage",
        "etags",
        "lastModified",
        "ramCache",
        "vary",
        "anonOnly",
    )

    # Default option values
    maxage = smaxage = etags = vary = None
    lastModified = ramCache = anonOnly = False

    def __init__(self, published, request):
        self.published = published
        self.request = request

    def interceptResponse(self, rulename, response, class_=None):
        options = lookupOptions(class_ or self.__class__, rulename)

        etags = options.get("etags") or self.etags
        anonOnly = options.get("anonOnly", self.anonOnly)
        ramCache = options.get("ramCache", self.ramCache)
        lastModified = options.get("lastModified", self.lastModified)

        # Add the ``anonymousOrRandom`` etag if we are anonymous only
        if anonOnly:
            if etags is None:
                etags = ["anonymousOrRandom"]
            elif "anonymousOrRandom" not in etags:
                etags = tuple(etags) + ("anonymousOrRandom",)

        etag = getETagAnnotation(self.published, self.request, keys=etags)
        lastModified = getLastModifiedAnnotation(
            self.published, self.request, lastModified=lastModified
        )

        # Remove Range from request if the If-Range condition is not fulfilled
        if_range = self.request.environ.get("HTTP_IF_RANGE", "").strip('"')
        if if_range:
            if "HTTP_RANGE" in self.request.environ:
                if_range_dt = parseDateTime(if_range)
                delta_sec = datetime.timedelta(seconds=1)
                if if_range_dt and (lastModified - if_range_dt) < delta_sec:
                    pass
                elif if_range == etag:
                    pass
                else:
                    del self.request.environ["HTTP_RANGE"]
            # If-Range check is done here so we could remove it from the request
            del self.request.environ["HTTP_IF_RANGE"]

        # Check for cache stop request variables
        if cacheStop(self.request, rulename):
            return None

        # Check if this should be a 304 response
        if not isModified(self.request, etag=etag, lastModified=lastModified):
            return notModified(
                self.published,
                self.request,
                response,
                etag=etag,
                lastModified=lastModified,
            )

        # Check if this is in the ram cache
        if ramCache:
            context = getContext(self.published)
            portal_state = getMultiAdapter(
                (context, self.request), name="plone_portal_state"
            )

            if portal_state.anonymous():
                cached = fetchFromRAMCache(
                    self.request, etag=etag, lastModified=lastModified
                )
                if cached is not None:
                    return cachedResponse(
                        self.published, self.request, response, *cached
                    )

        return None

    def modifyResponse(self, rulename, response, class_=None):
        options = lookupOptions(class_ or self.__class__, rulename)

        maxage = options.get("maxage", self.maxage)
        smaxage = options.get("smaxage", self.smaxage)
        etags = options.get("etags") or self.etags

        anonOnly = options.get("anonOnly", self.anonOnly)
        ramCache = options.get("ramCache", self.ramCache)
        vary = options.get("vary", self.vary)

        # Add the ``anonymousOrRandom`` etag if we are anonymous only
        if anonOnly:
            if etags is None:
                etags = ["anonymousOrRandom"]
            elif "anonymousOrRandom" not in etags:
                etags = tuple(etags) + ("anonymousOrRandom",)

        etag = getETagAnnotation(self.published, self.request, etags)
        lastModified = getLastModifiedAnnotation(
            self.published, self.request, options["lastModified"]
        )

        # Check for cache stop request variables
        if cacheStop(self.request, rulename):
            # only stop with etags if configured
            if etags:
                etag = f"{time.time()}{random.randint(0, 1000)}"
                return setCacheHeaders(
                    self.published,
                    self.request,
                    response,
                    etag=etag,
                )
            # XXX: should there be an else here? Last modified works without
            #      extra headers.
            #      Are there other config options?

        # Do the maxage/smaxage settings allow for proxy caching?
        proxyCache = smaxage or (maxage and smaxage is None)

        # Check if the content can be cached in shared caches
        public = True
        if ramCache or proxyCache:
            if etags is not None:
                if (
                    "userid" in etags
                    or "anonymousOrRandom" in etags
                    or "roles" in etags
                ):
                    context = getContext(self.published)
                    portal_state = getMultiAdapter(
                        (context, self.request),
                        name="plone_portal_state",
                    )
                    public = portal_state.anonymous()
            public = public and visibleToRole(self.published, role="Anonymous")

        if proxyCache and not public:
            # This is private so keep it out of both shared and browser caches
            maxage = smaxage = 0

        setCacheHeaders(
            self.published,
            self.request,
            response,
            maxage=maxage,
            smaxage=smaxage,
            etag=etag,
            lastModified=lastModified,
            vary=vary,
        )

        if ramCache and public:
            cacheInRAM(
                self.published,
                self.request,
                response,
                etag=etag,
                lastModified=lastModified,
            )


@provider(ICachingOperationType)
class WeakCaching(BaseCaching):
    """Weak caching operation. A subclass of the generic BaseCaching
    operation to help make the UI approachable by mortals
    """

    title = _("Weak caching")
    description = _(
        "Cache in browser but expire immediately and enable 304 "
        "responses on subsequent requests. 304's require configuration "
        "of the 'Last-modified' and/or 'ETags' settings. If "
        "Last-Modified  header is insufficient to ensure freshness, turn on "
        "ETag checking by listing each ETag components that should be used "
        "to construct the ETag header. To also cache public responses in "
        "Zope memory, set 'RAM cache' to True."
    )
    prefix = "plone.app.caching.weakCaching"
    sort = 3

    # Configurable options
    options = ("etags", "lastModified", "ramCache", "vary", "anonOnly")

    # Default option values
    maxage = 0
    smaxage = etags = vary = None
    lastModified = ramCache = anonOnly = False


@provider(ICachingOperationType)
class ModerateCaching(BaseCaching):
    """Moderate caching operation. A subclass of the generic BaseCaching
    operation to help make the UI approachable by mortals
    """

    title = _("Moderate caching")
    description = _(
        "Cache in browser but expire immediately (same as 'weak caching'), "
        "and cache in proxy (default: 24 hrs). "
        "Use a purgable caching reverse proxy for best results. "
        "Caution: If proxy cannot be purged, or cannot be configured "
        "to remove the 's-maxage' token from the response, then stale "
        "responses might be seen until the cached entry expires."
    )
    prefix = "plone.app.caching.moderateCaching"
    sort = 2

    # Configurable options
    options = ("smaxage", "etags", "lastModified", "ramCache", "vary", "anonOnly")

    # Default option values
    maxage = 0
    smaxage = 86400
    etags = vary = None
    lastModified = ramCache = anonOnly = False


@provider(ICachingOperationType)
class StrongCaching(BaseCaching):
    """Strong caching operation. A subclass of the generic BaseCaching
    operation to help make the UI approachable by mortals
    """

    title = _("Strong caching")
    description = _(
        "Cache in browser and proxy (default: 24 hrs). "
        "Caution: Only use for stable resources "
        "that never change without changing their URL, or resources "
        "for which temporary staleness is not critical."
    )
    prefix = "plone.app.caching.strongCaching"
    sort = 1

    # Configurable options
    options = (
        "maxage",
        "smaxage",
        "etags",
        "lastModified",
        "ramCache",
        "vary",
        "anonOnly",
    )

    # Default option values
    maxage = 86400
    smaxage = etags = vary = None
    lastModified = ramCache = anonOnly = False


@provider(ICachingOperationType)
class TerseCaching(BaseCaching):
    """Terse caching operation."""

    title = _("Terse caching")
    description = _(
        "Cache in browser (default: 10s) and proxy (default: 1 min). "
        "Keep very short in cache to buffer hi-load scenarios ",
        "Use for very dynamic content, like collecting data from "
        "the whole portal. "
        "Temporary outdated is less important than performance."
        "Reduce in-cache time to just 3-10 seconds to only buffer peak load "
        "if behind a proxy",
    )
    prefix = "plone.app.caching.terseCaching"
    sort = 4

    # Configurable options
    options = (
        "maxage",
        "smaxage",
        "etags",
        "lastModified",
        "ramCache",
        "vary",
        "anonOnly",
    )

    # Default option values
    maxage = 10
    smaxage = 60
    vary = "Accept"
    etags = None
    lastModified = ramCache = anonOnly = False


@implementer(ICachingOperation)
@provider(ICachingOperationType)
@adapter(Interface, IHTTPRequest)
class NoCaching:
    """A caching operation that tries to keep the response
    out of all caches.
    """

    title = _("No caching")
    description = _("Use this operation to keep the response " "out of all caches.")
    prefix = "plone.app.caching.noCaching"
    sort = 5
    options = ()

    def __init__(self, published, request):
        self.published = published
        self.request = request

    def interceptResponse(self, rulename, response):
        return None

    def modifyResponse(self, rulename, response):
        doNotCache(self.published, self.request, response)
