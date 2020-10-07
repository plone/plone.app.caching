Split views
-----------

A non-zero expiration for proxy or browser caching of a composite view will
often require some special handling to deal with "split view" caching.

Caching proxies and browsers keep track of cached entries by using the URL
as a key.  If a Vary header is included in the response then those request
headers listed in Vary are also included in the cache key.  In most cases,
this is sufficient to uniquely identify all responses.  However, there are
exceptions.  We call these exceptions "split views". Anytime you have
multiple views sharing the same cache key, you have a split view problem.
Split views cannot be cached in proxies or browsers without mixing up the
responses.

In the Plone case, most composite views are also split views because they
provide different views to anonymous and authenticated requests.
In Plone, authenticated requests are tracked via cookies which are not
usually used in cache keys.

One solution to this problem is to add a ``Vary:Cookie`` response header but,
unfortunately, since cookies are used for all sorts of state maintenance and
web tracking, this will usually result in very inefficient caching.

Another solution is to enforce a different domain name, different path,
or different protocol (https/http) for authenticated versus anonymous
responses.

Yet another solution involves intercepting the request and dynamically adding
a special ``X-Anonymous`` header to the anonymous request and then adding
``Vary:X-Anonymous`` to the split view response so that this header will added
to the cache key.
