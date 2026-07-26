import unittest
from datetime import datetime, timedelta
from app import calculate_priority


class TestPriority(unittest.TestCase):

    def test_critical_priority(self):
        due_date = datetime.now().date() + timedelta(days=1)

        result = calculate_priority(due_date)

        self.assertEqual(result, 5)


    def test_low_priority(self):
        due_date = datetime.now().date() + timedelta(days=20)

        result = calculate_priority(due_date)

        self.assertEqual(result, 1)


if __name__ == "__main__":
    unittest.main()