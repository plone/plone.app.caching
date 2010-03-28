import pkg_resources

import unittest
from cStringIO import StringIO

import datetime
import dateutil.parser
import dateutil.tz

from Products.PloneTestCase.ptc import FunctionalTestCase
from Products.PloneTestCase.ptc import portal_owner, default_user, default_password

from plone.app.caching.tests.layer import Layer

from Products.Five.testbrowser import Browser
import OFS.Image

from zope.component import getUtility

from zope.globalrequest import setRequest

from plone.registry.interfaces import IRegistry
from plone.caching.interfaces import ICacheSettings
from plone.cachepurging.interfaces import ICachePurgingSettings
from plone.cachepurging.interfaces import IPurger
from plone.app.caching.interfaces import IPloneCacheSettings

TEST_IMAGE = pkg_resources.resource_filename('plone.app.caching.tests', 'test.gif')
TEST_FILE = pkg_resources.resource_filename('plone.app.caching.tests', 'test.gif')


class TestProfileWithCaching(FunctionalTestCase):
    """This test aims to exercise the caching operations expected from the
    `with-caching-proxy` profile.
    
    Several of the operations are just duplicates of the ones for the
    `without-caching-proxy` profile but we still want to redo them in this
    context to ensure the profile has set the correct settings.
    """
    
    layer = Layer
    
    def afterSetUp(self):
        setRequest(self.portal.REQUEST)
        self.addProfile('plone.app.caching:with-caching-proxy')
        
        self.registry = getUtility(IRegistry)
        
        self.cacheSettings = self.registry.forInterface(ICacheSettings)
        self.cachePurgingSettings = self.registry.forInterface(ICachePurgingSettings)
        self.ploneCacheSettings = self.registry.forInterface(IPloneCacheSettings)
        
        self.cacheSettings.enabled = True
        
        self.purger = getUtility(IPurger)
        self.purger.reset()
    
    def beforeTearDown(self):
        setRequest(None)
    
    def test_composite_views(self):
        # This is a clone of the same test for 'without-caching-proxy'
        # Can we just call that test from this context?
        
        # Add folder content
        self.setRoles(('Manager',))
        self.portal.invokeFactory('Folder', 'f1')
        self.portal['f1'].setTitle(u"Folder one")
        self.portal['f1'].setDescription(u"Folder one description")
        self.portal['f1'].reindexObject()
        
        # Add page content
        self.portal['f1'].invokeFactory('Document', 'd1')
        self.portal['f1']['d1'].setTitle(u"Document one")
        self.portal['f1']['d1'].setDescription(u"Document one description")
        testText = "Testing... body one"
        self.portal['f1']['d1'].setText(testText)
        self.portal['f1']['d1'].reindexObject()
        
        # Publish the folder and page
        self.portal.portal_workflow.doActionFor(self.portal['f1'], 'publish')
        self.portal.portal_workflow.doActionFor(self.portal['f1']['d1'], 'publish')
        
        # Should we set up the etag components?
        # - set member?  No
        # - reset catalog counter?  Maybe
        # - set server language?
        # - turn on gzip?
        # - set skin?  Maybe
        # - leave status unlocked
        #
        
        # Request the quthenticated folder
        now = datetime.datetime.now(dateutil.tz.tzlocal())
        browser = Browser()
        browser.addHeader('Authorization', 'Basic %s:%s' % (default_user, default_password,))
        browser.open(self.portal['f1'].absolute_url())
        self.assertEquals('plone.content.folderView', browser.headers['X-Cache-Rule'])
        self.assertEquals('plone.app.caching.weakCaching', browser.headers['X-Cache-Operation'])
        # This should use cacheInBrowser
        self.assertEquals('max-age=0, must-revalidate, private', browser.headers['Cache-Control'])
        # XXX - Fix this.  The RR mod date element changes with each test run
        #self.assertEquals('|test_user_1_|51||0|Sunburst Theme|0', browser.headers['ETag'])
        self.assertEquals('"|test_user_1_|51||0|Sunburst Theme|0', browser.headers['ETag'][:37])
        self.failUnless(now > dateutil.parser.parse(browser.headers['Expires']))
        
        # Request the authenticated page
        now = datetime.datetime.now(dateutil.tz.tzlocal())
        browser = Browser()
        browser.addHeader('Authorization', 'Basic %s:%s' % (default_user, default_password,))
        browser.open(self.portal['f1']['d1'].absolute_url())
        self.failUnless(testText in browser.contents)
        self.assertEquals('plone.content.itemView', browser.headers['X-Cache-Rule'])
        self.assertEquals('plone.app.caching.weakCaching', browser.headers['X-Cache-Operation'])
        # This should use cacheInBrowser
        self.assertEquals('max-age=0, must-revalidate, private', browser.headers['Cache-Control'])
        # XXX - Fix this.  The RR mod date element changes with each test run
        self.assertEquals('"|test_user_1_|51||0|Sunburst Theme|0', browser.headers['ETag'][:37])
        self.failUnless(now > dateutil.parser.parse(browser.headers['Expires']))
        
        # Request the authenticated page again -- to test RAM cache.
        browser = Browser()
        browser.addHeader('Authorization', 'Basic %s:%s' % (default_user, default_password,))
        browser.open(self.portal['f1']['d1'].absolute_url())
        self.assertEquals('plone.content.itemView', browser.headers['X-Cache-Rule'])
        self.assertEquals('plone.app.caching.weakCaching', browser.headers['X-Cache-Operation'])
        # Authenticated should NOT be RAM cached
        self.assertEquals(None, browser.headers.get('X-RAMCache'))
        
        # Request the authenticated page again -- with an INM header to test 304
        etag = browser.headers['ETag']
        browser = Browser()
        browser.raiseHttpErrors = False  # we really do want to see the 304
        browser.addHeader('Authorization', 'Basic %s:%s' % (default_user, default_password,))
        browser.addHeader('If-None-Match', etag)
        browser.open(self.portal['f1']['d1'].absolute_url())
        # This should be a 304 response
        self.assertEquals('304 Not Modified', browser.headers['Status'])
        self.assertEquals('', browser.contents)
        
        # Request the anonymous folder
        now = datetime.datetime.now(dateutil.tz.tzlocal())
        browser = Browser()
        browser.open(self.portal['f1'].absolute_url())
        self.assertEquals('plone.content.folderView', browser.headers['X-Cache-Rule'])
        self.assertEquals('plone.app.caching.weakCaching', browser.headers['X-Cache-Operation'])
        # This should use cacheInBrowser
        self.assertEquals('max-age=0, must-revalidate, private', browser.headers['Cache-Control'])
        # XXX - Fix this.  The RR mod date element changes with each test run
        self.assertEquals('"||51||0|Sunburst Theme|0|', browser.headers['ETag'][:26])
        self.failUnless(now > dateutil.parser.parse(browser.headers['Expires']))
        
        # Request the anonymous page
        now = datetime.datetime.now(dateutil.tz.tzlocal())
        browser = Browser()
        browser.open(self.portal['f1']['d1'].absolute_url())
        self.assertEquals('plone.content.itemView', browser.headers['X-Cache-Rule'])
        self.assertEquals('plone.app.caching.weakCaching', browser.headers['X-Cache-Operation'])
        self.failUnless(testText in browser.contents)
        # This should use cacheInBrowser
        self.assertEquals('max-age=0, must-revalidate, private', browser.headers['Cache-Control'])
        # XXX - Fix this.  The RR mod date element changes with each test run
        self.assertEquals('"||51||0|Sunburst Theme|0|', browser.headers['ETag'][:26])
        self.failUnless(now > dateutil.parser.parse(browser.headers['Expires']))
        
        # Request the anonymous page again -- to test RAM cache.
        # Anonymous should be RAM cached
        now = datetime.datetime.now(dateutil.tz.tzlocal())
        browser = Browser()
        browser.open(self.portal['f1']['d1'].absolute_url())
        self.assertEquals('plone.content.itemView', browser.headers['X-Cache-Rule'])
        self.assertEquals('plone.app.caching.weakCaching', browser.headers['X-Cache-Operation'])
        # This should come from RAM cache
        self.assertEquals('plone.app.caching.operations.ramcache', browser.headers['X-RAMCache'])
        self.failUnless(testText in browser.contents)
        self.assertEquals('max-age=0, must-revalidate, private', browser.headers['Cache-Control'])
        self.assertEquals('"||51||0|Sunburst Theme|0|', browser.headers['ETag'][:26])
        self.failUnless(now > dateutil.parser.parse(browser.headers['Expires']))
        
        # Request the anonymous page again -- with an INM header to test 304.
        etag = browser.headers['ETag']
        browser = Browser()
        browser.raiseHttpErrors = False
        browser.addHeader('If-None-Match', etag)
        browser.open(self.portal['f1']['d1'].absolute_url())
        self.assertEquals('plone.content.itemView', browser.headers['X-Cache-Rule'])
        self.assertEquals('plone.app.caching.weakCaching', browser.headers['X-Cache-Operation'])
        # This should be a 304 response
        self.assertEquals('304 Not Modified', browser.headers['Status'])
        self.assertEquals('', browser.contents)
        
        # Edit the page to update the etag
        testText2 = "Testing... body two"
        self.portal['f1']['d1'].setText(testText2)
        self.portal['f1']['d1'].reindexObject()
        
        # Request the anonymous page again -- to test expiration of 304 and RAM.
        etag = browser.headers['ETag']
        browser = Browser()
        browser.addHeader('If-None-Match', etag)
        browser.open(self.portal['f1']['d1'].absolute_url())
        self.assertEquals('plone.content.itemView', browser.headers['X-Cache-Rule'])
        self.assertEquals('plone.app.caching.weakCaching', browser.headers['X-Cache-Operation'])
        # The etag has changed so we should get a fresh page.
        self.assertEquals(None, browser.headers.get('X-RAMCache'))
        self.assertEquals('200 Ok', browser.headers['Status'])
    
    def test_content_feeds(self):
        
        # Enable syndication
        self.setRoles(('Manager',))
        self.syndication = self.portal.portal_syndication
        self.syndication.editProperties(isAllowed=True)
        self.syndication.enableSyndication(self.portal)
        
        # Request the rss feed
        now = datetime.datetime.now(dateutil.tz.tzlocal())
        browser = Browser()
        browser.open(self.portal.absolute_url() + '/RSS')
        self.assertEquals('plone.content.feed', browser.headers['X-Cache-Rule'])
        self.assertEquals('plone.app.caching.moderateCaching', browser.headers['X-Cache-Operation'])
        # This should use cacheInProxy
        self.assertEquals('max-age=0, s-maxage=86400, must-revalidate', browser.headers['Cache-Control'])
        self.assertEquals('"||40||0|Sunburst Theme"', browser.headers['ETag'])
        self.failUnless(now > dateutil.parser.parse(browser.headers['Expires']))
        
        # Request the rss feed again -- to test RAM cache
        now = datetime.datetime.now(dateutil.tz.tzlocal())
        rssText = browser.contents
        browser = Browser()
        browser.open(self.portal.absolute_url() + '/RSS')
        self.assertEquals('plone.content.feed', browser.headers['X-Cache-Rule'])
        self.assertEquals('plone.app.caching.moderateCaching', browser.headers['X-Cache-Operation'])
        # This should come from the RAM cache
        self.assertEquals('plone.app.caching.operations.ramcache', browser.headers['X-RAMCache'])
        self.assertEquals(rssText, browser.contents)
        self.assertEquals('max-age=0, s-maxage=86400, must-revalidate', browser.headers['Cache-Control'])
        self.assertEquals('"||40||0|Sunburst Theme"', browser.headers['ETag'])
        self.failUnless(now > dateutil.parser.parse(browser.headers['Expires']))
        
        # Request the rss feed again -- with an INM header to test 304.
        etag = browser.headers['ETag']
        browser = Browser()
        browser.raiseHttpErrors = False
        browser.addHeader('If-None-Match', etag)
        browser.open(self.portal.absolute_url() + '/RSS')
        self.assertEquals('plone.content.feed', browser.headers['X-Cache-Rule'])
        self.assertEquals('plone.app.caching.moderateCaching', browser.headers['X-Cache-Operation'])
        # This should be a 304 response
        self.assertEquals('304 Not Modified', browser.headers['Status'])
        self.assertEquals('', browser.contents)
        
        # Request the authenticated rss feed
        now = datetime.datetime.now(dateutil.tz.tzlocal())
        browser = Browser()
        browser.addHeader('Authorization', 'Basic %s:%s' % (default_user, default_password,))
        browser.open(self.portal.absolute_url() + '/RSS')
        self.assertEquals('plone.content.feed', browser.headers['X-Cache-Rule'])
        self.assertEquals('plone.app.caching.moderateCaching', browser.headers['X-Cache-Operation'])
        # This should use cacheInBrowser
        self.assertEquals('max-age=0, must-revalidate, private', browser.headers['Cache-Control'])
        self.assertEquals('"|test_user_1_|40||0|Sunburst Theme"', browser.headers['ETag'])
        self.failUnless(now > dateutil.parser.parse(browser.headers['Expires']))
        
        # Request the authenticated rss feed again -- to test RAM cache
        browser = Browser()
        browser.addHeader('Authorization', 'Basic %s:%s' % (default_user, default_password,))
        browser.open(self.portal.absolute_url() + '/RSS')
        self.assertEquals('plone.content.feed', browser.headers['X-Cache-Rule'])
        self.assertEquals('plone.app.caching.moderateCaching', browser.headers['X-Cache-Operation'])
        # Authenticated should NOT be RAM cached
        self.assertEquals(None, browser.headers.get('X-RAMCache'))
    
    def test_content_files(self):
        
        # Add folder content
        self.setRoles(('Manager',))
        self.portal.invokeFactory('Folder', 'f1')
        self.portal['f1'].setTitle(u"Folder one")
        self.portal['f1'].setDescription(u"Folder one description")
        self.portal['f1'].reindexObject()
        
        # Add content image
        self.portal['f1'].invokeFactory('Image', 'i1')
        self.portal['f1']['i1'].setTitle(u"Image one")
        self.portal['f1']['i1'].setDescription(u"Image one description")
        self.portal['f1']['i1'].setImage(OFS.Image.Image('test.gif', 'test.gif', open(TEST_IMAGE, 'rb')))
        self.portal['f1']['i1'].reindexObject()
        
        # Request the image with Manager role
        now = datetime.datetime.now(dateutil.tz.tzlocal())
        browser = Browser()
        browser.addHeader('Authorization', 'Basic %s:%s' % (portal_owner, default_password,))
        browser.open(self.portal['f1']['i1'].absolute_url())
        self.assertEquals('plone.content.file', browser.headers['X-Cache-Rule'])
        self.assertEquals('plone.app.caching.moderateCaching', browser.headers['X-Cache-Operation'])
        # Folder not published yet so image should not be cached in proxy
        # so this should use cacheInBrowser
        self.assertEquals('max-age=0, must-revalidate, private', browser.headers['Cache-Control'])
        self.failIf(None == browser.headers.get('Last-Modified'))  # remove this when the next line works
        #self.assertEquals('---lastmodified---', browser.headers['Last-Modified'])
        self.failUnless(now > dateutil.parser.parse(browser.headers['Expires']))
        
        # Request an image scale with Manager role
        now = datetime.datetime.now(dateutil.tz.tzlocal())
        browser = Browser()
        browser.addHeader('Authorization', 'Basic %s:%s' % (portal_owner, default_password,))
        browser.open(self.portal['f1']['i1'].absolute_url() + '/image_preview')
        self.assertEquals('plone.content.file', browser.headers['X-Cache-Rule'])
        self.assertEquals('plone.app.caching.moderateCaching', browser.headers['X-Cache-Operation'])
        # Folder not published yet so image scale should not be cached in proxy
        # so this should use cacheInBrowser
        self.assertEquals('max-age=0, must-revalidate, private', browser.headers['Cache-Control'])
        self.failIf(None == browser.headers.get('Last-Modified'))  # remove this when the next line works
        #self.assertEquals('---lastmodified---', browser.headers['Last-Modified'])
        self.failUnless(now > dateutil.parser.parse(browser.headers['Expires']))
        
        # Publish the folder 
        self.portal.portal_workflow.doActionFor(self.portal['f1'], 'publish')
        
        # Request the image
        now = datetime.datetime.now(dateutil.tz.tzlocal())
        browser = Browser()
        browser.open(self.portal['f1']['i1'].absolute_url())
        self.assertEquals('plone.content.file', browser.headers['X-Cache-Rule'])
        self.assertEquals('plone.app.caching.moderateCaching', browser.headers['X-Cache-Operation'])
        # Now visible to anonymous so this should use cacheInProxy
        self.assertEquals('max-age=0, s-maxage=86400, must-revalidate', browser.headers['Cache-Control'])
        self.failIf(None == browser.headers.get('Last-Modified'))  # remove this when the next line works
        #self.assertEquals('---lastmodified---', browser.headers['Last-Modified'])
        self.failUnless(now > dateutil.parser.parse(browser.headers['Expires']))
        
        # Request the image again -- with an IMS header to test 304
        lastmodified = browser.headers['Last-Modified']
        browser = Browser()
        browser.raiseHttpErrors = False
        browser.addHeader('If-Modified-Since', lastmodified)
        browser.open(self.portal['f1']['i1'].absolute_url())
        self.assertEquals('plone.content.file', browser.headers['X-Cache-Rule'])
        self.assertEquals('plone.app.caching.moderateCaching', browser.headers['X-Cache-Operation'])
        # This should be a 304 response
        self.assertEquals('304 Not Modified', browser.headers['Status'])
        self.assertEquals('', browser.contents)
        
        # Request an image scale
        now = datetime.datetime.now(dateutil.tz.tzlocal())
        browser = Browser()
        browser.open(self.portal['f1']['i1'].absolute_url() + '/image_preview')
        self.assertEquals('plone.content.file', browser.headers['X-Cache-Rule'])
        self.assertEquals('plone.app.caching.moderateCaching', browser.headers['X-Cache-Operation'])
        # Now visible to anonymous so this should use cacheInProxy
        self.assertEquals('max-age=0, s-maxage=86400, must-revalidate', browser.headers['Cache-Control'])
        self.failIf(None == browser.headers.get('Last-Modified'))  # remove this when the next line works
        #self.assertEquals('---lastmodified---', browser.headers['Last-Modified'])
        self.failUnless(now > dateutil.parser.parse(browser.headers['Expires']))
    
    def test_resources(self):
        # This is a clone of the same test for 'without-caching-proxy'
        # Can we just call that test from this context?
        
        # Request a skin image
        now = datetime.datetime.now(dateutil.tz.tzlocal())
        browser = Browser()
        browser.open(self.portal.absolute_url() + '/rss.gif')
        self.assertEquals('plone.resource', browser.headers['X-Cache-Rule'])
        self.assertEquals('plone.app.caching.strongCaching', browser.headers['X-Cache-Operation'])
        # This should use cacheInBrowserAndProxy
        self.assertEquals('max-age=86400, proxy-revalidate, public', browser.headers['Cache-Control'])
        self.failIf(None == browser.headers.get('Last-Modified'))  # remove this when the next line works
        #self.assertEquals('---lastmodified---', browser.headers['Last-Modified'])
        timedelta = dateutil.parser.parse(browser.headers['Expires']) - now
        self.failUnless(timedelta > datetime.timedelta(seconds=86390))
        
        # Request the skin image again -- with an IMS header to test 304
        lastmodified = browser.headers['Last-Modified']
        browser = Browser()
        browser.raiseHttpErrors = False
        browser.addHeader('If-Modified-Since', lastmodified)
        browser.open(self.portal.absolute_url() + '/rss.gif')
        self.assertEquals('plone.resource', browser.headers['X-Cache-Rule'])
        self.assertEquals('plone.app.caching.strongCaching', browser.headers['X-Cache-Operation'])
        # This should be a 304 response
        self.assertEquals('304 Not Modified', browser.headers['Status'])
        self.assertEquals('', browser.contents)
        
        # Request a large datafile (over 64K) to test files that use
        # the "response.write()" function to initiate a streamed response.
        # This is of type OFS.Image.File but it should also apply to
        # large OFS.Image.Image, large non-blog ATImages/ATFiles, and
        # large Resource Registry cooked files, which all use the same
        # method to initiate a streamed response.
        s = "a" * (1 << 16) * 3
        self.portal.manage_addFile('bigfile', file=StringIO(s), content_type='application/octet-stream')
        browser = Browser()
        browser.open(self.portal['bigfile'].absolute_url())
        self.assertEquals('plone.resource', browser.headers['X-Cache-Rule'])
        self.assertEquals('plone.app.caching.strongCaching', browser.headers['X-Cache-Operation'])
        # This should use cacheInBrowserAndProxy
        self.assertEquals('max-age=86400, proxy-revalidate, public', browser.headers['Cache-Control'])
        self.failIf(None == browser.headers.get('Last-Modified'))  # remove this when the next line works
        #self.assertEquals('---lastmodified---', browser.headers['Last-Modified'])
        timedelta = dateutil.parser.parse(browser.headers['Expires']) - now
        self.failUnless(timedelta > datetime.timedelta(seconds=86390))
    
    def test_stable_resources(self):
        # This is a clone of the same test for 'without-caching-proxy'
        # Can we just call that test from this context?
        # (yes, this is not really testing anything. It's a placeholder)
        # 
        # We don't actually have any non-RR stable resources yet
        # What is the best way to test this?
        # Maybe not important since the RR test exercises the same code?
        pass
    
    def test_stable_resources_resource_registries(self):
        # This is a clone of the same test for 'without-caching-proxy'
        # Can we just call that test from this context?
        path = "/Sunburst%20Theme/public.css"
        
        # Request a ResourceRegistry resource
        cssregistry = self.portal.portal_css
        path = cssregistry.absolute_url() + "/Sunburst%20Theme/public.css"
        now = datetime.datetime.now(dateutil.tz.tzlocal())
        browser = Browser()
        browser.open(path)
        self.assertEquals('plone.stableResource', browser.headers['X-Cache-Rule'])
        self.assertEquals('plone.app.caching.strongCaching', browser.headers['X-Cache-Operation'])
        # This should use cacheInBrowserAndProxy
        self.assertEquals('max-age=31536000, proxy-revalidate, public', browser.headers['Cache-Control'])
        self.failIf(None == browser.headers.get('Last-Modified'))
        timedelta = dateutil.parser.parse(browser.headers['Expires']) - now
        self.failUnless(timedelta > datetime.timedelta(seconds=31535990))
        
        # Request the ResourceRegistry resource again -- with IMS header to test 304
        lastmodified = browser.headers['Last-Modified']
        browser = Browser()
        browser.raiseHttpErrors = False
        browser.addHeader('If-Modified-Since', lastmodified)
        browser.open(path)
        self.assertEquals('plone.stableResource', browser.headers['X-Cache-Rule'])
        self.assertEquals('plone.app.caching.strongCaching', browser.headers['X-Cache-Operation'])
        self.assertEquals('304 Not Modified', browser.headers['Status'])
        self.assertEquals('', browser.contents)
        self.assertEquals(None, browser.headers.get('Last-Modified'))
        self.assertEquals(None, browser.headers.get('Expires'))
        self.assertEquals(None, browser.headers.get('Cache-Control'))
        
        # Request the ResourceRegistry resource -- with RR in debug mode
        now = datetime.datetime.now(dateutil.tz.tzlocal())
        cssregistry.setDebugMode(True)
        browser = Browser()
        browser.open(path)
        self.assertEquals('plone.stableResource', browser.headers['X-Cache-Rule'])
        self.assertEquals('plone.app.caching.strongCaching', browser.headers['X-Cache-Operation'])
        # This should use doNotCache
        self.assertEquals('max-age=0, must-revalidate, private', browser.headers['Cache-Control'])
        self.assertEquals(None, browser.headers.get('Last-Modified'))
        self.failUnless(now > dateutil.parser.parse(browser.headers['Expires']))

def test_suite():
    return unittest.defaultTestLoader.loadTestsFromName(__name__)

