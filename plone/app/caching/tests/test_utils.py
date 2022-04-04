from Acquisition import Explicit
from datetime import date
from datetime import datetime
from plone.app.caching.interfaces import IPloneCacheSettings
from plone.app.caching.utils import getObjectDefaultView
from plone.app.caching.utils import isPurged
from plone.registry import Registry
from plone.registry.fieldfactory import persistentFieldAdapter
from plone.registry.interfaces import IRegistry
from plone.testing.zca import UNIT_TESTING
from Products.CMFCore.interfaces import IDynamicType
from Products.CMFDynamicViewFTI.interfaces import IBrowserDefault
from zope.component import getUtility
from zope.component import provideAdapter
from zope.component import provideUtility
from zope.interface import implementer

import pkg_resources
import pytz
import unittest


TEST_TIMEZONE = "Europe/Vienna"
TEST_IMAGE = pkg_resources.resource_filename("plone.app.caching.tests", "test.gif")


def stable_now():
    """Patch localized_now to allow stable results in tests."""
    tzinfo = pytz.timezone(TEST_TIMEZONE)
    now = datetime(2013, 5, 5, 10, 0, 0).replace(microsecond=0)
    now = tzinfo.localize(now)  # set tzinfo with correct DST offset
    return now


def normalize_etag(value):
    split_value = value.split("|")
    # The last component is expected to be the resourceRegistries ETag,
    # which is a time-based component, making it hard to test.
    last = split_value.pop()
    if str(date.today().year) in last:
        # yes, this is time based, remove it
        value = "|".join(split_value)
        return f'{value}|"'
    # return original
    return value


def test_image():
    from plone.namedfile.file import NamedBlobImage

    with open(TEST_IMAGE, "rb") as myfile:
        return NamedBlobImage(
            data=myfile.read(),
            filename=TEST_IMAGE,
        )


@implementer(IBrowserDefault, IDynamicType)
class DummyContent(Explicit):
    def __init__(self, portal_type="testtype", defaultView="defaultView"):
        self.portal_type = portal_type
        self._defaultView = defaultView

    def defaultView(self):
        return self._defaultView


class DummyNotContent(Explicit):
    pass


class DummyFTI:
    def __init__(self, portal_type, viewAction=""):
        self.id = portal_type
        self._actions = {
            "object/view": {"url": viewAction},
        }

    def getActionInfo(self, name):
        return self._actions[name]

    def queryMethodID(self, id, default=None, context=None):
        if id == "(Default)":
            return "defaultView"
        elif id == "view":
            return "@@defaultView"
        return default


@implementer(IDynamicType)
class DummyNotBrowserDefault(Explicit):
    def __init__(self, portal_type="testtype", viewAction=""):
        self.portal_type = portal_type
        self._viewAction = viewAction

    def getTypeInfo(self):
        return DummyFTI(self.portal_type, self._viewAction)


class TestIsPurged(unittest.TestCase):

    layer = UNIT_TESTING

    def setUp(self):
        provideAdapter(persistentFieldAdapter)

    def test_no_registry(self):
        content = DummyContent()
        self.assertFalse(isPurged(content))

    def test_no_settings(self):
        provideUtility(Registry(), IRegistry)
        content = DummyContent()
        self.assertFalse(isPurged(content))

    def test_no_portal_type(self):
        provideUtility(Registry(), IRegistry)
        registry = getUtility(IRegistry)
        registry.registerInterface(IPloneCacheSettings)

        ploneSettings = registry.forInterface(IPloneCacheSettings)
        ploneSettings.purgedContentTypes = ("testtype",)

        content = DummyNotContent()
        self.assertFalse(isPurged(content))

    def test_not_listed(self):
        provideUtility(Registry(), IRegistry)
        registry = getUtility(IRegistry)
        registry.registerInterface(IPloneCacheSettings)

        ploneSettings = registry.forInterface(IPloneCacheSettings)
        ploneSettings.purgedContentTypes = (
            "File",
            "Image",
        )

        content = DummyContent()
        self.assertFalse(isPurged(content))

    def test_listed(self):
        provideUtility(Registry(), IRegistry)
        registry = getUtility(IRegistry)
        registry.registerInterface(IPloneCacheSettings)

        ploneSettings = registry.forInterface(IPloneCacheSettings)
        ploneSettings.purgedContentTypes = (
            "File",
            "Image",
            "testtype",
        )

        content = DummyContent()
        self.assertTrue(isPurged(content))


class TestGetObjectDefaultPath(unittest.TestCase):

    layer = UNIT_TESTING

    def test_not_content(self):
        context = DummyNotContent()
        self.assertIsNone(getObjectDefaultView(context))

    def test_browserdefault(self):
        context = DummyContent()
        self.assertEqual("defaultView", getObjectDefaultView(context))

    def test_browserviewdefault(self):
        context = DummyContent(defaultView="@@defaultView")
        self.assertEqual("defaultView", getObjectDefaultView(context))

    def test_not_IBrowserDefault_methodid(self):
        context = DummyNotBrowserDefault("testtype", "string:${object_url}/view")
        self.assertEqual("defaultView", getObjectDefaultView(context))

    def test_not_IBrowserDefault_default_method(self):
        context = DummyNotBrowserDefault("testtype", "string:${object_url}/")
        self.assertEqual("defaultView", getObjectDefaultView(context))

    def test_not_IBrowserDefault_actiononly(self):
        context = DummyNotBrowserDefault("testtype", "string:${object_url}/defaultView")
        self.assertEqual("defaultView", getObjectDefaultView(context))
