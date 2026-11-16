"""Capture the real 2D game renderer without opening a visible window."""
import argparse
from pathlib import Path

from panda3d.core import Filename

from breach_shift.platformer.game import SideViewGame
from breach_shift.platformer.session import Controls
from breach_shift.combat.catalog import WeaponKind
from breach_shift.world.reality import Reality


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--level", type=int, choices=range(1,11), default=1)
    parser.add_argument("--boss", action="store_true", help="inspect the Warden arena in Breach")
    parser.add_argument("--crouch", action="store_true", help="inspect the player's low pose")
    parser.add_argument("--x", type=float, help="inspect a horizontal location in the selected map")
    parser.add_argument("--output", type=Path, default=Path("assets/previews/side-view.png"))
    args = parser.parse_args()
    game = SideViewGame(level=args.level, headless=True)
    try:
        session = game.session
        session.arsenal.select(WeaponKind.RIFLE)
        if args.x is not None:
            session.player.x = args.x
        if args.crouch:
            session.step(Controls(crouch=True),1/120)
        if args.boss:
            boss = next(enemy for enemy in session.enemies.values() if enemy.kind.value=="warden")
            session.player.x = boss.body.x - 8
            session.reality.state = Reality.BREACH
            game.aim = (boss.body.x,boss.body.z+1.5)
        game._rebuild()
        game.render_scene(.016)
        for _ in range(4):
            game.graphicsEngine.renderFrame()
        args.output.parent.mkdir(parents=True, exist_ok=True)
        if not game.win.saveScreenshot(Filename.fromOsSpecific(str(args.output.resolve()))):
            raise RuntimeError("Unable to capture 2D renderer.")
        print("Saved real 2D game preview:",args.output.name)
    finally:
        game.destroy()


if __name__=="__main__":
    main()
