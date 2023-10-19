from Acquisition import aq_base
from Acquisition import aq_inner
from plone.app.caching.interfaces import IETagValue
from plone.app.caching.operations.utils import getContext
from plone.app.caching.operations.utils import getLastModifiedAnnotation
from plone.base.utils import safe_hasattr
from plone.registry.interfaces import IRegistry
from Products.CMFCore.interfaces import ICatalogTool
from Products.CMFCore.interfaces import IMembershipTool
from Products.CMFCore.utils import getToolByName
from zope.component import adapter
from zope.component import queryMultiAdapter
from zope.component import queryUtility
from zope.interface import implementer
from zope.interface import Interface

import random
import time


try:
    # available since Plone 6.0.4
    from Products.CMFPlone.resources.browser.resource import _RESOURCE_REGISTRY_MTIME
except ImportError:
    _RESOURCE_REGISTRY_MTIME = None


@implementer(IETagValue)
@adapter(Interface, Interface)
class UserID:
    """The ``userid`` etag component, returning the current user's id"""

    def __init__(self, published, request):
        self.published = published
        self.request = request

    def __call__(self):
        tool = queryUtility(IMembershipTool)
        if tool is None:
            return

        member = tool.getAuthenticatedMember()
        if member is None:
            return

        return member.getId()


@implementer(IETagValue)
@adapter(Interface, Interface)
class Roles:
    """The ``roles`` etag component, returning the current user's roles,
    separated by semicolons
    """

    def __init__(self, published, request):
        self.published = published
        self.request = request

    def __call__(self):
        tool = queryUtility(IMembershipTool)
        if tool is None:
            return

        if bool(tool.isAnonymousUser()):
            return "Anonymous"

        member = tool.getAuthenticatedMember()
        if member is None:
            return

        return ";".join(sorted(member.getRolesInContext(getContext(self.published))))


@implementer(IETagValue)
@adapter(Interface, Interface)
class Language:
    """The ``language`` etag component, returning the value of the
    HTTP_ACCEPT_LANGUAGE request key.
    """

    def __init__(self, published, request):
        self.published = published
        self.request = request

    def __call__(self):
        return self.request.get("HTTP_ACCEPT_LANGUAGE", "")


@implementer(IETagValue)
@adapter(Interface, Interface)
class UserLanguage:
    """The ``userLanguage`` etag component, returning the user's preferred
    language
    """

    def __init__(self, published, request):
        self.published = published
        self.request = request

    def __call__(self):
        language = self.request.get("LANGUAGE", None)
        if language:
            return language
        context = getContext(self.published)
        language = aq_inner(context).Language()
        if language:
            return language
        portal_state = queryMultiAdapter(
            (context, self.request), name="plone_portal_state"
        )
        if portal_state is None:
            return
        return portal_state.default_language()


@implementer(IETagValue)
@adapter(Interface, Interface)
class LastModified:
    """The ``lastModified`` etag component, returning the last modification
    timestamp
    """

    def __init__(self, published, request):
        self.published = published
        self.request = request

    def __call__(self):
        lastModified = getLastModifiedAnnotation(self.published, self.request)
        if lastModified is None:
            return
        return str(time.mktime(lastModified.utctimetuple()))


@implementer(IETagValue)
@adapter(Interface, Interface)
class CatalogCounter:
    """The ``catalogCounter`` etag component, returning a counter which is
    incremented each time the catalog is updated.
    """

    def __init__(self, published, request):
        self.published = published
        self.request = request

    def __call__(self):
        catalog = queryUtility(ICatalogTool)
        if catalog is None:
            return
        return str(catalog.getCounter())


@implementer(IETagValue)
@adapter(Interface, Interface)
class ObjectLocked:
    """The ``locked`` etag component, returning 1 or 0 depending on whether
    the object is locked.
    """

    def __init__(self, published, request):
        self.published = published
        self.request = request

    def __call__(self):
        context = getContext(self.published)
        lock = queryMultiAdapter((context, self.request), name="plone_lock_info")

        if not lock:
            return "0"

        lock_info = lock.lock_info()
        if not lock_info:
            return "0"

        return lock_info["token"]


@implementer(IETagValue)
@adapter(Interface, Interface)
class Skin:
    """The ``skin`` etag component, returning the current skin name."""

    def __init__(self, published, request):
        self.published = published
        self.request = request

    def __call__(self):
        context = getContext(self.published)

        portal_skins = getToolByName(context, "portal_skins", None)
        if portal_skins is None:
            return

        requestVariable = portal_skins.getRequestVarname()
        if requestVariable in self.request:
            return self.request[requestVariable]

        return portal_skins.getDefaultSkin()


@implementer(IETagValue)
@adapter(Interface, Interface)
class AnonymousOrRandom:
    """The ``anonymousOrRandom`` etag component. This is normally added
    implicitly by the ``anonOnly`` setting. It will return for anonymous
    users, but a random number for logged-in ones. The idea is to force a
    re-fetch of a page every time for logged-in users.
    """

    def __init__(self, published, request):
        self.published = published
        self.request = request

    def __call__(self):
        tool = queryUtility(IMembershipTool)
        if tool is None:
            return
        if bool(tool.isAnonymousUser()):
            return
        return f"{time.time()}{random.randint(0, 1000)}"


@implementer(IETagValue)
@adapter(Interface, Interface)
class CopyCookie:
    """The ``copy`` etag component, returning 1 or 0 depending on whether
    the '__cp' cookie is set.
    """

    def __init__(self, published, request):
        self.published = published
        self.request = request

    def __call__(self):
        return "1" if self.request.get("__cp") else "0"


@implementer(IETagValue)
@adapter(Interface, Interface)
class ResourceRegistries:
    """The ``resourceRegistries`` etag component, returning a timestamp.

    This is the last modified timestamp from the Plone 5+ Resource Registries.
    This is useful for avoiding requests for expired resources from cached pages.
    """

    def __init__(self, published, request):
        self.published = published
        self.request = request

    def __call__(self):
        if _RESOURCE_REGISTRY_MTIME is None:
            return ""
        registry = queryUtility(IRegistry)
        if registry is None:
            return ""
        mtime = getattr(registry, _RESOURCE_REGISTRY_MTIME, None)
        if mtime is None:
            return ""
        return str(mtime)


@implementer(IETagValue)
@adapter(Interface, Interface)
class Layout:
    """The 'layout' etag component, returning they layout of a content item."""

    def __init__(self, published, request):
        self.published = published
        self.request = request

    def __call__(self):
        context = getContext(self.published)
        if not safe_hasattr(aq_base(context), "getLayout"):
            return
        return context.getLayout()
