=================
plone.app.caching
=================

Introduction
============

This package provides a Plone UI and default rules for managing HTTP response caching in Plone.
It builds on `z3c.caching <https://github.com/zopefoundation/z3c.caching>`_, `plone.caching <https://github.com/plone/plone.caching>`_ and `plone.cachepurging <https://github.com/plone/plone.cachepurging>`_.


Version information:

- Version 3.x requires Plone 6.0 or later. Plone 5.2 with Python 3 should work too.
- Plone 5.2 release uses the version 2.x series.
- Earlier Plone versions: use a release from 1.x series.


Installation
============

*plone.app.caching* is shipped as a dependency of the *Plone* package.
Caching is **not enabled by default**.
It is highly recommended to configure caching.

When you create a default Plone site, it is available in the Site Setup.
Under the Advanced header, look for the Caching control panel.
There you can enable caching.

When the Caching control panel is not there, there can be various reasons for this:

- If your buildout does not load the ``Plone`` egg, but only ``Products.CMFPlone``, then ``plone.app.caching`` is not included.
- If the package *is* included, but you add a Plone Site using the advanced form and disable caching, then the control panel is not there.

If you want to install it in an existing Plone Site:

1. Make sure the package is available in the Plone instance, by adding ``plone.app.caching`` or ``Plone`` to the eggs and running buildout.
2. From the Plone Site Setup go to the ZMI (Zope Management Interface).
3. Go to ``portal_setup``, and then to the Import tab.
4. Select the HTTP caching support profile, perhaps easiest by id: ``profile-plone.app.caching:default``.
5. Click 'Import all steps'.


Source Code
===========

Contributors please read the document `Process for Plone core's development <https://docs.plone.org/develop/coredev/docs/index.html>`_

Sources are at the `Plone code repository hosted at Github <https://github.com/plone/plone.app.caching>`_.
