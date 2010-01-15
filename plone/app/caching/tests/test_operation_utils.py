import unittest
import zope.component.testing

import time
import datetime
import dateutil.parser
import dateutil.tz
import wsgiref.handlers
from StringIO import StringIO

from zope.interface import implements
from zope.interface import Interface
from zope.interface import classImplements
from zope.interface import alsoProvides

from zope.component import provideAdapter
from zope.component import adapts

from z3c.caching.interfaces import ILastModified

from zope.annotation.interfaces import IAnnotations
from zope.annotation.interfaces import IAttributeAnnotatable
from zope.annotation.attribute import AttributeAnnotations

from ZPublisher.HTTPRequest import HTTPRequest
from ZPublisher.HTTPRequest import HTTPResponse

from OFS.SimpleItem import SimpleItem

from Products.CMFCore.interfaces import IContentish

class DummyPublished(object):
    
    def __init__(self, parent=None):
        self.__parent__ = parent

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
    
    def test_cacheInBrowser_lastModified(self):
        from plone.app.caching.operations.utils import cacheInBrowser
        
        environ = {'SERVER_NAME': 'example.com', 'SERVER_PORT': '80'}
        response = HTTPResponse()
        request = HTTPRequest(StringIO(), environ, response)
        published = DummyPublished()
        
        now = datetime.datetime.now(dateutil.tz.tzlocal())
        nowFormatted = wsgiref.handlers.format_date_time(time.mktime(now.timetuple()))
        
        cacheInBrowser(published, request, response, lastModified=now)
        
        self.assertEquals(200, response.getStatus())
        self.assertEquals('max-age=0, must-revalidate, private', response.getHeader('Cache-Control'))
        self.assertEquals(nowFormatted, response.getHeader('Last-Modified'))
        self.assertEquals(None, response.getHeader('ETag', literal=1))
        
        expires = dateutil.parser.parse(response.getHeader('Expires'))
        self.failUnless(now > expires)
    
    def test_cacheInBrowser_lastModified_and_etag(self):
        from plone.app.caching.operations.utils import cacheInBrowser
        
        environ = {'SERVER_NAME': 'example.com', 'SERVER_PORT': '80'}
        response = HTTPResponse()
        request = HTTPRequest(StringIO(), environ, response)
        published = DummyPublished()
        
        now = datetime.datetime.now(dateutil.tz.tzlocal())
        etag = "|foo|bar|"
        
        nowFormatted = wsgiref.handlers.format_date_time(time.mktime(now.timetuple()))
        
        cacheInBrowser(published, request, response, etag=etag, lastModified=now)
        
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
        
        cacheInProxy(published, request, response, smaxage=60, etag=etag, lastModified=now, vary=vary)
        
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
        
        cacheInBrowserAndProxy(published, request, response, maxage=60, etag=etag, lastModified=now, vary=vary)
        
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
        
        body = notModified(published, request, response, etag=etag, lastModified=now)
        
        self.assertEquals(u"", body)
        self.assertEquals(etag, response.getHeader('ETag', literal=1))
        self.assertEquals(nowFormatted, response.getHeader('Last-Modified'))
        self.assertEquals(304, response.getStatus())

class CacheCheckHelpersTest(unittest.TestCase):
    
    def setUp(self):
        provideAdapter(AttributeAnnotations)
        classImplements(HTTPRequest, IAttributeAnnotatable)
    
    def tearDown(self):
        zope.component.testing.tearDown()

    # isModified()
    
    def test_isModified_minimal(self):
        pass

    def test_isModified_full(self):
        pass
    
    # visibleToRole()
    
    def test_visibleToRole_not_real(self):
        from plone.app.caching.operations.utils import visibleToRole
        published = DummyPublished()
        self.assertEquals(False, visibleToRole(published, role='Anonymous'))
    
    def test_visibleToRole_permission(self):
        from plone.app.caching.operations.utils import visibleToRole
        
        s = SimpleItem()
        
        s.manage_permission('View', ('Member', 'Manager',))
        self.assertEquals(False, visibleToRole(s, role='Anonymous'))
        
        s.manage_permission('View', ('Member', 'Manager', 'Anonymous',))
        self.assertEquals(True, visibleToRole(s, role='Anonymous'))
    
    # fetchFromRAMCache()
    
    def test_fetchFromRAMCache_minimal(self):
        pass
    
    def test_fetchFromRAMCache_full(self):
        pass

class MiscHelpersTest(unittest.TestCase):
    
    def setUp(self):
        provideAdapter(AttributeAnnotations)
        classImplements(HTTPRequest, IAttributeAnnotatable)
    
    def tearDown(self):
        zope.component.testing.tearDown()
    
    # getContext()
    
    def test_getContext(self):
        from plone.app.caching.operations.utils import getContext
        
        class Parent(object):
            implements(IContentish)
        
        parent = Parent()
        published = DummyPublished(parent)
        
        self.failUnless(getContext(parent) is parent)
        self.failUnless(getContext(published) is parent)
        
    def test_getContext_custom_marker(self):
        from plone.app.caching.operations.utils import getContext
        
        class Parent(object):
            implements(IContentish)
            
            def __init__(self, parent=None):
                self.__parent__ = parent
        
        class IDummy(Interface):
            pass
        
        grandparent = Parent()
        parent = Parent(grandparent)
        published = DummyPublished(parent)
        
        self.failUnless(getContext(published, marker=IDummy) is None)
        self.failUnless(getContext(published, marker=(IDummy,)) is None)
        
        alsoProvides(grandparent, IDummy)
        
        self.failUnless(getContext(parent, marker=IDummy) is grandparent)
        self.failUnless(getContext(published, marker=(IDummy,)) is grandparent)
    
    # formatDateTime()
    
    def test_formatDateTime_utc(self):
        from plone.app.caching.operations.utils import formatDateTime
        
        dt = datetime.datetime(2010, 11, 24, 3, 4, 5, 6, dateutil.tz.tzutc())
        self.assertEquals('Wed, 24 Nov 2010 03:04:05 GMT', formatDateTime(dt))
    
    def test_formatDateTime_local(self):
        from plone.app.caching.operations.utils import formatDateTime
        
        dt = datetime.datetime(2010, 11, 24, 3, 4, 5, 6, dateutil.tz.tzlocal())
        self.assertEquals('Tue, 23 Nov 2010 19:04:05 GMT', formatDateTime(dt))
    
    def test_formatDateTime_naive(self):
        from plone.app.caching.operations.utils import formatDateTime
        
        dt = datetime.datetime(2010, 11, 24, 3, 4, 5, 6)
        inGMT = formatDateTime(dt)
        
        # Who knows what your local timezone is :-)
        self.failUnless('Nov 2010' in inGMT)
        
        # Can't compare offset aware and naive
        p = dateutil.parser.parse(inGMT).astimezone(dateutil.tz.tzlocal())
        self.assertEquals((2010, 11, 24, 3, 4, 5), (p.year, p.month, p.day, p.hour, p.minute, p.second))
    
    
    # parseDateTime()
    
    def test_parseDateTime_invalid(self):
        from plone.app.caching.operations.utils import parseDateTime
        
        self.assertEquals(None, parseDateTime("foo"))
    
    def test_parseDateTime_rfc1123(self):
        from plone.app.caching.operations.utils import parseDateTime
        
        dt = datetime.datetime(2010, 11, 24, 3, 4, 5, 0, dateutil.tz.tzlocal())
        self.assertEquals(dt, parseDateTime("'Tue, 23 Nov 2010 19:04:05 GMT'"))
    
    def test_formatDateTime_no_timezone(self):
        from plone.app.caching.operations.utils import parseDateTime
        
        # parser will assume input was local time
        dt = datetime.datetime(2010, 11, 23, 19, 4, 5, 0, dateutil.tz.tzlocal())
        self.assertEquals(dt, parseDateTime("'Tue, 23 Nov 2010 19:04:05'"))
    
    
    # getLastModified()
    
    def test_getLastModified_no_adaper(self):
        from plone.app.caching.operations.utils import getLastModified
        
        published = DummyPublished()
        self.assertEquals(None, getLastModified(published))
    
    def test_getLastModified_none(self):
        from plone.app.caching.operations.utils import getLastModified
        
        class DummyLastModified(object):
            implements(ILastModified)
            adapts(DummyPublished)
            
            def __init__(self, context):
                self.context = context
            
            def __call__(self):
                return None
        
        provideAdapter(DummyLastModified)
        
        published = DummyPublished()
        self.assertEquals(None, getLastModified(published))
    
    def test_getLastModified_missing_timezone(self):
        from plone.app.caching.operations.utils import getLastModified
        
        class DummyLastModified(object):
            implements(ILastModified)
            adapts(DummyPublished)
            
            def __init__(self, context):
                self.context = context
            
            def __call__(self):
                return datetime.datetime(2010, 11, 24, 3, 4, 5, 6)
        
        provideAdapter(DummyLastModified)
        
        published = DummyPublished()
        self.assertEquals(datetime.datetime(2010, 11, 24, 3, 4, 5, 6, dateutil.tz.tzlocal()),
                          getLastModified(published))
    
    def test_getLastModified_timezone(self):
        from plone.app.caching.operations.utils import getLastModified
        
        class DummyLastModified(object):
            implements(ILastModified)
            adapts(DummyPublished)
            
            def __init__(self, context):
                self.context = context
            
            def __call__(self):
                return datetime.datetime(2010, 11, 24, 3, 4, 5, 6, dateutil.tz.tzutc())
        
        provideAdapter(DummyLastModified)
        
        published = DummyPublished()
        self.assertEquals(datetime.datetime(2010, 11, 24, 3, 4, 5, 6, dateutil.tz.tzutc()),
                          getLastModified(published))
    
    
    # getExpiration()
    
    def test_getExpiration_0(self):
        from plone.app.caching.operations.utils import getExpiration
        
        now = datetime.datetime.now()
        val = getExpiration(0)
        
        difference = now - val
        
        # it's more than a year in the past, which is plenty; it's actually
        # more like 10 years in the past, but it's hard to compare when the
        # calculation is based on the current time of the test.
        self.failUnless(difference >= datetime.timedelta(days=365))
    
    def test_getExpiration_past(self):
        from plone.app.caching.operations.utils import getExpiration
        
        now = datetime.datetime.now()
        val = getExpiration(-1)
        
        difference = now - val
        
        # any value in the past basically has the same effect as setting -1
        self.failUnless(difference >= datetime.timedelta(days=365))
    
    def test_getExpiration_future(self):
        from plone.app.caching.operations.utils import getExpiration
        
        now = datetime.datetime.now()
        val = getExpiration(60)
        
        difference = val - now
        
        # give the test two seconds' leeway
        self.failUnless(difference >= datetime.timedelta(seconds=58))
    
    
    # getETag()
    
    def test_getETag_extra_only(self):
        from plone.app.caching.operations.utils import getETag
        
        environ = {'SERVER_NAME': 'example.com', 'SERVER_PORT': '80'}
        response = HTTPResponse()
        request = HTTPRequest(StringIO(), environ, response)
        published = DummyPublished()
        
        self.assertEquals('|foo|bar;baz', getETag(published, request, extraTokens=('foo', 'bar,baz')))
    
    def test_getETag_key_not_found(self):
        from plone.app.caching.operations.utils import getETag
        
        environ = {'SERVER_NAME': 'example.com', 'SERVER_PORT': '80'}
        response = HTTPResponse()
        request = HTTPRequest(StringIO(), environ, response)
        published = DummyPublished()
        
        self.assertEquals('|', getETag(published, request, keys=('foo', 'bar',)))
    
    def test_getETag_adapter_returns_none(self):
        from plone.app.caching.operations.utils import getETag
        from plone.app.caching.interfaces import IETagValue
        
        class FooETag(object):
            implements(IETagValue)
            adapts(DummyPublished, HTTPRequest)
            
            def __init__(self, published, request):
                self.published = published
                self.request = request
            
            def __call__(self):
                return 'foo'
        
        provideAdapter(FooETag, name=u"foo")
        
        class BarETag(object):
            implements(IETagValue)
            adapts(DummyPublished, HTTPRequest)
            
            def __init__(self, published, request):
                self.published = published
                self.request = request
            
            def __call__(self):
                return None
        
        provideAdapter(BarETag, name=u"bar")
        
        environ = {'SERVER_NAME': 'example.com', 'SERVER_PORT': '80'}
        response = HTTPResponse()
        request = HTTPRequest(StringIO(), environ, response)
        published = DummyPublished()
        
        self.assertEquals('|foo', getETag(published, request, keys=('foo', 'bar',)))
    
    def test_getETag_full(self):
        from plone.app.caching.operations.utils import getETag
        from plone.app.caching.interfaces import IETagValue
        
        class FooETag(object):
            implements(IETagValue)
            adapts(DummyPublished, HTTPRequest)
            
            def __init__(self, published, request):
                self.published = published
                self.request = request
            
            def __call__(self):
                return 'foo'
        
        provideAdapter(FooETag, name=u"foo")
        
        class BarETag(object):
            implements(IETagValue)
            adapts(DummyPublished, HTTPRequest)
            
            def __init__(self, published, request):
                self.published = published
                self.request = request
            
            def __call__(self):
                return 'bar'
        
        provideAdapter(BarETag, name=u"bar")
        
        environ = {'SERVER_NAME': 'example.com', 'SERVER_PORT': '80'}
        response = HTTPResponse()
        request = HTTPRequest(StringIO(), environ, response)
        published = DummyPublished()
        
        self.assertEquals('|foo|bar|baz;qux', getETag(published, request,
                keys=('foo', 'bar',), extraTokens=('baz,qux',)))
    
    
    # parseETags()
    
    def test_parseETags_empty(self):
        from plone.app.caching.operations.utils import parseETags
        self.assertEquals([], parseETags(''))
    
    def test_parseETags_None(self):
        from plone.app.caching.operations.utils import parseETags
        self.assertEquals([], parseETags(''))
    
    def test_parseETags_star(self):
        from plone.app.caching.operations.utils import parseETags
        self.assertEquals(['*'], parseETags('*'))
    
    def test_parseETags_star_quoted(self):
        from plone.app.caching.operations.utils import parseETags
        self.assertEquals(['*'], parseETags('"*"'))
    
    def test_parseETags_single(self):
        from plone.app.caching.operations.utils import parseETags
        self.assertEquals(['|foo|bar;baz'], parseETags('|foo|bar;baz'))
    
    def test_parseETags_single_quoted(self):
        from plone.app.caching.operations.utils import parseETags
        self.assertEquals(['|foo|bar;baz'], parseETags('"|foo|bar;baz"'))
    
    def test_parseETags_multiple(self):
        from plone.app.caching.operations.utils import parseETags
        self.assertEquals(['|foo|bar;baz', '1234'], parseETags('|foo|bar;baz, 1234'))
    
    def test_parseETags_multiple_quoted(self):
        from plone.app.caching.operations.utils import parseETags
        self.assertEquals(['|foo|bar;baz', '1234'], parseETags('"|foo|bar;baz", "1234"'))
    
    def test_parseETags_multiple_nospace(self):
        from plone.app.caching.operations.utils import parseETags
        self.assertEquals(['|foo|bar;baz', '1234'], parseETags('|foo|bar;baz,1234'))
    
    def test_parseETags_multiple_quoted_nospace(self):
        from plone.app.caching.operations.utils import parseETags
        self.assertEquals(['|foo|bar;baz', '1234'], parseETags('"|foo|bar;baz","1234"'))
    
    def test_parseETags_multiple_weak(self):
        from plone.app.caching.operations.utils import parseETags
        self.assertEquals(['|foo|bar;baz', '1234'], parseETags('|foo|bar;baz, W/1234'))
    
    def test_parseETags_multiple_quoted_weak(self):
        from plone.app.caching.operations.utils import parseETags
        self.assertEquals(['|foo|bar;baz', '1234'], parseETags('"|foo|bar;baz", W/"1234"'))
    
    def test_parseETags_multiple_weak_disallowed(self):
        from plone.app.caching.operations.utils import parseETags
        self.assertEquals(['|foo|bar;baz'], parseETags('|foo|bar;baz, W/1234', allowWeak=False))
    
    def test_parseETags_multiple_quoted_weak_disallowed(self):
        from plone.app.caching.operations.utils import parseETags
        self.assertEquals(['|foo|bar;baz'], parseETags('"|foo|bar;baz", W/"1234"', allowWeak=False))

class RAMCacheTest(unittest.TestCase):
    
    def setUp(self):
        provideAdapter(AttributeAnnotations)
        classImplements(HTTPRequest, IAttributeAnnotatable)
    
    def tearDown(self):
        zope.component.testing.tearDown()
    
    # getRAMCache()

    def test_getRAMCache_no_chooser(self):
        pass
    
    def test_getRAMCache_normal(self):
        pass
    
    # getRAMCacheKey()
    
    def test_getRAMCacheKey_no_etag(self):
        pass
    
    def test_getRAMCacheKey_etag(self):
        pass
    
    # storeResponseInRAMCache()

    def test_storeResponseInRAMCache_minimal(self):
        pass
    
    def test_storeResponseInRAMCache_full(self):
        pass

def test_suite():
    return unittest.defaultTestLoader.loadTestsFromName(__name__)


