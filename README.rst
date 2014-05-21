==============================================================================
plone.app.caching
==============================================================================


Introduction
============

``plone.app.caching`` provides a Plone UI and default rules for managing HTTP response caching in Plone. It builds on ``z3c.caching``, ``plone.caching`` and ``plone.cachepurging``.

``plone.app.caching`` requires Plone 4 or later.


Installation
============

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
