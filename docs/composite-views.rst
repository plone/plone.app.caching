Composite views
---------------

A ``composite view`` is just a general term for most page views you see when
you visit a Plone site. It includes all content item views, content folder
views, and many template views. For our purposes, the distinguishing
characteristic of composite views is the difficulty inherent in keeping track
of all changes that might affect the final composited view. Because of the
difficulty of dependancy tracking, composite views are often notoriously
difficult to purge reliably from caching proxies so the default caching
profiles set headers which expire the cache immediately (i.e. *weak caching*).

However, most of the inline resources linked to from the composite view (css,
javascript, images, etc.) can be cached very well in proxy so the overall
speed of most composite views will always be better with a caching proxy in
front despite the page itself not being cached.

Also, when using Squid as a caching proxy, we can still see some additional
speed improvement as Squid supports conditional requests to the backend and
304 responses from plone.app.caching are relatively quick.  This means that
even though the proxy cache will expire immediately, Squid can revalidate its
cache relatively quickly.  Varnish does not currently support conditional
requests to the backend.

For relatively stable composite views or for those views for which you can
tolerate some potential staleness, you might be tempted to try switching from
*weak caching* to *moderate caching* with the ``s-maxage`` expiration
value set to some tolerable value but first make sure you understand the
issues regarding "split view" caching (see below).
