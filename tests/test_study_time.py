import unittest
from app import total_minutes


class FakeSession:
    def __init__(self, duration):
        self.duration = duration


class FakeAssignment:
    def __init__(self):
        self.work_sessions = [
            FakeSession(30),
            FakeSession(45),
            FakeSession(60)
        ]


class TestStudyTracking(unittest.TestCase):

    def test_total_minutes(self):

        assignment = FakeAssignment()

        result = total_minutes(assignment)

        self.assertEqual(result, 135)


if __name__ == "__main__":
    unittest.main()