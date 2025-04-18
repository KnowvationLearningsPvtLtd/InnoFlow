import unittest
from src.monitor import process_request
from src.metrics import REQUEST_COUNT, ERROR_COUNT

class TestMonitor(unittest.TestCase):
    def test_request_success(self):
        result = process_request()
        self.assertTrue(result)
        self.assertEqual(REQUEST_COUNT._value.get(), 1)

    def test_request_failure(self):
        with unittest.mock.patch('random.random', return_value=0.1):
            result = process_request()
            self.assertFalse(result)
            self.assertEqual(ERROR_COUNT._value.get(), 1)

if __name__ == "__main__":
    unittest.main()