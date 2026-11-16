import unittest
from unittest.mock import patch

from breach_shift.app import main


class AppTests(unittest.TestCase):
    def test_default_entry_point_runs_the_campaign(self):
        with patch("breach_shift.campaign.game.CampaignGame") as campaign:
            self.assertEqual(main([]), 0)
        campaign.assert_called_once_with()
        campaign.return_value.run.assert_called_once_with()

    def test_training_flag_runs_the_original_training_arena(self):
        with patch("breach_shift.core.game.BreachShift") as training:
            self.assertEqual(main(["--training"]), 0)
        training.assert_called_once_with()
        training.return_value.run.assert_called_once_with()


if __name__ == "__main__":
    unittest.main()
