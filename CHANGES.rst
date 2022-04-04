Changelog
---------

.. You should *NOT* be adding new change log entries to this file.
   You should create a file in the news directory instead.
   For helpful instructions, please see:
   https://github.com/plone/plone.releaser/blob/master/ADD-A-NEWS-ITEM.rst

.. towncrier release notes start

3.0.0a12 (2022-04-04)
---------------------

Bug fixes:


- Test-only fix: caching checks for ``timestamp.txt`` in ``portal_resources`` which is no longer there.
  Update ETAG Headers accordingly.
  [pbauer] (#92)


3.0.0a11 (2022-02-24)
---------------------

Bug fixes:


- Updated control panel icon. Use iconresolver to get the proper svg icon.
  [yurj] (#91)


3.0.0a10 (2021-12-01)
---------------------

New features:


- When purging images also purge the field WITHOUT a size parameter (e.g. ``[...]/@@images/image``).
  [wolbernd] (#89)


3.0.0a9 (2021-11-23)
--------------------

Bug fixes:


- Remove translations endpoint test because it does not have the correct fixture
  [sneridagh] (#87)


3.0.0a8 (2021-10-22)
--------------------

Bug fixes:


- fix deprecated imports
  [petschki] (#86)


3.0.0a7 (2021-10-13)
--------------------

Bug fixes:


- Fix label in controlpanel.pt.  [brian.duncan] (#84)


3.0.0a6 (2021-09-15)
--------------------

Bug fixes:


- Add upgrade step to define the new base terse cache setting.
  [maurits] (#82)


3.0.0a5 (2021-09-01)
--------------------

New features:


- Add etag for layout property.
  This is not yet added to a caching profile, but this can be done later.
  Fixes `issue 80 <https://github.com/plone/plone.app.caching/issues/80>`_.
  [maurits] (#80)


3.0.0a4 (2021-05-14)
--------------------

Bug fixes:


- Fix ram-caching of binary files.
  [agitator] (#79)


3.0.0a3 (2021-02-25)
--------------------

Breaking changes:


- Update for Plone 6 with Bootstrap markup
  [ale-rt, jensens] (#63)


Bug fixes:


- Links with pat-modal:  Remove unused redirectOnResponse from data-pat-modal actionOptions.  (Products.CMFPlone#3197)
  [fulv] (#3197)


3.0.0a2 (2021-02-02)
--------------------

New features:


- Restored ``resourceRegistries`` ETag, but now for Plone 5 resource registries.
  Fixes warning "Could not find value adapter for ETag component resourceRegistries".
  [maurits] (#61)


Bug fixes:


- Add more purge paths for images and downloads [jensens] (#71)


3.0.0a1 (2020-12-03)
--------------------

Breaking changes:


- Remove traces of Archetypes
  [pbauer] (#68)
- Drop Python 2 support.
  Black code style and isort.
  [jensens] (#69)


New features:


- Introduce *terseCaching* operation and `plone.content.dynamic` ruleset.
  *terseCaching* is a rule with by default 10s in browser cache and 60s in edge cache.
  It is intended to be used for highly dynamic content defined in the `plone.content.dynamic` ruleset.
  The combination reduces load on the backend if there a lots of requests.
  [jensens] (66-1)
- Support for *plone.restapi*.
  Define `cache:ruleset` assignments for anonymous accessible endpoints.
  Attention: Relies on *Vary* header unless *plone.restapi* gives up content negotation.
  Latter may conflict with edge side cache not supporting the Vary header.
  [jensens] (66-2)


2.0.8 (2020-10-30)
------------------

Bug fixes:


- Do not assume request or request.URL is a string. It might be None. [jensens, iham] (#59)
- Remove hopelessly outdated proxy config examples.
  Look at plone.recipe.varnish for excellent examples!
  [jensens] (#64)


2.0.7 (2020-09-28)
------------------

Bug fixes:


- Fixed invalid escape sequences.
  [maurits] (#3130)


2.0.6 (2020-06-24)
------------------

New features:


- Remove Range from request if the If-Range condition is not fulfilled
  [mamico] (#58)


2.0.5 (2020-04-20)
------------------

Bug fixes:


- Minor packaging updates. (#1)


2.0.4 (2020-02-20)
------------------

Bug fixes:


- Purging image scales of behavior fields, e.g. lead image
  [ksuess] (#55)


2.0.3 (2019-09-13)
------------------

Bug fixes:


- Fix python3 related encoding error on manual purge page.
  [agitator] (#51)


2.0.2 (2019-04-10)
------------------

Bug fixes:


- fix typo "Purging is" and not "Purging ist" [vincentfretin] (#47)
- Fix controlpanel for Python 3
  [petschki] (#48)


2.0.1 (2019-03-03)
------------------

Bug fixes:


- Only fire 1 Purge() when deleting content, instead of 3 [skurfer]
  Detect and ignore content creation more reliably [skurfer]
  Also purge the parent object when something changes (since the parent probably displays a list that includes the item being changed)
  [skurfer] (#37)


2.0.0 (2019-02-08)
------------------

Breaking changes:


- Removed legacy resource registries [ksuess] (#45)


1.2.23 (2018-12-28)
-------------------

Bug fixes:

- Warn after save if caching was disabled while purging is still enabled.
  [jensens]

Clean-up

- Legacy code clean-up
  Handling of legacy resource registries Products.ResourceRegistries removed
  [ksuess]


1.2.22 (2018-09-23)
-------------------

New features:

- Python 3 support
  [pbauer, MatthewWilkes, ale-rt]


1.2.21 (2018-04-03)
-------------------

New features:

- Use plone as i18n domain in ZCML files too
  [erral]

- Use plone as i18n domain
  [erral]

Bug fixes:

- Fix backslash escapes in i18nstring (poedit complains).
  [jensens]


1.2.20 (2018-02-05)
-------------------

New features:

- Prepare for Python 2 / 3 compatibility
  [b4oshany, davilima6]


1.2.19 (2017-11-24)
-------------------

New features:

- Purging all image scale paths and file paths in custom dexterity content types. [karalics]


1.2.18 (2017-04-08)
-------------------

Bug fixes:

- Fixed blank edit forms of the per ruleset parameters.
  `Issue 1993 <https://github.com/plone/Products.CMFPlone/issues/1993>`_.
  [maurits]


1.2.17 (2017-04-02)
-------------------

Bug fixes:

- Fixed title and description of max age in strong caching rule for resources.
  They wrongly were the same as for shared max age.
  Fixes `issue 1989 <https://github.com/plone/Products.CMFPlone/issues/1989>`_.
  [maurits]


1.2.16 (2017-03-23)
-------------------

Bug fixes:

- Fix: Do not break Plone if there is no Archetypes available.
  [jensens]


1.2.15 (2017-01-12)
-------------------

Bug fixes:

- Remove dependency on unittest2; fix tests assertions.
  [hvelarde]

- Fixed tests when using ZODB 4.
  [davisagli]


1.2.14 (2016-11-18)
-------------------

Bug fixes:

- Update code to follow Plone styleguide.
  [gforcada]


1.2.13 (2016-10-05)
-------------------

Bug fixes:

- Code-Style: isort, utf8-headers, zca-decorators, manual cleanup.
  [jensens]


1.2.12 (2016-09-16)
-------------------

Bug fixes:

- Enable unload protection by using pattern class ``pat-formunloadalert`` instead ``enableUnloadProtection``.
  [thet]


1.2.11 (2016-08-17)
-------------------

Fixes:

- Use plone.namedfile for test image.
  [didrix]

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
