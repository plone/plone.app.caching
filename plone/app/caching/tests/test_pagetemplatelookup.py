import unittest

import zope.component.testing

from zope.component import adapts, provideUtility, provideAdapter, getUtility
from zope.interface import implements, Interface

from plone.caching.interfaces import IResponseMutator
from plone.caching.interfaces import ICacheInterceptor

from plone.registry.interfaces import IRegistry

from plone.registry import Registry
from plone.registry.fieldfactory import persistentFieldAdapter

from plone.caching.interfaces import ICacheSettings
from plone.app.caching.interfaces import IPloneCacheSettings

from plone.app.caching.lookup import PageTemplateLookup

from Acquisition import Explicit
from Products.PageTemplates.ZopePageTemplate import ZopePageTemplate
from Products.CMFDynamicViewFTI.interfaces import IBrowserDefault

class DummyContent(Explicit):
    implements(IBrowserDefault)
    
    def __init__(self, portal_type='testtype', defaultView='defaultView'):
        self.portal_type = portal_type
        self._defaultView = defaultView
    
    def defaultView(self):
        return self._defaultView

class DummyNotContent(Explicit):
    pass

class DummyFTI(object):
    
    def __init__(self, portal_type, viewAction=''):
        self.id = portal_type
        self._actions = {
                'object/view': {'url': viewAction},
            }
    
    def getActionInfo(self, name):
        return self._actions[name]
    
    def queryMethodID(self, id, default=None, context=None):
        if id == '(Default)':
            return 'defaultView'
        elif id == 'view': 
            return '@@defaultView'
        return default

class DummyNotBrowserDefault(Explicit):
    
    def __init__(self, portal_type='testtype', viewAction=''):
        self.portal_type = portal_type
        self._viewAction = viewAction
    
    def getTypeInfo(self):
        return DummyFTI(self.portal_type, self._viewAction)
    
class DummyResponse(dict):
    
    def addHeader(self, name, value):
        self.setdefault(name, []).append(value)

class DummyRequest(dict):
    def __init__(self, published, response):
        self['PUBLISHED'] = published
        self.response = response

class TestLookupResponseMutator(unittest.TestCase):
    
    def setUp(self):
        provideAdapter(persistentFieldAdapter)
    
    def tearDown(self):
        zope.component.testing.tearDown()
    
    def test_getResponseMutator_no_registry(self):
        published = ZopePageTemplate('someView')
        request = DummyRequest(published, DummyResponse())
        
        self.assertEquals((None, None, None,),
                PageTemplateLookup(published, request).getResponseMutator())
        
    def test_getResponseMutator_no_mapping(self):
        provideUtility(Registry(), IRegistry)
        registry = getUtility(IRegistry)
        registry.registerInterface(ICacheSettings)
        registry.registerInterface(IPloneCacheSettings)
        
        settings = registry.forInterface(ICacheSettings)
        settings.enabled = True
        
        published = ZopePageTemplate('someView')
        request = DummyRequest(published, DummyResponse())
        self.assertEquals((None, None, None,),
                PageTemplateLookup(published, request).getResponseMutator())
    
    def test_getResponseMutator_template_operation_not_found(self):
        provideUtility(Registry(), IRegistry)
        registry = getUtility(IRegistry)
        registry.registerInterface(ICacheSettings)
        registry.registerInterface(IPloneCacheSettings)
        
        settings = registry.forInterface(ICacheSettings)
        settings.enabled = True
        
        ploneSettings = registry.forInterface(IPloneCacheSettings)
        ploneSettings.templateRulesetMapping = {'someView': 'rule1'}
        settings.mutatorMapping = {'rule1': 'notfound'}

        published = ZopePageTemplate('someView')
        request = DummyRequest(published, DummyResponse())
        self.assertEquals(('rule1', 'notfound', None,),
                PageTemplateLookup(published, request).getResponseMutator())
    
    def test_getResponseMutator_contenttype_operation_not_found(self):
        provideUtility(Registry(), IRegistry)
        registry = getUtility(IRegistry)
        registry.registerInterface(ICacheSettings)
        registry.registerInterface(IPloneCacheSettings)
        
        settings = registry.forInterface(ICacheSettings)
        settings.enabled = True
        
        ploneSettings = registry.forInterface(IPloneCacheSettings)
        ploneSettings.templateRulesetMapping = {}
        ploneSettings.contentTypeRulesetMapping = {'testtype': 'rule1'}
        settings.mutatorMapping = {'rule1': 'notfound'}
        
        published = ZopePageTemplate('defaultView').__of__(DummyContent())
        request = DummyRequest(published, DummyResponse())
        self.assertEquals(('rule1', 'notfound', None,),
                PageTemplateLookup(published, request).getResponseMutator())
    
    def test_getResponseMutator_contenttype_not_default_view(self):
        provideUtility(Registry(), IRegistry)
        registry = getUtility(IRegistry)
        registry.registerInterface(ICacheSettings)
        registry.registerInterface(IPloneCacheSettings)
        
        settings = registry.forInterface(ICacheSettings)
        settings.enabled = True
        
        ploneSettings = registry.forInterface(IPloneCacheSettings)
        ploneSettings.templateRulesetMapping = {}
        ploneSettings.contentTypeRulesetMapping = {'testtype': 'rule1'}
        settings.mutatorMapping = {'rule1': 'notfound'}
        
        published = ZopePageTemplate('someView').__of__(DummyContent())
        request = DummyRequest(published, DummyResponse())
        self.assertEquals((None, None, None,),
                PageTemplateLookup(published, request).getResponseMutator())
    
    def test_getResponseMutator_parent_not_content(self):
        provideUtility(Registry(), IRegistry)
        registry = getUtility(IRegistry)
        registry.registerInterface(ICacheSettings)
        registry.registerInterface(IPloneCacheSettings)
        
        settings = registry.forInterface(ICacheSettings)
        settings.enabled = True
        
        ploneSettings = registry.forInterface(IPloneCacheSettings)
        ploneSettings.templateRulesetMapping = {}
        ploneSettings.contentTypeRulesetMapping = {'testtype': 'rule1'}
        settings.mutatorMapping = {'rule1': 'mutator'}
        
        published = ZopePageTemplate('defaultView').__of__(DummyNotContent())
        request = DummyRequest(published, DummyResponse())
        self.assertEquals((None, None, None,),
                PageTemplateLookup(published, request).getResponseMutator())
    
    def test_getResponseMutator_parent_not_IBrowserDefault_methodid(self):
        provideUtility(Registry(), IRegistry)
        registry = getUtility(IRegistry)
        registry.registerInterface(ICacheSettings)
        registry.registerInterface(IPloneCacheSettings)
        
        settings = registry.forInterface(ICacheSettings)
        settings.enabled = True
        
        ploneSettings = registry.forInterface(IPloneCacheSettings)
        ploneSettings.templateRulesetMapping = {}
        ploneSettings.contentTypeRulesetMapping = {'testtype': 'rule1'}
        settings.mutatorMapping = {'rule1': 'notfound'}
        
        published = ZopePageTemplate('defaultView').__of__(DummyNotBrowserDefault('testtype', 'string:${object_url}/view'))
        request = DummyRequest(published, DummyResponse())
        self.assertEquals(('rule1', 'notfound', None,),
                PageTemplateLookup(published, request).getResponseMutator())
    
    def test_getResponseMutator_parent_not_IBrowserDefault_default_method(self):
        provideUtility(Registry(), IRegistry)
        registry = getUtility(IRegistry)
        registry.registerInterface(ICacheSettings)
        registry.registerInterface(IPloneCacheSettings)
        
        settings = registry.forInterface(ICacheSettings)
        settings.enabled = True
        
        ploneSettings = registry.forInterface(IPloneCacheSettings)
        ploneSettings.templateRulesetMapping = {}
        ploneSettings.contentTypeRulesetMapping = {'testtype': 'rule1'}
        settings.mutatorMapping = {'rule1': 'notfound'}
        
        published = ZopePageTemplate('defaultView').__of__(DummyNotBrowserDefault('testtype', 'string:${object_url}/'))
        request = DummyRequest(published, DummyResponse())
        self.assertEquals(('rule1', 'notfound', None,),
                PageTemplateLookup(published, request).getResponseMutator())
    
    def test_getResponseMutator_parent_not_IBrowserDefault_actiononly(self):
        provideUtility(Registry(), IRegistry)
        registry = getUtility(IRegistry)
        registry.registerInterface(ICacheSettings)
        registry.registerInterface(IPloneCacheSettings)
        
        settings = registry.forInterface(ICacheSettings)
        settings.enabled = True
        
        ploneSettings = registry.forInterface(IPloneCacheSettings)
        ploneSettings.templateRulesetMapping = {}
        ploneSettings.contentTypeRulesetMapping = {'testtype': 'rule1'}
        settings.mutatorMapping = {'rule1': 'notfound'}
        
        published = ZopePageTemplate('defaultView').__of__(DummyNotBrowserDefault('testtype', 'string:${object_url}/defaultView'))
        request = DummyRequest(published, DummyResponse())
        
        self.assertEquals(('rule1', 'notfound', None,),
                PageTemplateLookup(published, request).getResponseMutator())
    
    def test_getResponseMutator_match_template_only(self):
        provideUtility(Registry(), IRegistry)
        registry = getUtility(IRegistry)
        registry.registerInterface(ICacheSettings)
        registry.registerInterface(IPloneCacheSettings)
        
        settings = registry.forInterface(ICacheSettings)
        settings.enabled = True
        
        ploneSettings = registry.forInterface(IPloneCacheSettings)
        ploneSettings.templateRulesetMapping = {'someView': 'rule1'}
        settings.mutatorMapping = {'rule1': 'mutator'}
        
        class DummyMutator(object):
            implements(IResponseMutator)
            adapts(Interface, Interface)
            
            def __init__(self, published, request):
                self.published = published
                self.request = request
            
            def __call__(self, rulename, response):
                response.addHeader('X-Cache-Foo', 'test')
        
        provideAdapter(DummyMutator, name="mutator")        
        
        published = ZopePageTemplate('someView')
        request = DummyRequest(published, DummyResponse())
        
        (rule, operation, mutator,) = PageTemplateLookup(published, request).getResponseMutator()
        self.assertEquals('rule1', rule)
        self.assertEquals('mutator', operation)
        self.failUnless(isinstance(mutator, DummyMutator))
    
    def test_getResponseMutator_match_content_only(self):
        provideUtility(Registry(), IRegistry)
        registry = getUtility(IRegistry)
        registry.registerInterface(ICacheSettings)
        registry.registerInterface(IPloneCacheSettings)
        
        settings = registry.forInterface(ICacheSettings)
        settings.enabled = True
        
        ploneSettings = registry.forInterface(IPloneCacheSettings)
        ploneSettings.templateRulesetMapping = {}
        ploneSettings.contentTypeRulesetMapping = {'testtype': 'rule1'}
        settings.mutatorMapping = {'rule1': 'mutator'}
        
        class DummyMutator(object):
            implements(IResponseMutator)
            adapts(Interface, Interface)
            
            def __init__(self, published, request):
                self.published = published
                self.request = request
            
            def __call__(self, rulename, response):
                response.addHeader('X-Cache-Foo', 'test')
        
        provideAdapter(DummyMutator, name="mutator")        
        
        published = ZopePageTemplate('defaultView').__of__(DummyContent())
        request = DummyRequest(published, DummyResponse())
        
        (rule, operation, mutator,) = PageTemplateLookup(published, request).getResponseMutator()
        self.assertEquals('rule1', rule)
        self.assertEquals('mutator', operation)
        self.failUnless(isinstance(mutator, DummyMutator))
    
    def test_getResponseMutator_match_template_and_content(self):
        provideUtility(Registry(), IRegistry)
        registry = getUtility(IRegistry)
        registry.registerInterface(ICacheSettings)
        registry.registerInterface(IPloneCacheSettings)
        
        settings = registry.forInterface(ICacheSettings)
        settings.enabled = True
        
        ploneSettings = registry.forInterface(IPloneCacheSettings)
        ploneSettings.templateRulesetMapping = {'defaultView': 'rule1'}
        ploneSettings.contentTypeRulesetMapping = {'testtype': 'rule2'}
        settings.mutatorMapping = {'rule1': 'mutator1', 'rule2': 'mutator2'}
        
        class DummyMutator1(object):
            implements(IResponseMutator)
            adapts(Interface, Interface)
            
            def __init__(self, published, request):
                self.published = published
                self.request = request
            
            def __call__(self, rulename, response):
                response.addHeader('X-Cache-Foo', 'test')
        
        provideAdapter(DummyMutator1, name="mutator1")
        
        class DummyMutator2(object):
            implements(IResponseMutator)
            adapts(Interface, Interface)
            
            def __init__(self, published, request):
                self.published = published
                self.request = request
            
            def __call__(self, rulename, response):
                response.addHeader('X-Cache-Bar', 'test')
        
        provideAdapter(DummyMutator2, name="mutator2")   
        
        published = ZopePageTemplate('defaultView').__of__(DummyContent())
        request = DummyRequest(published, DummyResponse())
        
        (rule, operation, mutator,) = PageTemplateLookup(published, request).getResponseMutator()
        self.assertEquals('rule1', rule)
        self.assertEquals('mutator1', operation)
        self.failUnless(isinstance(mutator, DummyMutator1))

    def test_getResponseMutator_match_template_and_content_template_not_found(self):
        provideUtility(Registry(), IRegistry)
        registry = getUtility(IRegistry)
        registry.registerInterface(ICacheSettings)
        registry.registerInterface(IPloneCacheSettings)
        
        settings = registry.forInterface(ICacheSettings)
        settings.enabled = True
        
        ploneSettings = registry.forInterface(IPloneCacheSettings)
        ploneSettings.templateRulesetMapping = {'defaultView': 'rule1'}
        ploneSettings.contentTypeRulesetMapping = {'testtype': 'rule2'}
        settings.mutatorMapping = {'rule1': 'mutator1', 'rule2': 'mutator2'}
        
        class DummyMutator2(object):
            implements(IResponseMutator)
            adapts(Interface, Interface)
            
            def __init__(self, published, request):
                self.published = published
                self.request = request
            
            def __call__(self, rulename, response):
                response.addHeader('X-Cache-Bar', 'test')
        
        provideAdapter(DummyMutator2, name="mutator2")   
        
        published = ZopePageTemplate('defaultView').__of__(DummyContent())
        request = DummyRequest(published, DummyResponse())
        
        (rule, operation, mutator,) = PageTemplateLookup(published, request).getResponseMutator()
        
        # We *don't* fall back on the content type mutator if the template was
        # mapped, but the mutator not found. This allows conditionally
        # disabling mutation for individual templates even if the content item
        # is mapped generally.
        self.assertEquals('rule1', rule)
        self.assertEquals('mutator1', operation)
        self.failUnless(mutator is None)

    def test_getResponseMutator_off_switch(self):
        provideUtility(Registry(), IRegistry)
        registry = getUtility(IRegistry)
        registry.registerInterface(ICacheSettings)
        registry.registerInterface(IPloneCacheSettings)
        
        settings = registry.forInterface(ICacheSettings)
        settings.enabled = False
        
        ploneSettings = registry.forInterface(IPloneCacheSettings)
        ploneSettings.templateRulesetMapping = {}
        ploneSettings.contentTypeRulesetMapping = {'testtype': 'rule1'}
        settings.mutatorMapping = {'rule1': 'mutator'}
        
        class DummyMutator(object):
            implements(IResponseMutator)
            adapts(Interface, Interface)
            
            def __init__(self, published, request):
                self.published = published
                self.request = request
            
            def __call__(self, rulename, response):
                response.addHeader('X-Cache-Foo', 'test')
        
        provideAdapter(DummyMutator, name="mutator")        
        
        published = ZopePageTemplate('defaultView').__of__(DummyContent())
        request = DummyRequest(published, DummyResponse())
        
        self.assertEquals((None, None, None,),
                PageTemplateLookup(published, request).getResponseMutator())

class TestLookupCacheInterceptor(unittest.TestCase):
    
    def setUp(self):
        provideAdapter(persistentFieldAdapter)
    
    def tearDown(self):
        zope.component.testing.tearDown()
    
    def test_getCacheInterceptor_no_registry(self):
        published = ZopePageTemplate('someView')
        request = DummyRequest(published, DummyResponse())
        
        self.assertEquals((None, None, None,),
                PageTemplateLookup(published, request).getCacheInterceptor())
        
    def test_getCacheInterceptor_no_mapping(self):
        provideUtility(Registry(), IRegistry)
        registry = getUtility(IRegistry)
        registry.registerInterface(ICacheSettings)
        registry.registerInterface(IPloneCacheSettings)
        
        settings = registry.forInterface(ICacheSettings)
        settings.enabled = True
        
        published = ZopePageTemplate('someView')
        request = DummyRequest(published, DummyResponse())
        self.assertEquals((None, None, None,),
                PageTemplateLookup(published, request).getCacheInterceptor())
    
    def test_getCacheInterceptor_template_operation_not_found(self):
        provideUtility(Registry(), IRegistry)
        registry = getUtility(IRegistry)
        registry.registerInterface(ICacheSettings)
        registry.registerInterface(IPloneCacheSettings)
        
        settings = registry.forInterface(ICacheSettings)
        settings.enabled = True
        
        ploneSettings = registry.forInterface(IPloneCacheSettings)
        ploneSettings.templateRulesetMapping = {'someView': 'rule1'}
        settings.interceptorMapping = {'rule1': 'notfound'}
        
        published = ZopePageTemplate('someView')
        request = DummyRequest(published, DummyResponse())
        self.assertEquals(('rule1', 'notfound', None,),
                PageTemplateLookup(published, request).getCacheInterceptor())
    
    def test_getCacheInterceptor_contenttype_operation_not_found(self):
        provideUtility(Registry(), IRegistry)
        registry = getUtility(IRegistry)
        registry.registerInterface(ICacheSettings)
        registry.registerInterface(IPloneCacheSettings)
        
        settings = registry.forInterface(ICacheSettings)
        settings.enabled = True
        
        ploneSettings = registry.forInterface(IPloneCacheSettings)
        ploneSettings.templateRulesetMapping = {}
        ploneSettings.contentTypeRulesetMapping = {'testtype': 'rule1'}
        settings.interceptorMapping = {'rule1': 'notfound'}
        
        published = ZopePageTemplate('defaultView').__of__(DummyContent())
        request = DummyRequest(published, DummyResponse())
        self.assertEquals(('rule1', 'notfound', None,),
                PageTemplateLookup(published, request).getCacheInterceptor())
    
    def test_getCacheInterceptor_contenttype_not_default_view(self):
        provideUtility(Registry(), IRegistry)
        registry = getUtility(IRegistry)
        registry.registerInterface(ICacheSettings)
        registry.registerInterface(IPloneCacheSettings)
        
        settings = registry.forInterface(ICacheSettings)
        settings.enabled = True
        
        ploneSettings = registry.forInterface(IPloneCacheSettings)
        ploneSettings.templateRulesetMapping = {}
        ploneSettings.contentTypeRulesetMapping = {'testtype': 'rule1'}
        settings.interceptorMapping = {'rule1': 'notfound'}
        
        published = ZopePageTemplate('someView').__of__(DummyContent())
        request = DummyRequest(published, DummyResponse())
        self.assertEquals((None, None, None,),
                PageTemplateLookup(published, request).getCacheInterceptor())
    
    def test_getCacheInterceptor_parent_not_content(self):
        provideUtility(Registry(), IRegistry)
        registry = getUtility(IRegistry)
        registry.registerInterface(ICacheSettings)
        registry.registerInterface(IPloneCacheSettings)
        
        settings = registry.forInterface(ICacheSettings)
        settings.enabled = True
        
        ploneSettings = registry.forInterface(IPloneCacheSettings)
        ploneSettings.templateRulesetMapping = {}
        ploneSettings.contentTypeRulesetMapping = {'testtype': 'rule1'}
        settings.interceptorMapping = {'rule1': 'notfound'}
        
        published = ZopePageTemplate('defaultView').__of__(DummyNotContent())
        request = DummyRequest(published, DummyResponse())
        self.assertEquals((None, None, None,),
                PageTemplateLookup(published, request).getCacheInterceptor())
    
    def test_getCacheInterceptor_parent_not_IBrowserDefault_methodid(self):
        provideUtility(Registry(), IRegistry)
        registry = getUtility(IRegistry)
        registry.registerInterface(ICacheSettings)
        registry.registerInterface(IPloneCacheSettings)
        
        settings = registry.forInterface(ICacheSettings)
        settings.enabled = True
        
        ploneSettings = registry.forInterface(IPloneCacheSettings)
        ploneSettings.templateRulesetMapping = {}
        ploneSettings.contentTypeRulesetMapping = {'testtype': 'rule1'}
        settings.interceptorMapping = {'rule1': 'notfound'}
        
        published = ZopePageTemplate('defaultView').__of__(DummyNotBrowserDefault('testtype', 'string:${object_url}/view'))
        request = DummyRequest(published, DummyResponse())
        self.assertEquals(('rule1', 'notfound', None,),
                PageTemplateLookup(published, request).getCacheInterceptor())
    
    def test_getCacheInterceptor_parent_not_IBrowserDefault_default_method(self):
        provideUtility(Registry(), IRegistry)
        registry = getUtility(IRegistry)
        registry.registerInterface(ICacheSettings)
        registry.registerInterface(IPloneCacheSettings)
        
        settings = registry.forInterface(ICacheSettings)
        settings.enabled = True
        
        ploneSettings = registry.forInterface(IPloneCacheSettings)
        ploneSettings.templateRulesetMapping = {}
        ploneSettings.contentTypeRulesetMapping = {'testtype': 'rule1'}
        settings.interceptorMapping = {'rule1': 'notfound'}
        
        published = ZopePageTemplate('defaultView').__of__(DummyNotBrowserDefault('testtype', 'string:${object_url}/'))
        request = DummyRequest(published, DummyResponse())
        self.assertEquals(('rule1', 'notfound', None,),
                PageTemplateLookup(published, request).getCacheInterceptor())
    
    def test_getCacheInterceptor_parent_not_IBrowserDefault_actiononly(self):
        provideUtility(Registry(), IRegistry)
        registry = getUtility(IRegistry)
        registry.registerInterface(ICacheSettings)
        registry.registerInterface(IPloneCacheSettings)
        
        settings = registry.forInterface(ICacheSettings)
        settings.enabled = True
        
        ploneSettings = registry.forInterface(IPloneCacheSettings)
        ploneSettings.templateRulesetMapping = {}
        ploneSettings.contentTypeRulesetMapping = {'testtype': 'rule1'}
        settings.interceptorMapping = {'rule1': 'notfound'}
        
        published = ZopePageTemplate('defaultView').__of__(DummyNotBrowserDefault('testtype', 'string:${object_url}/defaultView'))
        request = DummyRequest(published, DummyResponse())
        
        self.assertEquals(('rule1', 'notfound', None,),
                PageTemplateLookup(published, request).getCacheInterceptor())
    
    def test_getCacheInterceptor_match_template_only(self):
        provideUtility(Registry(), IRegistry)
        registry = getUtility(IRegistry)
        registry.registerInterface(ICacheSettings)
        registry.registerInterface(IPloneCacheSettings)
        
        settings = registry.forInterface(ICacheSettings)
        settings.enabled = True
        
        ploneSettings = registry.forInterface(IPloneCacheSettings)
        ploneSettings.templateRulesetMapping = {'someView': 'rule1'}
        settings.interceptorMapping = {'rule1': 'interceptor'}
        
        class DummyInterceptor(object):
            implements(ICacheInterceptor)
            adapts(Interface, Interface)
            
            def __init__(self, published, request):
                self.published = published
                self.request = request
            
            def __call__(self, rulename, response):
                response.addHeader('X-Cache-Foo', 'test')
        
        provideAdapter(DummyInterceptor, name="interceptor")        
        
        published = ZopePageTemplate('someView')
        request = DummyRequest(published, DummyResponse())
        
        (rule, operation, interceptor,) = PageTemplateLookup(published, request).getCacheInterceptor()
        self.assertEquals('rule1', rule)
        self.assertEquals('interceptor', operation)
        self.failUnless(isinstance(interceptor, DummyInterceptor))
    
    def test_getCacheInterceptor_match_content_only(self):
        provideUtility(Registry(), IRegistry)
        registry = getUtility(IRegistry)
        registry.registerInterface(ICacheSettings)
        registry.registerInterface(IPloneCacheSettings)
        
        settings = registry.forInterface(ICacheSettings)
        settings.enabled = True
        
        ploneSettings = registry.forInterface(IPloneCacheSettings)
        ploneSettings.templateRulesetMapping = {}
        ploneSettings.contentTypeRulesetMapping = {'testtype': 'rule1'}
        settings.interceptorMapping = {'rule1': 'interceptor'}
        
        class DummyInterceptor(object):
            implements(ICacheInterceptor)
            adapts(Interface, Interface)
            
            def __init__(self, published, request):
                self.published = published
                self.request = request
            
            def __call__(self, rulename, response):
                response.addHeader('X-Cache-Foo', 'test')
        
        provideAdapter(DummyInterceptor, name="interceptor")        
        
        published = ZopePageTemplate('defaultView').__of__(DummyContent())
        request = DummyRequest(published, DummyResponse())
        
        (rule, operation, interceptor,) = PageTemplateLookup(published, request).getCacheInterceptor()
        self.assertEquals('rule1', rule)
        self.assertEquals('interceptor', operation)
        self.failUnless(isinstance(interceptor, DummyInterceptor))
    
    def test_getCacheInterceptor_match_template_and_content(self):
        provideUtility(Registry(), IRegistry)
        registry = getUtility(IRegistry)
        registry.registerInterface(ICacheSettings)
        registry.registerInterface(IPloneCacheSettings)
        
        settings = registry.forInterface(ICacheSettings)
        settings.enabled = True
        
        ploneSettings = registry.forInterface(IPloneCacheSettings)
        ploneSettings.templateRulesetMapping = {'defaultView': 'rule1'}
        ploneSettings.contentTypeRulesetMapping = {'testtype': 'rule2'}
        settings.interceptorMapping = {'rule1': 'interceptor1',
                                       'rule2': 'interceptor2'}
        
        class DummyInterceptor1(object):
            implements(ICacheInterceptor)
            adapts(Interface, Interface)
            
            def __init__(self, published, request):
                self.published = published
                self.request = request
            
            def __call__(self, rulename, response):
                response.addHeader('X-Cache-Foo', 'test')
        
        provideAdapter(DummyInterceptor1, name="interceptor1")
        
        class DummyInterceptor2(object):
            implements(ICacheInterceptor)
            adapts(Interface, Interface)
            
            def __init__(self, published, request):
                self.published = published
                self.request = request
            
            def __call__(self, rulename, response):
                response.addHeader('X-Cache-Bar', 'test')
        
        provideAdapter(DummyInterceptor2, name="interceptor2")   
        
        published = ZopePageTemplate('defaultView').__of__(DummyContent())
        request = DummyRequest(published, DummyResponse())
        
        (rule, operation, interceptor,) = PageTemplateLookup(published, request).getCacheInterceptor()
        self.assertEquals('rule1', rule)
        self.assertEquals('interceptor1', operation)
        self.failUnless(isinstance(interceptor, DummyInterceptor1))

    def test_getCacheInterceptor_match_template_and_content_template_not_found(self):
        provideUtility(Registry(), IRegistry)
        registry = getUtility(IRegistry)
        registry.registerInterface(ICacheSettings)
        registry.registerInterface(IPloneCacheSettings)
        
        settings = registry.forInterface(ICacheSettings)
        settings.enabled = True
        
        ploneSettings = registry.forInterface(IPloneCacheSettings)
        ploneSettings.templateRulesetMapping = {'defaultView': 'rule1'}
        ploneSettings.contentTypeRulesetMapping = {'testtype': 'rule2'}
        settings.interceptorMapping = {'rule1': 'interceptor1',
                                       'rule2': 'interceptor2'}
        
        class DummyInterceptor2(object):
            implements(ICacheInterceptor)
            adapts(Interface, Interface)
            
            def __init__(self, published, request):
                self.published = published
                self.request = request
            
            def __call__(self, rulename, response):
                response.addHeader('X-Cache-Bar', 'test')
        
        provideAdapter(DummyInterceptor2, name="interceptor2")   
        
        published = ZopePageTemplate('defaultView').__of__(DummyContent())
        request = DummyRequest(published, DummyResponse())
        
        (rule, operation, interceptor,) = PageTemplateLookup(published, request).getCacheInterceptor()
        
        # We *don't* fall back on the content type interceptor if the template was
        # mapped, but the interceptor not found. This allows conditionally
        # disabling mutation for individual templates even if the content item
        # is mapped generally.
        self.assertEquals('rule1', rule)
        self.assertEquals('interceptor1', operation)
        self.failUnless(interceptor is None)

    def test_getCacheInterceptor_off_switch(self):
        provideUtility(Registry(), IRegistry)
        registry = getUtility(IRegistry)
        registry.registerInterface(ICacheSettings)
        registry.registerInterface(IPloneCacheSettings)
        
        settings = registry.forInterface(ICacheSettings)
        settings.enabled = False
        
        ploneSettings = registry.forInterface(IPloneCacheSettings)
        ploneSettings.templateRulesetMapping = {}
        ploneSettings.contentTypeRulesetMapping = {'testtype': 'rule1'}
        settings.interceptorMapping = {'rule1': 'interceptor'}
        
        class DummyInterceptor(object):
            implements(ICacheInterceptor)
            adapts(Interface, Interface)
            
            def __init__(self, published, request):
                self.published = published
                self.request = request
            
            def __call__(self, rulename, response):
                response.addHeader('X-Cache-Foo', 'test')
        
        provideAdapter(DummyInterceptor, name="interceptor")        
        
        published = ZopePageTemplate('defaultView').__of__(DummyContent())
        request = DummyRequest(published, DummyResponse())
        
        self.assertEquals((None, None, None,),
                PageTemplateLookup(published, request).getCacheInterceptor())

def test_suite():
    return unittest.defaultTestLoader.loadTestsFromName(__name__)