from plone.app.caching.interfaces import IPloneCacheSettings
from plone.app.caching.testing import getToken
from plone.app.caching.testing import PLONE_APP_CACHING_FUNCTIONAL_TESTING
from plone.app.testing import applyProfile
from plone.app.testing import setRoles
from plone.app.testing import SITE_OWNER_NAME
from plone.app.testing import SITE_OWNER_PASSWORD
from plone.app.testing import TEST_USER_ID
from plone.app.testing import TEST_USER_NAME
from plone.app.testing import TEST_USER_PASSWORD
from plone.app.textfield.value import RichTextValue
from plone.cachepurging.interfaces import ICachePurgingSettings
from plone.cachepurging.interfaces import IPurger
from plone.caching.interfaces import ICacheSettings
from plone.namedfile.file import NamedImage
from plone.registry.interfaces import IRegistry
from plone.testing.z2 import Browser
from zope.component import getUtility
from zope.globalrequest import setRequest

import OFS.Image
import pkg_resources
import unittest


TEST_IMAGE = pkg_resources.resource_filename("plone.app.caching.tests", "test.gif")
TEST_FILE = pkg_resources.resource_filename("plone.app.caching.tests", "test.gif")


class TestOperations(unittest.TestCase):
    """This test aims to exercise some generic caching operations in a semi-
    realistic scenario.

    The caching operations defined by GS profiles are grouped elsewhere.
    See `test_profile_without_caching_proxy.py` and
    `test_profile_with_caching_proxy.py`

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

    layer = PLONE_APP_CACHING_FUNCTIONAL_TESTING

    def setUp(self):
        self.app = self.layer["app"]
        self.portal = self.layer["portal"]

        setRequest(self.portal.REQUEST)

        applyProfile(self.portal, "plone.app.caching:without-caching-proxy")

        self.registry = getUtility(IRegistry)

        self.cacheSettings = self.registry.forInterface(ICacheSettings)
        self.cachePurgingSettings = self.registry.forInterface(ICachePurgingSettings)
        self.ploneCacheSettings = self.registry.forInterface(IPloneCacheSettings)

        self.purger = getUtility(IPurger)
        self.purger.reset()

    def tearDown(self):
        setRequest(None)

    def test_controlpanel(self):
        browser = Browser(self.app)
        browser.handleErrors = False
        browser.addHeader(
            "Authorization",
            f"Basic {SITE_OWNER_NAME}:{SITE_OWNER_PASSWORD}",
        )

        browser.open(f"{self.portal.absolute_url()}/@@caching-controlpanel")  # noqa
        browser.getControl(name="enabled:boolean").value = "checked"
        browser.getControl("Save").click()

    def test_disabled(self):
        self.cacheSettings.enabled = False

        setRoles(self.portal, TEST_USER_ID, ("Manager",))

        # Folder content
        self.portal.invokeFactory("Folder", "f1")
        self.portal["f1"].title = "Folder one"
        self.portal["f1"].description = "Folder one description"
        self.portal["f1"].reindexObject()

        # Publish the folder
        self.portal.portal_workflow.doActionFor(self.portal["f1"], "publish")

        # Non-folder content
        self.portal["f1"].invokeFactory("Document", "d1")
        self.portal["f1"]["d1"].title = "Document one"
        self.portal["f1"]["d1"].description = "Document one description"
        self.portal["f1"]["d1"].text = RichTextValue(
            "<p>Body one</p>",
            "text/plain",
            "text/html",
        )
        self.portal["f1"]["d1"].reindexObject()

        # Publish the document
        self.portal.portal_workflow.doActionFor(self.portal["f1"]["d1"], "publish")

        # Content image
        self.portal["f1"].invokeFactory("Image", "i1")
        self.portal["f1"]["i1"].title = "Image one"
        self.portal["f1"]["i1"].description = "Image one description"
        with open(TEST_IMAGE, "rb") as myfile:
            self.portal["f1"]["i1"].image = NamedImage(myfile, "image/gif", "test.gif")
        self.portal["f1"]["i1"].reindexObject()

        # Content file
        self.portal["f1"].invokeFactory("File", "f1")
        self.portal["f1"]["f1"].title = "File one"
        self.portal["f1"]["f1"].description = "File one description"
        with open(TEST_FILE, "rb") as myfile:
            self.portal["f1"]["f1"].file = OFS.Image.File(
                "test.gif", "test.gif", myfile
            )
        self.portal["f1"]["f1"].reindexObject()

        # OFS image (custom folder)
        with open(TEST_IMAGE, "rb") as myfile:
            OFS.Image.manage_addImage(
                self.portal["portal_skins"]["custom"],
                "test.gif",
                myfile,
            )

        setRoles(self.portal, TEST_USER_ID, ("Member",))

        import transaction

        transaction.commit()
        browser = Browser(self.app)
        browser.handleErrors = False

        # Check that we can open all without errors and without cache headers
        browser.open(self.portal.absolute_url())
        self.assertNotIn("Cache-Control", browser.headers)

        browser.open(self.portal["f1"].absolute_url())
        self.assertIn("Folder one description", browser.contents)
        self.assertNotIn("Cache-Control", browser.headers)

        browser.open(self.portal["f1"]["d1"].absolute_url())
        self.assertIn("Document one description", browser.contents)
        self.assertNotIn("Cache-Control", browser.headers)

        browser.open(self.portal["f1"]["i1"].absolute_url())
        self.assertNotIn("Cache-Control", browser.headers)

        browser.open(self.portal["f1"]["f1"].absolute_url())
        self.assertNotIn("Cache-Control", browser.headers)

        browser.open(self.portal.absolute_url() + "/portal_skins/custom/test.gif")
        self.assertNotIn("Cache-Control", browser.headers)

        browser.open(self.portal.absolute_url() + "/++resource++plone.app.caching.gif")
        # Set by resources themselves, but irrelevant to this test:
        # self.assertTrue('Cache-Control' in browser.headers)

    def test_auto_purge_content_types(self):

        setRoles(self.portal, TEST_USER_ID, ("Manager",))

        # Non-folder content
        self.portal.invokeFactory("Document", "d1")
        self.portal["d1"].title = "Document one"
        self.portal["d1"].description = "Document one description"
        self.portal["d1"].text = RichTextValue(
            "<p>Body one</p>",
            "text/plain",
            "text/html",
        )
        self.portal["d1"].reindexObject()

        setRoles(self.portal, TEST_USER_ID, ("Member",))

        # Purging disabled
        self.cachePurgingSettings.enabled = False
        self.cachePurgingSettings.cachingProxies = ()
        self.ploneCacheSettings.purgedContentTypes = ()
        url = self.portal["d1"].absolute_url()
        token = getToken(TEST_USER_NAME)
        editURL = f"{url}/edit?_authenticator={token}"

        import transaction

        transaction.commit()

        browser = Browser(self.app)
        browser.handleErrors = False
        browser.addHeader(
            "Authorization",
            f"Basic {TEST_USER_NAME}:{TEST_USER_PASSWORD}",
        )

        browser.open(editURL)

        browser.getControl(name="form.widgets.IDublinCore.title").value = "Title 1"
        browser.getControl("Save").click()

        self.assertEqual([], self.purger._sync)
        self.assertEqual([], self.purger._async)

        # Enable purging, but not the content type
        self.cachePurgingSettings.enabled = True
        self.cachePurgingSettings.cachingProxies = ("http://localhost:1234",)
        self.ploneCacheSettings.purgedContentTypes = ()

        import transaction

        transaction.commit()

        browser.open(editURL)
        browser.getControl(name="form.widgets.IDublinCore.title").value = "Title 2"
        browser.getControl("Save").click()

        self.assertEqual([], self.purger._sync)
        self.assertEqual([], self.purger._async)

        # Enable the content type, but disable purging
        self.cachePurgingSettings.enabled = False
        self.cachePurgingSettings.cachingProxies = ("http://localhost:1234",)
        self.ploneCacheSettings.purgedContentTypes = ()

        import transaction

        transaction.commit()

        browser.open(editURL)
        browser.getControl(name="form.widgets.IDublinCore.title").value = "Title 3"
        browser.getControl("Save").click()

        self.assertEqual([], self.purger._sync)
        self.assertEqual([], self.purger._async)

        # Enable properly
        self.cachePurgingSettings.enabled = True
        self.cachePurgingSettings.cachingProxies = ("http://localhost:1234",)
        self.ploneCacheSettings.purgedContentTypes = ("Document",)

        import transaction

        transaction.commit()

        browser.open(editURL)
        browser.getControl(name="form.widgets.IDublinCore.title").value = "Title 4"
        browser.getControl("Save").click()

        self.assertEqual([], self.purger._sync)
        self.assertEqual(
            {
                "http://localhost:1234/plone/d1",
                "http://localhost:1234/plone/d1/document_view",
                "http://localhost:1234/plone/d1/",
                "http://localhost:1234/plone/d1/view",
            },
            set(self.purger._async),
        )
