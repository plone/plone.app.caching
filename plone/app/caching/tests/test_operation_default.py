from plone.app.caching.testing import getToken
from plone.app.caching.testing import PLONE_APP_CACHING_FUNCTIONAL_TESTING
from plone.app.testing import setRoles
from plone.app.testing import TEST_USER_ID
from plone.app.testing import TEST_USER_NAME
from plone.app.testing import TEST_USER_PASSWORD
from plone.caching.interfaces import ICacheSettings
from plone.registry.interfaces import IRegistry
from plone.testing.z2 import Browser
from zope.component import getUtility
from zope.globalrequest import setRequest

import unittest


class TestOperationDefault(unittest.TestCase):
    """
    Test various edge cases.
    """

    layer = PLONE_APP_CACHING_FUNCTIONAL_TESTING

    def setUp(self):
        self.app = self.layer["app"]
        self.portal = self.layer["portal"]

        setRequest(self.portal.REQUEST)

        self.registry = getUtility(IRegistry)
        self.cacheSettings = self.registry.forInterface(ICacheSettings)
        self.cacheSettings.enabled = True

    def tearDown(self):
        setRequest(None)

    def test_last_modified_no_etags(self):
        """
        When a new content type is added, the resulting page should not be
        cached since it has messages. However, it should only trigger an etag
        if its been configured to use etags
        """
        # Add folder content
        setRoles(self.portal, TEST_USER_ID, ("Manager",))
        self.portal.invokeFactory("Folder", "f1")
        self.portal["f1"].title = "Folder one"
        self.portal["f1"].description = "Folder one description"
        self.portal["f1"].reindexObject()

        self.cacheSettings.operationMapping = {
            "plone.content.itemView": "plone.app.caching.weakCaching"
        }
        self.registry["plone.app.caching.weakCaching.lastModified"] = True
        self.registry["plone.app.caching.weakCaching.etags"] = None

        import transaction

        transaction.commit()

        # log in and create a content type
        browser = Browser(self.app)
        browser.addHeader(
            "Authorization",
            f"Basic {TEST_USER_NAME}:{TEST_USER_PASSWORD}",
        )
        browser.open(
            f"{self.portal['f1'].absolute_url()}/++add++Document",
        )
        browser.getControl(
            name="form.widgets.IDublinCore.title"
        ).value = "dummy content"
        browser.getControl("Save").click()
        self.assertNotIn("Etag", browser.headers)

        # now set up etags and make sure that a header is added
        self.registry["plone.app.caching.weakCaching.etags"] = ("lastModified",)
        import transaction

        transaction.commit()
        url = self.portal["f1"].absolute_url()
        token = getToken(TEST_USER_NAME)
        browser.open(f"{url}/dummy-content/edit?_authenticator={token}")
        browser.getControl(
            name="form.widgets.IDublinCore.title"
        ).value = "dummy content"
        browser.getControl("Save").click()
        self.assertIn("Etag", browser.headers)
