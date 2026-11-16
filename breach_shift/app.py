"""Start the side-view 2D campaign or firing range."""

import argparse
from collections.abc import Sequence


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="breach-shift",
        description="Play Breach Shift: a 2D side-view zombie campaign with two realities.",
    )
    parser.add_argument(
        "--training",
        action="store_true",
        help="start the 2D three-target firing range instead of the campaign",
    )
    parser.add_argument('--level',type=int,choices=range(1,11),
                        help='start at a campaign map (1-10), for local practice')
    arguments = parser.parse_args(argv)
    if arguments.training and arguments.level is not None:
        parser.error('--level selects a campaign map and cannot be used with --training')

    from breach_shift.platformer.game import SideViewGame

    game = SideViewGame(level=arguments.level or 1, training=arguments.training)

    game.run()
    return 0
