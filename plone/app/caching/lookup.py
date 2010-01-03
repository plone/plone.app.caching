from zope.interface import implements, Interface
from zope.component import adapts, queryUtility, queryMultiAdapter
from zope.pagetemplate.interfaces import IPageTemplate

from plone.registry.interfaces import IRegistry

from plone.caching.interfaces import ICacheInterceptor, IResponseMutator
from plone.caching.interfaces import IOperationLookup
from plone.caching.interfaces import ICacheSettings

from plone.app.caching.interfaces import IPloneCacheSettings

from Acquisition import aq_base
from Products.CMFDynamicViewFTI.interfaces import IBrowserDefault

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
        nyet = (None, None, None,)
    
        registry = queryUtility(IRegistry)
        if registry is None:
            return nyet
    
        cacheSettings = registry.forInterface(ICacheSettings, check=False)
        if not cacheSettings.enabled:
            return nyet
        
        ploneCacheSettings = registry.forInterface(IPloneCacheSettings, check=False)
        
        # First, try to look up the template name in the appropriate mapping
        templateName = getattr(self.published, '__name__', None)
        if templateName is None:
            return nyet
        
        if ploneCacheSettings.templateMutatorMapping is not None:
            name = ploneCacheSettings.templateMutatorMapping.get(templateName, None)
            if name is not None:
                mutator = queryMultiAdapter((self.published, self.request), IResponseMutator, name=name)
                return templateName, name, mutator
        
        # Next, check if this is the default view of the context, and if so
        # try to look up the name of the context in the appropriate mapping
        if ploneCacheSettings.contentTypeMutatorMapping is None:
            return nyet
        
        parent = getattr(self.published, '__parent__', None)
        if parent is None:
            return nyet
        
        parentPortalType = getattr(aq_base(parent), 'portal_type', None)
        if parentPortalType is None:
            return nyet
        
        defaultView = self._getObjectDefaultView(parent)
        if defaultView == templateName:
            name = ploneCacheSettings.contentTypeMutatorMapping.get(parentPortalType, None)
            if name is not None:
                mutator = queryMultiAdapter((self.published, self.request), IResponseMutator, name=name)
                return parentPortalType, name, mutator
        
        return nyet
    
    def getCacheInterceptor(self):
        nyet = (None, None, None,)
    
        registry = queryUtility(IRegistry)
        if registry is None:
            return nyet
    
        cacheSettings = registry.forInterface(ICacheSettings, check=False)
        if not cacheSettings.enabled:
            return nyet
        
        ploneCacheSettings = registry.forInterface(IPloneCacheSettings, check=False)
        
        # First, try to look up the template name in the appropriate mapping
        templateName = getattr(self.published, '__name__', None)
        if templateName is None:
            return nyet
        
        if ploneCacheSettings.templateInterceptorMapping is not None:
            name = ploneCacheSettings.templateInterceptorMapping.get(templateName, None)
            if name is not None:
                interceptor = queryMultiAdapter((self.published, self.request), ICacheInterceptor, name=name)
                return templateName, name, interceptor
        
        # Next, check if this is the default view of the context, and if so
        # try to look up the name of the context in the appropriate mapping
        if ploneCacheSettings.contentTypeInterceptorMapping is None:
            return nyet
        
        parent = getattr(self.published, '__parent__', None)
        if parent is None:
            return nyet
        
        parentPortalType = getattr(aq_base(parent), 'portal_type', None)
        if parentPortalType is None:
            return nyet
        
        defaultView = self._getObjectDefaultView(parent)
        if defaultView == templateName:
            name = ploneCacheSettings.contentTypeInterceptorMapping.get(parentPortalType, None)
            if name is not None:
                interceptor = queryMultiAdapter((self.published, self.request), ICacheInterceptor, name=name)
                return parentPortalType, name, interceptor
        
        return nyet
    
    def _getObjectDefaultView(self, context):
        """Get the id of an object's default view
        """
        
        # courtesy of Producs.CacheSetup
        
        browserDefault = IBrowserDefault(context, None)
        
        if browserDefault is not None:
            try:
                return browserDefault.defaultView()
            except AttributeError:
                # Might happen if FTI didn't migrate yet.
                pass

        fti = context.getTypeInfo()
        try:
            # XXX: This isn't quite right since it assumes the action starts with ${object_url}
            action = fti.getActionInfo('object/view')['url'].split('/')[-1]
        except ValueError:
            # If the action doesn't exist, stop
            return None

        # Try resolving method aliases because we need a real template_id here
        if action:
            action = fti.queryMethodID(action, default = action, context = context)
        else:
            action = fti.queryMethodID('(Default)', default = action, context = context)

        # Strip off leading / and/or @@
        if action and action[0] == '/':
            action = action[1:]
        if action and action.startswith('@@'):
            action = action[2:]
        return action
