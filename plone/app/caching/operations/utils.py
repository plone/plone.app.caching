import wsgiref.handlers
import time
import datetime

from AccessControl.User import nobody
from OFS.interfaces import ITraversable

from zope.interface import alsoProvides
from zope.component import getMultiAdapter
from zope.component import queryUtility

from zope.annotation.interfaces import IAnnotations

from plone.memoize.interfaces import ICacheChooser
from plone.app.caching.interfaces import IRAMCached

from z3c.caching.interfaces import ILastModified
from plone.registry.interfaces import IRegistry
from plone.app.caching.interfaces import IPloneCacheSettings

from Products.CMFCore.interfaces import IContentish

PAGE_CACHE_KEY = 'plone.app.caching.operations.pagecache'
PAGE_CACHE_ANNOTATION_KEY = 'plone.app.caching.operations.pagecache.key'

#
# Basic helper functions
# 

def getContext(published, marker=IContentish):
    """Given a published object, attempt to look up a context
    
    ``published`` is the object that was published.
    ``marker`` is a marker interface to look for
    
    Returns an item providing ``marker`` or None, if it cannot be found.
    """
    
    while (
        published is not None
        and not marker.providedBy(published)
        and hasattr(published, '__parent__',)
    ):
        published = published.__parent__
    
    return published

def formatDateTime(dt):
    """Format a Python datetime object as an RFC1123 date.
    
    Returns a string.
    """
    
    return wsgiref.handlers.format_date_time(time.mktime(dt.timetuple()))

def safeLastModified(published):
    """Get a last modified date or None
    """
    
    lastModified = ILastModified(published, None)
    if lastModified is None:
        return None
    
    return lastModified()

def getExpiration(maxage):
    """Get an expiration date as a datetime.
    
    ``maxage`` is the maximum age of the item, in seconds.
    """
    
    now = datetime.datetime.now()
    if maxage > 0:
        return now + datetime.timedelta(seconds=maxage)
    else:
        return now - datetime.timedelta(seconds=10*365*24*3600)

def getRAMCache(globalKey=PAGE_CACHE_KEY):
    """Get a RAM cache instance for the given key. The return value is ``None``
    if no RAM cache can be found, or a mapping object supporting at least
    ``__getitem__()``, ``__setitem__()`` and ``get()`` that can be used to get
    or set cache values.
    
    ``key`` is the global cache key, which must be unique site-wide. Most
    commonly, this will be the operation dotted name.
    """
    
    chooser = queryUtility(ICacheChooser)
    if chooser is None:
        return None
    
    return chooser(globalKey)

def getRAMCacheKey(published, request):
    """Calculate the cache key for pages cached in RAM
    """
    
    # XXX: improve
    if hasattr(published, '__parent__'):
        content = published.__parent__
        if ITraversable.providedBy(content):
            return content.absolute_url_path()
    return request['ACTUAL_URL']

def getEtag(published, request, keys, extraTokens=()):
    """Calculate an Etag.
    
    ``keys`` is a list of types of items to include in the ETag. Valid values
    include:
    
    * member, the 
    * roles
    * permissions
    * skin
    * language
    * user_language
    * gzip
    * last_modified
    * catalog_modified
    * object_locked
    
    ``extraTokens`` is a list of additional Etag tokens to include, verbatim.
    
    All tokens will be concatenated into an Etag string, separated by pipes.
    """
    
    if not keys:
        return None
    
    context = getContext(published)
    if context is None:
        return None
    
    portal_state = getMultiAdapter((context, request), name=u'plone_portal_state')
    context_state = getMultiAdapter((context, request), name=u'plone_context_state')
    tools = getMultiAdapter((context, request), name=u'plone_tools')
    
    member = portal_state.member()
    etags = []
    
    if 'member' in keys:
        if member is not None:
            username = member.getUserName()
        else:
            username = ''
        etags.append(username)
    
    if 'roles' in keys or 'permissions' in keys:
        
        if member is None:
            mtool = tools.membership()
            member = mtool.wrapUser(nobody)
        
        roles = list(member.getRolesInContext(context))
        roles.sort()
        etags.append(';'.join(roles))
        
        if 'permissions' in keys:
            # CacheFu kept a global counter for permissions modifications.
            # Do we need to add something equivalent?
            # Perhaps this is a usecase for a "purge all content views" action instead?
            # XXX etag.append(????.get_permissions_counter())
            pass
    
    if 'skin' in keys:
        # In CacheFu we lookup and add the skin name here.
        # Another "purge all content views" usecase?
        pass
    
    if 'language' in keys:
        # Does anyone really need this?  I've heard good arguments
        # that server-negotiated content based on HTTP_ACCEPT_LANGUAGE
        # is just plain unworkable.  It's better to allow users to select
        # their language and have the choice reflected in the url.
        # In which case, there is no need to track this with etags.
        pass
    
    if 'user_language' in keys:
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
    
    if 'gzip' in keys:
        registry = queryUtility(IRegistry)
        if registry is not None:
            settings = registry.forInterface(IPloneCacheSettings, check=False)
            gzip_capable = request.get('HTTP_ACCEPT_ENCODING', '').find('gzip') != -1
            etags.append(str(int(settings.enableCompression and gzip_capable)))
    
    if 'last_modified' in keys:
        lastModified = safeLastModified(published)
        if lastModified is not None:
            etags.append(lastModified.isoformat())
    
    if 'catalog_modified' in keys:
        # CacheFu kept a counter for catalog modifications.
        # Do we need to add something equivalent?
        # XXX etags.append(????.get_catalog_modified_counter())
        pass
    
    if 'object_locked' in keys:
        etags.append(str(context_state.is_locked()))
    
    for token in extraTokens:
        etags.append(token)
    
    etag = '|' + '|'.join(etags)
    return etag.replace(',',';')  # commas are bad in etags

#
# Mutator helpers
# 

def doNotCache(published, request, response):
    """Set response headers to ensure that the response is not cached by
    web browsers or caching proxies.
    
    This is an IE-safe operation. Under certain conditions, IE chokes on
    ``no-cache`` and ``no-store`` cache-control tokens so instead we just
    expire immediately and disable validation.
    """
    
    response.unsetHeader('Last-Modified')
    response.setHeader('Expires', formatDateTime(getExpiration(0)))
    response.setHeader('Cache-Control', 'max-age=0, must-revalidate, private')

def cacheInBrowser(published, request, response, etag=None, lastmodified=None):
    """Set response headers to indicate that browsers should cache the
    response but expire immediately and revalidate the cache on every
    subsequent request.
    
    ``etag`` is a string value indicating an Etag to use.
    ``lastmodified`` is a datetime object
    
    If neither etag nor lastmodified is given then no validation is
    possible and this becomes equivalent to doNotCache()
    """
    
    if etag is not None:
        response.setHeader('ETag', etag)
    if lastmodified is not None:
        response.setHeader('Last-Modified', formatDateTime(lastmodified))
    response.setHeader('Expires', formatDateTime(getExpiration(0)))
    response.setHeader('Cache-Control', 'max-age=0, must-revalidate, private')
    # -> enable 304s

def cacheInProxy(published, request, response, smaxage, lastmodified=None, etag=None, vary=None):
    """Set headers to cache the response in a caching proxy.
    
    ``smaxage`` is the timeout value in seconds.
    ``lastmodified`` is a datetime object for the last modified time
    ``etag`` is an etag string
    ``vary`` is a vary header string
    """
    
    if lastmodified is not None:
        response.setHeader('Last-Modified', formatDateTime(lastmodified))
        # -> enable 304s
    
    if etag is not None:
        response.setHeader('ETag', etag)
        # -> enable 304s
    
    response.setHeader('Expires', formatDateTime(getExpiration(0)))
    response.setHeader('Cache-Control', 'max-age=0, s-maxage=%s, must-revalidate' %smaxage)
    
    if vary is not None:
        response.setHeader('Vary', vary)

def cacheEverywhere(published, request, response, maxage, lastmodified=None, etag=None, vary=None):
    """Set headers to cache the response in the browser and caching proxy if
    applicable.
    
    ``maxage`` is the timeout value in seconds
    ``lastmodified`` is a datetime object for the last modified time
    ``etag`` is an etag string
    ``vary`` is a vary header string
    """
    
    # Slightly misleading name as caching in RAM is not done here
    if lastmodified is not None:
        response.setHeader('Last-Modified', formatDateTime(lastmodified))
        # -> enable 304s
    
    if etag is not None:
        response.setHeader('ETag', etag)
        # -> enable 304s
    
    response.setHeader('Expires', formatDateTime(getExpiration(0)))
    response.setHeader('Cache-Control', 'max-age=%s, must-revalidate, public' %maxage)
    
    if vary is not None:
        response.setHeader('Vary', vary)

def cacheInRAM(published, request, response, key=None, annotationsKey=PAGE_CACHE_ANNOTATION_KEY):
    """Set a flag indicating that the response for the given request
    should be cached in RAM.
    
    This will signal to a transform chain step after the response has been
    generated to store the result in the RAM cache.
    
    To actually use the cached response, you will need to configure the
    'plone.app.caching.operations.pagecache' mutator.
    
    ``key`` is the caching key to use. If not set, it is calculated by
    calling getRAMCacheKey(published, request). Note that this needs to be
    the same key that is used by the interceptor, so passing a custom key
    implies using a custom interceptor as well.
    
    ``annotationsKey`` is the key used by the transform to look up the
    caching key.
    """

    annotations = IAnnotations(request, None)
    if annotations is None:
        return None
    
    if key is None:
        key = getRAMCacheKey(published, request)
    
    annotations[annotationsKey] = key
    alsoProvides(request, IRAMCached)

#
# RAM cache management
# 

def fetchFromRAMCache(published, request, response, key=None, globalKey=PAGE_CACHE_KEY):
    """Return a page cached in RAM, or None if it cannot be found.
    
    ``key`` is the cache key. If not given, it will be calculated by calling
    ``getRAMCacheKey()``
    
    ``globalKey`` is the global cache key. This needs to be the same key
    as the one used to store the data, so changing it assumes using a
    different storage mechanism than the default
    ``plone.app.caching.operations.pagecache` transform chain step.
    """
    
    cache = getRAMCache(globalKey)
    if cache is None:
        return None

    if key is None:
        key = getRAMCacheKey(published, request)
    
    if not key:
        return None
    
    return cache.get(key)

def cachedResponse(published, request, response, cached):
    """Returned a cached page. Modifies the request (status and headers)
    and returns the cached body.
    
    ``cached`` is an object as returned by ``fetchFromRAMCache()`` and stored
    by ``storeResponseInRAMCache()``, i.e. a triple of (status, header, body).
    """
    
    status, headers, body = cached
    response.setStatus(status)

    for k, v in headers.items():
        if k == 'ETag':
            response.setHeader(k, v, literal=1)
        else:
            response.setHeader(k, v)
    
    return body

def storeResponseInRAMCache(published, request, response, result, globalKey=PAGE_CACHE_KEY, annotationsKey=PAGE_CACHE_ANNOTATION_KEY):
    """Store the given response in the RAM cache.
    
    ``result`` should be the response body as a string.

    ``globalKey`` is the global cache key. This needs to be the same key
    as the one used to fetch the data, so changing it assumes using a
    different interceptor than the default
    ``plone.app.caching.operations.pagecache``

    ``annotationsKey`` is the key in annotations on the request from which 
    the caching key should be retrieved. The default is that used by the
    ``cacheInRAM()`` helper function.
    """
    
    annotations = IAnnotations(request, None)
    if annotations is None:
        return
    
    key = annotations.get(annotationsKey)
    if not key:
        return
    
    cache = getRAMCache(globalKey)
    if cache is None:
        return
    
    status = response.getStatus()
    headers = dict(request.response.headers)
    cache[key] = (status, headers, result)
