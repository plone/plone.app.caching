from Products.CMFCore.utils import getToolByName

def importVarious(context):
    
    if not context.readDataFile('plone.app.caching.txt'):
        return
    
    site = context.getSite()
    
    error_log = getToolByName(site, 'error_log')
    
    properties = error_log.getProperties()
    ignored = properties.get('ignored_exceptions', ())
    
    # These exception types are used for common statuses. Others may get
    # logged.
    
    modified = False
    for exceptionName in ('OK', 'MovedPermanently', 'MovedTemporarily', 'NotModified'):
        if exceptionName not in ignored:
            ignored += (exceptionName,)
            modified = True
    
    if modified:
        error_log.setProperties(properties.get('keep_entries', 10),
                                properties.get('copy_to_zlog', True),
                                ignored)
