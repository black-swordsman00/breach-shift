"""Decode every effect through Panda3D/OpenAL; use ALSOFT_DRIVERS=null for silent QA."""

from panda3d.core import AudioManager, NodePath, loadPrcFileData
from direct.showbase.Audio3DManager import Audio3DManager

from breach_shift.audio.bank import SOUNDS, SoundBank


def main():
    loadPrcFileData("audio-check", "audio-library-name p3openal_audio")
    manager = AudioManager.createAudioManager()
    if "OpenAL" not in manager.getType().getName():
        raise RuntimeError("The OpenAL backend is unavailable; real playback remains unverified.")

    class Loader:
        def loadSfx(self, path):
            return manager.getSound(path, False)

    root = NodePath("audio-check-root")
    listener = root.attachNewNode("listener")
    enemy = root.attachNewNode("enemy")
    enemy.setPos(2, 5, 0)
    spatial = Audio3DManager(manager, listener_target=listener, root=root)
    bank = SoundBank(Loader(), spatial)
    try:
        for cue in SOUNDS:
            sound = bank.play(cue, node=enemy if cue.startswith("zombie_") else None)
            if sound.length() <= 0:
                raise RuntimeError(f"Effect did not decode: {cue}")
            print(f"{cue}: {sound.length():.2f}s")
        spatial.update(None)
    finally:
        bank.stop_all()
        spatial.disable()
        manager.shutdown()


if __name__ == "__main__":
    main()
