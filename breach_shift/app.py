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
    parser.add_argument('--level',type=int,choices=range(1,11),
                        help='start at a campaign map (1-10), for local practice')
    arguments = parser.parse_args(argv)
    if arguments.training and arguments.level is not None:
        parser.error('--level selects a campaign map and cannot be used with --training')

    if arguments.training:
        from breach_shift.core.game import BreachShift

        game = BreachShift()
    else:
        from breach_shift.campaign.game import CampaignGame

        game = CampaignGame()
        if arguments.level is not None:
            game.progress.level_index=arguments.level-1
            game.load_level()

    game.run()
    return 0
