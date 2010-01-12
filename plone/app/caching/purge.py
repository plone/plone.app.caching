from zope.interface import implements
from zope.component import adapts, adapter
from zope.event import notify

from zope.lifecycleevent.interfaces import IObjectModifiedEvent
from zope.lifecycleevent.interfaces import IObjectMovedEvent

from plone.cachepurging import Purge
from plone.cachepurging.interfaces import IPurgePaths

from Products.CMFCore.interfaces import IDiscussionResponse
from Products.CMFCore.interfaces import IContentish

from plone.app.caching.utils import isPurged

try:
    from Products.Archetypes.interfaces import IBaseObject
    HAVE_AT = True
except:
    HAVE_AT = False

class DiscussionItemPurgePaths(object):
    """Paths to purge for Discussion Item
    """
    
    implements(IPurgePaths)
    adapts(IDiscussionResponse)
    
    def __init__(self, context):
        self.context = context

    def getRelativePaths(self):
        return []
        
    def getAbsolutePaths(self):
        return []
    
class ContentViewPurgePaths(object):
    """Paths to purge for content items
    """
    
    implements(IPurgePaths)
    adapts(IContentish)
    
    def getRelativePaths(self):
        return []
        
    def getAbsolutePaths(self):
        return []

if HAVE_AT:

    class ObjectFieldPurgePaths(object):
        """Paths to purge for Archetypes object fields
        """
    
        implements(IPurgePaths)
        adapts(IBaseObject)
    
        def getRelativePaths(self):
            return []
        
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
