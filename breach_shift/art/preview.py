"""Render actual Panda3D gameplay or model previews without opening a visible window."""

import argparse
from pathlib import Path

from panda3d.core import (AmbientLight, DirectionalLight, Filename,
                         TextNode, loadPrcFileData)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--mode", choices=("game", "roster", "weapons"), default="game")
    parser.add_argument("--output", type=Path, default=Path("assets/previews/gameplay.png"))
    arguments = parser.parse_args()
    loadPrcFileData("preview", "audio-library-name null\nwin-size 1600 900\nsync-video false\nshow-frame-rate-meter false")

    from breach_shift.art.characters import make_zombie_model
    from breach_shift.art.weapons import make_weapon_model
    from breach_shift.combat.catalog import WEAPON_ORDER, WeaponKind
    from breach_shift.enemies.catalog import ZOMBIE_ORDER

    if arguments.mode == "game":
        from breach_shift.campaign.game import CampaignGame

        game = CampaignGame(headless=True)
        game.player.setPos(0, 2, 0)
        game.select_weapon(WeaponKind.RIFLE)
        for index, zombie in enumerate(game.zombies.values()):
            if index < 2:
                zombie.root.setPos(-2 if index == 0 else 3, 9 + index * 4, 0)
            zombie.update_animation(.016, game.player.getPos())
        game.update_campaign_hud()
    else:
        from direct.showbase.ShowBase import ShowBase

        game = ShowBase(windowType="offscreen")
        game.disableMouse()
        game.setBackgroundColor(.055, .065, .08)
        ambient = AmbientLight("preview-fill")
        ambient.setColor((.5, .52, .55, 1))
        game.render.setLight(game.render.attachNewNode(ambient))
        key = DirectionalLight("preview-key")
        key.setColor((.9, .82, .70, 1))
        light = game.render.attachNewNode(key)
        light.setHpr(-30, -40, 0)
        game.render.setLight(light)
        if arguments.mode == "roster":
            game.camera.setPos(0, -10, 2.8)
            game.camera.lookAt(0, 0, 2.7)
            game.camLens.setFov(55)
            for index, kind in enumerate(ZOMBIE_ORDER):
                model = make_zombie_model(kind)
                model.reparentTo(game.render)
                row_height = 3.0 if index < 5 else 0.0
                model.setPos((index % 5 - 2) * 1.9, 0, row_height)
                model.setH(180)
                label = TextNode(f"{kind.value}-label")
                label.setText(kind.value.title())
                label.setAlign(TextNode.ACenter)
                node = game.render.attachNewNode(label)
                node.setPos(model.getX(), -.05, row_height - .24)
                node.setScale(.16)
                node.setBillboardPointEye()
                node.setLightOff(2)
        else:
            game.camera.setPos(1.7, -2.9, 1.6)
            game.camera.lookAt(0, .2, 0)
            game.camLens.setFov(50)
            for index, kind in enumerate(WEAPON_ORDER):
                model = make_weapon_model(kind)
                model.reparentTo(game.render)
                model.setPos((index - 1.5) * .85, 0, 0)

    try:
        for _ in range(5):
            game.graphicsEngine.renderFrame()
        arguments.output.parent.mkdir(parents=True, exist_ok=True)
        if not game.win.saveScreenshot(Filename.fromOsSpecific(str(arguments.output.resolve()))):
            raise RuntimeError("Unable to save the Panda3D preview.")
        print(arguments.output.resolve())
    finally:
        game.destroy()


if __name__ == "__main__":
    main()
