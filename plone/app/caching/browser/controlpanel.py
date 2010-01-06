import datetime

from zope.interface import implements
from zope.component import getUtility
from zope.component import getUtilitiesFor
from zope.component import queryUtility

from zope.publisher.interfaces import IPublishTraverse
from zope.publisher.interfaces import NotFound

from plone.memoize.instance import memoize

from plone.registry.interfaces import IRegistry

from z3c.caching.interfaces import IRulesetType
from z3c.caching.registry import enumerateTypes

from plone.caching.interfaces import ICacheSettings
from plone.caching.interfaces import ICacheOperationType
from plone.caching.interfaces import IResponseMutatorType
from plone.caching.interfaces import ICacheInterceptorType

from plone.app.caching.interfaces import IPloneCacheSettings
from plone.app.caching.interfaces import ICacheProfiles
from plone.app.caching.interfaces import _
from plone.app.caching.browser.edit import EditForm

from Products.GenericSetup.interfaces import BASE, EXTENSION
from Products.CMFCore.utils import getToolByName
from Products.statusmessages.interfaces import IStatusMessage

class ControlPanel(object):
    """Control panel view
    """
    
    implements(IPublishTraverse)
    
    # Used by the publishTraverse() adapter - see below
    editGlobal = False
    editRuleset = False
    editOperationName = None
    editRulesetName = None
    
    def __init__(self, context, request):
        self.context = context
        self.request = request

    def __call__(self):
        self.update()
        if self.request.response.getStatus() not in (301, 302):
            return self.render()
        return ''
    
    def publishTraverse(self, request, name):
        """Allow the following types of URLs:
        
        /
            Render the standard control panel (no publish traverse invoked)
            
        /edit-operation-global/${operation-name}
            Render an edit form for global operation parameters
            
        /edit-operation-rulset/${operation-name}/${ruleset-name}
            Render an edit form for per-ruleset operation parameters
        """
        
        # Step 1 - find which type of editing we want to do
        if not self.editGlobal and not self.editRuleset:
            if name == 'edit-operation-global':
                self.editGlobal = True  
            elif name == 'edit-operation-ruleset':
                self.editRuleset = True
            else:
                raise NotFound(self, name)
            return self # traverse again to get operation name

        # Step 2a - get operation name
        if (self.editGlobal or self.editRuleset) and not self.editOperationName:
            self.editOperationName = name
            
            if self.editGlobal:
                
                operation = queryUtility(ICacheOperationType, name=self.editOperationName)
                if operation is None:
                    raise NotFound(self, operation)
                
                return EditForm(self.context, self.request, self.editOperationName, operation)
            elif self.editRuleset:
                return self # traverse again to get ruleset name
            else:
                raise NotFound(self, name)
            
        # Step 3 - if this is ruleset traversal, get the ruleset name
        if self.editRuleset and self.editOperationName and not self.editRulesetName:
            self.editRulesetName = name
            
            operation = queryUtility(ICacheOperationType, name=self.editOperationName)
            if operation is None:
                raise NotFound(self, self.operationName)
            
            rulesetType = queryUtility(IRulesetType, name=self.editRulesetName)
            if rulesetType is None:
                raise NotFound(self, self.editRulesetName)
            
            return EditForm(self.context, self.request,
                            self.editOperationName, operation,
                            self.editRulesetName, rulesetType)
        
        raise NotFound(self, name)
        
    def update(self):
        
        self.registry = getUtility(IRegistry)
        
        self.settings = self.registry.forInterface(ICacheSettings)
        self.ploneSettings = self.registry.forInterface(IPloneCacheSettings)
        
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
            
            ruleset = ruleset.replace('-', '.')
            interceptorMapping[ruleset] = interceptor
        
        for ruleset, mutator in mutators.items():
            
            if not ruleset or not mutator:
                continue
            
            if isinstance(ruleset, unicode): # should be ASCII
                ruleset = ruleset.encode('utf-8')
            
            if isinstance(mutator, unicode): # should be ASCII
                mutator = mutator.encode('utf-8')
            
            ruleset = ruleset.replace('-', '.')
            mutatorMapping[ruleset] = mutator

        for ruleset, contentTypes in contentTypesMap.items():
            
            if not ruleset:
                continue
            
            if isinstance(ruleset, unicode): # should be ASCII
                ruleset = ruleset.encode('utf-8')
            
            ruleset = ruleset.replace('-', '.')
            
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
            
            ruleset = ruleset.replace('-', '.')
            
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
    
    # Rule types - used as the index column
    
    @property
    @memoize
    def ruleTypes(self):
        types = []
        for type_ in enumerateTypes():
            types.append(dict(name=type_.name,
                              title=type_.title or type_.name,
                              description=type_.description,
                              safeName=type_.name.replace('.', '-')))
        return types
    
    # Safe access to the main mappings, which may be None - we want to treat
    # that as {} to make TAL expressions simpler
    
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
    
    # Type lookups (for accessing settings)
    
    @property
    @memoize
    def interceptorTypesLookup(self):
        lookup = {}
        for name, type_ in getUtilitiesFor(ICacheInterceptorType):
            lookup[name] = dict(
                name=name,
                title=type_.title,
                description=type_.description,
                prefix=type_.prefix,
                options=type_.options,
                hasOptions=self.hasGlobalOptions(type_),
                type=type_,
            )
        return lookup
    
    @property
    @memoize
    def mutatorTypesLookup(self):
        lookup = {}
        for name, type_ in getUtilitiesFor(IResponseMutatorType):
            lookup[name] = dict(
                name=name,
                title=type_.title,
                description=type_.description,
                prefix=type_.prefix,
                options=type_.options,
                hasOptions=self.hasGlobalOptions(type_),
                type=type_,
            )
        return lookup
    
    @property
    @memoize
    def contentTypesLookup(self):
        types = {}
        portal_types = getToolByName(self.context, 'portal_types')
        for fti in portal_types.objectValues():
            types[fti.id] = dict(title=fti.title or fti.id, description=fti.description)
        return types
    
    # Sorted lists (e.g. for drop-downs)
    
    @property
    @memoize
    def interceptorTypes(self):
        interceptors = [v for k, v in self.interceptorTypesLookup.items()]
        interceptors.sort(lambda x,y: cmp(x['title'], y['title']))
        return interceptors

    @property
    @memoize
    def mutatorTypes(self):
        mutators = [v for k, v in self.mutatorTypesLookup.items()]
        mutators.sort(lambda x,y: cmp(x['title'], y['title']))
        return mutators
    
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

    # We store template and content type mappings as template -> ruleset and
    # content type -> ruleset. In the UI, we reverse this, so that the user
    # enters a list of templates and selects a set of content types for each
    # ruleset. This is more natural (whereas the storage is more efficient).
    # These mappings support that UI
    
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
    
    # Since the widget for the templates is a textarea with one item per line,
    # pre-calculate the default output here
    
    @property
    @memoize
    def reverseTemplateMappingAsStrings(self):
        mapping = {}
        for key, values in self.reverseTemplateMapping.items():
            mapping[key] = '\n'.join(values)
        return mapping

    # For the ruleset mappings page, we need to know whether a particular
    # operation has global and per-ruleset parameters. If there is at least
    # one option set, we consider it to have options.
    
    def hasGlobalOptions(self, operationType):
        prefix = operationType.prefix
        options = operationType.options
        
        if not options or not prefix:
            return False
        
        for option in options:
            if '%s.%s' % (prefix, option,) in self.registry.records:
                return True
        
        return False
    
    def hasRulesetOptions(self, operationType, ruleset):
        prefix = operationType.prefix
        options = operationType.options
        
        if not options or not prefix:
            return False
        
        for option in options:
            if '%s.%s.%s' % (prefix, ruleset, option,) in self.registry.records:
                return True
        
        return False
