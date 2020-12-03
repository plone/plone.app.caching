from Acquisition import aq_parent
from plone.app.caching.utils import getObjectDefaultView
from plone.app.caching.utils import isPurged
from plone.behavior.interfaces import IBehaviorAssignable
from plone.cachepurging.interfaces import IPurgePathRewriter
from plone.dexterity.interfaces import IDexterityFTI
from plone.dexterity.interfaces import IDexteritySchema
from plone.memoize.instance import memoize
from plone.namedfile.interfaces import INamedBlobFileField
from plone.namedfile.interfaces import INamedImageField
from plone.registry.interfaces import IRegistry
from Products.CMFCore.interfaces import IContentish
from Products.CMFCore.interfaces import IDiscussionResponse
from Products.CMFCore.interfaces import IDynamicType
from Products.CMFCore.utils import getToolByName
from z3c.caching.interfaces import IPurgePaths
from z3c.caching.purge import Purge
from zope.component import adapter
from zope.component import getAdapters
from zope.component import getUtility
from zope.event import notify
from zope.globalrequest import getRequest
from zope.interface import implementer
from zope.lifecycleevent.interfaces import IObjectAddedEvent
from zope.lifecycleevent.interfaces import IObjectModifiedEvent
from zope.lifecycleevent.interfaces import IObjectMovedEvent
from zope.lifecycleevent.interfaces import IObjectRemovedEvent
from zope.schema import getFieldsInOrder

import pkg_resources


try:
    pkg_resources.get_distribution("plone.restapi")
    HAS_RESTAPI = True
except pkg_resources.DistributionNotFound:
    HAS_RESTAPI = False

CONTENT_PATHS_POSTFIXES = [
    "/view",
]
if HAS_RESTAPI:
    CONTENT_PATHS_POSTFIXES += [
        "/@comments",
    ]


def _append_paths(paths, prefix=""):
    for postfix in CONTENT_PATHS_POSTFIXES:
        paths.append(prefix + postfix)


@implementer(IPurgePaths)
@adapter(IDynamicType)
class ContentPurgePaths:
    """Paths to purge for content items

    Includes:

    * ${object_path}/ (e.g. for folders)
    * ${object_path}/view
    * ${object_path}/${object_default_view}
    * a bunch of restapi endpoints

    If the object is the default view of its parent, also purge:

    * ${parent_path}
    * ${parent_path}/
    """

    def __init__(self, context):
        self.context = context

    def getRelativePaths(self):
        prefix = "/" + self.context.virtual_url_path()
        paths = [prefix + "/", prefix + "/view"]

        defaultView = getObjectDefaultView(self.context)
        if defaultView:
            path = prefix + "/" + defaultView
            if path not in paths:  # it could be
                paths.append(path)

        parent = aq_parent(self.context)
        if parent is None:
            return paths

        parentDefaultView = getObjectDefaultView(parent)
        if parentDefaultView == self.context.getId():
            parentPrefix = "/" + parent.virtual_url_path()
            paths.append(parentPrefix)
            if parentPrefix == "/":
                # special handling for site root since parentPrefix
                # does not make sense in that case.
                # Additionally, empty site roots were not getting
                # purge paths
                # /VirtualHostBase/http/site.com:80/site1/VirtualHostRoot/_vh_site1/
                # was getting generated but not
                # /VirtualHostBase/http/site.com:80/site1/VirtualHostRoot/_vh_site1
                # which would translate to http://site.come/ getting
                # invalidated but not http://site.come
                paths.append("")
                _append_paths(paths)
            else:
                paths.append(parentPrefix + "/")
                _append_paths(paths, prefix=parentPrefix)

        return paths

    def getAbsolutePaths(self):
        return []


@implementer(IPurgePaths)
@adapter(IDiscussionResponse)
class DiscussionItemPurgePaths:
    """Paths to purge for Discussion Item.

    Looks up paths for the ultimate parent.
    """

    def __init__(self, context):
        self.context = context

    def getRelativePaths(self):
        root = self._getRoot()
        if root is None:
            return

        request = getRequest()
        if request is None:
            return

        rewriter = IPurgePathRewriter(request, None)
        for name, pathProvider in getAdapters((root,), IPurgePaths):
            # add relative paths, which are rewritten
            relativePaths = pathProvider.getRelativePaths()
            if relativePaths:
                for relativePath in relativePaths:
                    if rewriter is None:
                        yield relativePath
                        continue
                    rewrittenPaths = rewriter(relativePath) or []
                    for rewrittenPath in rewrittenPaths:
                        yield rewrittenPath

    def getAbsolutePaths(self):
        root = self._getRoot()
        if root is None:
            return

        request = getRequest()
        if request is None:
            return

        for name, pathProvider in getAdapters((root,), IPurgePaths):
            # add absoute paths, which are not
            absolutePaths = pathProvider.getAbsolutePaths()
            if absolutePaths:
                yield from absolutePaths

    @memoize
    def _getRoot(self):

        plone_utils = getToolByName(self.context, "plone_utils", None)
        if plone_utils is None:
            return None

        thread = plone_utils.getDiscussionThread(self.context)
        if not thread:
            return None

        return thread[0]


@implementer(IPurgePaths)
@adapter(IDexteritySchema)
class ScalesPurgePaths:
    """Paths to purge for Dexterity object fields"""

    def __init__(self, context):
        self.context = context

    def getScales(self):
        registry = getUtility(IRegistry)
        reg_list = registry["plone.allowed_sizes"]
        sizes = [i.split(" ", 1)[0] for i in reg_list]
        sizes.append("download")
        return sizes

    def getRelativePaths(self):
        prefix = "/" + self.context.virtual_url_path()

        def fieldFilter():
            portal_type = self.context.getPortalTypeName()
            fti = getUtility(IDexterityFTI, name=portal_type)
            schema = fti.lookupSchema()
            fields = getFieldsInOrder(schema)
            assignable = IBehaviorAssignable(self.context, None)
            for behavior in assignable.enumerateBehaviors():
                new_fields = getFieldsInOrder(behavior.interface)
                if len(new_fields) > 0:
                    fields = fields + new_fields

            obj_fields = []
            for key, value in fields:
                is_image = INamedImageField.providedBy(value)
                is_file = INamedBlobFileField.providedBy(value)
                if is_image or is_file:
                    obj_fields.append(value)
            return obj_fields

        for item in fieldFilter():
            field = item.getName()
            value = item.get(self.context)
            if not value:
                continue

            if INamedImageField.providedBy(item):
                for size in self.getScales():
                    yield "{}/@@images/{}/{}".format(
                        prefix,
                        field,
                        size,
                    )
                    yield f"{prefix}/@@download/{field}"
            else:
                filename = value.filename
                yield "{}/view/{}.{}/@@download/{}".format(
                    prefix, "++widget++form.widgets", field, filename
                )
                yield f"{prefix}/@@download/{field}/{filename}"

    def getAbsolutePaths(self):
        return []


# Event redispatch for content items - we check the list of content items
# instead of the marker interface


@adapter(IContentish, IObjectModifiedEvent)
def purgeOnModified(object, event):
    if isPurged(object):
        notify(Purge(object))


@adapter(IContentish, IObjectMovedEvent)
def purgeOnMovedOrRemoved(object, event):
    request = getRequest()
    confirmed_delete = (
        request is not None
        and getattr(request, "URL", None)
        and "delete_confirmation" in request.URL
        and request.REQUEST_METHOD == "POST"
        and "form.submitted" in request.form
    )
    if not confirmed_delete and IObjectRemovedEvent.providedBy(event):
        # ignore extra delete events
        return
    # Don't purge when added
    if IObjectAddedEvent.providedBy(event):
        return
    if isPurged(object) and "portal_factory" not in request.URL:
        notify(Purge(object))
    parent = object.getParentNode()
    if parent:
        notify(Purge(parent))
