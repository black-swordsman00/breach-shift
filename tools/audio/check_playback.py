"""Decode every effect through Panda3D/OpenAL; use ALSOFT_DRIVERS=null for silent QA."""

from panda3d.core import AudioManager, loadPrcFileData

from breach_shift.audio.bank import SOUNDS, SoundBank


def main():
    loadPrcFileData("audio-check", "audio-library-name p3openal_audio")
    manager = AudioManager.createAudioManager()
    if "OpenAL" not in manager.getType().getName():
        raise RuntimeError("The OpenAL backend is unavailable; real playback remains unverified.")

    class Loader:
        def loadSfx(self, path):
            return manager.getSound(path, False)

    bank = SoundBank(Loader())
    try:
        for cue in SOUNDS:
            sound = bank.play(cue)
            if sound.length() <= 0:
                raise RuntimeError(f"Effect did not decode: {cue}")
            print(f"{cue}: {sound.length():.2f}s")
    finally:
        bank.stop_all()
        manager.shutdown()


if __name__ == "__main__":
    main()
