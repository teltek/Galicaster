import datetime
import unittest

from mediapackage import *

class TestSequenceFunctions(unittest.TestCase):

    def setUp(self):
        self.mp = Mediapackage()
        self.mp.get_mediapackage('resources/data.zip')

    def test_metadata(self):
        self.assertEqual(self.mp.title, "Land and Vegetation: Key players on the Climate Scene")
        #self.assertEqual(mp.gettdate(), datetime.time(2005, 7, 14))

if __name__ == '__main__':
    unittest.main()
