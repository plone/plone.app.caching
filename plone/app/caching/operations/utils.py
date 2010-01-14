from AccessControl.User import nobody
from App.Common import rfc1123_date
from DateTime import DateTime

from zope.component import getMultiAdapter
from zope.component import queryUtility

from z3c.caching.interfaces import ILastModified
from plone.registry.interfaces import IRegistry
from plone.app.caching.interfaces import IPloneCacheSettings

def doNotCache(response):
    response.unsetHeader('Last-Modified')
    response.setHeader('Expires', getExpiration(0))
    response.setHeader('Cache-Control', 'max-age=0, must-revalidate, private')

def cacheInBrowser(response, etag=None, lastmodified=None):
    # Note: if neither etag nor lastmodified is given
    # then this is the same as doNotCache()
    if etag is not None:
        response.setHeader('ETag', etag)
    if lastmodified is not None:
        response.setHeader('Last-Modified', lastmodified)
    response.setHeader('Expires', getExpiration(0))
    response.setHeader('Cache-Control', 'max-age=0, must-revalidate, private')
    # -> enable 304s

def cacheInRAM(response, etag):
    # XXX need Zope RAM code here...
    # if anonymous and zoperam_enabled:
    #     ... cache this in zope ram ...
    # 
    # -> add zope ram interceptor?
    # -> enable 304s
    pass

def cacheInProxy(response, smaxage, lastmodified=None, etag=None, vary=None):
    if lastmodified is not None:
        response.setHeader('Last-Modified', lastmodified)
        # -> enable 304s
    if etag is not None:
        response.setHeader('ETag', etag)
        # -> enable 304s
    response.setHeader('Expires', getExpiration(0))
    response.setHeader('Cache-Control', 'max-age=0, s-maxage=%s, must-revalidate' %smaxage)
    if vary is not None:
        response.setHeader('Vary', vary)

def cacheEverywhere(response, maxage, lastmodified=None, etag=None, vary=None):
    # Slightly misleading name as caching in RAM is not done here
    if lastmodified is not None:
        response.setHeader('Last-Modified', lastmodified)
        # -> enable 304s
    if etag is not None:
        response.setHeader('ETag', etag)
        # -> enable 304s
    response.setHeader('Expires', getExpiration(0))
    response.setHeader('Cache-Control', 'max-age=%s, must-revalidate, public' %maxage)
    if vary is not None:
        response.setHeader('Vary', vary)

def getExpiration(maxage):
    now = DateTime().timeTime()
    if maxage > 0:
        expiration_time = now + maxage
    else:
        expiration_time = now - 10*365*24*3600
    return rfc1123_date(expiration_time)

def getEtag(published, request, values, *extras):
   if values is None:
       return None
   portal_state = getMultiAdapter((published, request), name=u'plone_portal_state')
   context_state = getMultiAdapter((published, request), name=u'plone_context_state')
   tools = getMultiAdapter((published, request), name=u'plone_tools')
   member = portal_state.member()
   etags = []
   if len(values):
       if 'member' in tokens:
           if member is not None:
               username = member.getUserName()
           else:
               username = ''
           etags.append(username)
       if 'roles' in values or 'permissions' in values:
           if member is None:
               mtool = tools.membership()
               member = mtool.wrapUser(nobody)
           roles = list(member.getRolesInContext(context))
           roles.sort()
           etags.append(';'.join(roles))
           if 'permissions' in values:
               # CacheFu kept a global counter for permissions modifications.
               # Do we need to add something equivalent?
               # Perhaps this is a usecase for a "purge all content views" action instead?
               # XXX etag.append(????.get_permissions_counter())
               pass
       if 'skin' in values:
           # In CacheFu we lookup and add the skin name here.
           # Another "purge all content views" usecase?
           pass
       if 'language' in values:
           # Does anyone really need this?  I've heard good arguments
           # that server-negotiated content based on HTTP_ACCEPT_LANGUAGE
           # is just plain unworkable.  It's better to allow users to select
           # their language and have the choice reflected in the url.
           # In which case, there is no need to track this with etags.
           pass
       if 'user_language' in values:
           # But... if cookie negotiation is used for language binding
           # we still need to get the current language selection.
           # Note, I don't know enough about how the language tool works
           # so I'm not sure if the following makes sense.
           ltool = tools.languages()   # is this right?
           if ltool is None:
               ptool = tools.properties()  # is this right?
               lang = ptool.site_properties.default_language
           else:
               lang = ltool.getPreferredLanguage()
           etags.append(lang)
       if 'gzip' in values:
           registry = queryUtility(IRegistry)
           if registry is not None:
               settings = registry.forInterface(IPloneCacheSettings, check=False)
               gzip_capable = request.get('HTTP_ACCEPT_ENCODING', '').find('gzip') != -1
               etags.append(int(settings.enableCompression and gzip_capable))
       if 'last_modified' in values:
           etag.append(ILastModified(published)())
       if 'catalog_modified' in values:
           # CacheFu kept a counter for catalog modifications.
           # Do we need to add something equivalent?
           # XXX etags.append(????.get_catalog_modified_counter())
           pass
       if 'object_locked' in values:
           etags.append(context_state.is_locked())
       for token in extras:
           etags.append(token)
       etag = '|' + '|'.join(etags)
       return etag.replace(',',';')  # commas are bad in etags
