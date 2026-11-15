"""Select a game mode and start Panda3D through a single entry point."""

import argparse
from collections.abc import Sequence


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="breach-shift",
        description="Play the Breach Shift zombie campaign or practice in the training arena.",
    )
    parser.add_argument(
        "--training",
        action="store_true",
        help="start the original three-target training arena instead of the campaign",
    )
    arguments = parser.parse_args(argv)

    if arguments.training:
        from breach_shift.core.game import BreachShift

        game = BreachShift()
    else:
        from breach_shift.campaign.game import CampaignGame

        game = CampaignGame()

    game.run()
    return 0
