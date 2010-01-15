from StringIO import StringIO

import unittest
import zope.component.testing

from zope.interface import classImplements
from zope.component import provideAdapter

from zope.annotation.interfaces import IAnnotations
from zope.annotation.interfaces import IAttributeAnnotatable
from zope.annotation.attribute import AttributeAnnotations

import time
import datetime
import dateutil.parser
import dateutil.tz
import wsgiref.handlers

from ZPublisher.HTTPRequest import HTTPRequest
from ZPublisher.HTTPRequest import HTTPResponse

class DummyPublished(object):
    pass

class ResponseModificationHelpersTest(unittest.TestCase):
    
    def setUp(self):
        provideAdapter(AttributeAnnotations)
        classImplements(HTTPRequest, IAttributeAnnotatable)
    
    def tearDown(self):
        zope.component.testing.tearDown()
    
    # doNotCache()
    
    def test_doNotCache(self):
        from plone.app.caching.operations.utils import doNotCache
        
        environ = {'SERVER_NAME': 'example.com', 'SERVER_PORT': '80'}
        response = HTTPResponse()
        request = HTTPRequest(StringIO(), environ, response)
        published = DummyPublished()
        
        now = datetime.datetime.now(dateutil.tz.tzlocal())
        
        doNotCache(published, request, response)
        
        self.assertEquals(200, response.getStatus())
        self.assertEquals('max-age=0, must-revalidate, private', response.getHeader('Cache-Control'))
        self.assertEquals(None, response.getHeader('Last-Modified'))
        
        expires = dateutil.parser.parse(response.getHeader('Expires'))
        self.failUnless(now > expires)
    
    def test_doNotCache_deletes_last_modified(self):
        from plone.app.caching.operations.utils import doNotCache
        
        environ = {'SERVER_NAME': 'example.com', 'SERVER_PORT': '80'}
        response = HTTPResponse()
        request = HTTPRequest(StringIO(), environ, response)
        published = DummyPublished()
        
        now = datetime.datetime.now(dateutil.tz.tzlocal())
        response.setHeader('Last-Modified', wsgiref.handlers.format_date_time(time.mktime(now.timetuple())))
        
        now = datetime.datetime.now(dateutil.tz.tzlocal())
        
        doNotCache(published, request, response)
        
        self.assertEquals(200, response.getStatus())
        self.assertEquals('max-age=0, must-revalidate, private', response.getHeader('Cache-Control'))
        self.assertEquals(None, response.getHeader('Last-Modified'))
        
        expires = dateutil.parser.parse(response.getHeader('Expires'))
        self.failUnless(now > expires)
    
    # cacheInBrowser()
    
    def test_cacheInBrowser_no_etag_no_last_modified(self):
        from plone.app.caching.operations.utils import cacheInBrowser
        
        environ = {'SERVER_NAME': 'example.com', 'SERVER_PORT': '80'}
        response = HTTPResponse()
        request = HTTPRequest(StringIO(), environ, response)
        published = DummyPublished()
        
        now = datetime.datetime.now(dateutil.tz.tzlocal())
        
        cacheInBrowser(published, request, response)
        
        self.assertEquals(200, response.getStatus())
        self.assertEquals('max-age=0, must-revalidate, private', response.getHeader('Cache-Control'))
        self.assertEquals(None, response.getHeader('Last-Modified'))
        self.assertEquals(None, response.getHeader('ETag', literal=1))
        
        expires = dateutil.parser.parse(response.getHeader('Expires'))
        self.failUnless(now > expires)
    
    def test_cacheInBrowser_etag(self):
        from plone.app.caching.operations.utils import cacheInBrowser
        
        environ = {'SERVER_NAME': 'example.com', 'SERVER_PORT': '80'}
        response = HTTPResponse()
        request = HTTPRequest(StringIO(), environ, response)
        published = DummyPublished()
        
        now = datetime.datetime.now(dateutil.tz.tzlocal())
        etag = "|foo|bar|"
        
        cacheInBrowser(published, request, response, etag=etag)
        
        self.assertEquals(200, response.getStatus())
        self.assertEquals('max-age=0, must-revalidate, private', response.getHeader('Cache-Control'))
        self.assertEquals(None, response.getHeader('Last-Modified'))
        self.assertEquals("|foo|bar|", response.getHeader('ETag', literal=1))
        
        expires = dateutil.parser.parse(response.getHeader('Expires'))
        self.failUnless(now > expires)
    
    def test_cacheInBrowser_lastmodified(self):
        from plone.app.caching.operations.utils import cacheInBrowser
        
        environ = {'SERVER_NAME': 'example.com', 'SERVER_PORT': '80'}
        response = HTTPResponse()
        request = HTTPRequest(StringIO(), environ, response)
        published = DummyPublished()
        
        now = datetime.datetime.now(dateutil.tz.tzlocal())
        nowFormatted = wsgiref.handlers.format_date_time(time.mktime(now.timetuple()))
        
        cacheInBrowser(published, request, response, lastmodified=now)
        
        self.assertEquals(200, response.getStatus())
        self.assertEquals('max-age=0, must-revalidate, private', response.getHeader('Cache-Control'))
        self.assertEquals(nowFormatted, response.getHeader('Last-Modified'))
        self.assertEquals(None, response.getHeader('ETag', literal=1))
        
        expires = dateutil.parser.parse(response.getHeader('Expires'))
        self.failUnless(now > expires)
    
    def test_cacheInBrowser_lastmodified_and_etag(self):
        from plone.app.caching.operations.utils import cacheInBrowser
        
        environ = {'SERVER_NAME': 'example.com', 'SERVER_PORT': '80'}
        response = HTTPResponse()
        request = HTTPRequest(StringIO(), environ, response)
        published = DummyPublished()
        
        now = datetime.datetime.now(dateutil.tz.tzlocal())
        etag = "|foo|bar|"
        
        nowFormatted = wsgiref.handlers.format_date_time(time.mktime(now.timetuple()))
        
        cacheInBrowser(published, request, response, etag=etag, lastmodified=now)
        
        self.assertEquals(200, response.getStatus())
        self.assertEquals('max-age=0, must-revalidate, private', response.getHeader('Cache-Control'))
        self.assertEquals(nowFormatted, response.getHeader('Last-Modified'))
        self.assertEquals("|foo|bar|", response.getHeader('ETag', literal=1))
        
        expires = dateutil.parser.parse(response.getHeader('Expires'))
        self.failUnless(now > expires)
    
    # cacheInProxy()
    
    def test_cacheInProxy_minimal(self):
        from plone.app.caching.operations.utils import cacheInProxy
        
        environ = {'SERVER_NAME': 'example.com', 'SERVER_PORT': '80'}
        response = HTTPResponse()
        request = HTTPRequest(StringIO(), environ, response)
        published = DummyPublished()
        
        now = datetime.datetime.now(dateutil.tz.tzlocal())
        
        cacheInProxy(published, request, response, smaxage=60)
        
        self.assertEquals(200, response.getStatus())
        self.assertEquals('max-age=0, s-maxage=60, must-revalidate', response.getHeader('Cache-Control'))
        self.assertEquals(None, response.getHeader('Last-Modified'))
        self.assertEquals(None, response.getHeader('ETag', literal=1))
        self.assertEquals(None, response.getHeader('Vary'))
        
        expires = dateutil.parser.parse(response.getHeader('Expires'))
        self.failUnless(now > expires)
    
    def test_cacheInProxy_full(self):
        from plone.app.caching.operations.utils import cacheInProxy
        
        environ = {'SERVER_NAME': 'example.com', 'SERVER_PORT': '80'}
        response = HTTPResponse()
        request = HTTPRequest(StringIO(), environ, response)
        published = DummyPublished()
        
        now = datetime.datetime.now(dateutil.tz.tzlocal())
        etag = '|foo|bar|'
        vary = 'Accept-Language'
        
        nowFormatted = wsgiref.handlers.format_date_time(time.mktime(now.timetuple()))
        
        cacheInProxy(published, request, response, smaxage=60, etag=etag, lastmodified=now, vary=vary)
        
        self.assertEquals(200, response.getStatus())
        self.assertEquals('max-age=0, s-maxage=60, must-revalidate', response.getHeader('Cache-Control'))
        self.assertEquals(nowFormatted, response.getHeader('Last-Modified'))
        self.assertEquals('|foo|bar|', response.getHeader('ETag', literal=1))
        self.assertEquals('Accept-Language', response.getHeader('Vary'))
        
        expires = dateutil.parser.parse(response.getHeader('Expires'))
        self.failUnless(now > expires)
    
    # cacheInBrowserAndProxy()
    
    def test_cacheInBrowserAndProxy_minimal(self):
        from plone.app.caching.operations.utils import cacheInBrowserAndProxy
        
        environ = {'SERVER_NAME': 'example.com', 'SERVER_PORT': '80'}
        response = HTTPResponse()
        request = HTTPRequest(StringIO(), environ, response)
        published = DummyPublished()
        
        now = datetime.datetime.now(dateutil.tz.tzlocal())
        
        cacheInBrowserAndProxy(published, request, response, maxage=60)
        
        self.assertEquals(200, response.getStatus())
        self.assertEquals('max-age=60, must-revalidate, public', response.getHeader('Cache-Control'))
        self.assertEquals(None, response.getHeader('Last-Modified'))
        self.assertEquals(None, response.getHeader('ETag', literal=1))
        self.assertEquals(None, response.getHeader('Vary'))
        
        expires = dateutil.parser.parse(response.getHeader('Expires'))
        self.failUnless(now > expires)
    
    def test_cacheInBrowserAndProxy_full(self):
        from plone.app.caching.operations.utils import cacheInBrowserAndProxy
        
        environ = {'SERVER_NAME': 'example.com', 'SERVER_PORT': '80'}
        response = HTTPResponse()
        request = HTTPRequest(StringIO(), environ, response)
        published = DummyPublished()
        
        now = datetime.datetime.now(dateutil.tz.tzlocal())
        etag = '|foo|bar|'
        vary = 'Accept-Language'
        
        nowFormatted = wsgiref.handlers.format_date_time(time.mktime(now.timetuple()))
        
        cacheInBrowserAndProxy(published, request, response, maxage=60, etag=etag, lastmodified=now, vary=vary)
        
        self.assertEquals(200, response.getStatus())
        self.assertEquals('max-age=60, must-revalidate, public', response.getHeader('Cache-Control'))
        self.assertEquals(nowFormatted, response.getHeader('Last-Modified'))
        self.assertEquals('|foo|bar|', response.getHeader('ETag', literal=1))
        self.assertEquals('Accept-Language', response.getHeader('Vary'))
        
        expires = dateutil.parser.parse(response.getHeader('Expires'))
        self.failUnless(now > expires)
    
    # cacheInRAM()
    
    def test_cacheInRAM_no_etag(self):
        from plone.app.caching.operations.utils import cacheInRAM
        from plone.app.caching.operations.utils import PAGE_CACHE_ANNOTATION_KEY
        
        from plone.app.caching.interfaces import IRAMCached
        
        environ = {'SERVER_NAME': 'example.com', 'SERVER_PORT': '80'}
        response = HTTPResponse()
        request = HTTPRequest(StringIO(), environ, response)
        published = DummyPublished()
        
        request.environ['PATH_INFO'] = '/foo'
        
        assert not IRAMCached.providedBy(response)
        
        cacheInRAM(published, request, response)
        
        annotations = IAnnotations(request)
        self.assertEquals("/foo?", annotations[PAGE_CACHE_ANNOTATION_KEY])
        self.failUnless(IRAMCached.providedBy(request))
    
    def test_cacheInRAM_etag(self):
        from plone.app.caching.operations.utils import cacheInRAM
        from plone.app.caching.operations.utils import PAGE_CACHE_ANNOTATION_KEY
        
        from plone.app.caching.interfaces import IRAMCached
        
        environ = {'SERVER_NAME': 'example.com', 'SERVER_PORT': '80'}
        response = HTTPResponse()
        request = HTTPRequest(StringIO(), environ, response)
        published = DummyPublished()
        
        request.environ['PATH_INFO'] = '/foo'
        etag = '|foo|bar|'
        
        assert not IRAMCached.providedBy(response)
        
        cacheInRAM(published, request, response, etag=etag)
        
        annotations = IAnnotations(request)
        self.assertEquals("|foo|bar|||/foo?", annotations[PAGE_CACHE_ANNOTATION_KEY])
        self.failUnless(IRAMCached.providedBy(request))
    
    def test_cacheInRAM_etag_alternate_key(self):
        from plone.app.caching.operations.utils import cacheInRAM
        
        from plone.app.caching.interfaces import IRAMCached
        
        environ = {'SERVER_NAME': 'example.com', 'SERVER_PORT': '80'}
        response = HTTPResponse()
        request = HTTPRequest(StringIO(), environ, response)
        published = DummyPublished()
        
        request.environ['PATH_INFO'] = '/foo'
        etag = '|foo|bar|'
        
        assert not IRAMCached.providedBy(response)
        
        cacheInRAM(published, request, response, etag=etag, annotationsKey="alt.key")
        
        annotations = IAnnotations(request)
        self.assertEquals("|foo|bar|||/foo?", annotations["alt.key"])
        self.failUnless(IRAMCached.providedBy(request))

class ResponseInterceptorHelpersTest(unittest.TestCase):
    
    def setUp(self):
        provideAdapter(AttributeAnnotations)
        classImplements(HTTPRequest, IAttributeAnnotatable)
    
    def tearDown(self):
        zope.component.testing.tearDown()
    
    # cachedResponse()
    
    def test_cachedResponse(self):
        from plone.app.caching.operations.utils import cachedResponse
        
        environ = {'SERVER_NAME': 'example.com', 'SERVER_PORT': '80'}
        response = HTTPResponse()
        request = HTTPRequest(StringIO(), environ, response)
        published = DummyPublished()
        
        headers = {
            'X-Cache-Rule': 'foo',
            'X-Foo': 'bar',
            'ETag': '||blah||',
        }
        
        response.setHeader('X-Foo', 'baz')
        response.setHeader('X-Bar', 'qux')
        response.setStatus(200)
        
        body = cachedResponse(published, request, response, 404, headers, u"body")
        
        self.assertEquals(u"body", body)
        self.assertEquals(404, response.getStatus())
        self.assertEquals('foo', response.getHeader('X-Cache-Rule'))
        self.assertEquals('bar', response.getHeader('X-Foo'))
        self.assertEquals('qux', response.getHeader('X-Bar'))
        self.assertEquals('||blah||', response.getHeader('ETag', literal=1))
    
    # notModified()
    
    def test_notModified_minimal(self):
        from plone.app.caching.operations.utils import notModified
        
        environ = {'SERVER_NAME': 'example.com', 'SERVER_PORT': '80'}
        response = HTTPResponse()
        request = HTTPRequest(StringIO(), environ, response)
        published = DummyPublished()
        
        response.setStatus(200)
        
        body = notModified(published, request, response)
        
        self.assertEquals(u"", body)
        self.assertEquals(304, response.getStatus())
    
    def test_notModified_full(self):
        from plone.app.caching.operations.utils import notModified
        
        environ = {'SERVER_NAME': 'example.com', 'SERVER_PORT': '80'}
        response = HTTPResponse()
        request = HTTPRequest(StringIO(), environ, response)
        published = DummyPublished()
        
        response.setStatus(200)
        
        now = datetime.datetime.now(dateutil.tz.tzlocal())
        etag = "|foo|bar|"
        
        nowFormatted = wsgiref.handlers.format_date_time(time.mktime(now.timetuple()))
        
        body = notModified(published, request, response, etag=etag, lastmodified=now)
        
        self.assertEquals(u"", body)
        self.assertEquals(etag, response.getHeader('ETag', literal=1))
        self.assertEquals(nowFormatted, response.getHeader('Last-Modified'))
        self.assertEquals(304, response.getStatus())
    
def test_suite():
    return unittest.defaultTestLoader.loadTestsFromName(__name__)
