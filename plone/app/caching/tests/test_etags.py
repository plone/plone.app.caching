import unittest

def test_suite():
    return unittest.defaultTestLoader.loadTestsFromName(__name__)
