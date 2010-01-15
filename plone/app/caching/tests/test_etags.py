import unittest
import zope.component.testing

class TestETags(unittest.TestCase):
    
    def setUp(self):
        pass
    
    def tearDown(self):
        zope.component.testing.tearDown()
    
    # UserID
    
    def test_UserID_anonymous(self):
        pass
    
    def test_UserID_member(self):
        pass
    
    # Roles
    
    def test_Roles_anonymous(self):
        pass
    
    def test_Roles_member(self):
        pass
    
    # Language
    
    def test_Language_no_header(self):
        pass
    
    def test_Language_with_header(self):
        pass
    
    # UserLanguage
    
    def test_UserLanguage(self):
        pass
    
    # GZip
    
    def test_GZip(self):
        pass
    
    # LastModified
    
    def test_LastModified_None(self):
        pass
    
    def test_LastModified(self):
        pass
    
    # CatalogCounter
    
    def test_CatalogCounter(self):
        pass
    
    # ObjectLocked
    
    def test_ObjectLocked(self):
        pass
    
    # Skin
    
    def test_Skin_request_variable(self):
        pass
    
    def test_Skin_default(self):
        pass
    
def test_suite():
    return unittest.defaultTestLoader.loadTestsFromName(__name__)
