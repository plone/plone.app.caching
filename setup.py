from setuptools import setup, find_packages
import os

version = '1.0a1'

setup(name='plone.app.caching',
      version=version,
      description="Plone UI and default rules for plone.caching/z3c.caching",
      long_description=open("README.txt").read() + "\n" +
                       open(os.path.join("docs", "HISTORY.txt")).read(),
      # Get more strings from http://www.python.org/pypi?%3Aaction=list_classifiers
      classifiers=[
        "Framework :: Plone",
        "Programming Language :: Python",
        "Topic :: Software Development :: Libraries :: Python Modules",
        ],
      keywords='plone caching',
      author='Plone Foundation',
      author_email='plone-developers@lists.sourceforge.net',
      url='http://pypi.python.org/pypi/plone.app.caching',
      license='GPL',
      packages=find_packages(exclude=['ez_setup']),
      namespace_packages=['plone', 'plone.app'],
      include_package_data=True,
      zip_safe=False,
      install_requires=[
          'setuptools',
          'python-dateutil',
          'plone.caching',
          'plone.cachepurging',
          'plone.app.registry',
          'zope.interface',
          'zope.component',
          'zope.publisher',
          'zope.pagetemplate',
          'plone.memoize',
          'plone.protect',
          'Products.CMFDynamicViewFTI',
          'Products.GenericSetup',
          'Products.CMFCore',
          'Products.statusmessages',
          'Zope2',
          'Acquisition',
          'plone.app.z3cform',
          'z3c.form',
          'z3c.zcmlhook',
      ],
      extras_require={'tests': ['collective.testcaselayer']},
      entry_points="""
      [z3c.autoinclude.plugin]
      target = plone
      """,
      )
