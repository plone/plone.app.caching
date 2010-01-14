from zope.interface import implements
from zope.interface import classProvides
from zope.interface import alsoProvides
from zope.interface import Interface

from zope.component import adapts

from zope.annotation.interfaces import IAnnotations

from plone.transformchain.interfaces import ITransform

from plone.caching.interfaces import ICacheInterceptor
from plone.caching.interfaces import ICacheInterceptorType

from plone.app.caching.interfaces import _
from plone.app.caching.interfaces import IRAMCached

from plone.app.caching.operations.utils import getRAMCache

GLOBAL_KEY = 'plone.app.caching.operations.pagecache'

class PageCache(object):
    """Caching interceptor which allows entire responses to be cached in
    RAM.
    """
    
    implements(ICacheInterceptor)
    adapts(Interface, Interface)
    
    # Type metadata
    classProvides(ICacheInterceptorType)
    
    title = _(u"Cache in memory")
    description = _(u"Allows a page to be cached in memory")
    prefix = GLOBAL_KEY
    options = ()
    
    def __init__(self, published, request):
        self.published = published
        self.request = request
        
    def __call__(self, rulename, response):
        import pdb; pdb.set_trace( )
        
        key = self._getKey()
        if key is None:
            return None
        
        cache = getRAMCache(GLOBAL_KEY)
        if cache is None:
            return
        
        cached = cache.get(key)
        
        # We don't have a cached value - save the key and enable the transform
        # to cache later
        if cached is None:
            annotations = IAnnotations(self.request, None)
            if annotations is None:
                return None
            
            annotations[GLOBAL_KEY + '.key'] = key
            alsoProvides(self.request, IRAMCached)
        else:
            status, headers, body = cached
            self.request.response.setStatus(status)
            
            for k, v in headers.items():
                if k == 'ETag':
                    self.request.response.setHeader(k, v, literal=1)
                else:
                    self.request.response.setHeader(k, v)
            
            return body

    def _getKey(self):
        # TODO: This needs to be made a lot smarter
        #   - calculate an ETag and only set if one can be prepared
        #   - only cache if we have an ETag
        #   - only cache 200 responses
        
        return self.request.get('ACTUAL_URL')

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
        import pdb; pdb.set_trace( )
        status = self.request.response.getStatus()
        if status != 200:
            return
        
        self.cache(result.encode(encoding))
        return None
    
    def transformBytes(self, result, encoding):
        import pdb; pdb.set_trace( )
        status = self.request.response.getStatus()
        if status != 200:
            return
        
        self.cache(result)
        return None
    
    def transformIterable(self, result, encoding):
        import pdb; pdb.set_trace( )
        status = self.request.response.getStatus()
        if status != 200:
            return
        
        self.cache(''.join(result))
        return None
    
    def cache(self, result):
        
        annotations = IAnnotations(self.request, None)
        if annotations is None:
            return
        
        key = annotations.get(GLOBAL_KEY + '.key')
        if not key:
            return
        
        cache = getRAMCache(GLOBAL_KEY)
        if cache is None:
            return
        
        status = self.request.response.getStatus()
        headers = dict(self.request.response.headers)
                
        cache[key] = (status, headers, result)
