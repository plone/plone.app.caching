from pathlib import Path
from setuptools import find_packages
from setuptools import setup


version = "3.1.5"

long_description = f"""
{Path("README.md").read_text()}\n
{Path("CHANGES.md").read_text()}\n
"""

setup(
    name="plone.app.caching",
    version=version,
    description="Plone UI and default rules for plone.caching/z3c.caching",
    long_description=long_description,
    long_description_content_type="text/markdown",
    # Get more strings from
    # https://pypi.org/classifiers/
    classifiers=[
        "Development Status :: 5 - Production/Stable",
        "Environment :: Web Environment",
        "Framework :: Plone",
        "Framework :: Plone :: 6.0",
        "Framework :: Plone :: Core",
        "Framework :: Zope :: 5",
        "License :: OSI Approved :: GNU General Public License v2 (GPLv2)",
        "Operating System :: OS Independent",
        "Programming Language :: Python",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
    ],
    keywords="plone caching",
    author="Plone Foundation",
    author_email="plone-developers@lists.sourceforge.net",
    url="https://github.com/plone/plone.app.caching",
    license="GPL version 2",
    packages=find_packages(),
    namespace_packages=["plone", "plone.app"],
    include_package_data=True,
    zip_safe=False,
    python_requires=">=3.8",
    install_requires=[
        "Products.CMFCore",
        "Products.CMFDynamicViewFTI",
        "Products.CMFPlone",
        "Products.GenericSetup",
        "Products.statusmessages",
        "Zope",
        "setuptools",
        "python-dateutil",
        "plone.app.registry",
        "plone.base",
        "plone.caching",
        "plone.dexterity",
        "plone.cachepurging",
        "plone.memoize",
        "plone.namedfile",
        "plone.protect",
        "plone.registry",
        "plone.transformchain",
        "plone.z3cform",
        "z3c.caching",
        "z3c.form",
        "z3c.zcmlhook",
        "zope.ramcache",
    ],
    extras_require={
        "test": [
            "persistent",
            "plone.app.contenttypes[test]",
            "plone.app.testing",
            "plone.app.textfield",
            "plone.behavior",
            "plone.testing",
            "pytz",
            "transaction",
        ]
    },
    entry_points="""
    [z3c.autoinclude.plugin]
    target = plone
    """,
)
