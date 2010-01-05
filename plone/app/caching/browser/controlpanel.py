import datetime

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
from Products.statusmessages.interfaces import IStatusMessage

from plone.app.caching.interfaces import _

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
        
        if self.request.method != 'POST':
            return
        
        if 'form.button.Save' in self.request.form:
            self.processSave()
        elif 'form.button.Cancel' in self.request.form:
            self.request.response.redirect("%s/plone_control_panel" % self.context.absolute_url())
        elif 'form.button.Import' in self.request.form:
            self.processImport()
        
    def render(self):
        return self.index()
    
    def processSave(self):
        
        form = self.request.form
        
        # Form data
        enabled         = form.get('enabled', False)
        contentTypesMap = form.get('contenttypes', {})
        templatesMap    = form.get('templates', {})
        interceptors    = form.get('interceptors', {})
        mutators        = form.get('mutators', {})
        
        # Settings
        
        interceptorMapping        = {}
        mutatorMapping            = {}
        contentTypeRulesetMapping = {}
        templateRulesetMapping    = {}
        
        # Errors
        errors = {}
        
        # Process mappings and validate
        
        for ruleset, interceptor in interceptors.items():
            
            if not ruleset or not interceptor:
                continue
            
            if isinstance(ruleset, unicode): # should be ASCII
                ruleset = ruleset.encode('utf-8')
            
            if isinstance(interceptor, unicode): # should be ASCII
                interceptor = interceptor.encode('utf-8')
            
            interceptorMapping[ruleset] = interceptor
        
        for ruleset, mutator in mutators.items():
            
            if not ruleset or not mutator:
                continue
            
            if isinstance(ruleset, unicode): # should be ASCII
                ruleset = ruleset.encode('utf-8')
            
            if isinstance(mutator, unicode): # should be ASCII
                mutator = mutator.encode('utf-8')
            
            mutatorMapping[ruleset] = mutator

        for ruleset, contentTypes in contentTypesMap.items():
            
            if not ruleset:
                continue
            
            if isinstance(ruleset, unicode): # should be ASCII
                ruleset = ruleset.encode('utf-8')
            
            for contentType in contentTypes:
                
                if not contentType:
                    continue
                
                if isinstance(contentType, unicode): # should be ASCII
                    contentType = contentType.encode('utf-8')
                
                if contentType in contentTypeRulesetMapping:
                    errors.setdefault('contenttypes', {})[ruleset] = \
                        _(u"Content type ${contentType} is already mapped to the rule ${ruleset}", 
                            mapping={'contentType': self.contentTypesLookup.get(contentType, {}).get('title', contentType), 
                                     'ruleset': contentTypeRulesetMapping[contentType]})
                else:
                    contentTypeRulesetMapping[contentType] = ruleset
        
        for ruleset, templates in templatesMap.items():
            
            if not ruleset:
                continue
            
            if isinstance(ruleset, unicode): # should be ASCII
                ruleset = ruleset.encode('utf-8')
            
            for template in templates.split('\n'):
                
                template = template.strip()
                
                if not template:
                    continue
                
                if isinstance(template, unicode): # should be ASCII
                    template = template.encode('utf-8')
                
                if template in templateRulesetMapping:
                    errors.setdefault('templates', {})[ruleset] = \
                        _(u"Template ${template} is already mapped to the rule ${ruleset}", 
                            mapping={'template': template,
                                      'ruleset': templateRulesetMapping[template]})
                else:
                    templateRulesetMapping[template] = ruleset
        
        # Check for errors
        if errors:
            IStatusMessage(self.request).addStatusMessage(_(u"There were errors"), "error")
            self.request.set('errors', errors)
            return
        
        # Save settings
        self.settings.enabled = enabled
        self.settings.interceptorMapping = interceptorMapping
        self.settings.mutatorMapping = mutatorMapping
        
        self.ploneSettings.templateRulesetMapping = templateRulesetMapping
        self.ploneSettings.contentTypeRulesetMapping = contentTypeRulesetMapping
        
        IStatusMessage(self.request).addStatusMessage(_(u"Changes saved"), "info")
    
    def processImport(self):
        profile = self.request.form.get('profile', None)
        snapshot = self.request.form.get('snapshot', True)
        
        errors = {}
        
        if not profile:
            errors['profile'] = _(u"You must select a profile to import")
        
        if errors:
            IStatusMessage(self.request).addStatusMessage(_(u"There were errors"), "error")
            self.request.set('errors', errors)
            return
        
        portal_setup = getToolByName(self.context, 'portal_setup')
        
        # Create a snapshot
        if snapshot:
            snapshotId = "plone.app.caching.beforeimport.%s" % \
                            datetime.datetime.now().isoformat().replace(':', '.')
            portal_setup.createSnapshot(snapshotId)
        
        # Import the new profile
        portal_setup.runAllImportStepsFromProfile("profile-%s" % profile)
        
        IStatusMessage(self.request).addStatusMessage(_(u"Import complete"), "info")
        
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
    def reverseContentTypeMapping(self):
        mapping = {}
        for contentType, ruleset in self.contentTypeMapping.items():
            mapping.setdefault(ruleset, []).append(contentType)
        return mapping

    @property
    @memoize
    def reverseTemplateMapping(self):
        mapping = {}
        for template, ruleset in self.templateMapping.items():
            mapping.setdefault(ruleset, []).append(template)
        return mapping
    
    @property
    @memoize
    def reverseTemplateMappingAsStrings(self):
        mapping = {}
        for key, values in self.reverseTemplateMapping.items():
            mapping[key] = '\n'.join(values)
        return mapping
    
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
    def contentTypesLookup(self):
        types = {}
        portal_types = getToolByName(self.context, 'portal_types')
        for fti in portal_types.objectValues():
            types[fti.id] = dict(title=fti.title or fti.id, description=fti.description)
        return types
    
    @property
    @memoize
    def contentTypes(self):
        types = [
            dict(
                name=name,
                title=info['title'],
                description=info['description']
            ) for name, info in self.contentTypesLookup.items()
        ]
        types.sort(lambda x,y: cmp(x['title'], y['title']))
        return types
