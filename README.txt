plone.app.caching
=================

Plone UI and default rules for plone.caching/z3c.caching

Requires Plone 4.

Installation
------------

To install ``plone.app.caching``, add it to the ``eggs`` list in your
``buildout.cfg``, or as a dependency of one of your own packages in 
``setup.py``. ZCML configuration will be automatically loaded via a
``z3c.autoinclude`` entry point. You will also need to install the package
in Plone's Add-ons control panel as normal.

This package depends on a number of other packages, including ``z3c.form`` and
``plone.app.registry``, that do not ship with Plone. You will probably want
to lock down the versions for those packages using a known good set. Add
this to the the ``extends`` line in your ``buildout.cfg``, *after* the
line that includes the Plone KGS::

    extends =
        ...
        http://good-py.appspot.com/release/plone.app.caching/1.0a1

Update the version number at the end of the URL as appropriate. You can find
an overview of the versions 
`here <http://good-py.appspot.com/release/plone.app.caching>`_

The caching control panel
-------------------------

After installation, you will find a Caching control panel in Plone's site
setup. This consists of three main tabs:

* *Cache settings*, where you can control caching behaviour
* *Import settings*, where you can import pre-defined profiles of cache
  settings
* *Purge*, where you can manually purge content from a caching proxy. This
  tab only appears if you have purging enabled under *Cache settings*.

Under the settings tab, you will find four fieldsets:

* *General settings*, for global options such as turning caching on or off.
* *Caching proxies*, where you can control Plone's use of a caching proxy
  such as Squid or Varnish.
* *Mappings*, where caching rulesets (hints about views and resources used for
  caching purposes) can be associated with caching operations (which either
  intercept a request to return a cached response, or mutates a response to
  add cache control headers). This is also where rulesets for legacy page
  templates (created through the web or the portal_skins tool) are
  configured.
* *Detailed settings*, where you can configure parameters for individual
  caching operations.

Declaring cache rules and writing caching operations
----------------------------------------------------

The caching infrastructure works on the principle of *rulesets* mapped to
*cache interceptors* and *response mutators*, collectively known as
*caching operations*. A ruleset is basically just a name, and is normally
applied in ZCML by the author of a particular view. There are also some
default rulesets applied to general resources - see below.

Caching operations are components written in Python which either interrupt
rendering to provide a cached response (such as a ``304 NOT MODIFIED``
response), in the case of interceptors, or add caching information to a
response (such as setting the ``Cache-Control`` HTTP response header), in the
case of mutators.

For more details on how to use these components, see the documentation for
`plone.caching`_.

Please note that ``plone.app.caching`` places the caching ruleset registry
into "explicit" mode. This means that you *must* declare a caching rulset
(with the ``<cache:rulesetType />`` directive) before you can use it.

Once ruleset and caching operation types have been registered, they will
appear in the caching control panel.

Default cache ruleset types
---------------------------

``plone.app.caching`` declares a few default ruleset types, which you map in
its control panel and use in ``<cache:ruleset />`` directives in your own
code. They are listed with descriptions in the control panel.

Default cache operations
------------------------

``plone.app.caching`` also declares a number of default operation types,
most of which can be configured via the GUI or through the configuration
registry directly (see below). These are listed in the control panel as
available operations for the various ruleset types. Hover your mouse over
an operation in the drop-down list to view its description.

Managing caching profiles
-------------------------

All persistent configuration for the caching machinery is stored in the
configuration registry, as managed by ``plone.app.registry``. This can be
modified using the ``registry.xml`` GenericSetup import step. The *Import
settings* tab of the control panel allows you to import these profiles.

A GenericSetup profile used for caching should be registered for the
``ICacheProfiles`` marker interface to distinguish it from more general
profiles used to install a product, say. This also hides the profile from
Plone's Add-ons control panel.

Here is an example from this package::

    <genericsetup:registerProfile
        name="with-caching-proxy"
        title="With caching proxy"
        description="Settings useful for setups with a caching proxy such as Squid or Varnish"
        directory="profiles/with-caching-proxy"
        provides="Products.GenericSetup.interfaces.EXTENSION"
        for="plone.app.caching.interfaces.ICacheProfiles"
        />

The directory ``profiles/with-caching-proxy`` contains a single import step,
``registry.xml``, containing settings to configure the ruleset to interceptor
and mutator mappings, and setting options for various operations. It may be
useful looking at that file for inspiration if you are building your own
caching profile. Alternatively, you can export the registry from the
``portal_setup`` tool and pull out the records under the prefixes
``plone.caching`` and ``plone.app.caching``.

Typically, ``registry.xml`` is all that is required, but you are free to add
additional import steps if required. You can also add a ``metadata.xml`` and
use the GenericSetup dependency mechanism to install other profiles on the
fly.

Caching operation helper functions
----------------------------------

If you are writing a custom caching operation, you will find the
implementations of the default caching operations in the package
``plone.app.caching.operations``. The ``utils`` module contains helper
functions which you may find useful.

Caching proxies and purging
---------------------------

It is common to place a so-called caching reverse proxy in front of Zope
when hosting large Plone sites. On Unix, the best option is generally
considered to be `Varnish`_, although `Squid`_ will also work. On Windows,
you can use Squid or the (commercial, but better) `Enfold Proxy`_.

Some operations in ``plone.app.caching`` can set response headers that
instruct the caching proxy how best to cache content [1]_. For example, it is
normally a good idea to cache static resources (such as images and
stylesheets) and "downloadables" (such as Plone content of the types ``File``
or ``Image``) in the proxy. This content will then be served to most users
straight from the proxy, which is much faster than Zope.

The downside of this approach is that an old version of a content item may
returned to a user, because the cache has not been updated since the item
was modified. There are three general strategies for dealing with this:

* Since resources are cached in the proxy based on their URL, you can
  "invalidate" the cached copy by changing an item's URL when it is updated.
  This is the approach taken by Plone's ResourceRegistries (``portal_css``,
  ``portal_javascript`` & co): in production mode, the links that are inserted
  into Plone's content pages for resource managed by ResourceRegistries
  contain a time-based token, which changes when the ResourceRegistries
  are updated. This approach has the benefit of also being able to
  "invalidate" content stored in a user's browser cache.
* All caching proxies support setting timeouts. This means that content may
  be stale, but typically only up to a few minutes. This is sometimes an
  acceptable policy for high-volume sites where most users do not log in.
* Most caching proxies support receiving PURGE requests for paths that
  should be purged. For example, if the proxy has cached a resource at
  ``/logo.jpg``, and that object is modified, a PURGE request could be sent
  to the proxy (originating from Zope, not the client) with the same path to
  force the proxy to fetch a new version the next time the item is requested.

The final option, of course is to avoid caching content in the proxy
altogether. The default policies will not allow standard content pages to
be cached in the proxy, because it is too difficult to invalidate cached
instances. For example, if you change a content item's title, that may
require invalidation of a number of pages where that title appears in the
navigation tree, folder listings, ``Collections``, portlets, and so on.
Tracking all these dependencies and purging in an efficient manner is
impossible unless the caching proxy configuration is highly customised for
the site.

Synchronous and asynchronous purging is enabled via `plone.cachepurging`_.
In the control panel, you can configure the use of a proxy via various
options, such as:

* Whether or not to enable purging globally.
* The address of the caching server to which PURGE requests should be sent.
* Whether or not virtual host rewriting takes place before the caching proxy
  receives a URL or not. This has implications for how the PURGE path is
  constructed.
* Any domain aliases for your site, to enable correct purging of content
  served via e.g. http://example.com and http://www.example.com.

The default purging policy is geared mainly towards purging file and image
resources, not content pages, although basic purging of content pages is
included. The actual paths to purge are constructed from a number of
components providing the ``IPurgePaths`` interface. See ``plone.cachepurging``
for details on how this works, especially if you need to write your own.

The default purge paths include:

* ${object_path}, -- the object's canonical path
* ${object_path}/ -- in case the object is a folder
* ${object_path}/view -- the ``view`` method alias
* ${object_path}/${default-view} -- in case a default view template is used
* The download URLs for any Archetypes object fields, in the case of
  Archetypes content. This includes support for the standard ``File`` and
  ``Image`` types.

Files and images created (or customised) in the ZMI are purged automatically
when modified. Files managed through the ResourceRegistries do not need
purging, since they have "stable" URLs. To purge Plone content when modified
(or removed), you must select the content types in the control panel. By
default, only the ``File`` and ``Image`` types are purged.

You should not enable purging for types that are not likely to be cached in
the proxy. Although purging happens asynchronously at the end of the request,
it may still place unnecessary load on your server.

Finally, you can use the *Purge* tab in the control panel to manually purge
one or more URLs. This is a useful way to debug cache purging, as well as
a quick solution for the awkward situation where your boss walks in and
wonders why the "about us" page is still showing that old picture of him,
before he had a new haircut.

Debug logging
-------------

It can sometimes be useful to see which rulesets and operations (if any)
are being applied to published resources. If you enable the DEBUG logging
level for the ``plone.caching`` logger, you will get this output in your
event log. One way to do that is to set the global Zope logging level to
DEBUG in ``zope.conf``::

    <eventlog>
        level DEBUG
        <logfile>
            path <file path here>
            level DEBUG
        </logfile>
    </eventlog>    

If you are using `plone.recipe.zope2instance`_ to create your Zope instances,
you can set the logging level with the ``event-log-level`` option.

You should see output in the log like::

    2010-01-11 16:44:10 DEBUG plone.caching Published: <ATImage at /test/i> Ruleset: plone.download Interceptor: None
    2010-01-11 16:44:10 DEBUG plone.caching Published: <ATImage at /test/i> Ruleset: plone.download Mutator: plone.caching.operations.chain

The ``None`` indicates that no ruleset or operation was mapped.

It is probably not a good idea to leave debug logging on for production use,
as it can produce a lot of output, filling up log files and adding unnecessary
load to your disks.

.. _plone.caching: http://pypi.python.org/pypi/plone.caching
.. _plone.cachepurging: http://pypi.python.org/pypi/plone.cachepurging
.. _plone.recipe.zope2instance: http://pypi.python.org/pypi/plone.recipe.zope2instance
.. _Varnish: http://varnish-cache.org
.. _Squid: http://squid-cache.org
.. _Enfold Proxy: http://enfoldsystems.com/software/proxy/

.. [1] It is important to realise that whilst ``plone.app.caching`` provides
       some functionality for controlling how Plone interacts with a caching
       proxy, the proxy itself must be configured separately.
