from hashlib import sha1 as sha
from plone.app.contenttypes.testing import PLONE_APP_CONTENTTYPES_FIXTURE
from plone.app.testing import applyProfile
from plone.app.testing import FunctionalTesting
from plone.app.testing import IntegrationTesting
from plone.app.testing import PloneSandboxLayer
from plone.cachepurging.interfaces import IPurger
from plone.protect.authenticator import _getKeyring
from plone.restapi.testing import PLONE_RESTAPI_DX_PAM_FIXTURE
from plone.testing import z2
from zope.component import getUtility
from zope.component import provideUtility
from zope.interface import implementer

import hmac


@implementer(IPurger)
class FauxPurger:
    def __init__(self):
        self.reset()

    def reset(self):
        self._sync = []
        self._async = []

    def purgeAsync(self, url, httpVerb="PURGE"):
        self._async.append(url)

    def purgeSync(self, url, httpVerb="PURGE"):
        self._sync.append(url)

    def stopThreads(self, wait=False):
        pass

    errorHeaders = ("X-Squid-Error",)
    http_1_1 = True


class PloneAppCachingBase(PloneSandboxLayer):
    def setUpZope(self, app, configurationContext):

        # Load ZCML
        import plone.app.caching

        self.loadZCML(package=plone.app.caching)

        # Install fake purger
        self.oldPurger = getUtility(IPurger)
        provideUtility(FauxPurger(), IPurger)

    def setUpPloneSite(self, portal):
        applyProfile(portal, "plone.app.caching:default")
        portal["portal_workflow"].setDefaultChain("simple_publication_workflow")

    def tearDownZope(self, app):
        # Store old purger
        provideUtility(self.oldPurger, IPurger)


class PloneAppCaching(PloneAppCachingBase):

    defaultBases = (PLONE_APP_CONTENTTYPES_FIXTURE,)


class PloneAppCachingRestAPI(PloneAppCachingBase):

    defaultBases = (PLONE_RESTAPI_DX_PAM_FIXTURE,)


PLONE_APP_CACHING_FIXTURE = PloneAppCaching()
PLONE_APP_CACHING_RESTAPI_FIXTURE = PloneAppCachingRestAPI()
PLONE_APP_CACHING_INTEGRATION_TESTING = IntegrationTesting(
    bases=(PLONE_APP_CACHING_FIXTURE,),
    name="PloneAppCaching:Integration",
)
PLONE_APP_CACHING_FUNCTIONAL_TESTING = FunctionalTesting(
    bases=(PLONE_APP_CACHING_FIXTURE,),
    name="PloneAppCaching:Functional",
)

PLONE_APP_CACHING_FUNCTIONAL_RESTAPI_TESTING = FunctionalTesting(
    bases=(PLONE_APP_CACHING_RESTAPI_FIXTURE, z2.ZSERVER_FIXTURE),
    name="PloneAppCachingRestAPI:Functional",
)


def getToken(username):
    ring = _getKeyring(username)
    secret = ring.random().encode("utf8")
    return hmac.new(secret, username.encode("utf8"), sha).hexdigest()
