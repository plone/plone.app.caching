from zope.interface import implements
from zope.interface import Interface

from zope.component import adapts
from zope.component import queryUtility

from plone.registry.interfaces import IRegistry
from plone.transformchain.interfaces import ITransform

from plone.app.caching.interfaces import IPloneCacheSettings

class GZipTransform(object):
    """Transformation using plone.transformchain.
    
    This is registered at order 10000, i.e. "late", but before the caching 
    operation hook. A typical transform chain order may include:
    
    * lxml transforms (e.g. plone.app.blocks, collectivexdv) => 8000-8999
    * gzip => 10000
    * caching => 12000
    
    This transformer is uncommon in that it doesn't actually change the
    response body. Instead, we set a flag on the response to enable
    compression. This flag will take effect when plone.transformchain
    completes and sets the body back on the object.
    """
    
    implements(ITransform)
    adapts(Interface, Interface)
    
    order = 10000
    
    def __init__(self, published, request):
        self.published = published
        self.request = request
    
    def transformUnicode(self, result, encoding):
        self.setGzip()
        return None
    
    def transformBytes(self, result, encoding):
        self.setGzip()
        return None
    
    def transformIterable(self, result, encoding):
        self.setGzip()
        return None
    
    def setGzip(self):
        
        registry = queryUtility(IRegistry)
        if registry is None:
            return
        
        settings = registry.forInterface(IPloneCacheSettings, check=False)
        if settings.enableCompression:
            self.request.response.enableHTTPCompression(self.request)
