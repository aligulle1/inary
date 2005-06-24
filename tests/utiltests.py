
import unittest
import os

from pisi import version
from pisi.util import *

class UtilTestCase(unittest.TestCase):
    def setUp(self):
        pass
        
    def testSubPath(self):
        self.assert_(subpath('usr', 'usr'))
        self.assert_(subpath('usr', 'usr/local/src'))
        self.assert_(not subpath('usr/local', 'usr'))

suite = unittest.makeSuite(UtilTestCase)
