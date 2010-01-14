from zope.interface import implements, classProvides, Interface
from zope.component import adapts

from zope.publisher.interfaces.http import IHTTPRequest

from plone.caching.interfaces import ICacheInterceptor
from plone.caching.interfaces import ICacheInterceptorType
from plone.caching.utils import lookupOptions

from plone.app.caching.interfaces import _

class Dummy(object):
    implements(ICacheInterceptor)
    adapts(Interface, IHTTPRequest)

    # Type metadata
    classProvides(ICacheInterceptorType)

    title = _(u"Some interceptor")
    description = _(u"Just an interceptor stub")
    prefix = 'plone.app.caching.dummy'
    # options = ('dummy',)

    def __init__(self, published, request):
        self.published = published
        self.request = request
    
    def __call__(self, rulename, response):
        options = lookupOptions(self.__class__, rulename)
        if options['dummy']:
            return None
        return None

