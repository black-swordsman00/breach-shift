import unittest

from training_session import TrainingSession


class TrainingSessionTests(unittest.TestCase):
    def setUp(self):
        self.session = TrainingSession()

    def assert_empty_session(self):
        self.assertEqual(self.session.shots, 0)
        self.assertEqual(self.session.hits, 0)
        self.assertEqual(self.session.accuracy, 0.0)
        self.assertEqual(self.session.elapsed_time(100.0), 0.0)
        self.assertFalse(self.session.is_complete)

    def test_new_session_has_safe_zero_accuracy_and_no_timer(self):
        self.assert_empty_session()

    def test_miss_starts_timer_and_counts_as_a_shot(self):
        self.session.record_shot(10.0)

        self.assertEqual(self.session.shots, 1)
        self.assertEqual(self.session.hits, 0)
        self.assertEqual(self.session.accuracy, 0.0)
        self.assertEqual(self.session.elapsed_time(12.5), 2.5)

    def test_accuracy_includes_misses_and_later_shots_keep_start_time(self):
        self.session.record_shot(10.0)
        self.session.record_hit()
        self.session.record_shot(11.0)
        self.session.record_shot(12.0)

        self.assertEqual(self.session.shots, 3)
        self.assertEqual(self.session.hits, 1)
        self.assertAlmostEqual(self.session.accuracy, 100.0 / 3)
        self.assertEqual(self.session.elapsed_time(14.0), 4.0)

    def test_hit_requires_a_recorded_shot(self):
        self.session.record_hit()
        self.assert_empty_session()

        self.session.record_shot(0.0)
        self.session.record_hit()
        self.session.record_hit()
        self.assertEqual(self.session.hits, 1)
        self.assertEqual(self.session.accuracy, 100.0)

    def test_completion_freezes_counts_accuracy_and_time(self):
        self.session.record_shot(10.0)
        self.session.record_hit()
        self.session.record_shot(11.0)
        self.session.finish(12.5)

        self.session.record_shot(20.0)
        self.session.record_hit()
        self.session.finish(30.0)

        self.assertTrue(self.session.is_complete)
        self.assertEqual(self.session.shots, 2)
        self.assertEqual(self.session.hits, 1)
        self.assertEqual(self.session.accuracy, 50.0)
        self.assertEqual(self.session.elapsed_time(100.0), 2.5)

    def test_completion_without_shots_keeps_session_ready(self):
        self.session.finish(10.0)
        self.assert_empty_session()

        self.session.record_shot(20.0)
        self.assertEqual(self.session.elapsed_time(21.0), 1.0)

    def test_zero_timestamp_is_a_valid_start_and_finish(self):
        self.session.record_shot(0.0)
        self.session.finish(0.0)

        self.assertTrue(self.session.is_complete)
        self.assertEqual(self.session.elapsed_time(10.0), 0.0)

    def test_reset_clears_running_and_completed_sessions(self):
        for completed in (False, True):
            with self.subTest(completed=completed):
                self.session.record_shot(10.0)
                self.session.record_hit()
                if completed:
                    self.session.finish(12.0)

                self.session.reset()
                self.assert_empty_session()

                self.session.record_shot(20.0)
                self.assertEqual(self.session.shots, 1)
                self.assertEqual(self.session.elapsed_time(22.0), 2.0)
                self.session.reset()


if __name__ == "__main__":
    unittest.main()
