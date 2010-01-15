import re
import time
import datetime
import logging
import dateutil.parser
import dateutil.tz
import wsgiref.handlers

from thread import allocate_lock

from zope.interface import alsoProvides
from zope.component import queryMultiAdapter
from zope.component import queryUtility

from zope.annotation.interfaces import IAnnotations

from plone.memoize.interfaces import ICacheChooser

from plone.app.caching.interfaces import IRAMCached
from plone.app.caching.interfaces import IETagValue

from z3c.caching.interfaces import ILastModified

from AccessControl.PermissionRole import rolesForPermissionOn
from Products.CMFCore.interfaces import IContentish
from Products.CMFCore.interfaces import ISiteRoot

PAGE_CACHE_KEY = 'plone.app.caching.operations.ramcache'
PAGE_CACHE_ANNOTATION_KEY = 'plone.app.caching.operations.ramcache.key'

logger = logging.getLogger('plone.app.caching')

parseETagLock = allocate_lock()
etagQuote = re.compile('(\s*\"([^\"]*)\"\s*,{0,1})')
etagNoQuote = re.compile('(\s*([^,]*)\s*,{0,1})')

#
# Operation helpers, used in the implementations of interceptResponse() and
# modifyResponse().
# 
# These all take three parameters, published, request and response, as well
# as any additional keyword parameters required.
# 

def doNotCache(published, request, response):
    """Set response headers to ensure that the response is not cached by
    web browsers or caching proxies.
    
    This is an IE-safe operation. Under certain conditions, IE chokes on
    ``no-cache`` and ``no-store`` cache-control tokens so instead we just
    expire immediately and disable validation.
    """
    
    if response.getHeader('Last-Modified'):
        del response.headers['last-modified']
    
    response.setHeader('Expires', formatDateTime(getExpiration(0)))
    response.setHeader('Cache-Control', 'max-age=0, must-revalidate, private')

def cacheInBrowser(published, request, response, etag=None, lastmodified=None):
    """Set response headers to indicate that browsers should cache the
    response but expire immediately and revalidate the cache on every
    subsequent request.
    
    ``etag`` is a string value indicating an ETag to use.
    ``lastmodified`` is a datetime object
    
    If neither etag nor lastmodified is given then no validation is
    possible and this becomes equivalent to doNotCache()
    """
    
    if etag is not None:
        response.setHeader('ETag', etag, literal=1)
        # -> enable 304s
        
    if lastmodified is not None:
        response.setHeader('Last-Modified', formatDateTime(lastmodified))
        # -> enable 304s
    
    response.setHeader('Expires', formatDateTime(getExpiration(0)))
    response.setHeader('Cache-Control', 'max-age=0, must-revalidate, private')

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
        response.setHeader('ETag', etag, literal=1)
        # -> enable 304s
    
    if vary is not None:
        response.setHeader('Vary', vary)
    
    response.setHeader('Expires', formatDateTime(getExpiration(0)))
    response.setHeader('Cache-Control', 'max-age=0, s-maxage=%s, must-revalidate' %smaxage)
    

def cacheInBrowserAndProxy(published, request, response, maxage, lastmodified=None, etag=None, vary=None):
    """Set headers to cache the response in the browser and caching proxy if
    applicable.
    
    ``maxage`` is the timeout value in seconds
    ``lastmodified`` is a datetime object for the last modified time
    ``etag`` is an etag string
    ``vary`` is a vary header string
    """
    
    if lastmodified is not None:
        response.setHeader('Last-Modified', formatDateTime(lastmodified))
        # -> enable 304s
    
    if etag is not None:
        response.setHeader('ETag', etag, literal=1)
        # -> enable 304s
    
    if vary is not None:
        response.setHeader('Vary', vary)
    
    response.setHeader('Expires', formatDateTime(getExpiration(0)))
    response.setHeader('Cache-Control', 'max-age=%s, must-revalidate, public' %maxage)

def cacheInRAM(published, request, response, etag=None, annotationsKey=PAGE_CACHE_ANNOTATION_KEY):
    """Set a flag indicating that the response for the given request
    should be cached in RAM.
    
    This will signal to a transform chain step after the response has been
    generated to store the result in the RAM cache.
    
    To actually use the cached response, you can implement
    ``interceptResponse()`` in your caching operation to call
    ``fetchFromRAMCache()`` and then return the value of the
    ``cachedResponse()`` helper.
    
    ``etag`` is a string identifying the resource.
    
    ``annotationsKey`` is the key used by the transform to look up the
    caching key when storing the response in the cache. It should match that
    passed to ``storeResponseInRAMCache()``.
    """

    annotations = IAnnotations(request, None)
    if annotations is None:
        return None
    
    key = getRAMCacheKey(request, etag=etag)
    
    annotations[annotationsKey] = key
    alsoProvides(request, IRAMCached)

def cachedResponse(published, request, response, cached):
    """Returned a cached page. Modifies the response (status and headers)
    and returns the cached body.
    
    ``cached`` is an object as returned by ``fetchFromRAMCache()`` and stored
    by ``storeResponseInRAMCache()``, i.e. a triple of
    ``(status, header, body)``.
    """
    
    status, headers, body = cached
    response.setStatus(status)

    for k, v in headers.items():
        if k.lower() == 'etag':
            response.setHeader(k, v, literal=1)
        else:
            response.setHeader(k, v)
    
    return body

def notModified(published, request, response, etag=None, lastmodified=None):
    """Return a ``304 NOT MODIFIED`` response. Modifies the response (status)
    and returns an empty body to indicate the request should be interrupted.
    
    ``etag`` is an ETag to set on the response
    ``lastmodified`` is the last modified date to set on the response
    
    Both ``etag`` and ``lastmodified`` are optional.
    """
    
    if etag is not None:
        response.setHeader('ETag', etag, literal=1)
    
    if lastmodified is not None:
        response.setHeader('Last-Modified', formatDateTime(lastmodified)) 
    
    response.setStatus(304)
    return u""

#
# Cache checks
# 

def isModified(request, etag=None, lastmodified=None):
    """Return True or False depending on whether the published resource has
    been modified.
    
    ``etag`` is the current etag, to be checked against the If-None-Match
    header.
    
    ``lastmodified`` is the current last-modified datetime, to be checked
    against the If-Modified-Since header.
    """
    
    ifModifiedSince = request.getHeader('If-Modified-Since', None)
    ifNoneMatch = request.getHeader('If-None-Match', None)

    if ifModifiedSince is None and ifNoneMatch is None:
        return True

    etagMatched = False

    # Check etags
    if ifNoneMatch and etag is not None:
        if not etag:
            return True

        clientETags = parseETags(ifNoneMatch)
        if not clientETags:
            return True

        # is the current etag in the list of client-side etags?
        if etag not in clientETags and '*' not in clientETags:
            return True
        
        etagMatched = True

    # Check the modification date
    if ifModifiedSince and lastmodified is not None:

        # Attempt to get a date
        
        try:
            ifModifiedSince = ifModifiedSince.split(';')[0]
            ifModifiedSince = parseDateTime(ifModifiedSince)
        except:
            return True
        
        # has content been modified since the if-modified-since time?
        try:
            if lastmodified > ifModifiedSince:
                return True
        except TypeError:
            logger.exception("Could not compare dates")
        
        # If we generate an ETag, don't validate the conditional GET unless 
        # the client supplies an ETag.  This may be more conservative than the
        # spec requires.
        if etag is not None:
            if not etagMatched:
                return True

    return False

def fetchFromRAMCache(request, etag, globalKey=PAGE_CACHE_KEY):
    """Return a page cached in RAM, or None if it cannot be found.
    
    ``etag`` is an ETag for the content, and is used as a basis for the
    cache key.
    
    ``globalKey`` is the global cache key. This needs to be the same key
    as the one used to store the data, i.e. it must correspond to the one
    used when calling ``storeResponseInRAMCache()``.
    """
    
    cache = getRAMCache(globalKey)
    if cache is None:
        return None

    key = getRAMCacheKey(request, etag)
    if key is None:
        return None
    
    return cache.get(key)

def visibleToRole(published, role, permission='View'):
    """Determine if the published object would be visible to the given
    role.
    
    ``role`` is a role name, e.g. ``Anonymous``.
    ``permission`` is the permission to check for.
    """
    return role in rolesForPermissionOn(permission, published)

def storeResponseInRAMCache(request, response, result, globalKey=PAGE_CACHE_KEY, annotationsKey=PAGE_CACHE_ANNOTATION_KEY):
    """Store the given response in the RAM cache.
    
    ``result`` should be the response body as a string.

    ``globalKey`` is the global cache key. This needs to be the same key
    as the one used to fetch the data.

    ``annotationsKey`` is the key in annotations on the request from which 
    the (resource-identifying) caching key should be retrieved. The default
    is that used by the ``cacheInRAM()`` helper function.
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

#
# Basic helper functions
# 

def getContext(published, marker=(IContentish, ISiteRoot,)):
    """Given a published object, attempt to look up a context
    
    ``published`` is the object that was published.
    ``marker`` is a marker interface to look for
    
    Returns an item providing ``marker`` or None, if it cannot be found.
    """
    
    if not isinstance(marker, (list, tuple,)):
        marker = (marker,)
    
    def checkType(context):
        for m in marker:
            if m.providedBy(context):
                return True
        return False
    
    while (
        published is not None
        and not checkType(published)
        and hasattr(published, '__parent__',)
    ):
        published = published.__parent__
    
    if not checkType(published):
        return None
    
    return published

def formatDateTime(dt):
    """Format a Python datetime object as an RFC1123 date.
    
    Returns a string.
    """
    
    return wsgiref.handlers.format_date_time(time.mktime(dt.timetuple()))

def parseDateTime(str):
    """Return a Python datetime object from an an RFC1123 date.
    
    Returns a datetime object with a timezone. If no timezone is found in the
    input string, assume UTC.
    """
    
    dt = dateutil.parser.parse(str)
    if not dt:
        return None
    
    if dt.tzinfo is None:
        dt = datetime.datetime(dt.year, dt.month, dt.day,
                               dt.hour, dt.minute, dt.second, dt.microsecond,
                               dateutil.tz.tzutc())
    
    return dt

def getLastModified(published):
    """Get a last modified date or None.
    
    If an ``ILastModified`` adapter can be found, and returns a date that is
    not timezone aware, force it to UTC.
    """
    
    lastModified = ILastModified(published, None)
    if lastModified is None:
        return None
    
    dt = lastModified()
    if dt is None:
        return None
    
    if dt.tzinfo is None:
        dt = datetime.datetime(dt.year, dt.month, dt.day,
                               dt.hour, dt.minute, dt.second, dt.microsecond,
                               dateutil.tz.tzutc())
    
    return dt

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

def getRAMCacheKey(request, etag=None):
    """Calculate the cache key for pages cached in RAM.
    
    ``etag`` is a unique etag string. The cache key is a combination of the
    resource's path and the etag.
    """
    
    resourceKey = request['PATH_INFO'] + '?' + request['QUERY_STRING']
    if etag:
        resourceKey = etag + '||' + resourceKey
    return resourceKey

def getETag(published, request, keys=(), extraTokens=()):
    """Calculate an ETag.
    
    ``keys`` is a list of types of items to include in the ETag. These must
    match named multi-adapters on (published, request) providing
    ``IETagValue``.
    
    ``extraTokens`` is a list of additional ETag tokens to include, verbatim
    as strings.
    
    All tokens will be concatenated into an ETag string, separated by pipes.
    """
    
    tokens = []
    for key in keys:
        component = queryMultiAdapter((published, request), IETagValue, name=key)
        if component is None:
            logger.warning("Could not find value adapter for ETag component %s", key)
        else:
            value = component()
            if value is not None:
                tokens.append(value)
    
    for token in extraTokens:
        tokens.append(token)
    
    etag = '|' + '|'.join(tokens)
    return etag.replace(',',';')  # commas are bad in etags

# Adapted from Products.CMFCore.utils

def parseETags(text, result=None):
    """Parse a header value into a list of etags. Handles fishy quoting and
    other browser quirks.
    
    Returns a list of strings.
    """

    if result is None:
        result = []
    
    if not len(text):
        return result
    
    # Lock, since regular expressions are not threadsafe
    parseETagLock.acquire()
    try:
        m = etagQuote.match(text)
        if m:
            # Match quoted etag (spec-observing client)
            l     = len(m.group(1))
            value = m.group(2)
        else:
            # Match non-quoted etag (lazy client)
            m = etagNoQuote.match(text)
            if m:
                l     = len(m.group(1))
                value = m.group(2)
            else:
                return result
    finally:
        parseETagLock.release()

    if value:
        result.append(value)
    
    return parseETags(text[l:], result)

