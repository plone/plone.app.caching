from zope.interface import Interface

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
