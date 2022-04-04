from Acquisition import aq_base
from Acquisition import aq_inner
from plone.app.caching.interfaces import IETagValue
from plone.app.caching.operations.utils import getContext
from plone.app.caching.operations.utils import getLastModifiedAnnotation
from Products.CMFCore.interfaces import ICatalogTool
from Products.CMFCore.interfaces import IMembershipTool
from Products.CMFCore.utils import getToolByName
from Products.CMFPlone.utils import safe_hasattr
from zope.component import adapter
from zope.component import queryMultiAdapter
from zope.component import queryUtility
from zope.interface import implementer
from zope.interface import Interface


try:
    from Products.CMFPlone.resources.utils import get_override_directory
    from Products.CMFPlone.resources.utils import PRODUCTION_RESOURCE_DIRECTORY
except ImportError:
    # Plone < 6
    from Products.CMFPlone.resources.browser.combine import get_override_directory
    from Products.CMFPlone.resources.browser.combine import (
        PRODUCTION_RESOURCE_DIRECTORY,
    )

import random
import time


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
            return None

        member = tool.getAuthenticatedMember()
        if member is None:
            return None

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
            return None

        if bool(tool.isAnonymousUser()):
            return "Anonymous"

        member = tool.getAuthenticatedMember()
        if member is None:
            return None

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
            return None
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
            return None
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
            return None
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
        context_state = queryMultiAdapter(
            (context, self.request), name="plone_context_state"
        )
        if context_state is None:
            return None
        return "1" if context_state.is_locked() else "0"


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
            return None

        requestVariable = portal_skins.getRequestVarname()
        if requestVariable in self.request:
            return self.request[requestVariable]

        return portal_skins.getDefaultSkin()


@implementer(IETagValue)
@adapter(Interface, Interface)
class AnonymousOrRandom:
    """The ``anonymousOrRandom`` etag component. This is normally added
    implicitly by the ``anonOnly`` setting. It will return None for anonymous
    users, but a random number for logged-in ones. The idea is to force a
    re-fetch of a page every time for logged-in users.
    """

    def __init__(self, published, request):
        self.published = published
        self.request = request

    def __call__(self):
        tool = queryUtility(IMembershipTool)
        if tool is None:
            return None
        if bool(tool.isAnonymousUser()):
            return None
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
class ResourceRegistries(object):
    """The ``resourceRegistries`` etag component, returning a timestamp.

    This is the last modified timestamp from the Plone 5+ Resource Registries.
    This is useful for avoiding requests for expired resources from cached pages.
    """

    def __init__(self, published, request):
        self.published = published
        self.request = request

    def __call__(self):
        context = getContext(self.published)
        container = get_override_directory(context)
        if PRODUCTION_RESOURCE_DIRECTORY not in container:
            return ""
        production_folder = container[PRODUCTION_RESOURCE_DIRECTORY]
        filename = "timestamp.txt"
        if filename not in production_folder:
            return ""
        timestamp = production_folder.readFile(filename)
        if not timestamp:
            return ""
        # timestamp is in bytes, and we must return a string.
        # On Python 2 this is the same, but not on Python 3.
        if not isinstance(timestamp, str):
            timestamp = timestamp.decode("utf-8")
        return timestamp


@implementer(IETagValue)
@adapter(Interface, Interface)
class Layout(object):
    """The 'layout' etag component, returning they layout of a content item."""

    def __init__(self, published, request):
        self.published = published
        self.request = request

    def __call__(self):
        context = getContext(self.published)
        if not safe_hasattr(aq_base(context), "getLayout"):
            return
        return context.getLayout()
