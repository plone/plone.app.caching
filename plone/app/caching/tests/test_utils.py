import unittest

import zope.component.testing

from zope.component import provideUtility, provideAdapter, getUtility

from plone.registry.interfaces import IRegistry

from plone.registry import Registry
from plone.registry.fieldfactory import persistentFieldAdapter

from plone.app.caching.interfaces import IPloneCacheSettings

from plone.app.caching.utils import isPurged

class FauxContentObject(object):
    portal_type = 'testtype'

class NotContentObject(object):
    pass

class TestIsPurged(unittest.TestCase):
    
    def setUp(self):
        provideAdapter(persistentFieldAdapter)
    
    def tearDown(self):
        zope.component.testing.tearDown()
    
    def test_no_registry(self):
        content = FauxContentObject()
        self.assertEquals(False, isPurged(content))
        
    def test_no_settings(self):
        provideUtility(Registry(), IRegistry)
        content = FauxContentObject()
        self.assertEquals(False, isPurged(content))
    
    def test_no_portal_type(self):
        provideUtility(Registry(), IRegistry)
        registry = getUtility(IRegistry)
        registry.registerInterface(IPloneCacheSettings)
        
        ploneSettings = registry.forInterface(IPloneCacheSettings)
        ploneSettings.purgedContentTypes = ('testtype',)
        
        content = NotContentObject()
        self.assertEquals(False, isPurged(content))
    
    def test_not_listed(self):
        provideUtility(Registry(), IRegistry)
        registry = getUtility(IRegistry)
        registry.registerInterface(IPloneCacheSettings)
        
        ploneSettings = registry.forInterface(IPloneCacheSettings)
        ploneSettings.purgedContentTypes = ('File', 'Image',)
        
        content = FauxContentObject()
        self.assertEquals(False, isPurged(content))
    
    def test_listed(self):
        provideUtility(Registry(), IRegistry)
        registry = getUtility(IRegistry)
        registry.registerInterface(IPloneCacheSettings)
        
        ploneSettings = registry.forInterface(IPloneCacheSettings)
        ploneSettings.purgedContentTypes = ('File', 'Image', 'testtype',)
        
        content = FauxContentObject()
        self.assertEquals(True, isPurged(content))
    
def test_suite():
    return unittest.defaultTestLoader.loadTestsFromName(__name__)
