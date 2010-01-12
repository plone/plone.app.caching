from zope.component import queryUtility
from plone.registry.interfaces import IRegistry
from plone.app.caching.interfaces import IPloneCacheSettings

from Acquisition import aq_base

def isPurged(object):
    """Determine if object is of a content type that should be purged.
    
    This inspects ``purgedContentTypes`` in the registry.
    """
    
    registry = queryUtility(IRegistry)
    if registry is None:
        return False
    
    settings = registry.forInterface(IPloneCacheSettings, check=False)
    if not settings.purgedContentTypes:
        return False
    
    portal_type = getattr(aq_base(object), 'portal_type', None)
    if portal_type is None:
        return False
    
    return (portal_type in settings.purgedContentTypes)


