from zope.interface import implements
from zope.interface import classProvides
from zope.interface import Interface
from zope.component import adapts

from zope.publisher.interfaces.http import IHTTPRequest

from plone.caching.interfaces import IResponseMutator
from plone.caching.interfaces import IResponseMutatorType
from plone.caching.interfaces import ICacheInterceptor
from plone.caching.interfaces import ICacheInterceptorType
from plone.caching.utils import lookupOptions

from plone.app.caching.interfaces import _

class MaxAge(object):
    implements(IResponseMutator)
    adapts(Interface, IHTTPRequest)

    # Type metadata
    classProvides(IResponseMutatorType)

    title = _(u"Max age")
    description = _(u"Sets a fixed max age value")
    prefix = 'plone.app.caching.maxage'
    options = ('maxAge',)

    def __init__(self, published, request):
        self.published = published
        self.request = request
    
    def __call__(self, rulename, response):
        options = lookupOptions(self.__class__, rulename)
        maxAge = options['maxAge'] or 3600
        response.setHeader('Cache-Control', 'max-age=%s, must-revalidate' % maxAge)

class Always304(object):
    implements(ICacheInterceptor)
    adapts(Interface, IHTTPRequest)

    # Type metadata
    classProvides(ICacheInterceptorType)

    title = _(u"Always send 304")
    description = _(u"It's not modified, dammit!")
    prefix = 'plone.app.caching.always304'
    options = ('temporarilyDisable',)

    def __init__(self, published, request):
        self.published = published
        self.request = request
    
    def __call__(self, rulename, response):
        options = lookupOptions(self.__class__, rulename)
        if options['temporarilyDisable']:
            return None
        
        response.setStatus(304)
        return u""
