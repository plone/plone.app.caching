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

This package depends on a number of packages, such as ``z3c.form`` and
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
setup. This consists of four sections:

* *General settings*, for global options such as turning caching on or off.
* *Mappings*, where caching rulesets (hints about views and resources used for
  caching purposes) can be associated with caching operations (which either
  intercept a request to return a cached response, or mutates a response to
  add cache control headers). This is also where rulesets for legacy page
  templates (created through the web or the portal_skins tool) are
  configured.
* *Detailed settings*, where you can configure parameters for individual
  caching operations.
* *Import settings*, whence you can import caching profiles installed by 
  third party products or shipping with ``plone.app.caching`` itself. This is
  a convenient way to get started.

Declaring cache rules and writing caching operations
----------------------------------------------------

The caching infrastructure works on the principle of *rulesets* mapped to
*cache interceptors* and *response mutators*, collectively known as
*caching operations*. A ruleset is basically just a name, and is normally
applied in ZCML by the author of a particular view. There are also some
default rulesets applied to general resources - see below. Caching operations
are components written in Python which either interrupt rendering to provide
a cached response (such as a ``304 NOT MODIFIED`` response), in the case of
interceptors, or add caching information to a response (such as setting the
``Cache-Control`` HTTP response header), in the case of mutators.

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
modified using the ``registry.xml`` GenericSetup import step. The *Import*
section of the control panel allows you to import these profiles.

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

.. _plone.caching: http://pypi.python.org/pypi/plone.caching
