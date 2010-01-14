from zope.interface import implements
from zope.interface import classProvides
from zope.interface import Interface

from zope.component import adapts

from plone.transformchain.interfaces import ITransform

from plone.caching.interfaces import ICacheInterceptor
from plone.caching.interfaces import ICacheInterceptorType

from plone.app.caching.interfaces import _
from plone.app.caching.interfaces import IRAMCached

from plone.app.caching.operations.utils import fetchFromRAMCache
from plone.app.caching.operations.utils import cachedResponse
from plone.app.caching.operations.utils import storeResponseInRAMCache

GLOBAL_KEY = 'plone.app.caching.operations.pagecache'

class PageCache(object):
    """Caching interceptor which allows entire responses to be cached in
    RAM.
    """
    
    implements(ICacheInterceptor)
    adapts(Interface, Interface)
    
    # Type metadata
    classProvides(ICacheInterceptorType)
    
    title = _(u"Fetch from RAM cache")
    description = _(u"Allow a RAM-cached page to be fetched")
    prefix = GLOBAL_KEY
    options = ()
    
    def __init__(self, published, request):
        self.published = published
        self.request = request
        
    def __call__(self, rulename, response):
        
        cached = fetchFromRAMCache(self.published, self.request, response)
        if cached is None:
            return None
            
        return cachedResponse(self.published, self.request, response, cached)

class Store(object):
    """Transform chain element which actually saves the page in RAM.
    
    This is registered for the ``IRAMCached`` request marker, which is set by
    the interceptor above. Thus, the transform is only used if the interceptor
    requested it.
    """
    
    implements(ITransform)
    adapts(Interface, IRAMCached)
    
    order = 90000
    
    def __init__(self, published, request):
        self.published = published
        self.request = request
    
    def transformUnicode(self, result, encoding):
        status = self.request.response.getStatus()
        if status != 200:
            return None
        
        storeResponseInRAMCache(self.published, self.request, self.request.response, result.encode(encoding))
        return None
    
    def transformBytes(self, result, encoding):
        status = self.request.response.getStatus()
        if status != 200:
            return None
        
        storeResponseInRAMCache(self.published, self.request, self.request.response, result)
        return None
    
    def transformIterable(self, result, encoding):
        status = self.request.response.getStatus()
        if status != 200:
            return None
        
        storeResponseInRAMCache(self.published, self.request, self.request.response,''.join(result))
        return None
