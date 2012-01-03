import unittest2 as unittest
from plone.testing.zca import UNIT_TESTING

import os
import time
import datetime
import DateTime

from dateutil.tz import tzlocal

from persistent.TimeStamp import TimeStamp

from zope.component import provideAdapter
from z3c.caching.interfaces import ILastModified

from plone.app.caching import lastmodified

class FauxDataManager(object):

    def setstate(self, object):
        pass

    def oldstate(self, obj, tid):
        pass

    def register(self, object):
        pass

class TestLastModified(unittest.TestCase):

    layer = UNIT_TESTING

    def setUp(self):
        provideAdapter(lastmodified.PageTemplateDelegateLastModified)
        provideAdapter(lastmodified.FSPageTemplateDelegateLastModified)
        provideAdapter(lastmodified.OFSFileLastModified)
        provideAdapter(lastmodified.FSObjectLastModified)
        provideAdapter(lastmodified.CatalogableDublinCoreLastModified)
        provideAdapter(lastmodified.DCTimesLastModified)
        provideAdapter(lastmodified.ResourceLastModified)

    def test_PageTemplateDelegateLastModified(self):
        from persistent import Persistent
        from Acquisition import Explicit

        class Dummy(Persistent, Explicit):
            _p_mtime = None

        provideAdapter(lastmodified.PersistentLastModified, adapts=(Dummy,))

        d = Dummy()

        from Products.PageTemplates.ZopePageTemplate import ZopePageTemplate
        zpt = ZopePageTemplate('zpt').__of__(d)
        self.assertEquals(None, ILastModified(zpt)())


        timestamp = 987654321.0 # time stamp (in UTC)
        # equivalent in local time, which is what the last-modified adapter
        # should return
        mod = datetime.datetime.fromtimestamp(timestamp, tzlocal())

        d._p_mtime = 987654321.0
        self.assertEquals(mod, ILastModified(zpt)())

    def test_FSPageTemplateDelegateLastModified(self):
        from persistent import Persistent
        from Acquisition import Explicit

        class Dummy(Persistent, Explicit):
            _p_mtime = None

        provideAdapter(lastmodified.PersistentLastModified, adapts=(Dummy,))

        d = Dummy()

        from Products.CMFCore.FSPageTemplate import FSPageTemplate
        zpt = FSPageTemplate('zpt', __file__).__of__(d)
        self.assertEquals(None, ILastModified(zpt)())


        timestamp = 987654321.0 # time stamp (in UTC)
        # equivalent in local time, which is what the last-modified adapter
        # should return
        mod = datetime.datetime.fromtimestamp(timestamp, tzlocal())

        d._p_mtime = 987654321.0
        self.assertEquals(mod, ILastModified(zpt)())

    def test_OFSFileLastModified_File(self):
        from OFS.Image import File

        dummy = File('dummy', 'Dummy', 'data')
        self.assertEquals(None, ILastModified(dummy)())

        timestamp = 987654321.0 # time stamp (in UTC)
        ts = TimeStamp(*time.gmtime(timestamp)[:6]) # corresponding TimeStamp

        # equivalent in local time, which is what the last-modified adapter
        # should return
        mod = datetime.datetime.fromtimestamp(timestamp, tzlocal())

        dummy._p_jar = FauxDataManager()
        dummy._p_serial = repr(ts)
        self.assertEquals(mod, ILastModified(dummy)())

    def test_OFSFileLastModified_Image(self):
        from OFS.Image import Image

        dummy = Image('dummy', 'Dummy', 'data')
        self.assertEquals(None, ILastModified(dummy)())

        timestamp = 987654321.0 # time stamp (in UTC)
        ts = TimeStamp(*time.gmtime(timestamp)[:6]) # corresponding TimeStamp

        # equivalent in local time, which is what the last-modified adapter
        # should return
        mod = datetime.datetime.fromtimestamp(timestamp, tzlocal())

        dummy._p_jar = FauxDataManager()
        dummy._p_serial = repr(ts)
        self.assertEquals(mod, ILastModified(dummy)())

    def test_FSObjectLastModified_FSFile(self):
        from Products.CMFCore.FSFile import FSFile

        dummy = FSFile('dummy', __file__)

        modtime = float(os.path.getmtime(__file__))
        mod = datetime.datetime.fromtimestamp(modtime, tzlocal())

        self.assertEquals(mod, ILastModified(dummy)())

    def test_FSObjectLastModified_FSImage(self):
        from Products.CMFCore.FSImage import FSImage

        dummy = FSImage('dummy', __file__) # not really an image, but anyway

        modtime = float(os.path.getmtime(__file__))
        mod = datetime.datetime.fromtimestamp(modtime, tzlocal())

        self.assertEquals(mod, ILastModified(dummy)())

    def test_CatalogableDublinCoreLastModified(self):
        from Products.CMFCore.interfaces import ICatalogableDublinCore
        from zope.interface import implements

        class Dummy(object):
            implements(ICatalogableDublinCore)

            _mod = None

            def modified(self):
                if self._mod is not None: return DateTime.DateTime(self._mod)
                return None

        d = Dummy()

        self.assertEquals(None, ILastModified(d)())

        d._mod = datetime.datetime(2001, 4, 19, 12, 25, 21, 120000)
        self.assertEquals(d._mod, ILastModified(d)())

    def test_DCTimesLastModified(self):
        from zope.dublincore.interfaces import IDCTimes
        from zope.interface import implements

        class Dummy(object):
            implements(IDCTimes)

            _mod = None

            @property
            def modified(self):
                return self._mod

        d = Dummy()

        self.assertEquals(None, ILastModified(d)())

        d._mod = datetime.datetime(2001, 4, 19, 12, 25, 21, 120000)
        self.assertEquals(d._mod, ILastModified(d)())

    def test_ResourceLastModified_zope_app(self):
        from zope.app.publisher.browser.fileresource import FileResource
        from zope.app.publisher.fileresource import File

        class DummyRequest(dict):
            pass

        request = DummyRequest()

        f = File(__file__, 'test_lastmodified.py')
        r = FileResource(f, request)

        modtime = float(os.path.getmtime(__file__))
        mod = datetime.datetime.fromtimestamp(modtime, tz=tzlocal())

        self.assertEquals(mod, ILastModified(r)())

    def test_ResourceLastModified_Five(self):
        from Products.Five.browser.resource import FileResource
        from zope.app.publisher.fileresource import Image

        class DummyRequest(dict):
            pass

        request = DummyRequest()

        f = Image(__file__, 'test_lastmodified.py') # not really an image
        r = FileResource(f, request)

        modtime = float(os.path.getmtime(__file__))
        mod = datetime.datetime.fromtimestamp(modtime, tz=tzlocal())

        self.assertEquals(mod, ILastModified(r)())
