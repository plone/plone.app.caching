# -*- coding: utf-8 -*-
from plone.app.caching.interfaces import IETagValue
from plone.app.caching.operations.utils import getContext
from plone.app.caching.operations.utils import getLastModifiedAnnotation
from Products.CMFCore.utils import getToolByName
from zope.component import adapter
from zope.component import queryMultiAdapter
from zope.interface import implementer
from zope.interface import Interface

import random
import time


@implementer(IETagValue)
@adapter(Interface, Interface)
class UserID(object):
    """The ``userid`` etag component, returning the current user's id
    """

    def __init__(self, published, request):
        self.published = published
        self.request = request

    def __call__(self):
        context = getContext(self.published)
        portal_state = queryMultiAdapter(
            (context, self.request), name=u'plone_portal_state')
        if portal_state is None:
            return None

        member = portal_state.member()
        if member is None:
            return None

        return member.getId()


@implementer(IETagValue)
@adapter(Interface, Interface)
class Roles(object):
    """The ``roles`` etag component, returning the current user's roles,
    separated by semicolons
    """

    def __init__(self, published, request):
        self.published = published
        self.request = request

    def __call__(self):
        context = getContext(self.published)
        portal_state = queryMultiAdapter(
            (context, self.request), name=u'plone_portal_state')
        if portal_state is None:
            return None

        if portal_state.anonymous():
            return 'Anonymous'

        member = portal_state.member()
        if member is None:
            return None

        return ';'.join(sorted(member.getRolesInContext(context)))


@implementer(IETagValue)
@adapter(Interface, Interface)
class Language(object):
    """The ``language`` etag component, returning the value of the
    HTTP_ACCEPT_LANGUAGE request key.
    """

    def __init__(self, published, request):
        self.published = published
        self.request = request

    def __call__(self):
        return self.request.get('HTTP_ACCEPT_LANGUAGE', '')


@implementer(IETagValue)
@adapter(Interface, Interface)
class UserLanguage(object):
    """The ``userLanguage`` etag component, returning the user's preferred
    language
    """

    def __init__(self, published, request):
        self.published = published
        self.request = request

    def __call__(self):
        context = getContext(self.published)
        portal_state = queryMultiAdapter(
            (context, self.request), name=u'plone_portal_state')
        if portal_state is None:
            return None

        return portal_state.language()


@implementer(IETagValue)
@adapter(Interface, Interface)
class LastModified(object):
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
class CatalogCounter(object):
    """The ``catalogCounter`` etag component, returning a counter which is
    incremented each time the catalog is updated.
    """

    def __init__(self, published, request):
        self.published = published
        self.request = request

    def __call__(self):
        context = getContext(self.published)
        tools = queryMultiAdapter((context, self.request), name=u'plone_tools')
        if tools is None:
            return None

        return str(tools.catalog().getCounter())


@implementer(IETagValue)
@adapter(Interface, Interface)
class ObjectLocked(object):
    """The ``locked`` etag component, returning 1 or 0 depending on whether
    the object is locked.
    """

    def __init__(self, published, request):
        self.published = published
        self.request = request

    def __call__(self):
        context = getContext(self.published)
        context_state = queryMultiAdapter(
            (context, self.request), name=u'plone_context_state')
        if context_state is None:
            return None
        return str(int(context_state.is_locked()))


@implementer(IETagValue)
@adapter(Interface, Interface)
class Skin(object):
    """The ``skin`` etag component, returning the current skin name.
    """

    def __init__(self, published, request):
        self.published = published
        self.request = request

    def __call__(self):
        context = getContext(self.published)

        portal_skins = getToolByName(context, 'portal_skins', None)
        if portal_skins is None:
            return None

        requestVariable = portal_skins.getRequestVarname()
        if requestVariable in self.request:
            return self.request[requestVariable]

        return portal_skins.getDefaultSkin()


@implementer(IETagValue)
@adapter(Interface, Interface)
class ResourceRegistries(object):
    """The ``resourceRegistries`` etag component, returning the most recent
    last modified timestamp from all three Resource Registries.  This is
    useful for avoiding requests for expired resources from cached pages.
    """

    def __init__(self, published, request):
        self.published = published
        self.request = request

    def __call__(self):
        context = getContext(self.published)

        registries = []
        registries.append(getToolByName(context, 'portal_css', None))
        registries.append(getToolByName(context, 'portal_javascripts', None))
        registries.append(getToolByName(context, 'portal_kss', None))

        mtimes = []
        now = time.time()
        for registry in registries:
            mtime = now
            if registry is not None:
                mtime = getattr(registry.aq_base, '_p_mtime', now)
                mtimes.append(mtime)

        mtimes.sort()
        return str(mtimes[-1])


@implementer(IETagValue)
@adapter(Interface, Interface)
class AnonymousOrRandom(object):
    """The ``anonymousOrRandom`` etag component. This is normally added
    implicitly by the ``anonOnly`` setting. It will return None for anonymous
    users, but a random number for logged-in ones. The idea is to force a
    re-fetch of a page every time for logged-in users.
    """

    def __init__(self, published, request):
        self.published = published
        self.request = request

    def __call__(self):
        context = getContext(self.published)
        portal_state = queryMultiAdapter(
            (context, self.request), name=u'plone_portal_state')
        if portal_state is None:
            return None
        if portal_state.anonymous():
            return None
        return '{0}{1}'.format(time.time(), random.randint(0, 1000))


@implementer(IETagValue)
@adapter(Interface, Interface)
class CopyCookie(object):
    """The ``copy`` etag component, returning 1 or 0 depending on whether
    the '__cp' cookie is set.
    """

    def __init__(self, published, request):
        self.published = published
        self.request = request

    def __call__(self):
        return self.request.get('__cp') and '1' or '0'
