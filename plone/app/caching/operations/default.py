from zope.interface import implements
from zope.interface import classProvides
from zope.interface import Interface
from zope.component import adapts
from zope.component import getMultiAdapter

from zope.publisher.interfaces.http import IHTTPRequest

from plone.caching.interfaces import ICachingOperation
from plone.caching.interfaces import ICachingOperationType
from plone.caching.utils import lookupOptions

from plone.app.caching.operations.utils import doNotCache
from plone.app.caching.operations.utils import cacheInBrowser
from plone.app.caching.operations.utils import cacheInProxy
from plone.app.caching.operations.utils import cacheInBrowserAndProxy
from plone.app.caching.operations.utils import cacheInRAM

from plone.app.caching.operations.utils import cachedResponse
from plone.app.caching.operations.utils import notModified

from plone.app.caching.operations.utils import getETagAnnotation
from plone.app.caching.operations.utils import getContext
from plone.app.caching.operations.utils import getLastModifiedAnnotation

from plone.app.caching.operations.utils import fetchFromRAMCache
from plone.app.caching.operations.utils import isModified
from plone.app.caching.operations.utils import visibleToRole

from plone.app.caching.interfaces import _

try:
    from Products.ResourceRegistries.interfaces import ICookedFile
    from Products.ResourceRegistries.interfaces import IResourceRegistry
    HAVE_RESOURCE_REGISTRIES = True
except ImportError:
    HAVE_RESOURCE_REGISTRIES = False

class CompositeViews(object):
    implements(ICachingOperation)
    adapts(Interface, IHTTPRequest)

    # Type metadata
    classProvides(ICachingOperationType)

    title = _(u"Cache composite views")
    description = _(u"Composite views (content item views and templates) can "
                    u"include dependencies that are difficult to track in "
                    u"the general case, so we cache these in the browser but "
                    u"expire immediately and enable ETag validation checks. "
                    u"If anonymous, then also cache in memory in Zope")
    prefix = 'plone.app.caching.compositeviews'
    options = ('etags',)
    
    # Fallback option values
    etags = ('userid', 'catalogCounter', 'language', 'gzip', 'skin', 'locked')

    def __init__(self, published, request):
        self.published = published
        self.request = request
    
    def interceptResponse(self, rulename, response):
        options = lookupOptions(CompositeViews, rulename)
        etag = getETagAnnotation(self.published, self.request, options['etags'] or self.etags)
        
        if not isModified(self.request, etag=etag):
            return notModified(self.published, self.request, response, etag=etag)
        
        context = getContext(self.published)
        portal_state = getMultiAdapter((context, self.request), name=u'plone_portal_state')
        
        if portal_state.anonymous():
            cached = fetchFromRAMCache(self.request, etag=etag)
            if cached is not None:
                return cachedResponse(self.published, self.request, response, *cached)
        
        return None
    
    def modifyResponse(self, rulename, response):
        options = lookupOptions(CompositeViews, rulename)
        etag = getETagAnnotation(self.published, self.request, options['etags'] or self.etags)
        
        cacheInBrowser(self.published, self.request, response, etag=etag)
        
        context = getContext(self.published)
        portal_state = getMultiAdapter((context, self.request), name=u'plone_portal_state')
        
        if portal_state.anonymous():
            cacheInRAM(self.published, self.request, response, etag=etag)

class ContentFeeds(object):
    implements(ICachingOperation)
    adapts(Interface, IHTTPRequest)

    # Type metadata
    classProvides(ICachingOperationType)

    title = _(u"Cache content feeds")
    description = _(u"Content feeds can change so we cache these in the "
                    u"browser but expire immediately and enable ETag "
                    u"validation checks. If anonymous then also cache in "
                    u"memory in Zope")
    prefix = 'plone.app.caching.contentfeeds'
    options = ('etags',)
    
    # Fallback option values
    etags = ('userid', 'catalogCounter', 'language', 'gzip', 'skin')

    def __init__(self, published, request):
        self.published = published
        self.request = request
    
    def interceptResponse(self, rulename, response):
        options = lookupOptions(ContentFeeds, rulename)
        etag = getETagAnnotation(self.published, self.request, options['etags'] or self.etags)
        
        if not isModified(self.request, etag=etag):
            return notModified(self.published, self.request, response, etag=etag)
        
        context = getContext(self.published)
        portal_state = getMultiAdapter((context, self.request), name=u'plone_portal_state')
        
        if portal_state.anonymous():
            cached = fetchFromRAMCache(self.request, etag=etag)
            if cached is not None:
                return cachedResponse(self.published, self.request, response, *cached)
        
        return None
    
    def modifyResponse(self, rulename, response):
        options = lookupOptions(ContentFeeds, rulename)
        etag = getETagAnnotation(self.published, self.request, options['etags'] or self.etags)
        
        cacheInBrowser(self.published, self.request, response, etag=etag)
        
        context = getContext(self.published)
        portal_state = getMultiAdapter((context, self.request), name=u'plone_portal_state')
        
        if portal_state.anonymous():            
            cacheInRAM(self.published, self.request, response, etag=etag)

class ContentFeedsWithProxy(object):
    implements(ICachingOperation)
    adapts(Interface, IHTTPRequest)

    # Type metadata
    classProvides(ICachingOperationType)

    title = _(u"Cache content feeds with proxy")
    description = _(u"Content feeds can change so we cache these in the "
                    u"browser but expire immediately and enable ETag "
                    u"validation checks. If anonymous then also cache in "
                    u"Zope RAM.  We also cache in proxy for 'maxage' seconds "
                    u"(default 24 hours) since staleness is not critical in "
                    u"this case.")
    prefix = 'plone.app.caching.contentfeedswithproxy'
    options = ('etags', 'smaxage', 'vary')
    
    # Fallback option values
    etags = ('userid', 'catalogCounter', 'language', 'gzip', 'skin')
    smaxage = 86400
    vary = None

    def __init__(self, published, request):
        self.published = published
        self.request = request
    
    def interceptResponse(self, rulename, response):
        options = lookupOptions(ContentFeedsWithProxy, rulename)
        etag = getETagAnnotation(self.published, self.request, options['etags'] or self.etags)
        
        if not isModified(self.request, etag=etag):
            return notModified(self.published, self.request, response, etag=etag)
        
        context = getContext(self.published)
        portal_state = getMultiAdapter((context, self.request), name=u'plone_portal_state')
        
        if portal_state.anonymous():
            cached = fetchFromRAMCache(self.request, etag=etag)
            if cached is not None:
                return cachedResponse(self.published, self.request, response, *cached)
        
        return None
    
    def modifyResponse(self, rulename, response):
        options = lookupOptions(ContentFeedsWithProxy, rulename)
        etag = getETagAnnotation(self.published, self.request, options['etags'] or self.etags)
        smaxage = options['smaxage'] or self.smaxage
        vary = options['vary'] or self.vary
        
        context = getContext(self.published)
        portal_state = getMultiAdapter((context, self.request), name=u'plone_portal_state')
        
        if portal_state.anonymous():            
            cacheInProxy(self.published, self.request, response, smaxage=smaxage, etag=etag, vary=vary)
            cacheInRAM(self.published, self.request, response, etag=etag)
        else:
            cacheInBrowser(self.published, self.request, response, etag=etag)

class Downloads(object):
    implements(ICachingOperation)
    adapts(Interface, IHTTPRequest)

    # Type metadata
    classProvides(ICachingOperationType)

    title = _(u"Cache downloads")
    description = _(u"Downloads (like File and Image content items) can "
                    u"change so we cache these in the browser but expire "
                    u"immediately and enable Last-Modified validation checks")
    prefix = 'plone.app.caching.downloads'
    options = ()
    
    def __init__(self, published, request):
        self.published = published
        self.request = request
    
    def interceptResponse(self, rulename, response):
        lastModified = getLastModifiedAnnotation(self.published, self.request)
        if not isModified(self.request, lastModified=lastModified):
            return notModified(self.published, self.request, response, lastModified=lastModified)
        return None
    
    def modifyResponse(self, rulename, response):
        lastModified = getLastModifiedAnnotation(self.published, self.request)
        cacheInBrowser(self.published, self.request, response, lastModified=lastModified)

class DownloadsWithProxy(object):
    implements(ICachingOperation)
    adapts(Interface, IHTTPRequest)

    # Type metadata
    classProvides(ICachingOperationType)

    title = _(u"Cache downloads with proxy")
    description = _(u"Downloads (like File and Image content items) can "
                    u"change so we cache these in the browser but expire "
                    u"immediately and enable Last-Modified validation "
                    u"checks. We also cache in proxy for 'maxage' seconds "
                    u"since we can purge this cache if it changes (default "
                    u"maxage is 24 hours).")
    prefix = 'plone.app.caching.downloadswithproxy'
    options = ('smaxage','vary')
    
    # Fallback option values
    smaxage = 86400
    vary = None
    
    def __init__(self, published, request):
        self.published = published
        self.request = request
    
    def interceptResponse(self, rulename, response):
        lastModified = getLastModifiedAnnotation(self.published, self.request)
        if not isModified(self.request, lastModified=lastModified):
            return notModified(self.published, self.request, response, lastModified=lastModified)
        return None
    
    def modifyResponse(self, rulename, response):
        options = lookupOptions(DownloadsWithProxy, rulename)
        
        smaxage = options['smaxage'] or self.smaxage
        vary = options['vary'] or self.vary
        
        lastModified = getLastModifiedAnnotation(self.published, self.request)
        
        if visibleToRole(self.published, role='Anonymous'):
            cacheInProxy(self.published, self.request, response, 
                smaxage=smaxage, lastModified=lastModified, vary=vary)
        else:
            cacheInBrowser(self.published, self.request, response, lastModified=lastModified)

class Resources(object):
    implements(ICachingOperation)
    adapts(Interface, IHTTPRequest)

    # Type metadata
    classProvides(ICachingOperationType)

    title = _(u"Cache resources")
    description = _(u"Standard resources (like skin images and filesystem "
                    u"resources) don't change often so it's often safe to "
                    u"cache these everywhere for a short while (default "
                    u"maxage is 24 hours)""")
    prefix = 'plone.app.caching.resources'
    options = ('maxage','vary')
    
    # Fallback option values
    maxage = 86400
    vary = None

    def __init__(self, published, request):
        self.published = published
        self.request = request
    
    def interceptResponse(self, rulename, response):
        lastModified = getLastModifiedAnnotation(self.published, self.request)
        if not isModified(self.request, lastModified=lastModified):
            return notModified(self.published, self.request, response, 
                lastModified=lastModified)
        return None
    
    def modifyResponse(self, rulename, response):
        options = lookupOptions(Resources, rulename)
        
        maxage = options['maxage'] or self.maxage
        vary = options['vary'] or self.vary
        
        lastModified = getLastModifiedAnnotation(self.published, self.request)
        cacheInBrowserAndProxy(self.published, self.request, response, 
            maxage=maxage, lastModified=lastModified, vary=vary)

class StableResources(object):
    implements(ICachingOperation)
    adapts(Interface, IHTTPRequest)

    # Type metadata
    classProvides(ICachingOperationType)

    title = _(u"Cache stable resources")
    description = _(u"Stable resources (like ResourceRegistry-maintained "
                    u"css and js files) never change without changing their "
                    u"URL so it's safe to cache these 'forever' (maxage "
                    u"defaults to 1 year)")
    prefix = 'plone.app.caching.stableresources'
    options = ('maxage', 'etags', 'vary')
    
    # Fallback option values
    
    maxage = 31536000
    etags = ()
    vary = None

    def __init__(self, published, request):
        self.published = published
        self.request = request
    
    def interceptResponse(self, rulename, response):
        options = lookupOptions(StableResources, rulename)
        
        lastModified = getLastModifiedAnnotation(self.published, self.request)
        etag = getETagAnnotation(self.published, self.request, options['etags'] or self.etags)
        
        if not isModified(self.request, etag=etag, lastModified=lastModified):
            return notModified(self.published, self.request, response, 
                etag=etag, lastModified=lastModified)
        
        return None
    
    def modifyResponse(self, rulename, response):
        options = lookupOptions(StableResources, rulename)
        
        maxage = options['maxage'] or self.maxage
        etag = getETagAnnotation(self.published, self.request, options['etags'] or self.etags)
        vary = options['vary'] or self.vary
        
        lastModified = getLastModifiedAnnotation(self.published, self.request)
        cacheInBrowserAndProxy(self.published, self.request, response,
            maxage=maxage, etag=etag, lastModified=lastModified, vary=vary)

if HAVE_RESOURCE_REGISTRIES:

    class ResourceRegistriesStableResources(StableResources):
        """Override for StableResources which checks ResourceRegistries
        cacheability
        """
        
        adapts(ICookedFile, IHTTPRequest)

        def modifyResponse(self, rulename, response):
            registry = getContext(self.published, IResourceRegistry)
            
            if registry is not None:
                if registry.getDebugMode() or not registry.isCacheable(self.published.__name__):
                    doNotCache(self.published, self.request, response)
                    return
            
            super(ResourceRegistriesStableResources, self).__call__(rulename, response)
