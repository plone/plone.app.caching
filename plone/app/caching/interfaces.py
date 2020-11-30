from zope import schema
from zope.interface import Interface

import zope.i18nmessageid


_ = zope.i18nmessageid.MessageFactory("plone.app.caching")


class ICacheProfiles(Interface):
    """Marker interface for extension profiles that contain cache settings.
    These will primarily include a ``registry.xml`` file to configure cache
    settings.

    To use the marker interface, you can do::

        <genericsetup:registerProfile
            name="my-cache-settings"
            title="My cache settings"
            directory="profiles/my-cache-settings"
            description="My cache settings"
            for="plone.app.caching.interfaces.ICacheProfiles"
            provides="Products.GenericSetup.interfaces.EXTENSION"
            />

    This will hide the profile from the Plone quickinstaller, and make it
    available for installation in the cache settings control panel.
    """


class IPloneCacheSettings(Interface):
    """Settings stored in the registry.

    Basic cache settings are represented by
    ``plone.caching.interfaces.ICacheSettings``. These are additional,
    Plone-specific settings.
    """

    templateRulesetMapping = schema.Dict(
        title=_("Page template/ruleset mapping"),
        description=_("Maps skin layer page template names to ruleset names"),
        key_type=schema.ASCIILine(title=_("Page template name")),
        value_type=schema.DottedName(title=_("Ruleset name")),
    )

    contentTypeRulesetMapping = schema.Dict(
        title=_("Content type/ruleset mapping"),
        description=_("Maps content type names to ruleset names"),
        key_type=schema.ASCIILine(title=_("Content type name")),
        value_type=schema.DottedName(title=_("Ruleset name")),
    )

    purgedContentTypes = schema.Tuple(
        title=_("Content types to purge"),
        description=_("List content types which should be purged when modified"),
        value_type=schema.ASCIILine(title=_("Content type name")),
        default=(
            "File",
            "Image",
            "News Item",
        ),
    )

    cacheStopRequestVariables = schema.Tuple(
        title=_("Request variables that prevent caching"),
        description=_("Variables in the request that prevent caching if present"),
        value_type=schema.ASCIILine(title=_("Request variables")),
        default=(
            "statusmessages",
            "SearchableText",
        ),
    )


class IETagValue(Interface):
    """ETag component builder

    Register a named multi-adapter from ``(published, request)`` to this
    interface to provide the values for ETag compnents. Various caching
    operations will look up such adapters to compose an ETag value. The
    adapter name is used in options configuring those components.
    """

    def __call__():
        """Return the ETag component, as a string."""


class IRAMCached(Interface):
    """Marker interface applied to the request if it should be RAM cached.

    The cache key will be stored in request annotations.
    """
