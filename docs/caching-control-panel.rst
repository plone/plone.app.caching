The caching control panel
-------------------------

After installation, you will find a Caching control panel in Plone's site
setup. This consists of four main tabs:

* *Change settings*, where you can control caching behaviour

* *Import settings*, where you can import pre-defined profiles of cache
  settings

* *Purge caching proxy*, where you can manually purge content from a caching
  proxy. This tab only appears if you have purging enabled under
  *Change settings*.

* *RAM cache*, where you can view statistics about and purge the RAM cache.

Under the settings tab, you will find four fieldsets:

* *General settings*, for global options such as turning caching on or off.

* *Caching proxies*, where you can control Plone's use of a caching proxy
  such as Squid or Varnish.

* *Caching operation mappings*, where caching rulesets (hints about views and
  resources used for caching purposes) can be associated with caching
  operations (which either intercept a request to return a cached response, or
  modifies a response to add cache control headers). This is also where
  rulesets for legacy page templates (created through the web or the
  portal_skins tool) are configured.

* *Detailed settings*, where you can configure parameters for individual
  caching operations.
