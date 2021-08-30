import unittest
import data_stream

class MyTest(unittest.TestCase):
    def test(self):
        self.assertEqual(data_stream.generateData("timestamp"), '{"success": "true", "status": 200, "message": "datapoint_timestamp"}')

if __name__ == '__main__':
    unittest.main()