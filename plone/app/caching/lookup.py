from zope.interface import implements, Interface
from zope.component import adapts, queryUtility
from zope.pagetemplate.interfaces import IPageTemplate

from plone.registry.interfaces import IRegistry

from plone.caching.interfaces import IRulesetLookup
from plone.app.caching.interfaces import IPloneCacheSettings

from Acquisition import aq_base

from plone.app.caching.utils import getObjectDefaultView

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
    different ruleset lookup semantics for these objects when published:
    
    * First, look up the page template name in the registry under the key
      ``plone.app.caching.interfaces.IPloneCacheSettings.templateRulesetMapping``.
      If this is found, return the corresponding ruleset.
    * If no template-specific mapping is found, find the ``__parent__`` of the
      template. If this is a content type, check whether the template is one
      of its default views. If so, look up a cache ruleset under the key
      ``plone.app.caching.interfaces.IPloneCacheSettings.contentTypeRulesetMapping``. 
    * Otherwise, abort.
    
    Note that this lookup is *not* invoked for a view which happens to use a
    page template to render itself.
    """
    
    implements(IRulesetLookup)
    adapts(IPageTemplate, Interface)
    
    def __init__(self, published, request):
        self.published = published
        self.request = request
    
    def __call__(self):
        
        registry = queryUtility(IRegistry)
        if registry is None:
            return None
    
        ploneCacheSettings = registry.forInterface(IPloneCacheSettings, check=False)
        
        # First, try to look up the template name in the appropriate mapping
        templateName = getattr(self.published, '__name__', None)
        if templateName is None:
            return None
        
        if ploneCacheSettings.templateRulesetMapping is not None:
            name = ploneCacheSettings.templateRulesetMapping.get(templateName, None)
            if name is not None:
                return name
        
        # Next, check if this is the default view of the context, and if so
        # try to look up the name of the context in the appropriate mapping
        if ploneCacheSettings.contentTypeRulesetMapping is None:
            return None
        
        parent = getattr(self.published, '__parent__', None)
        if parent is None:
            return None
        
        parentPortalType = getattr(aq_base(parent), 'portal_type', None)
        if parentPortalType is None:
            return None
        
        defaultView = getObjectDefaultView(parent)
        if defaultView == templateName:
            name = ploneCacheSettings.contentTypeRulesetMapping.get(parentPortalType, None)
            if name is not None:
                return name
        
        return None
