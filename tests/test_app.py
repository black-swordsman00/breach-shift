import unittest
from unittest.mock import patch

from breach_shift.app import main


class AppTests(unittest.TestCase):
    def test_default_entry_point_runs_the_campaign(self):
        with patch("breach_shift.platformer.game.SideViewGame") as campaign:
            self.assertEqual(main([]), 0)
        campaign.assert_called_once_with(level=1, training=False)
        campaign.return_value.run.assert_called_once_with()

    def test_training_flag_runs_the_2d_firing_range(self):
        with patch("breach_shift.platformer.game.SideViewGame") as training:
            self.assertEqual(main(["--training"]), 0)
        training.assert_called_once_with(level=1, training=True)
        training.return_value.run.assert_called_once_with()

    def test_requested_boss_map_loads_before_the_game_runs(self):
        with patch('breach_shift.platformer.game.SideViewGame') as campaign:
            self.assertEqual(main(['--level','10']),0)
        game=campaign.return_value
        campaign.assert_called_once_with(level=10,training=False)
        game.run.assert_called_once_with()

    def test_training_rejects_a_campaign_map(self):
        with self.assertRaises(SystemExit),patch('sys.stderr'):
            main(['--training','--level','10'])


if __name__ == "__main__":
    unittest.main()
