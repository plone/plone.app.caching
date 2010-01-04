from datetime import datetime
from persistent.interfaces import IPersistent

from zope.interface import implementer, implements, Interface
from zope.component import adapter, adapts, queryMultiAdapter

from zope.pagetemplate.interfaces import IPageTemplate
from z3c.caching.interfaces import ILastModified

from Acquisition import aq_base

@implementer(ILastModified)
@adapter(IPageTemplate, Interface)
def pageTemplateDelegateLastModified(template, request):
    """When looking up an ILastModified for a page template, look up an
    ILastModified for its context. May return None, in which case adaptation
    will fail.
    """
    return queryMultiAdapter((template.__parent__, request), ILastModified)

class PersistentModified(object):
    """General ILastModified adapter for persistent objects that have a
    _p_mtime.
    """
    implements(ILastModified)
    adapts(IPersistent)
    
    def __init__(self, context):
        self.context = context
    
    def __call__(self):
        context = aq_base(self.context)
        mtime = getattr(context, '_p_mtime', None)
        if mtime is not None and mtime > 0:
            return datetime.datetime(self.context_p_mtime)
        return None

