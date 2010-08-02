import unittest

from Products.PloneTestCase.ptc import FunctionalTestCase
from Products.PloneTestCase.ptc import default_user, default_password

from plone.app.caching.tests.layer import Layer

from Products.Five.testbrowser import Browser

from zope.component import getUtility

from zope.globalrequest import setRequest

from plone.registry.interfaces import IRegistry
from plone.caching.interfaces import ICacheSettings

class TestOperationParameters(FunctionalTestCase):
    """This test aims to test the effect of changing various caching operation
    parameters.
    """
    
    layer = Layer
    
    def afterSetUp(self):
        setRequest(self.portal.REQUEST)
        self.registry = getUtility(IRegistry)
        self.cacheSettings = self.registry.forInterface(ICacheSettings)
        self.cacheSettings.enabled = True
    
    def beforeTearDown(self):
        setRequest(None)
    
    def test_anon_only(self):
        
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
        
        # Set pages to have strong caching so that we can see the difference
        # between logged in and anonymous
        
        self.cacheSettings.operationMapping = {'plone.content.itemView': 'plone.app.caching.strongCaching'}
        self.registry['plone.app.caching.strongCaching.anonOnly'] = True
        
        # Publish the folder and page
        self.portal.portal_workflow.doActionFor(self.portal['f1'], 'publish')
        self.portal.portal_workflow.doActionFor(self.portal['f1']['d1'], 'publish')
        
        # View the page as anonymous
        browser = Browser()
        browser.open(self.portal['f1']['d1'].absolute_url())
        self.assertEquals('plone.content.itemView', browser.headers['X-Cache-Rule'])
        self.assertEquals('plone.app.caching.strongCaching', browser.headers['X-Cache-Operation'])
        self.failUnless(testText in browser.contents)
        self.assertEquals('max-age=86400, proxy-revalidate, public', browser.headers['Cache-Control'])
        
        # View the page as logged-in
        browser = Browser()
        browser.addHeader('Authorization', 'Basic %s:%s' % (default_user, default_password,))
        browser.open(self.portal['f1']['d1'].absolute_url())
        self.assertEquals('plone.content.itemView', browser.headers['X-Cache-Rule'])
        self.assertEquals('plone.app.caching.strongCaching', browser.headers['X-Cache-Operation'])
        self.failUnless(testText in browser.contents)
        self.assertEquals('max-age=0, must-revalidate, private', browser.headers['Cache-Control'])
        
def test_suite():
    return unittest.defaultTestLoader.loadTestsFromName(__name__)

