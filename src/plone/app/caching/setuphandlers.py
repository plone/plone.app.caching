from plone.base.interfaces import INonInstallable
from Products.CMFCore.utils import getToolByName
from zope.interface import implementer


@implementer(INonInstallable)
class NonInstallable:

    def getNonInstallableProfiles(self):
        return [
            "plone.app.caching:uninstall",
            "plone.app.caching:v2",
        ]


def enableExplicitMode():
    """ZCML startup hook to put the ruleset registry into explicit mode.
    This means we require people to declare ruleset types before using them.
    """
    from z3c.caching.registry import getGlobalRulesetRegistry

    registry = getGlobalRulesetRegistry()
    if registry is not None:
        registry.explicit = True


def post_handler(context):
    error_log = getToolByName(context, "error_log")

    properties = error_log.getProperties()
    ignored = properties.get("ignored_exceptions", ())

    modified = False
    for exceptionName in ("Intercepted",):
        if exceptionName not in ignored:
            ignored += (exceptionName,)
            modified = True

    if modified:
        error_log.setProperties(
            properties.get("keep_entries", 10),
            properties.get("copy_to_zlog", True),
            ignored,
        )
