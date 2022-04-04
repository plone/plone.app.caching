from Acquisition import aq_base
from Acquisition import Explicit
from os.path import dirname
from os.path import join
from plone.app.caching.interfaces import IPloneCacheSettings
from plone.app.caching.purge import ContentPurgePaths
from plone.app.caching.purge import DiscussionItemPurgePaths
from plone.app.caching.purge import purgeOnModified
from plone.app.caching.purge import purgeOnMovedOrRemoved
from plone.app.caching.purge import ScalesPurgePaths
from plone.app.caching.testing import PLONE_APP_CACHING_FUNCTIONAL_TESTING
from plone.app.contenttypes.behaviors.leadimage import ILeadImageBehavior
from plone.app.contenttypes.interfaces import IDocument
from plone.app.testing import setRoles
from plone.app.testing import TEST_USER_ID
from plone.app.testing import TEST_USER_ROLES
from plone.behavior.interfaces import IBehavior
from plone.behavior.interfaces import IBehaviorAssignable
from plone.namedfile.file import NamedFile
from plone.namedfile.file import NamedImage
from plone.registry import Registry
from plone.registry.fieldfactory import persistentFieldAdapter
from plone.registry.interfaces import IRegistry
from plone.testing.zca import UNIT_TESTING
from Products.CMFCore.interfaces import IContentish
from Products.CMFCore.interfaces import IDiscussionResponse
from Products.CMFDynamicViewFTI.interfaces import IBrowserDefault
from z3c.caching.interfaces import IPurgeEvent
from z3c.caching.interfaces import IPurgePaths
from zope.component import adapter
from zope.component import getUtility
from zope.component import provideAdapter
from zope.component import provideHandler
from zope.component import provideUtility
from zope.component import queryUtility
from zope.component.event import objectEventNotify
from zope.event import notify
from zope.globalrequest import setRequest
from zope.interface import implementer
from zope.lifecycleevent import ObjectAddedEvent
from zope.lifecycleevent import ObjectModifiedEvent
from zope.lifecycleevent import ObjectMovedEvent
from zope.lifecycleevent import ObjectRemovedEvent

import unittest


def getData(filename):
    filename = join(dirname(__file__), filename)
    with open(filename, "rb") as fh:
        data = fh.read()
    return data


class Handler:
    def __init__(self):
        self.invocations = []

    @adapter(IPurgeEvent)
    def handler(self, event):
        self.invocations.append(event)


class FauxRequest(dict):
    REQUEST_METHOD = "POST"
    URL = "http://nohost/test"
    form = ("form.submitted",)


@implementer(IContentish)
class FauxNonContent(Explicit):
    def __init__(self, name=None):
        self.__name__ = name
        self.__parent__ = None  # may be overridden by acquisition

    def getId(self):
        return self.__name__

    def virtual_url_path(self):
        parent = aq_base(self.__parent__)
        if parent is not None:
            return parent.virtual_url_path() + "/" + self.__name__
        else:
            return self.__name__

    def getPhysicalPath(self):
        return ("",)

    def getParentNode(self):
        return FauxNonContent("folder")


@implementer(IBrowserDefault)
class FauxContent(FauxNonContent):

    portal_type = "testtype"

    def defaultView(self):
        return "default-view"


@implementer(IDiscussionResponse)
class FauxDiscussable(Explicit):
    pass


class TestPurgeRedispatch(unittest.TestCase):

    layer = UNIT_TESTING

    def setUp(self):
        self.handler = Handler()
        provideHandler(self.handler.handler)
        provideHandler(objectEventNotify)
        provideHandler(purgeOnModified)
        provideHandler(purgeOnMovedOrRemoved)
        provideAdapter(persistentFieldAdapter)
        provideUtility(Registry(), IRegistry)
        registry = getUtility(IRegistry)
        registry.registerInterface(IPloneCacheSettings)
        ploneSettings = registry.forInterface(IPloneCacheSettings)
        ploneSettings.purgedContentTypes = ("testtype",)

    def test_not_purged(self):
        context = FauxNonContent("new").__of__(FauxContent())

        notify(ObjectModifiedEvent(context))
        notify(ObjectAddedEvent(context))
        notify(ObjectRemovedEvent(context))

        self.assertEqual(0, len(self.handler.invocations))

    def test_modified(self):
        context = FauxContent()

        notify(ObjectModifiedEvent(context))

        self.assertEqual(1, len(self.handler.invocations))
        self.assertEqual(context, self.handler.invocations[0].object)

    def test_added(self):
        context = FauxContent("new").__of__(FauxContent())

        notify(ObjectAddedEvent(context, context.__parent__, "new"))

        self.assertEqual(0, len(self.handler.invocations))

    def test_moved(self):
        context = FauxContent("new").__of__(FauxContent())
        request = FauxRequest()
        setRequest(request)

        notify(
            ObjectMovedEvent(context, FauxContent(), "old", context.__parent__, "new")
        )

        self.assertEqual(2, len(self.handler.invocations))
        self.assertEqual(context, self.handler.invocations[0].object)

    def test_renamed(self):
        context = FauxContent("new").__of__(FauxContent())

        notify(
            ObjectMovedEvent(
                context, context.__parent__, "old", context.__parent__, "new"
            )
        )

        self.assertEqual(2, len(self.handler.invocations))
        self.assertEqual(context, self.handler.invocations[0].object)

    def test_removed(self):
        context = FauxContent("new").__of__(FauxContent())
        request = FauxRequest()
        request.URL = "http://nohost/delete_confirmation"
        setRequest(request)

        notify(ObjectRemovedEvent(context, context.__parent__, "new"))

        self.assertEqual(2, len(self.handler.invocations))
        self.assertEqual(context, self.handler.invocations[0].object)


class TestContentPurgePaths(unittest.TestCase):

    layer = UNIT_TESTING

    def test_no_default_view(self):
        context = FauxNonContent("foo")
        purger = ContentPurgePaths(context)

        self.assertEqual(["/foo/", "/foo/view"], list(purger.getRelativePaths()))
        self.assertEqual([], list(purger.getAbsolutePaths()))

    def test_default_view(self):
        context = FauxContent("foo")
        purger = ContentPurgePaths(context)

        self.assertEqual(
            ["/foo/", "/foo/view", "/foo/default-view"], list(purger.getRelativePaths())
        )
        self.assertEqual([], list(purger.getAbsolutePaths()))

    def test_parent_not_default_view(self):
        context = FauxContent("foo").__of__(FauxContent("bar"))
        purger = ContentPurgePaths(context)

        self.assertEqual(
            ["/bar/foo/", "/bar/foo/view", "/bar/foo/default-view"],
            list(purger.getRelativePaths()),
        )
        self.assertEqual([], list(purger.getAbsolutePaths()))

    def test_parent_default_view(self):
        context = FauxContent("default-view").__of__(FauxContent("bar"))
        purger = ContentPurgePaths(context)
        self.assertEqual(
            [
                "/bar/default-view/",
                "/bar/default-view/view",
                "/bar/default-view/default-view",
                "/bar",
                "/bar/",
                "/bar/view",
                "/bar/@comments",
            ],
            list(purger.getRelativePaths()),
        )
        self.assertEqual([], list(purger.getAbsolutePaths()))


class TestDiscussionItemPurgePaths(unittest.TestCase):

    layer = UNIT_TESTING

    def setUp(self):
        @implementer(IPurgePaths)
        @adapter(FauxContent)
        class FauxContentPurgePaths:
            def __init__(self, context):
                self.context = context

            def getRelativePaths(self):
                return ["/" + self.context.virtual_url_path()]

            def getAbsolutePaths(self):
                return ["/purgeme"]

        provideAdapter(FauxContentPurgePaths, name="testpurge")

    def test_no_tool(self):
        root = FauxContent("")
        content = FauxContent("foo").__of__(root)
        discussable = FauxDiscussable().__of__(content)

        request = FauxRequest()
        setRequest(request)

        purge = DiscussionItemPurgePaths(discussable)

        self.assertEqual([], list(purge.getRelativePaths()))
        self.assertEqual([], list(purge.getAbsolutePaths()))

    def test_no_request(self):
        root = FauxContent("app")
        content = FauxContent("foo").__of__(root)
        discussable = FauxDiscussable().__of__(content)

        class FauxPloneTool:
            def getDiscussionThread(self, item):
                return [content, item]

        root.plone_utils = FauxPloneTool()

        setRequest(None)

        purge = DiscussionItemPurgePaths(discussable)

        self.assertEqual([], list(purge.getRelativePaths()))
        self.assertEqual([], list(purge.getAbsolutePaths()))

    def test_no_discussion_thread(self):
        root = FauxContent("app")
        content = FauxContent("foo").__of__(root)
        discussable = FauxDiscussable().__of__(content)

        class FauxPloneTool:
            def getDiscussionThread(self, item):
                return []

        root.plone_utils = FauxPloneTool()

        request = FauxRequest()
        setRequest(request)

        purge = DiscussionItemPurgePaths(discussable)

        self.assertEqual([], list(purge.getRelativePaths()))
        self.assertEqual([], list(purge.getAbsolutePaths()))

    def test_paths_of_root(self):
        root = FauxContent("app")
        content = FauxContent("foo").__of__(root)
        discussable = FauxDiscussable().__of__(content)

        class FauxPloneTool:
            def getDiscussionThread(self, item):
                return [content, item]

        root.plone_utils = FauxPloneTool()

        request = FauxRequest()
        setRequest(request)

        purge = DiscussionItemPurgePaths(discussable)

        self.assertEqual(["/app/foo"], list(purge.getRelativePaths()))
        self.assertEqual(["/purgeme"], list(purge.getAbsolutePaths()))


class TestScalesPurgePaths(unittest.TestCase):

    layer = PLONE_APP_CACHING_FUNCTIONAL_TESTING

    def setUp(self):

        self.portal = self.layer["portal"]
        setRoles(self.portal, TEST_USER_ID, ["Manager"])
        self.portal.invokeFactory("Folder", "media")
        self.folder = self.portal.media
        self.folder.invokeFactory("Image", "image", title="Test Image")
        self.image_type = self.folder["image"]
        self.image_type.image = NamedImage(
            getData("data/plone-app-caching.jpg"), "image/jpg", "plone-app-caching.jpg"
        )
        self.folder.invokeFactory("File", "file", title="Töst File")
        self.file = self.folder["file"]
        self.file.file = NamedFile(
            getData("data/testfile.csv"), "text/csv", "data/töstfile.csv"
        )

        # Create a page with a lead image.
        # For the purposes of testing, we will use the Document type and
        # a custom IBehaviorAssignable adapter to mark the behavior as enabled.

        @implementer(IBehaviorAssignable)
        @adapter(IDocument)
        class TestingAssignable:

            enabled = [ILeadImageBehavior]
            name = "plone.leadimage"

            def __init__(self, context):
                self.context = context

            def supports(self, behavior_interface):
                return behavior_interface in self.enabled

            def enumerateBehaviors(self):
                behavior = queryUtility(IBehavior, name=self.name)
                if behavior is not None:
                    yield behavior

        provideAdapter(TestingAssignable)

        self.folder.invokeFactory("Document", "page", title="Test Page")
        self.page = self.folder["page"]

        leadimage_adapter = ILeadImageBehavior(self.page)
        leadimage_adapter.image = NamedImage(
            getData("data/plone-app-caching.jpg"), "image/jpg", "plone-app-caching.jpg"
        )

        setRoles(self.portal, TEST_USER_ID, TEST_USER_ROLES)

    def test_scale_purge_paths_image(self):
        prefix = "/".join(self.image_type.getPhysicalPath())
        purge = ScalesPurgePaths(self.image_type)

        scales = purge.getScales()
        scalepaths = [prefix + "/@@images/image/" + str(i) for i in scales]
        scalepaths += [prefix + "/images/image/" + str(i) for i in scales]

        paths = [x for x in purge.getRelativePaths()]
        [self.assertIn(j, paths) for j in scalepaths]

    def test_scale_purge_paths_page(self):
        prefix = "/".join(self.page.getPhysicalPath())
        purge = ScalesPurgePaths(self.page)

        scales = purge.getScales()
        scalepaths = [prefix + "/@@images/image/" + str(i) for i in scales]
        scalepaths += [prefix + "/images/image/" + str(i) for i in scales]

        paths = [x for x in purge.getRelativePaths()]
        [self.assertIn(j, paths) for j in scalepaths]

    def test_scale_purge_paths_unicode(self):
        purge = ScalesPurgePaths(self.file)
        expected = [
            "/plone/media/file/view/++widget++form.widgets.file/@@download/data/töstfile.csv",
            "/plone/media/file/download/file",
            "/plone/media/file/download/file/data/töstfile.csv",
            "/plone/media/file/@@download/file",
            "/plone/media/file/@@download/file/data/töstfile.csv",
        ]
        self.assertListEqual(
            expected,
            list(purge.getRelativePaths()),
        )
