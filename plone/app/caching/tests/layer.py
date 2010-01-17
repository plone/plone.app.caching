from Products.PloneTestCase import ptc
import collective.testcaselayer.ptc

from zope.interface import implements

from zope.component import getUtility
from zope.component import provideUtility

from z3c.caching.registry import getGlobalRulesetRegistry
from plone.cachepurging.interfaces import IPurger

ptc.setupPloneSite()

class FauxPurger(object):
    implements(IPurger)
    
    def __init__(self):
        self.reset()
    
    def reset(self):
        self._sync = []
        self._async = []
    
    def purgeAsync(self, url, httpVerb='PURGE'):
        self._async.append(url)
    
    def purgeSync(self, url, httpVerb='PURGE'):
        self._sync.append(url)
    
    def stopThreads(self, wait=False):
        pass
    
    errorHeaders = ('X-Squid-Error',)
    http_1_1 = True

class IntegrationTestLayer(collective.testcaselayer.ptc.BasePTCLayer):
    
    def afterSetUp(self):
        # Install caching
        self.addProfile('plone.app.caching:default')
        
        # Install fake purger
        self.oldPurger = getUtility(IPurger)
        provideUtility(FauxPurger(), IPurger)

    def beforeTearDown(self):
        # Store old purger
        provideUtility(self.oldPurger, IPurger)
        
        # Undo what our custom ZCML statement does
        getGlobalRulesetRegistry().explicit = False

Layer = IntegrationTestLayer([collective.testcaselayer.ptc.ptc_layer])
