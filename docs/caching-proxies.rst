Caching proxies
---------------

It is common to place a so-called caching reverse proxy in front of Zope when hosting large Plone sites.
If hosted by yourself, a popular option is `Varnish`_.
On the other hand there are commercial hosted CDN services like Cloudflare, CloudFront, Fastly and more.

It is important to realise that whilst ``plone.app.caching`` provides some functionality for controlling how Plone interacts with a caching proxy.
The proxy itself must be configured separately.

Some operations in ``plone.app.caching`` can set response headers that instruct the caching proxy how best to cache content.
For example, it is normally a good idea to cache static resources (such as images and stylesheets) and "downloadables"  in the proxy.
This are i.e. Plone content of the types ``File`` or ``Image``.
This content will then be served to most users straight from the proxy, which is much faster than Zope.

The downside of this approach is that an old version of a content item may returned to a user, because the cache has not been updated since the item was modified.
There are three general strategies for dealing with this:

* Since resources are cached in the proxy based on their URL, you can "invalidate" the cached copy by changing an item's URL when it is updated.
  This is the approach taken by Plone's resource management:
  in production mode, the links that are inserted into Plone's content pages for resource managed by Plone  contain a hash-based token, which changes when the main bundle file changes.
  This approach has the benefit of also being able to "invalidate" content stored in a user's browser cache.

* All caching proxies support setting timeouts.
  This means that content may be stale, but typically only up to a few minutes.
  This is sometimes an acceptable policy for high-volume sites where most users do not log in.

* Most caching proxies support receiving PURGE requests for paths that should be purged.
  Given the proxy has cached a resource at ``/logo.jpg``, and that object is modified.
  Then a PURGE request could be sent to the proxy (originating from Zope, not the client) with the same path to force the proxy to fetch a new version the next time the item is requested.

The final option, of course is to avoid caching content in the proxy altogether.
The default policies will not allow standard listing pages to be cached in the proxy, because it is too difficult to invalidate cached instances.
For example, if you change a content item's title, that may require invalidation of a number of pages where that title appears in the navigation tree, folder listings, ``Collections``, portlets, and so on.
Tracking all these dependencies and purging in an efficient manner is impossible unless the caching proxy configuration is highly customised for the site.

Nevertheless a "terse" policy allows caching for just a few seconds of all pages to reduce the load on the backend on high traffic situations.


Purging a caching proxy
~~~~~~~~~~~~~~~~~~~~~~~

Synchronous and asynchronous purging is enabled via `plone.cachepurging`_.
In the control panel, you can configure the use of a proxy via various options, such as:

* Whether or not to enable purging globally.

* The address of the caching server to which PURGE requests should be sent.

* Whether or not virtual host rewriting takes place before the caching proxy receives a URL or not.
  This has implications for how the PURGE path is constructed.

* Any domain aliases for your site, to enable correct purging of content served via e.g. http://example.com and http://www.example.com.

The default purging policy is geared mainly towards purging file and image resources, not content pages, although basic purging of content pages is included.
The actual paths to purge are constructed from a number of components providing the ``IPurgePaths`` interface.
See ``plone.cachepurging`` for details on how this works, especially if you need to write your own.

The default purge paths include:

* ${object_path}, -- the object's canonical path

* ${object_path}/ -- in case the object is a folder

* ${object_path}/view -- the ``view`` method alias

* ${object_path}/${default-view} -- in case a default view template is used

* The download URLs for any content object fields, given the type contains blobs.
This includes support for the standard ``File`` and  ``Image`` types.

Files and images created (or customised) in the ZMI are purged automatically when modified.
Bundles managed through the resource registration do not need purging, since they have "stable" URLs.
To purge Plone content when modified (or removed), you must select the content types in the control panel.
By default, only the ``File`` and ``Image`` types are purged.

You should not enable purging for types that are not likely to be cached in the proxy.
Although purging happens asynchronously at the end of the request, it may still place unnecessary load on your server.

Finally, you can use the *Purge* tab in the control panel to manually purge one or more URLs.
This is a useful way to debug cache purging.
It offers as well as a quick solution for the awkward situation where your boss walks in and wonders why the "about us" page is still showing that old picture of him, before he had a new haircut.


Installing and configuring a caching proxy
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

There is a buildout recipes for building and configuring proxy configs: `plone.recipe.varnish`_.

.. _Varnish: http://varnish-cache.org
.. _plone.recipe.varnish: http://pypi.python.org/pypi/plone.recipe.varnish
.. _plone.cachepurging: http://pypi.python.org/pypi/plone.cachepurging
