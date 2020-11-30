from Acquisition import aq_base
from plone.app.caching.interfaces import IPloneCacheSettings
from plone.registry.interfaces import IRegistry
from Products.CMFCore.interfaces import IDynamicType
from Products.CMFDynamicViewFTI.interfaces import IBrowserDefault
from zope.component import queryUtility


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

    portal_type = getattr(aq_base(object), "portal_type", None)
    if portal_type is None:
        return False

    return portal_type in settings.purgedContentTypes


def stripLeadingCharacters(name):
    """Strip off leading / and/or @@"""

    if name and name[0] == "/":
        name = name[1:]
    if name and name.startswith("@@"):
        name = name[2:]

    return name


def getObjectDefaultView(context):
    """Get the id of an object's default view"""

    # courtesy of Producs.CacheSetup

    browserDefault = IBrowserDefault(context, None)

    if browserDefault is not None:
        try:
            return stripLeadingCharacters(browserDefault.defaultView())
        except AttributeError:
            # Might happen if FTI didn't migrate yet.
            pass

    if not IDynamicType.providedBy(context):
        return None

    fti = context.getTypeInfo()
    try:
        # XXX: This isn't quite right since it assumes the action starts
        # with ${object_url}
        action = fti.getActionInfo("object/view")["url"].split("/")[-1]
    except ValueError:
        # If the action doesn't exist, stop
        return None

    # Try resolving method aliases because we need a real template_id here
    if action:
        action = fti.queryMethodID(action, default=action, context=context)
    else:
        action = fti.queryMethodID("(Default)", default=action, context=context)

    return stripLeadingCharacters(action)
