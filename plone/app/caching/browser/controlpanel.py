from zope.component import getUtility
from zope.component import getUtilitiesFor

from plone.registry.interfaces import IRegistry

from z3c.caching.registry import enumerateTypes
from plone.caching.interfaces import ICacheSettings
from plone.app.caching.interfaces import IPloneCacheSettings

from plone.app.caching.interfaces import ICacheProfiles
from plone.caching.interfaces import IResponseMutatorType
from plone.caching.interfaces import ICacheInterceptorType

from plone.memoize.instance import memoize

from Products.GenericSetup.interfaces import BASE, EXTENSION
from Products.CMFCore.utils import getToolByName

class ControlPanel(object):
    """Control panel view
    """
    
    def __init__(self, context, request):
        self.context = context
        self.request = request

    def __call__(self):
        self.update()
        if self.request.response.getStatus() not in (301, 302):
            return self.render()
        return ''
    
    def update(self):
        registry = getUtility(IRegistry)
        
        self.settings = registry.forInterface(ICacheSettings)
        self.ploneSettings = registry.forInterface(IPloneCacheSettings)
        
    def render(self):
        return self.index()
    
    # Properties accessed in the template
    
    @property
    @memoize
    def profiles(self):
        portal_setup = getToolByName(self.context, 'portal_setup')
        return [profile for profile in portal_setup.listProfileInfo(ICacheProfiles) 
                  if profile.get('type', BASE) == EXTENSION and profile.get('for') is not None]
    
    @property
    def interceptorMapping(self):
        return self.settings.interceptorMapping or {}
    
    @property
    def mutatorMapping(self):
        return self.settings.mutatorMapping or {}
    
    @property
    def templateMapping(self):
        return self.ploneSettings.templateRulesetMapping or {}
    
    @property
    def contentTypeMapping(self):
        return self.ploneSettings.contentTypeRulesetMapping or {}
    
    @property
    @memoize
    def ruleTypes(self):
        return list(enumerateTypes())
    
    @property
    @memoize
    def interceptorTypes(self):
        interceptors = [
            dict(
                name=name,
                title=type_.title,
                description=type_.description,
                prefx=type_.prefix,
                options=type_.options,
            ) for name, type_ in getUtilitiesFor(ICacheInterceptorType)
        ]
        interceptors.sort(lambda x,y: cmp(x['title'], y['title']))
        return interceptors

    @property
    @memoize
    def mutatorTypes(self):
        mutators = [
            dict(
                name=name,
                title=type_.title,
                description=type_.description,
                prefx=type_.prefix,
                options=type_.options,
            ) for name, type_ in getUtilitiesFor(IResponseMutatorType)
        ]
        mutators.sort(lambda x,y: cmp(x['title'], y['title']))
        return mutators

    @property
    @memoize
    def contentTypes(self):
        portal_types = getToolByName(self.context, 'portal_types')
        types = [
            dict(
                name=fti.id,
                title=fti.title or fti.id,
                description=fti.description,
            ) for fti in portal_types.objectValues()
        ]
        types.sort(lambda x,y: cmp(x['title'], y['title']))
        return types
    
    def templatesFor(self, ruleset):
        templates = set()
        for template, mapped in self.templateMapping:
            if mapped == ruleset:
                templates.add(template)
        return sorted(templates)
    
    def contentTypesFor(self, ruleset):
        contentTypes = set()
        for contentType, mapped in self.contentTypeMapping:
            if mapped == ruleset:
                contentTypes.add(contentType)
        return sorted(contentTypes)
