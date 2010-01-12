import unittest
import zope.component.testing

from zope.interface import implements

from zope.component import getUtility
from zope.component import adapter
from zope.component import provideHandler
from zope.component import provideUtility
from zope.component import provideAdapter

from zope.component.event import objectEventNotify

from zope.event import notify

from zope.lifecycleevent import ObjectModifiedEvent
from zope.lifecycleevent import ObjectAddedEvent
from zope.lifecycleevent import ObjectRemovedEvent
from zope.lifecycleevent import ObjectMovedEvent

from plone.registry.interfaces import IRegistry
from plone.registry.fieldfactory import persistentFieldAdapter
from plone.registry import Registry

from plone.cachepurging.interfaces import IPurgeEvent

from plone.app.caching.interfaces import IPloneCacheSettings

from plone.app.caching.purge import purgeOnModified
from plone.app.caching.purge import purgeOnMovedOrRemoved

from Products.CMFCore.interfaces import IContentish

class Handler(object):
    
    def __init__(self):
        self.invocations = []
    
    @adapter(IPurgeEvent)
    def handler(self, event):
        self.invocations.append(event)

class FauxContainer(dict):
    pass

class FauxNonContent(object):
    implements(IContentish)
    
    def __init__(self, parent=None, name=None):
        self.__parent__ = parent
        self.__name__ = name

class FauxContent(object):
    implements(IContentish)
    
    portal_type = 'testtype'
    
    def __init__(self, parent=None, name=None):
        self.__parent__ = parent
        self.__name__ = name

class TestPurgeRedispatch(unittest.TestCase):
    
    def setUp(self):
        self.handler = Handler()
        provideHandler(self.handler.handler)
        
        provideHandler(objectEventNotify)
        provideHandler(purgeOnModified)
        provideHandler(purgeOnMovedOrRemoved)
        
        provideAdapter(persistentFieldAdapter)
        provideUtility(Registry(), IRegistry)
        registry = getUtility(IRegistry)
        registry.registerInterface(IPloneCacheSettings)
        
        ploneSettings = registry.forInterface(IPloneCacheSettings)
        ploneSettings.purgedContentTypes = ('testtype',)
    
    def tearDown(self):
        zope.component.testing.tearDown()

    def test_not_purged(self):
        context = FauxNonContent(FauxContainer(), 'new')
        
        notify(ObjectModifiedEvent(context))
        notify(ObjectAddedEvent(context))
        notify(ObjectRemovedEvent(context))
        
        self.assertEquals(0, len(self.handler.invocations))
    
    def test_modified(self):
        context = FauxContent()
        
        notify(ObjectModifiedEvent(context))
        
        self.assertEquals(1, len(self.handler.invocations))
        self.assertEquals(context, self.handler.invocations[0].object)
    
    def test_added(self):
        context = FauxContent(FauxContainer(), 'new')
        
        notify(ObjectAddedEvent(context, context.__parent__, 'new'))
        
        self.assertEquals(0, len(self.handler.invocations))
    
    def test_moved(self):
        context = FauxContent(FauxContainer(), 'new')
        
        notify(ObjectMovedEvent(context, FauxContainer(), 'old',
                                context.__parent__, 'new'))
        
        self.assertEquals(1, len(self.handler.invocations))
        self.assertEquals(context, self.handler.invocations[0].object)
    
    def test_renamed(self):
        context = FauxContent(FauxContainer(), 'new')
        
        notify(ObjectMovedEvent(context,
                                context.__parent__, 'old',
                                context.__parent__, 'new'))
        
        self.assertEquals(1, len(self.handler.invocations))
        self.assertEquals(context, self.handler.invocations[0].object)
    
    def test_removed(self):
        context = FauxContent(FauxContainer(), 'new')
        
        notify(ObjectRemovedEvent(context, context.__parent__, 'new'))
        
        self.assertEquals(1, len(self.handler.invocations))
        self.assertEquals(context, self.handler.invocations[0].object)
    
def test_suite():
    return unittest.defaultTestLoader.loadTestsFromName(__name__)


