import unittest

from breach_shift.campaign.director import WaveDirector


class WaveDirectorTests(unittest.TestCase):
    def test_first_wave_waits_thirty_seconds(self):
        director = WaveDirector()
        self.assertEqual(director.advance(29, 6), 0)
        self.assertEqual(director.advance(1, 6), 3)
        self.assertEqual(director.wave, 1)

    def test_later_waves_are_larger_and_more_frequent(self):
        director = WaveDirector()
        first = director.advance(30, 0)
        first_wait = director.remaining
        later = director.advance(60, 0)
        self.assertGreater(later, first)
        self.assertLess(director.remaining, first_wait)

    def test_alive_cap_and_large_time_steps_never_create_a_catchup_burst(self):
        director = WaveDirector()
        self.assertEqual(director.advance(1000, 32), 0)
        self.assertEqual(director.advance(0, 31), 1)
        self.assertEqual(director.advance(0, 0), 0)

    def test_recovering_a_core_permanently_stops_reinforcements_for_the_map(self):
        director = WaveDirector()
        director.advance(10, 0)
        director.seal()
        self.assertEqual(director.advance(1000, 0), 0)
        self.assertEqual(director.wave, 0)

    def test_negative_time_does_not_move_the_clock_backwards(self):
        director = WaveDirector()
        director.advance(10, 0)
        director.advance(-20, 0)
        self.assertEqual(director.elapsed, 10)
