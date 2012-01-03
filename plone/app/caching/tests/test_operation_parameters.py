import unittest2 as unittest

from plone.testing.z2 import Browser

from plone.app.testing import TEST_USER_ID, TEST_USER_PASSWORD
from plone.app.testing import setRoles

from zope.component import getUtility

from zope.globalrequest import setRequest

from plone.registry.interfaces import IRegistry
from plone.caching.interfaces import ICacheSettings

from plone.app.caching.testing import PLONE_APP_CACHING_FUNCTIONAL_TESTING

class TestOperationParameters(unittest.TestCase):
    """This test aims to test the effect of changing various caching operation
    parameters.
    """

    layer = PLONE_APP_CACHING_FUNCTIONAL_TESTING

    def setUp(self):
        self.app = self.layer['app']
        self.portal = self.layer['portal']

        setRequest(self.portal.REQUEST)

        self.registry = getUtility(IRegistry)
        self.cacheSettings = self.registry.forInterface(ICacheSettings)
        self.cacheSettings.enabled = True

    def tearDown(self):
        setRequest(None)

    def test_anon_only(self):

        # Add folder content
        setRoles(self.portal, TEST_USER_ID, ('Manager',))
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

        self.cacheSettings.operationMapping = {'plone.content.itemView': 'plone.app.caching.moderateCaching'}
        self.registry['plone.app.caching.moderateCaching.smaxage'] = 60
        self.registry['plone.app.caching.moderateCaching.vary'] = 'X-Anonymous'
        self.registry['plone.app.caching.moderateCaching.anonOnly'] = True

        # Publish the folder and page
        self.portal.portal_workflow.doActionFor(self.portal['f1'], 'publish')
        self.portal.portal_workflow.doActionFor(self.portal['f1']['d1'], 'publish')

        import transaction; transaction.commit()

        # View the page as anonymous
        browser = Browser(self.app)
        browser.open(self.portal['f1']['d1'].absolute_url())
        self.assertEquals('plone.content.itemView', browser.headers['X-Cache-Rule'])
        self.assertEquals('plone.app.caching.moderateCaching', browser.headers['X-Cache-Operation'])
        self.failUnless(testText in browser.contents)
        self.assertEquals('max-age=0, s-maxage=60, must-revalidate', browser.headers['Cache-Control'])
        self.assertEquals('X-Anonymous', browser.headers['Vary'])
        self.failIf('Etag' in browser.headers)

        # View the page as logged-in
        browser = Browser(self.app)
        browser.addHeader('Authorization', 'Basic %s:%s' % (TEST_USER_ID, TEST_USER_PASSWORD,))
        browser.open(self.portal['f1']['d1'].absolute_url())
        self.assertEquals('plone.content.itemView', browser.headers['X-Cache-Rule'])
        self.assertEquals('plone.app.caching.moderateCaching', browser.headers['X-Cache-Operation'])
        self.failUnless(testText in browser.contents)
        self.assertEquals('max-age=0, must-revalidate, private', browser.headers['Cache-Control'])
        self.failUnless('Etag' in browser.headers)
