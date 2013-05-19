Changelog
---------

1.1.4 (unreleased)
~~~~~~~~~~~~~~~~~~

- Fixed purge paths for virtual hosting scenarios using virtual path components.
  [dokai]


1.1.3 (2013-03-05)
~~~~~~~~~~~~~~~~~~

- Provide message for newbies to suggest importing
  pre-defined caching rule set.
  [vangheem]



1.1.2 (2012-12-27)
~~~~~~~~~~~~~~~~~~

- Add other feed types to plone.content.feed purge policy
  [vangheem]

- Fix bug where resource registries etag is calculated incorrectly if a registry
  is missing.
  [davisagli]

- Fix bug `12038 <http://dev.plone.org/ticket/12038>`_. If transformIterable
  iterates on the 'result' iterable, it must return a new one.
  [ebrehault]


1.1.1 (2012-08-30)
~~~~~~~~~~~~~~~~~~

- Nothing changed yet.


1.1 (2012-05-25)
~~~~~~~~~~~~~~~~

- Use zope.browserresource instead of zope.app.publisher.
  [hannosch]

- Deprecated methods aliases were replaced on tests.
  [hvelarde]


1.0.4 (unreleased)
~~~~~~~~~~~~~~~~~~

- Fix possible test failures by logging in with the user name.
  Note that user id and user name (login name) can differ.
  [maurits]


1.0.3 (2012-04-15)
~~~~~~~~~~~~~~~~~~

- Fix packaging issue.
  [esteele]


1.0.2 (2012-04-15)
~~~~~~~~~~~~~~~~~~
- Handle caching of resource registries in RAM cache by not storing empty
  bodies in the RAMCache
  [eleddy with major tseaver support]


1.0.1 (2012-01-26)
~~~~~~~~~~~~~~~~~~
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
~~~~~~~~~~~~~~~~~~

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
~~~~~~~~~~~~~~~~~~

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
~~~~~~~~~~~~~~~~~~

- Initial release.
  [optilude, newbery, smcmahon]
