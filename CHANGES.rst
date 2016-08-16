Changelog
---------

1.2.11 (2016-08-17)
-------------------

Fixes:

- Use zope.interface decorator.
  [gforcada]


1.2.10 (2016-03-29)
-------------------

New:

- Show status after synchronous purge if it is an error status.
  [maurits]


1.2.9 (2016-02-19)
------------------

Fixes:

- Fixed deprecated imports in tests.  [thet]


1.2.8 (2015-11-28)
------------------

Fixes:

- Updated Site Setup link in all control panels.
  Fixes https://github.com/plone/Products.CMFPlone/issues/1255
  [davilima6]


1.2.7 (2015-09-09)
------------------

- fix cache settings modal settings so they do not show content
  inline on save.
  [vangheem]


1.2.6 (2015-07-18)
------------------

- Remove gzip option, silly to be done at this layer.
  [vangheem]

- Change the category of the configlet to 'plone-advanced'
  [sneridagh]


1.2.5 (2015-06-09)
------------------

- correctly create purge paths for root of site, prevent double slashes
  and the empty root of site(no trailing slash) not getting a purge
  path generated
  [vangheem]


1.2.4 (2015-06-05)
------------------

- update first time here warning
  [vangheem]

- make control panel work for both plone 4 and plone 5 with tabs
  [vangheem]


1.2.3 (2015-05-04)
------------------

- Fixed getObjectDefaultView method to strip off leading / and/or @@.
  [alecghica]

- Fix the portalPath used in the controlpanel for manual purging URL's.
  This bug resulted in rarely doing all the purging required.
  [puittenbroek]


1.2.2 (2014-10-23)
------------------

- Remove DL's from portal message templates.
  https://github.com/plone/Products.CMFPlone/issues/153
  [khink]

- Fix ruleset registry test isolation so that is no longer order dependent.
  [jone]


1.2.1 (2014-04-01)
------------------

- Fix tests that fail on the day before the switch to daylight saving time.
  [pbauer]


1.2.0 (2014-02-26)
------------------

- Use the PLONE_APP_CONTENTTYPES_FIXTURE test layer for Plone 5 compatibility.
  [timo]


1.1.7 (unreleased)
------------------

- Make it possible to set a maxage of zero in strong caching. This is
  an edge case since this would ordinarily be handled by moderate caching.
  [smcmahon]

- Add some testing for weak caching operations.
  [smcmahon]

- Fix handling of anon-only flag for cases where maxage is not zero. It
  was effectively ignored. Added operation test for strong caching.
  [smcmahon]


1.1.6 (2013-08-14)
------------------

- Fix double purge of paths for items whose default view is the same as /view
  [eleddy]


1.1.5 (2013-08-13)
------------------

- Register the plone.atobjectfields adapter not only when Products.Archetypes
  but also plone.app.blob is installed.
  [thet]


1.1.4 (2013-06-13)
------------------

- Fixed purge paths for virtual hosting scenarios using virtual path components.
  [dokai]


1.1.3 (2013-03-05)
------------------

- Provide message for newbies to suggest importing
  pre-defined caching rule set.
  [vangheem]



1.1.2 (2012-12-27)
------------------

- Add other feed types to plone.content.feed purge policy
  [vangheem]

- Fix bug where resource registries etag is calculated incorrectly if a registry
  is missing.
  [davisagli]

- Fix bug `12038 <http://dev.plone.org/ticket/12038>`_. If transformIterable
  iterates on the 'result' iterable, it must return a new one.
  [ebrehault]


1.1.1 (2012-08-30)
------------------

- Nothing changed yet.


1.1 (2012-05-25)
~~~~~~~~~~~~~~~~

- Use zope.browserresource instead of zope.app.publisher.
  [hannosch]

- Deprecated methods aliases were replaced on tests.
  [hvelarde]


1.0.4 (unreleased)
------------------

- Fix possible test failures by logging in with the user name.
  Note that user id and user name (login name) can differ.
  [maurits]


1.0.3 (2012-04-15)
------------------

- Fix packaging issue.
  [esteele]


1.0.2 (2012-04-15)
------------------
- Handle caching of resource registries in RAM cache by not storing empty
  bodies in the RAMCache
  [eleddy with major tseaver support]


1.0.1 (2012-01-26)
------------------
- Properly handle a changed configuration from with etags to no etags by
  forcing a page refresh
  [eleddy]

- When not caching with etags, don't sent an etag header to stop caching
  [eleddy]

- When there was an error like Unauthorized, 200 status and empty body would be
  cached in RAMCache instead of not caching anything.
  This is due to a bug with Zope 2.13 publication events :
  response.status is not set when IPubBeforeAbort is notified.
  Fixed by using error_status stored on request by plone.transformchain.
  [gotcha]

- Added 12 translation strings for ruleset's title and description. Corresponding translation
  strings have been added in plone.app.caching-manual.pot in PloneTranslations
  [giacomos]

- Added 6 translation strings for caching profiles' title and description. Corresponding translation
  strings have been added in plone.app.caching-manual.pot in PloneTranslations
  [giacomos]

- Changed wrong i18n domain in the messagefactory. plone.caching -> plone.app.caching.
  [giacomos]

1.0 - 2011-05-12
~~~~~~~~~~~~~~~~

- Use the `userLanguage` ETag component in place of the language ETag component
  in the default configs to allow ETags to be used for anonymous users with
  caching.
  [elro]

- Add the SERVER_URL to the RAM cache key.
  [elro]

- Declare `plone.namedfile.scaling.ImageScale` to be a `plone.stableResource`.
  [elro]

- Add MANIFEST.in.
  [WouterVH]

- Fixed tests failing on Zope 2.13 due to the HTTP status no longer being
  included in the response headers.
  [davisagli]

- Add an ILastModified adapter for FSPageTemplate as the FSObject adapter
  would otherwise take precedence.
  [stefan]


1.0b2 - 2011-02-10
------------------

- Added `News Item` to the list of `purgedContentTypes`, so the image field
  and its scales gets purged.
  [stefan, hannosch]

- Associated `file_view`, `image_view` and `image_view_fullscreen` by default
  with the `plone.content.itemView` ruleset, since none of them is the default
  view of their respective content type, they didn't get the automated
  handling.
  [stefan, hannosch]

- Added purging for plone.app.blob's BlobFields.
  [stefan, hannosch]

- Fix documentation to refer to the correct `resourceRegistries` instead of
  the singular version.
  [stefan, hannosch]

- Use plone.registry ``FieldRefs`` to manage parameter overrides. This
  requires plone.app.registry 1.0b3 and plone.app.registry 1.0b3 or later.
  [optilude]

- Update distribution metadata to current best practice.
  [hannosch]

- Added an etag component to track the existence of a copy/cut cookie
  [newbery]

- Fixed various i18n issues.
  [vincentfretin]


1.0b1 - 2010-08-04
------------------

- Add an option for "anonymous only" caching to the default operations.
  This is a simple way to switch off caching for logged-in users. See
  the README for more details.
  [optilude]

- Add basic plone.namedfile caching rules, if plone.namedfile is installed
  [optilude]

- Implement lookup based on portal type class/interface as well as name,
  and set up defaults for items and folders.
  [optilude]

- template fixes for cmf.pt compatibility
  [pilz]


1.0a1 - 2010-04-24
------------------

- Initial release.
  [optilude, newbery, smcmahon]
