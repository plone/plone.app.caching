<p align="center">
    <img alt="Plone Logo" width="200px" src="https://raw.githubusercontent.com/plone/.github/main/plone-logo.png">
</p>

<h1 align="center">
  plone.app.caching
</h1>

<div align="center">

[![PyPI - Wheel](https://img.shields.io/pypi/wheel/plone.app.caching)](https://pypi.org/project/plone.app.caching/)
[![PyPI - License](https://img.shields.io/pypi/l/plone.app.caching)](https://pypi.org/project/plone.app.caching/)
[![PyPI - Status](https://img.shields.io/pypi/status/plone.app.caching)](https://pypi.org/project/plone.app.caching/)

[![GitHub contributors](https://img.shields.io/github/contributors/plone/plone.app.caching)](https://github.com/plone/plone.app.caching)
![GitHub Repo stars](https://img.shields.io/github/stars/plone/plone.app.caching?style=flat-square)

</div>

## Introduction

This package provides a Plone UI and default rules for managing HTTP response caching in Plone.
It builds on [z3c.caching](https://github.com/zopefoundation/z3c.caching), [plone.caching](https://github.com/plone/plone.caching) and [plone.cachepurging](https://github.com/plone/plone.cachepurging).


### Compatibility

| Version | Plone |
|------|-----|
| 3.x | 6.0 or above |
| 2.x | 5.2 |
| 1.x | 5.1, 5.0, 4.3, 4.2, 4.1 |


## Installation

`plone.app.caching` is shipped as a dependency of the *Plone* package, and it should be available on all Plone installations, but
Caching is **not enabled by default**, although it is highly recommended to configure caching for every new Plone site.

After creating a new Plone site, go to `Site Setup`, then `Addons` and install `HTTP caching support`.

Under the Advanced header, look for the Caching control panel -- currently only supported on the Classic UI.

### Troubleshooting

When the Caching control panel is not there, there can be various reasons for this:

- If your installation does not load the `Plone` package, but only `Products.CMFPlone`, then `plone.app.caching` is not included.
- If the package *is* included, but you add a Plone Site using the advanced form and disable caching, then the control panel is not there.

If you want to install it in an existing Plone Site:

1. Make sure the package is available in the Plone instance, by adding `plone.app.caching` or `Plone` to your installation.
2. From the Plone Site Setup go to the ZMI (Zope Management Interface).
3. Go to ``portal_setup``, and then to the Import tab.
4. Select the HTTP caching support profile, perhaps easiest by id: `profile-plone.app.caching:default`.
5. Click 'Import all steps'.


## Source Code

Contributors, please read the document [Process for Plone core's development](https://5.docs.plone.org/develop/coredev/docs/index.html)

Sources are at the [Plone code repository hosted at Github ](https://github.com/plone/plone.app.caching).

## This project is supported by

<a href="https://plone.org/foundation/">
    <img alt="Plone Logo" width="200px" src="https://raw.githubusercontent.com/plone/.github/main/plone-foundation.png">
</a>

## License

The project is licensed under GPLv2.
