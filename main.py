from direct.showbase.ShowBase import ShowBase
from panda3d.core import AmbientLight, DirectionalLight, NodePath
class BreachShift(ShowBase):

    def load_single_model(self, path: str) -> NodePath:
        if self.loader is None:
            raise RuntimeError("Model loader is not initialized.")
        model = self.loader.loadModel(path)

        if not isinstance(model, NodePath):
            raise RuntimeError(f"Failed to load model: {path}")

        return model

    def __init__(self):
        super().__init__()

        if self.camera is None:
            raise RuntimeError("The camera has not been initialized.")
        if self.loader is None:
            raise RuntimeError("The loader has not been initialized.")

        self.setBackgroundColor(0.05, 0.05, 0.08)
        self.accept("escape", self.userExit)
        # Camera
        self.disableMouse()
        self.camera.setPos(8,-14,10)
        self.camera.lookAt(0,6,1)

        #Floor
        self.floor = self.load_single_model("models/box")
        self.floor.reparentTo(self.render)
        self.floor.setScale(20, 25, 0.2)
        self.floor.setPos(-10, -5, -0.2)
        self.floor.setTextureOff(1)
        self.floor.setColor(0.25, 0.28, 0.32, 1)

        #Red Crate
        self.crate = self.load_single_model("models/box")
        self.crate.reparentTo(self.render)
        self.crate.setScale(2, 2, 2)
        self.crate.setPos(-1, 5, 0)
        self.crate.setTextureOff(1)
        self.crate.setColor(0.85, 0.2, 0.12, 1)

        #Ambient Light
        ambient = AmbientLight("ambient")
        ambient.setColor((0.3, 0.3, 0.3, 1))
        ambient_node = self.render.attachNewNode(ambient)
        self.render.setLight(ambient_node)

        #Directional Light

        sunlight = DirectionalLight("sunlight")
        sunlight.setColor((0.8, 0.8, 0.8, 1))
        sunlight_node = self.render.attachNewNode(sunlight)
        sunlight_node.setHpr(-30, -60, 0)
        self.render.setLight(sunlight_node)


if __name__ == "__main__":
    game = BreachShift()
    game.run()

