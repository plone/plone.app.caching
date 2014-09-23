=================
plone.app.caching
=================

Introduction
============

``plone.app.caching`` provides a Plone UI and default rules for managing HTTP response caching in Plone.
It builds on ``z3c.caching``, ``plone.caching`` and ``plone.cachepurging``.

``plone.app.caching`` requires Plone 4 or later.

Installation
============

Plone >=4.1
-----------

**From Plone 4.1 onwards, ``plone.app.caching`` is shipped as a dependency of Plone core.**

It is available from the Control Panel, but **not enabled by default**.
You can enable it from the "add-ons" menu option.

Plone 4.0
---------

Add ``plone.app.caching`` to the ``eggs`` list in your ``buildout.cfg``, or as a dependency of one of your own packages in ``setup.py``.
ZCML configuration will be automatically loaded via a ``z3c.autoinclude`` entry point.
You will also need to install the package in Plone's Add-ons control panel as normal.

This package depends on a number of other packages, including ``z3c.form`` and ``plone.app.registry``, that do not ship with Plone 4.0.
You will probably want to lock down the versions for those packages using a known good set.
Add this to the the ``extends`` line in your ``buildout.cfg``, *after* the line that includes the Plone KGS::

    extends =
        ...
        http://good-py.appspot.com/release/plone.app.caching/1.0a1

Update the version number at the end of the URL as appropriate.
You can find here an `overview of the versions <http://good-py.appspot.com/release/plone.app.caching>`_

Source Code
===========

Contributors please read the document `Process for Plone core's development <http://docs.plone.org/develop/plone-coredev/index.html>`_

Sources are at the `Plone code repository hosted at Github <https://github.com/plone/plone.app.caching>`_.
