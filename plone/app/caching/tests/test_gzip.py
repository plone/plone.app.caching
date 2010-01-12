import unittest
from StringIO import StringIO

import zope.component.testing

from zope.component import provideUtility, provideAdapter, getUtility

from plone.registry.interfaces import IRegistry

from plone.registry import Registry
from plone.registry.fieldfactory import persistentFieldAdapter

from plone.app.caching.interfaces import IPloneCacheSettings

from plone.app.caching.gzip import GZipTransform

from ZPublisher.HTTPRequest import HTTPRequest
from ZPublisher.HTTPResponse import HTTPResponse

class DummyPublished(object):
    pass

class TestGZip(unittest.TestCase):
    
    def setUp(self):
        provideAdapter(persistentFieldAdapter)
    
    def tearDown(self):
        zope.component.testing.tearDown()
    
    def test_no_registry(self):
        environ = {'SERVER_NAME': 'example.com', 'SERVER_PORT': '80'}
        response = HTTPResponse()
        request = HTTPRequest(StringIO(), environ, response)
        
        published = DummyPublished()
        GZipTransform(published, request).transformUnicode(u"", "utf-8")
        
        self.assertEquals(0, response.enableHTTPCompression(query=True))
        
    def test_disabled(self):
        provideUtility(Registry(), IRegistry)
        registry = getUtility(IRegistry)
        registry.registerInterface(IPloneCacheSettings)
        
        environ = {'SERVER_NAME': 'example.com', 'SERVER_PORT': '80'}
        response = HTTPResponse()
        request = HTTPRequest(StringIO(), environ, response)
        
        published = DummyPublished()
        GZipTransform(published, request).transformUnicode(u"", "utf-8")
        
        self.assertEquals(0, response.enableHTTPCompression(query=True))
    
    def test_enabled_not_accepted(self):
        provideUtility(Registry(), IRegistry)
        registry = getUtility(IRegistry)
        registry.registerInterface(IPloneCacheSettings)
        
        ploneSettings = registry.forInterface(IPloneCacheSettings)
        ploneSettings.enableCompression = True
        
        environ = {'SERVER_NAME': 'example.com', 'SERVER_PORT': '80'}
        response = HTTPResponse()
        request = HTTPRequest(StringIO(), environ, response)
        
        published = DummyPublished()
        GZipTransform(published, request).transformUnicode(u"", "utf-8")
        
        self.assertEquals(0, response.enableHTTPCompression(query=True))
    
    def test_enabled_accepted(self):
        provideUtility(Registry(), IRegistry)
        registry = getUtility(IRegistry)
        registry.registerInterface(IPloneCacheSettings)
        
        ploneSettings = registry.forInterface(IPloneCacheSettings)
        ploneSettings.enableCompression = True

        environ = {'SERVER_NAME': 'example.com', 'SERVER_PORT': '80', 'HTTP_ACCEPT_ENCODING': 'gzip'}
        response = HTTPResponse()
        request = HTTPRequest(StringIO(), environ, response)
        
        published = DummyPublished()
        GZipTransform(published, request).transformUnicode(u"", "utf-8")
        
        self.assertEquals(1, response.enableHTTPCompression(query=True)) 
    
def test_suite():
    return unittest.defaultTestLoader.loadTestsFromName(__name__)
