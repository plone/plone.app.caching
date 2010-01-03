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
    
    templateMutatorMapping = schema.Dict(
            title=_(u"Page template/response mutator mapping"),
            description=_(u"Maps skin layer page template names to response mutator operation names"),
            key_type=schema.DottedName(title=_(u"Page template name")),
            value_type=schema.DottedName(title=_(u"Response mutator name")),
        )
    
    templateInterceptorMapping = schema.Dict(
            title=_(u"Page template/interceptor mapping"),
            description=_(u"Maps skin layer page template names to cache interceptor operation names"),
            key_type=schema.DottedName(title=_(u"Page template name")),
            value_type=schema.DottedName(title=_(u"Interceptor name")),
        )

    contentTypeMutatorMapping = schema.Dict(
            title=_(u"Content type/response mutator mapping"),
            description=_(u"Maps content type names to response mutator operation names"),
            key_type=schema.DottedName(title=_(u"Content type name")),
            value_type=schema.DottedName(title=_(u"Response mutator name")),
        )
    
    contentTypeInterceptorMapping = schema.Dict(
            title=_(u"Content type/interceptor mapping"),
            description=_(u"Maps contnet type names to cache interceptor operation names"),
            key_type=schema.DottedName(title=_(u"Content type name")),
            value_type=schema.DottedName(title=_(u"Interceptor name")),
        )
