import pkg_resources

import unittest

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

#from z3c.caching.interfaces import ILastModified

from plone.registry.interfaces import IRegistry
from plone.caching.interfaces import ICacheSettings
from plone.cachepurging.interfaces import ICachePurgingSettings
from plone.cachepurging.interfaces import IPurger
from plone.app.caching.interfaces import IPloneCacheSettings

TEST_IMAGE = pkg_resources.resource_filename('plone.app.caching.tests', 'test.gif')
TEST_FILE = pkg_resources.resource_filename('plone.app.caching.tests', 'test.gif')


class TestOperations(FunctionalTestCase):
    """This test aims to exercise the various caching operations in a semi-
    realistic scenario.
    
    Note: Changes made using the API, accessing objects directly, are done
    with the Manager role set. Interactions are tested using the testbrowser.
    Unless explicitly logged in (e.g. by adding a HTTP Basic Authorization
    header), this accesses Plone as an anonymous user.
    
    The usual pattern is:
    
    * Configure caching settings
    * Set up test content
    * Create a new testbrowser
    * Set any request headers
    * Access content
    * Inspect response headers and body
    * Repeat as necessary
    
    To test purging, check the self.purger._sync and self.purger._async lists.
    """
    
    layer = Layer
    
    def afterSetUp(self):
        setRequest(self.portal.REQUEST)
        self.addProfile('plone.app.caching:without-caching-proxy')
        
        self.registry = getUtility(IRegistry)
        
        self.cacheSettings = self.registry.forInterface(ICacheSettings)
        self.cachePurgingSettings = self.registry.forInterface(ICachePurgingSettings)
        self.ploneCacheSettings = self.registry.forInterface(IPloneCacheSettings)
        
        self.purger = getUtility(IPurger)
        self.purger.reset()
    
    def beforeTearDown(self):
        setRequest(None)
    
    def test_disabled(self):
        self.cacheSettings.enabled = False
        
        self.setRoles(('Manager',))
        
        # Folder content
        self.portal.invokeFactory('Folder', 'f1')
        self.portal['f1'].setTitle(u"Folder one")
        self.portal['f1'].setDescription(u"Folder one description")
        self.portal['f1'].reindexObject()
        
        # Non-folder content
        self.portal['f1'].invokeFactory('Document', 'd1')
        self.portal['f1']['d1'].setTitle(u"Document one")
        self.portal['f1']['d1'].setDescription(u"Document one description")
        self.portal['f1']['d1'].setText("<p>Body one</p>")
        self.portal['f1']['d1'].reindexObject()
        
        # Content image
        self.portal['f1'].invokeFactory('Image', 'i1')
        self.portal['f1']['i1'].setTitle(u"Image one")
        self.portal['f1']['i1'].setDescription(u"Image one description")
        self.portal['f1']['i1'].setImage(OFS.Image.Image('test.gif', 'test.gif', open(TEST_IMAGE, 'rb')))
        self.portal['f1']['i1'].reindexObject()
        
        # Content file
        self.portal['f1'].invokeFactory('File', 'f1')
        self.portal['f1']['f1'].setTitle(u"File one")
        self.portal['f1']['f1'].setDescription(u"File one description")
        self.portal['f1']['f1'].setFile(OFS.Image.File('test.gif', 'test.gif', open(TEST_FILE, 'rb')))
        self.portal['f1']['f1'].reindexObject()
        
        # OFS image (custom folder)
        OFS.Image.manage_addImage(self.portal['portal_skins']['custom'], 'test.gif', open(TEST_IMAGE, 'rb'))
        
        # Resource registries resource
        cssResourcePath = self.portal['portal_css'].getEvaluatedResources(self.portal)[0].getId()
        
        self.setRoles(('Member',))
        
        browser = Browser()
        
        # Check that we can open all without errors and without cache headers
        browser.open(self.portal.absolute_url())
        self.failIf('Cache-Control' in browser.headers)
        
        browser.open(self.portal['f1'].absolute_url())
        self.failIf('Cache-Control' in browser.headers)
        
        browser.open(self.portal['f1']['d1'].absolute_url())
        self.failIf('Cache-Control' in browser.headers)
        
        browser.open(self.portal['f1']['i1'].absolute_url())
        self.failIf('Cache-Control' in browser.headers)
        
        browser.open(self.portal['f1']['f1'].absolute_url())
        self.failIf('Cache-Control' in browser.headers)
        
        browser.open(self.portal.absolute_url() + '/portal_skins/custom/test.gif')
        self.failIf('Cache-Control' in browser.headers)
        
        browser.open(self.portal.absolute_url() + '/++resource++plone.app.caching.gif')
        # Set by resources themselves, but irrelevant to this test:
        # self.failUnless('Cache-Control' in browser.headers)
        
        browser.open(self.portal.absolute_url() + '/portal_css/' + cssResourcePath)
        # Set by ResourceRegistries, btu irrelevant ot this test
        # self.failUnless('Cache-Control' in browser.headers)
    
    def test_gzip_setting(self):
        self.cacheSettings.enabled = True
        
        self.setRoles(('Manager',))
        
        # Folder content
        self.portal.invokeFactory('Folder', 'f1')
        self.portal['f1'].setTitle(u"Folder one")
        self.portal['f1'].setDescription(u"Folder one description")
        self.portal['f1'].reindexObject()
        
        # Non-folder content
        self.portal['f1'].invokeFactory('Document', 'd1')
        self.portal['f1']['d1'].setTitle(u"Document one")
        self.portal['f1']['d1'].setDescription(u"Document one description")
        self.portal['f1']['d1'].setText("<p>Body one</p>")
        self.portal['f1']['d1'].reindexObject()
        
        # GZip disabled, not accepted
        browser = Browser()
        self.ploneCacheSettings.enableCompression = False
        browser.open(self.portal['f1']['d1'].absolute_url())
        self.failIf('Vary' in browser.headers)
        self.failIf('gzip' in browser.headers.get('Content-Encoding', ''))
        
        # GZip disabled, accepted
        browser = Browser()
        browser.addHeader('Accept-Encoding', 'gzip')
        self.ploneCacheSettings.enableCompression = False
        browser.open(self.portal['f1']['d1'].absolute_url())
        self.failIf('Vary' in browser.headers)
        self.failIf('gzip' in browser.headers.get('Content-Encoding', ''))
        
        # GZip enabled, not accepted
        browser = Browser()
        self.ploneCacheSettings.enableCompression = True
        browser.open(self.portal['f1']['d1'].absolute_url())
        self.failIf('Vary' in browser.headers)
        self.failIf('gzip' in browser.headers.get('Content-Encoding', ''))
        
        # GZip enabled, accepted
        browser = Browser()
        self.ploneCacheSettings.enableCompression = True
        browser.addHeader('Accept-Encoding', 'gzip')
        browser.open(self.portal['f1']['d1'].absolute_url())
        self.failUnless('Accept-Encoding' in browser.headers['Vary'])
        self.assertEquals('gzip', browser.headers['Content-Encoding'])
        
        # Test as logged in (should not make any difference)
        browser = Browser()
        self.ploneCacheSettings.enableCompression = True
        
        browser.addHeader('Accept-Encoding', 'gzip')
        browser.addHeader('Authorization', 'Basic %s:%s' % (default_user, default_password,))
        
        browser.open(self.portal['f1']['d1'].absolute_url())
        self.failUnless('Accept-Encoding' in browser.headers['Vary'])
        self.assertEquals('gzip', browser.headers['Content-Encoding'])
    
    def test_composite_views(self):
        self.cacheSettings.enabled = True
        
        self.setRoles(('Manager',))
        testText = "Testing... body one"
        testText2 = "Testing... body two"
        
        # Folder content
        self.portal.invokeFactory('Folder', 'f1')
        self.portal['f1'].setTitle(u"Folder one")
        self.portal['f1'].setDescription(u"Folder one description")
        self.portal['f1'].reindexObject()
        
        # Page content
        self.portal['f1'].invokeFactory('Document', 'd1')
        self.portal['f1']['d1'].setTitle(u"Document one")
        self.portal['f1']['d1'].setDescription(u"Document one description")
        self.portal['f1']['d1'].setText(testText)
        self.portal['f1']['d1'].reindexObject()
        
        # Publish the folder and page
        self.portal.portal_workflow.doActionFor(self.portal['f1'], 'publish')
        self.portal.portal_workflow.doActionFor(self.portal['f1']['d1'], 'publish')
        
        now = datetime.datetime.now(dateutil.tz.tzlocal())
        
        # Should we set up the etag components?
        # - set member?  No
        # - reset catalog counter?  Maybe
        # - set server language?
        # - turn on gzip?
        # - set skin?  Maybe
        # - leave status unlocked
        #
        
        # Request the quthenticated folder
        browser = Browser()
        browser.addHeader('Authorization', 'Basic %s:%s' % (default_user, default_password,))
        browser.open(self.portal['f1'].absolute_url())
        self.assertEquals('plone.content.folderView', browser.headers['X-Cache-Rule'])
        self.assertEquals('plone.app.caching.weakCaching', browser.headers['X-Cache-Operation'])
        # This should use cacheInBrowser
        self.assertEquals('max-age=0, must-revalidate, private', browser.headers['Cache-Control'])
        self.assertEquals('|test_user_1_|51||0|Sunburst Theme|0', browser.headers['ETag'])
        self.failUnless(now > dateutil.parser.parse(browser.headers['Expires']))
        
        # Request the quthenticated page
        browser = Browser()
        browser.addHeader('Authorization', 'Basic %s:%s' % (default_user, default_password,))
        browser.open(self.portal['f1']['d1'].absolute_url())
        self.failUnless(testText in browser.contents)
        self.assertEquals('plone.content.itemView', browser.headers['X-Cache-Rule'])
        self.assertEquals('plone.app.caching.weakCaching', browser.headers['X-Cache-Operation'])
        # This should use cacheInBrowser
        self.assertEquals('max-age=0, must-revalidate, private', browser.headers['Cache-Control'])
        self.assertEquals('|test_user_1_|51||0|Sunburst Theme|0', browser.headers['ETag'])
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
        browser = Browser()
        browser.open(self.portal['f1'].absolute_url())
        self.assertEquals('plone.content.folderView', browser.headers['X-Cache-Rule'])
        self.assertEquals('plone.app.caching.weakCaching', browser.headers['X-Cache-Operation'])
        # This should use cacheInBrowser
        self.assertEquals('max-age=0, must-revalidate, private', browser.headers['Cache-Control'])
        self.assertEquals('||51||0|Sunburst Theme|0', browser.headers['ETag'])
        self.failUnless(now > dateutil.parser.parse(browser.headers['Expires']))
        
        # Request the anonymous page
        browser = Browser()
        browser.open(self.portal['f1']['d1'].absolute_url())
        self.assertEquals('plone.content.itemView', browser.headers['X-Cache-Rule'])
        self.assertEquals('plone.app.caching.weakCaching', browser.headers['X-Cache-Operation'])
        self.failUnless(testText in browser.contents)
        # This should use cacheInBrowser
        self.assertEquals('max-age=0, must-revalidate, private', browser.headers['Cache-Control'])
        self.assertEquals('||51||0|Sunburst Theme|0', browser.headers['ETag'])
        self.failUnless(now > dateutil.parser.parse(browser.headers['Expires']))
        
        # Request the anonymous page again -- to test RAM cache.
        # Anonymous should be RAM cached
        browser = Browser()
        browser.open(self.portal['f1']['d1'].absolute_url())
        self.assertEquals('plone.content.itemView', browser.headers['X-Cache-Rule'])
        self.assertEquals('plone.app.caching.weakCaching', browser.headers['X-Cache-Operation'])
        # This should come from RAM cache
        self.assertEquals('plone.app.caching.operations.ramcache', browser.headers['X-RAMCache'])
        self.failUnless(testText in browser.contents)
        self.assertEquals('max-age=0, must-revalidate, private', browser.headers['Cache-Control'])
        self.assertEquals('||51||0|Sunburst Theme|0', browser.headers['ETag'])
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
        self.cacheSettings.enabled = True
        
        self.setRoles(('Manager',))
        
        # Enable syndication
        self.syndication = self.portal.portal_syndication
        self.syndication.editProperties(isAllowed=True)
        self.syndication.enableSyndication(self.portal)
        
        now = datetime.datetime.now(dateutil.tz.tzlocal())
        
        # Request the rss feed
        browser = Browser()
        browser.open(self.portal.absolute_url() + '/RSS')
        self.assertEquals('plone.content.feed', browser.headers['X-Cache-Rule'])
        self.assertEquals('plone.app.caching.weakCaching', browser.headers['X-Cache-Operation'])
        # This should use cacheInBrowser
        self.assertEquals('max-age=0, must-revalidate, private', browser.headers['Cache-Control'])
        self.assertEquals('||40||0|Sunburst Theme', browser.headers['ETag'])
        self.failUnless(now > dateutil.parser.parse(browser.headers['Expires']))
        
        # Request the rss feed again -- to test RAM cache
        rssText = browser.contents
        browser = Browser()
        browser.open(self.portal.absolute_url() + '/RSS')
        self.assertEquals('plone.content.feed', browser.headers['X-Cache-Rule'])
        self.assertEquals('plone.app.caching.weakCaching', browser.headers['X-Cache-Operation'])
        # This should come from RAM cache
        self.assertEquals('plone.app.caching.operations.ramcache', browser.headers['X-RAMCache'])
        self.assertEquals(rssText, browser.contents)
        self.assertEquals('max-age=0, must-revalidate, private', browser.headers['Cache-Control'])
        self.assertEquals('||40||0|Sunburst Theme', browser.headers['ETag'])
        self.failUnless(now > dateutil.parser.parse(browser.headers['Expires']))
        
        # Request the rss feed again -- with an INM header to test 304.
        etag = browser.headers['ETag']
        browser = Browser()
        browser.raiseHttpErrors = False
        browser.addHeader('If-None-Match', etag)
        browser.open(self.portal.absolute_url() + '/RSS')
        self.assertEquals('plone.content.feed', browser.headers['X-Cache-Rule'])
        self.assertEquals('plone.app.caching.weakCaching', browser.headers['X-Cache-Operation'])
        # This should be a 304 response
        self.assertEquals('304 Not Modified', browser.headers['Status'])
        self.assertEquals('', browser.contents)
        
        # Request the authenticated rss feed
        browser = Browser()
        browser.addHeader('Authorization', 'Basic %s:%s' % (default_user, default_password,))
        browser.open(self.portal.absolute_url() + '/RSS')
        self.assertEquals('plone.content.feed', browser.headers['X-Cache-Rule'])
        self.assertEquals('plone.app.caching.weakCaching', browser.headers['X-Cache-Operation'])
        # This should use cacheInBrowser
        self.assertEquals('max-age=0, must-revalidate, private', browser.headers['Cache-Control'])
        self.assertEquals('|test_user_1_|40||0|Sunburst Theme', browser.headers['ETag'])
        self.failUnless(now > dateutil.parser.parse(browser.headers['Expires']))
        
        # Request the authenticated rss feed again -- to test RAM cache
        browser = Browser()
        browser.addHeader('Authorization', 'Basic %s:%s' % (default_user, default_password,))
        browser.open(self.portal.absolute_url() + '/RSS')
        self.assertEquals('plone.content.feed', browser.headers['X-Cache-Rule'])
        self.assertEquals('plone.app.caching.weakCaching', browser.headers['X-Cache-Operation'])
        # Authenticated should NOT be RAM cached
        self.assertEquals(None, browser.headers.get('X-RAMCache'))
    
    def test_content_feeds_proxy(self):
        self.addProfile('plone.app.caching:with-caching-proxy')
        self.cacheSettings.enabled = True
        
        self.setRoles(('Manager',))
        
        # Enable syndication
        self.syndication = self.portal.portal_syndication
        self.syndication.editProperties(isAllowed=True)
        self.syndication.enableSyndication(self.portal)
        
        now = datetime.datetime.now(dateutil.tz.tzlocal())
        
        # Request the rss feed
        browser = Browser()
        browser.open(self.portal.absolute_url() + '/RSS')
        self.assertEquals('plone.content.feed', browser.headers['X-Cache-Rule'])
        self.assertEquals('plone.app.caching.moderateCaching', browser.headers['X-Cache-Operation'])
        # This should use cacheInProxy
        self.assertEquals('max-age=0, s-maxage=86400, must-revalidate', browser.headers['Cache-Control'])
        self.assertEquals('||40||0|Sunburst Theme', browser.headers['ETag'])
        self.failUnless(now > dateutil.parser.parse(browser.headers['Expires']))
        
        # Request the rss feed again -- to test RAM cache
        rssText = browser.contents
        browser = Browser()
        browser.open(self.portal.absolute_url() + '/RSS')
        self.assertEquals('plone.content.feed', browser.headers['X-Cache-Rule'])
        self.assertEquals('plone.app.caching.moderateCaching', browser.headers['X-Cache-Operation'])
        # This should come from the RAM cache
        self.assertEquals('plone.app.caching.operations.ramcache', browser.headers['X-RAMCache'])
        self.assertEquals(rssText, browser.contents)
        self.assertEquals('max-age=0, s-maxage=86400, must-revalidate', browser.headers['Cache-Control'])
        self.assertEquals('||40||0|Sunburst Theme', browser.headers['ETag'])
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
        browser = Browser()
        browser.addHeader('Authorization', 'Basic %s:%s' % (default_user, default_password,))
        browser.open(self.portal.absolute_url() + '/RSS')
        self.assertEquals('plone.content.feed', browser.headers['X-Cache-Rule'])
        self.assertEquals('plone.app.caching.moderateCaching', browser.headers['X-Cache-Operation'])
        # This should use cacheInBrowser
        self.assertEquals('max-age=0, must-revalidate, private', browser.headers['Cache-Control'])
        self.assertEquals('|test_user_1_|40||0|Sunburst Theme', browser.headers['ETag'])
        self.failUnless(now > dateutil.parser.parse(browser.headers['Expires']))
        
        # Request the authenticated rss feed again -- to test RAM cache
        browser = Browser()
        browser.addHeader('Authorization', 'Basic %s:%s' % (default_user, default_password,))
        browser.open(self.portal.absolute_url() + '/RSS')
        self.assertEquals('plone.content.feed', browser.headers['X-Cache-Rule'])
        self.assertEquals('plone.app.caching.moderateCaching', browser.headers['X-Cache-Operation'])
        # Authenticated should NOT be RAM cached
        self.assertEquals(None, browser.headers.get('X-RAMCache'))
    
    def test_downloads(self):
        self.cacheSettings.enabled = True
        
        self.setRoles(('Manager',))
        
        # Folder content
        self.portal.invokeFactory('Folder', 'f1')
        self.portal['f1'].setTitle(u"Folder one")
        self.portal['f1'].setDescription(u"Folder one description")
        self.portal['f1'].reindexObject()
        
        # Content image
        self.portal['f1'].invokeFactory('Image', 'i1')
        self.portal['f1']['i1'].setTitle(u"Image one")
        self.portal['f1']['i1'].setDescription(u"Image one description")
        self.portal['f1']['i1'].setImage(OFS.Image.Image('test.gif', 'test.gif', open(TEST_IMAGE, 'rb')))
        self.portal['f1']['i1'].reindexObject()
        
        # Publish the folder 
        self.portal.portal_workflow.doActionFor(self.portal['f1'], 'publish')
        
        now = datetime.datetime.now(dateutil.tz.tzlocal())
        
        # Request the image
        browser = Browser()
        browser.open(self.portal['f1']['i1'].absolute_url())
        self.assertEquals('plone.download', browser.headers['X-Cache-Rule'])
        self.assertEquals('plone.app.caching.weakCaching', browser.headers['X-Cache-Operation'])
        # This should use cacheInBrowser
        self.assertEquals('max-age=0, must-revalidate, private', browser.headers['Cache-Control'])
        self.failIf(None == browser.headers.get('Last-Modified'))  # remove this when the next line works
        #self.assertEquals('---lastmodified---', browser.headers['Last-Modified'])
        self.failUnless(now > dateutil.parser.parse(browser.headers['Expires']))
        
        # Request the image again -- with an IMS header to test 304
        lastmodified = browser.headers['Last-Modified']
        browser = Browser()
        browser.raiseHttpErrors = False
        browser.addHeader('If-Modified-Since', lastmodified)
        browser.open(self.portal['f1']['i1'].absolute_url())
        self.assertEquals('plone.download', browser.headers['X-Cache-Rule'])
        self.assertEquals('plone.app.caching.weakCaching', browser.headers['X-Cache-Operation'])
        # This should be a 304 response
        self.assertEquals('304 Not Modified', browser.headers['Status'])
        self.assertEquals('', browser.contents)
        
        # Request an image scale
        browser = Browser()
        browser.open(self.portal['f1']['i1'].absolute_url() + '/image_preview')
        self.assertEquals('plone.download', browser.headers['X-Cache-Rule'])
        self.assertEquals('plone.app.caching.weakCaching', browser.headers['X-Cache-Operation'])
        # This should use cacheInBrowser
        self.assertEquals('max-age=0, must-revalidate, private', browser.headers['Cache-Control'])
        self.failIf(None == browser.headers.get('Last-Modified'))  # remove this when the next line works
        #self.assertEquals('---lastmodified---', browser.headers['Last-Modified'])
        self.failUnless(now > dateutil.parser.parse(browser.headers['Expires']))
    
    def test_downloads_proxy(self):
        self.addProfile('plone.app.caching:with-caching-proxy')
        self.cacheSettings.enabled = True
        
        self.setRoles(('Manager',))
        
        # Folder content
        self.portal.invokeFactory('Folder', 'f1')
        self.portal['f1'].setTitle(u"Folder one")
        self.portal['f1'].setDescription(u"Folder one description")
        self.portal['f1'].reindexObject()
        
        # Content image
        self.portal['f1'].invokeFactory('Image', 'i1')
        self.portal['f1']['i1'].setTitle(u"Image one")
        self.portal['f1']['i1'].setDescription(u"Image one description")
        self.portal['f1']['i1'].setImage(OFS.Image.Image('test.gif', 'test.gif', open(TEST_IMAGE, 'rb')))
        self.portal['f1']['i1'].reindexObject()
        
        now = datetime.datetime.now(dateutil.tz.tzlocal())
        
        # Request the image with Manager role
        browser = Browser()
        browser.addHeader('Authorization', 'Basic %s:%s' % (portal_owner, default_password,))
        browser.open(self.portal['f1']['i1'].absolute_url())
        self.assertEquals('plone.download', browser.headers['X-Cache-Rule'])
        self.assertEquals('plone.app.caching.moderateCaching', browser.headers['X-Cache-Operation'])
        # Folder not published yet so image should not be cached in proxy
        # so this should use cacheInBrowser
        self.assertEquals('max-age=0, must-revalidate, private', browser.headers['Cache-Control'])
        self.failIf(None == browser.headers.get('Last-Modified'))  # remove this when the next line works
        #self.assertEquals('---lastmodified---', browser.headers['Last-Modified'])
        self.failUnless(now > dateutil.parser.parse(browser.headers['Expires']))
        
        # Request an image scale with Manager role
        browser = Browser()
        browser.addHeader('Authorization', 'Basic %s:%s' % (portal_owner, default_password,))
        browser.open(self.portal['f1']['i1'].absolute_url() + '/image_preview')
        self.assertEquals('plone.download', browser.headers['X-Cache-Rule'])
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
        browser = Browser()
        browser.open(self.portal['f1']['i1'].absolute_url())
        self.assertEquals('plone.download', browser.headers['X-Cache-Rule'])
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
        self.assertEquals('plone.download', browser.headers['X-Cache-Rule'])
        self.assertEquals('plone.app.caching.moderateCaching', browser.headers['X-Cache-Operation'])
        # This should be a 304 response
        self.assertEquals('304 Not Modified', browser.headers['Status'])
        self.assertEquals('', browser.contents)
        
        # Request an image scale
        browser = Browser()
        browser.open(self.portal['f1']['i1'].absolute_url() + '/image_preview')
        self.assertEquals('plone.download', browser.headers['X-Cache-Rule'])
        self.assertEquals('plone.app.caching.moderateCaching', browser.headers['X-Cache-Operation'])
        # Now visible to anonymous so this should use cacheInProxy
        self.assertEquals('max-age=0, s-maxage=86400, must-revalidate', browser.headers['Cache-Control'])
        self.failIf(None == browser.headers.get('Last-Modified'))  # remove this when the next line works
        #self.assertEquals('---lastmodified---', browser.headers['Last-Modified'])
        self.failUnless(now > dateutil.parser.parse(browser.headers['Expires']))
    
    def test_resources(self):
        self.cacheSettings.enabled = True
        
        now = datetime.datetime.now(dateutil.tz.tzlocal())
        
        # Request a skin image
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
    
    def test_stable_resources(self):
        # We don't actually have any non-RR stable resources
        # What is the best way to test this?
        # Maybe not important since the RR test exercises the same code?
        pass
    
    def test_stable_resources_resource_registries(self):
        self.cacheSettings.enabled = True
        cssregistry = self.portal.portal_css
        
        now = datetime.datetime.now(dateutil.tz.tzlocal())
        
        # Request a ResourceRegistry resource
        browser = Browser()
        browser.open(cssregistry.absolute_url() + '/public.css')
        self.assertEquals('plone.stableResource', browser.headers['X-Cache-Rule'])
        self.assertEquals('plone.app.caching.strongCaching', browser.headers['X-Cache-Operation'])
        # This should use cacheInBrowserAndProxy
        self.assertEquals('max-age=31536000, proxy-revalidate, public', browser.headers['Cache-Control'])
        self.failIf(None == browser.headers.get('Last-Modified'))  # remove this when the next line works
        # self.assertEquals('---lastmodified---', browser.headers['Last-Modified'])
        timedelta = dateutil.parser.parse(browser.headers['Expires']) - now
        self.failUnless(timedelta > datetime.timedelta(seconds=31535990))
        # self.failUnless(timedelta > datetime.timedelta(seconds=604790))
        
        # Request the ResourceRegistry resource again -- with IMS header to test 304
        lastmodified = browser.headers['Last-Modified']
        browser = Browser()
        browser.raiseHttpErrors = False
        browser.addHeader('If-Modified-Since', lastmodified)
        browser.open(cssregistry.absolute_url() + '/public.css')
        self.assertEquals('plone.stableResource', browser.headers['X-Cache-Rule'])
        self.assertEquals('plone.app.caching.strongCaching', browser.headers['X-Cache-Operation'])
        # This should be a 304 response
        self.assertEquals('304 Not Modified', browser.headers['Status'])
        self.assertEquals('', browser.contents)
        
        # Request the ResourceRegistry resource -- with RR in debug mode
        cssregistry.setDebugMode(True)
        browser = Browser()
        browser.open(cssregistry.absolute_url() + '/public.css')
        self.assertEquals('plone.stableResource', browser.headers['X-Cache-Rule'])
        self.assertEquals('plone.app.caching.strongCaching', browser.headers['X-Cache-Operation'])
        # This should use doNotCache
        self.assertEquals('max-age=0, must-revalidate, private', browser.headers['Cache-Control'])
        self.assertEquals(None, browser.headers.get('Last-Modified'))
        self.failUnless(now > dateutil.parser.parse(browser.headers['Expires']))
    
    def test_auto_purge_content_types(self):
        
        self.setRoles(('Manager',))
        
        # Non-folder content
        self.portal.invokeFactory('Document', 'd1')
        self.portal['d1'].setTitle(u"Document one")
        self.portal['d1'].setDescription(u"Document one description")
        self.portal['d1'].setText("<p>Body one</p>")
        self.portal['d1'].reindexObject()
        
        self.setRoles(('Member',))
        
        # Purging disabled
        self.cachePurgingSettings.enabled = False
        self.cachePurgingSettings.cachingProxies = ()
        self.ploneCacheSettings.purgedContentTypes = ()
        
        editURL = self.portal['d1'].absolute_url() + '/edit'
        
        browser = Browser()
        browser.handleErrors = False
        
        browser.open(self.portal.absolute_url() + '/login')
        browser.getControl(name='__ac_name').value = default_user
        browser.getControl(name='__ac_password').value = default_password
        browser.getControl('Log in').click()
        
        browser.open(editURL)
        browser.getControl(name='title').value = u"Title 1"
        browser.getControl(name='form.button.save').click()
        
        self.assertEquals([], self.purger._sync)
        self.assertEquals([], self.purger._async)
        
        # Enable purging, but not the content type
        self.cachePurgingSettings.enabled = True
        self.cachePurgingSettings.cachingProxies = ('http://localhost:1234',)
        self.ploneCacheSettings.purgedContentTypes = ()
        
        browser.open(editURL)
        browser.getControl(name='title').value = u"Title 2"
        browser.getControl(name='form.button.save').click()
        
        self.assertEquals([], self.purger._sync)
        self.assertEquals([], self.purger._async)
        
        # Enable the content type, but disable purging
        self.cachePurgingSettings.enabled = False
        self.cachePurgingSettings.cachingProxies = ('http://localhost:1234',)
        self.ploneCacheSettings.purgedContentTypes = ()
        
        browser.open(editURL)
        browser.getControl(name='title').value = u"Title 3"
        browser.getControl(name='form.button.save').click()
        
        self.assertEquals([], self.purger._sync)
        self.assertEquals([], self.purger._async)
        
        # Enable properly
        self.cachePurgingSettings.enabled = True
        self.cachePurgingSettings.cachingProxies = ('http://localhost:1234',)
        self.ploneCacheSettings.purgedContentTypes = ('Document',)
        
        browser.open(editURL)
        browser.getControl(name='title').value = u"Title 4"
        browser.getControl(name='form.button.save').click()
        
        self.assertEquals([], self.purger._sync)
        self.assertEquals(set([
                'http://localhost:1234/plone/d1',
                'http://localhost:1234/plone/d1/document_view',
                'http://localhost:1234/plone/d1/',
                'http://localhost:1234/plone/d1/view']), set(self.purger._async))
        

def test_suite():
    return unittest.defaultTestLoader.loadTestsFromName(__name__)





