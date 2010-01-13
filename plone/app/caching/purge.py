from zope.interface import implements
from zope.component import adapts, adapter
from zope.event import notify
from zope.globalrequest import getRequest

from zope.lifecycleevent.interfaces import IObjectModifiedEvent
from zope.lifecycleevent.interfaces import IObjectMovedEvent

from plone.cachepurging import Purge
from plone.cachepurging.interfaces import IPurgePaths
from plone.cachepurging.utils import getPathsToPurge

from Products.CMFCore.interfaces import IDiscussionResponse
from Products.CMFCore.interfaces import IContentish
from Products.CMFCore.interfaces import IDynamicType
from Products.CMFCore.utils import getToolByName

from plone.app.caching.utils import isPurged
from plone.app.caching.utils import getObjectDefaultView

from Acquisition import aq_parent

try:
    from Products.Archetypes.interfaces import IBaseObject
    from Products.Archetypes.interfaces import IFileField, IImageField
    HAVE_AT = True
except:
    HAVE_AT = False
    

class ContentPurgePaths(object):
    """Paths to purge for content items
    
    Includes:
    
    * ${object_path}/ (e.g. for folders)
    * ${object_path}/view
    * ${object_path}/${object_default_view}

    If the object is the default view of its parent, also purge:

    * ${parent_path}
    * ${parent_path}/
    """
    
    implements(IPurgePaths)
    adapts(IDynamicType)
    
    def getRelativePaths(self):
        prefix = self.context.absolute_url_path()
        
        yield prefix + '/'
        yield prefix + '/view'
        
        defaultView = getObjectDefaultView(self.context)
        if defaultView:
            yield prefix + '/' + defaultView
        
        parent = aq_parent(self.context)
        if parent is not None:
            parentDefaultView = getObjectDefaultView(parent)
            if parentDefaultView == self.context.getId():
                parentPrefix = parent.absolute_url_path()
                yield parentPrefix
                yield parentPrefix + '/'
    
    def getAbsolutePaths(self):
        return []

class DiscussionItemPurgePaths(object):
    """Paths to purge for Discussion Item.
    
    Looks up paths for the ultimate parent.
    """
    
    implements(IPurgePaths)
    adapts(IDiscussionResponse)
    
    def __init__(self, context):
        self.context = context

    def getRelativePaths(self):
        plone_utils = getToolByName(self.context, 'plone_utils', None)
        if plone_utils is None:
            return
        
        request = getRequest()
        if request is None:
            return
        
        root = plone_utils.getDiscussionThread(self.context)[0]
        for path in getPathsToPurge(root, request):
            yield path
        
    def getAbsolutePaths(self):
        return []

if HAVE_AT:

    class ObjectFieldPurgePaths(object):
        """Paths to purge for Archetypes object fields
        """
    
        implements(IPurgePaths)
        adapts(IBaseObject)
    
        def getRelativePaths(self):
            prefix = self.context.absolute_url_path()
            schema = self.context.Schema()

            def fieldFilter(field):
                return IFileField.providedBy(field) or IImageField.providedBy(field)

            for field in schema.filterFields(fieldFilter):
                yield prefix + '/download'
                yield prefix + '/at_download'
                yield prefix + '/at_download/' + field.getName()
                
                fieldURL = "%s/%s" % (prefix, field.getName(),)
                yield fieldURL

                if IImageField.providedBy(field):
                    for size in field.getAvailableSizes(self.context).keys():
                        yield "%s_%s" % (fieldURL, size,)
        
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
    # Don't purge when added
    if event.oldName is not None and event.oldParent is not None:
        if isPurged(object):
            notify(Purge(object))
