"""Render actual Panda3D gameplay or model previews without opening a visible window."""

import argparse
from pathlib import Path

from panda3d.core import (AmbientLight, DirectionalLight, Filename,
                         TextNode, loadPrcFileData)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--mode", choices=("game", "roster", "weapons"), default="game")
    parser.add_argument("--output", type=Path, default=Path("assets/previews/gameplay.png"))
    parser.add_argument("--model-dir", type=Path, help="inspect a candidate exported model library")
    arguments = parser.parse_args()
    if arguments.model_dir is not None:
        import breach_shift.art.library as library
        library.MODEL_ROOT = arguments.model_dir.resolve()
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
        import simplepbr
        from breach_shift.art.lighting import environment_map
        simplepbr.init(enable_shadows=False, use_normal_maps=True, msaa_samples=2,
                       env_map=environment_map("studio"))
        game.disableMouse()
        from breach_shift.art.color import atmosphere_input
        game.setBackgroundColor(*atmosphere_input((.035, .045, .06)))
        ambient = AmbientLight("preview-fill")
        ambient.setColor((.72, .76, .82, 1))
        game.render.setLight(game.render.attachNewNode(ambient))
        key = DirectionalLight("preview-key")
        key.setColor((1.7, 1.5, 1.25, 1))
        light = game.render.attachNewNode(key)
        light.setHpr(-30, -40, 0)
        game.render.setLight(light)
        if arguments.mode == "roster":
            game.camera.setPos(0, -12, 2.7)
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
                node.setShaderOff(2)
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
            game.taskMgr.step()
        arguments.output.parent.mkdir(parents=True, exist_ok=True)
        if not game.win.saveScreenshot(Filename.fromOsSpecific(str(arguments.output.resolve()))):
            raise RuntimeError("Unable to save the Panda3D preview.")
        print(arguments.output.resolve())
    finally:
        game.destroy()


if __name__ == "__main__":
    main()
