from setuptools import setup, find_packages

version = '1.0.1'

setup(name='plone.app.caching',
      version=version,
      description="Plone UI and default rules for plone.caching/z3c.caching",
      long_description=open("README.txt").read() + "\n" +
                       open("CHANGES.txt").read(),
      classifiers=[
          "Environment :: Web Environment",
          "Framework :: Plone",
          "Framework :: Zope2",
          "License :: OSI Approved :: GNU General Public License (GPL)",
          "Operating System :: OS Independent",
          "Programming Language :: Python",
        ],
      keywords='plone caching',
      author='Plone Foundation',
      author_email='plone-developers@lists.sourceforge.net',
      url='http://pypi.python.org/pypi/plone.app.caching',
      license='GPL version 2',
      packages=find_packages(exclude=['ez_setup']),
      namespace_packages=['plone', 'plone.app'],
      include_package_data=True,
      zip_safe=False,
      install_requires=[
          'setuptools',
          'python-dateutil',
          'plone.caching',
          'plone.cachepurging',
          'plone.app.registry >= 1.0b5',
          'zope.interface',
          'zope.component',
          'zope.publisher',
          'zope.pagetemplate',
          'plone.memoize',
          'plone.protect',
          'plone.registry >= 1.0b4',
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
      extras_require={'test': ['plone.app.testing']},
      entry_points="""
      [z3c.autoinclude.plugin]
      target = plone
      """,
      )
