from zope.interface import implements
from zope.interface import Interface

from zope.component import adapts
from zope.annotation.interfaces import IAnnotations

from plone.transformchain.interfaces import ITransform

from plone.app.caching.interfaces import IRAMCached

from plone.app.caching.operations.utils import storeResponseInRAMCache

GLOBAL_KEY = 'plone.app.caching.operations.ramcache'

class Store(object):
    """Transform chain element which actually saves the page in RAM.

    This is registered for the ``IRAMCached`` request marker, which is set by
    the ``cacheInRAM()`` helper method. Thus, the transform is only used if
    the caching operation requested it.
    """

    implements(ITransform)
    adapts(Interface, Interface)

    order = 90000

    def __init__(self, published, request):
        self.published = published
        self.request = request

    def transformUnicode(self, result, encoding):
        if not IRAMCached.providedBy(self.request) or self.inError():
            return None

        storeResponseInRAMCache(self.request, self.request.response, result.encode(encoding))
        return None

    def transformBytes(self, result, encoding):
        if not IRAMCached.providedBy(self.request) or self.inError():
            return None

        storeResponseInRAMCache(self.request, self.request.response, result)
        return None

    def transformIterable(self, result, encoding):
        if not IRAMCached.providedBy(self.request) or self.inError():
            return None

        storeResponseInRAMCache(self.request, self.request.response,''.join(result))
        return None

    def inError(self):
        status = self.request.response.getStatus()
        annotations = IAnnotations(self.request.response, None)
        if annotations is None:
            error_status = None
        else:
            error_status = annotations['error_status']
        return status != 200 or error_status and error_status != 200
