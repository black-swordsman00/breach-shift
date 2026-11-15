import unittest

from campaign_state import CampaignProgress
from level_data import load_levels
from zombie_catalog import ZOMBIE_ORDER


class CampaignStateTests(unittest.TestCase):
    def test_core_and_clear_are_both_required_and_each_map_requires_a_new_core(self):
        progress = CampaignProgress(10)
        for index in range(10):
            self.assertEqual(progress.level_index, index)
            self.assertFalse(progress.advance(0))
            self.assertTrue(progress.collect_core())
            self.assertFalse(progress.collect_core())
            self.assertFalse(progress.advance(1))
            self.assertTrue(progress.advance(0))
        self.assertTrue(progress.complete)
        self.assertFalse(progress.advance(0))
        self.assertFalse(progress.collect_core())

    def test_retry_preserves_current_map_and_restarts_a_finished_campaign(self):
        progress = CampaignProgress(2)
        progress.collect_core()
        progress.advance(0)
        progress.collect_core()
        progress.retry()
        self.assertEqual(progress.level_index, 1)
        self.assertFalse(progress.core_collected)
        progress.collect_core()
        progress.advance(0)
        progress.retry()
        self.assertEqual(progress.level_index, 0)
        self.assertFalse(progress.complete)

    def test_map_rosters_introduce_exactly_one_new_kind_in_order(self):
        levels = load_levels()
        self.assertEqual(len(levels), 10)
        for level in levels:
            with self.subTest(level=level.name):
                self.assertIs(level.introduced, ZOMBIE_ORDER[level.number - 1])
                self.assertIn(level.introduced, [spawn.kind for spawn in level.spawns])
                self.assertTrue(all(spawn.kind in ZOMBIE_ORDER[:level.number] for spawn in level.spawns))
                self.assertTrue(level.briefing)

    def test_empty_campaign_is_rejected(self):
        with self.assertRaises(ValueError):
            CampaignProgress(0)
