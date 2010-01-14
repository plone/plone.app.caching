from AccessControl.PermissionRole import rolesForPermissionOn

from zope.interface import implements
from zope.interface import classProvides
from zope.interface import Interface
from zope.component import adapts
from zope.component import queryMultiAdapter
from zope.component import getMultiAdapter

from zope.publisher.interfaces.http import IHTTPRequest

from z3c.caching.interfaces import ILastModified

from plone.caching.interfaces import IResponseMutator
from plone.caching.interfaces import IResponseMutatorType
from plone.caching.utils import lookupOptions

from plone.app.caching.operations.utils import doNotCache
from plone.app.caching.operations.utils import cacheInBrowser
from plone.app.caching.operations.utils import cacheInProxy
from plone.app.caching.operations.utils import cacheEverywhere
from plone.app.caching.operations.utils import cacheInRAM
from plone.app.caching.operations.utils import getEtag
from plone.app.caching.interfaces import _

class CompositeViews(object):
    implements(IResponseMutator)
    adapts(Interface, IHTTPRequest)

    # Type metadata
    classProvides(IResponseMutatorType)

    title = _(u"Cache composite views")
    description = _(u"""Composite views (content item views and templates) can
        include dependencies that are difficult to track in the general case so
        we cache these in the browser but expire immediately and enable ETag 
        validation checks. If anonymous then also cache in Zope RAM""")
    prefix = 'plone.app.caching.compositeviews'
    options = ('etags',)
    etags = ('member','catalog_modified','language','gzip','skin','object_locked')

    def __init__(self, published, request):
        self.published = published
        self.request = request
    
    def __call__(self, rulename, response):
        portal_state = getMultiAdapter((self.published, self.request), name=u'plone_portal_state')
        options = lookupOptions(self.__class__, rulename)
        etag = getEtag(self.published, self.request, options['etags'] or etags)
        cacheInBrowser(response, etag=etag)
        if portal_state.anonymous():            
            cacheInRAM(response, etag)

class ContentFeeds(object):
    implements(IResponseMutator)
    adapts(Interface, IHTTPRequest)

    # Type metadata
    classProvides(IResponseMutatorType)

    title = _(u"Cache content feeds")
    description = _(u"""Content feeds can change so we cache these in the 
        browser but expire immediately and enable ETag validation checks. 
        If anonymous then also cache in Zope RAM""")
    prefix = 'plone.app.caching.contentfeeds'
    options = ('etags',)
    etags = ('member','catalog_modified','language','gzip','skin')

    def __init__(self, published, request):
        self.published = published
        self.request = request
    
    def __call__(self, rulename, response):
        portal_state = getMultiAdapter((self.published, self.request), name=u'plone_portal_state')
        options = lookupOptions(self.__class__, rulename)
        etag = getEtag(self.published, self.request, options['etags'] or etags)
        cacheInBrowser(response, etag=etag)
        if portal_state.anonymous():            
            cacheInRAM(response, etag)

class ContentFeedsWithProxy(object):
    implements(IResponseMutator)
    adapts(Interface, IHTTPRequest)

    # Type metadata
    classProvides(IResponseMutatorType)

    title = _(u"Cache content feeds with proxy")
    description = _(u"""Content feeds can change so we cache these in the 
        browser but expire immediately and enable ETag validation checks. 
        If anonymous then also cache in Zope RAM.  We also cache in proxy 
        for 'maxage' seconds (default 24 hours) since staleness is not 
        critical in this case.""")
    prefix = 'plone.app.caching.contentfeedswithproxy'
    options = ('etags','s-maxage','vary')
    etags = ('member','catalog_modified','language','gzip','skin')
    smaxage = 86400

    def __init__(self, published, request):
        self.published = published
        self.request = request
    
    def __call__(self, rulename, response):
        portal_state = getMultiAdapter((self.published, self.request), name=u'plone_portal_state')
        options = lookupOptions(self.__class__, rulename)
        etag = getEtag(self.published, self.request, options['etags'] or etags)
        smaxage = options['s-maxage'] or smaxage
        vary = options['vary']
        if portal_state.anonymous():            
            cacheInProxy(response, smaxage, etag=etag, vary=vary)
            cacheInRAM(response, etag)
        else:
            cacheInBrowser(response, etag=etag)

class Downloads(object):
    implements(IResponseMutator)
    adapts(Interface, IHTTPRequest)

    # Type metadata
    classProvides(IResponseMutatorType)

    title = _(u"Cache downloads")
    description = _(u"""Downloads (like File and Image content items) can 
        change so we cache these in the browser but expire immediately and 
        enable Last-Modified validation checks""")
    prefix = 'plone.app.caching.downloads'

    def __init__(self, published, request):
        self.published = published
        self.request = request
    
    def __call__(self, rulename, response):
        if 'Anonymous' in rolesForPermissionOn('View', self.published):
            lastmodified = ILastModified(self.published)()
            cacheInBrowser(response, lastmodified=lastmodified)
        else:
            doNotCache(response)

class DownloadsWithProxy(object):
    implements(IResponseMutator)
    adapts(Interface, IHTTPRequest)

    # Type metadata
    classProvides(IResponseMutatorType)

    title = _(u"Cache downloads with proxy")
    description = _(u"""Downloads (like File and Image content items) can 
        change so we cache these in the browser but expire immediately and 
        enable Last-Modified validation checks. We also cache in proxy for 
        'maxage' seconds since we can purge this cache if it changes 
        (default maxage is 24 hours).""")
    prefix = 'plone.app.caching.downloadswithproxy'
    options = ('s-maxage','vary')
    smaxage = 86400

    def __init__(self, published, request):
        self.published = published
        self.request = request
    
    def __call__(self, rulename, response):
        if 'Anonymous' in rolesForPermissionOn('View', self.published):
            options = lookupOptions(self.__class__, rulename)
            smaxage = options['smaxage'] or smaxage
            vary = options['vary']
            lastmodified = ILastModified(self.published)()
            cacheInProxy(response, smaxage, lastmodified=lastmodified, vary=vary)
        else:
            doNotCache(response)
    
class Resources(object):
    implements(IResponseMutator)
    adapts(Interface, IHTTPRequest)

    # Type metadata
    classProvides(IResponseMutatorType)

    title = _(u"Cache resources")
    description = _(u"""Standard resources (like skin images and 
        Zope 3 resources) don't change often so it's often safe to cache 
        these everywhere for a short while (default maxage is 24 hours)""")
    prefix = 'plone.app.caching.resources'
    options = ('max-age','vary')
    maxage = 86400

    def __init__(self, published, request):
        self.published = published
        self.request = request
    
    def __call__(self, rulename, response):
        options = lookupOptions(self.__class__, rulename)
        maxage = options['max-age'] or maxage
        vary = options['vary']
        lastmodified = ILastModified(self.published)()
        cacheEverywhere(response, maxage, lastmodified=lastmodified, vary=vary)

class StableResources(object):
    implements(IResponseMutator)
    adapts(Interface, IHTTPRequest)

    # Type metadata
    classProvides(IResponseMutatorType)

    title = _(u"Cache stable resources")
    description = _(u"""Stable resources (like ResourceRegistry-maintained 
        css and js files) never change without changing their URL so it's safe
        to cache these forever (maxage defaults to 1 year)""")
    prefix = 'plone.app.caching.stableresources'
    options = ('max-age','etags','vary')
    maxage = 31536000

    def __init__(self, published, request):
        self.published = published
        self.request = request
    
    def __call__(self, rulename, response):
        rr = None  # XXX get the Resource Registry for this item or return None if this is a non-RR item
        if rr is None or (rr.isCacheable(self.published.getId()) and not rr.getDebugMode()):
            options = lookupOptions(self.__class__, rulename)
            maxage = options['max-age'] or maxage
            etag = getEtag(self.published, self.request, options['etags'])
            vary = options['vary']
            lastmodified = ILastModified(self.published)()
            cacheEverywhere(response, maxage, lastmodified=lastmodified, etag=etag, vary=vary)
        else:
            doNotCache(response)

