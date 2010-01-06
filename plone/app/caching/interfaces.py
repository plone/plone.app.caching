import zope.i18nmessageid

from zope.interface import Interface
from zope import schema

_ = zope.i18nmessageid.MessageFactory('plone.caching')

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
            title=_(u"Page template/ruleset mapping"),
            description=_(u"Maps skin layer page template names to ruleset names"),
            key_type=schema.ASCIILine(title=_(u"Page template name")),
            value_type=schema.DottedName(title=_(u"Ruleset name")),
        )
    
    contentTypeRulesetMapping = schema.Dict(
            title=_(u"Content type/ruleset mapping"),
            description=_(u"Maps content type names to ruleset names"),
            key_type=schema.ASCIILine(title=_(u"Content type name")),
            value_type=schema.DottedName(title=_(u"Ruleset name")),
        )
