from zope.interface import implements, Interface
from zope.component import adapts

from zope.pagetemplate.interfaces import IPageTemplate
from plone.caching.interfaces import IOperationLookup

class PageTemplateLookup(object):
    """Page templates defined through skin layers or created through the web
    are published as one of the following types of object:
    
    ``Products.CMFCore.FSPageTemplate.FSPageTemplate``
        Templates in a filesystem directory view
    ``Products.PageTemplates.ZopePageTemplate.ZopePageTemplate``
        A template created or customised through the web
    ``Products.CMFFormController.FSControllerPageTemplate.FSControllerPageTemplate``
        A CMFFormController page template in a filesystem directory view
    ``Products.CMFFormController.ControllerPageTemplate.ControllerPageTemplate``
        A CMFFormController page template created or customised through the
        web.
    
    All of these implement ``IPageTemplate``, but there is typically not a
    meaningful per-resource interface or class. Therefore, we implement
    different lookup semantics for these objects when published:
    
    * First, look up the page template name in the registry, under the keys
      ``templateMutatorMapping`` or ``templateInterceptorMapping`` as
      appropriate, under the prefix
      ``plone.app.caching.interfaces.IPloneCacheSettings``. If found, return
      the corresponding operation.
    * If no template-specific mapping is found, find the ``__parent__`` of the
      template. If this is a content type, check whether the template is one
      of its default views. If so, look up a cache rule under the keys
      ``contentTypeMutatorMapping`` or ``contentTypeInterceptorMapping`` as
      appropriate. If found, return the corresponding operation.
    * Otherwise, abort.
    
    Note that this lookup is *not* invoked for a view which happens to use a
    page template to render itself.
    """
    
    implements(IOperationLookup)
    adapts(IPageTemplate, Interface)
    
    def getResponseMutator(self):
        return None, None, None
    
    def getCacheInterceptor(self):
        return None, None, None
