from direct.showbase.ShowBase import ShowBase
from direct.task import Task
from panda3d.core import (AmbientLight, ClockObject, DirectionalLight,
                            KeyboardButton, NodePath, Vec3, GraphicsWindow, WindowProperties, BitMask32,
                            CollisionBox, CollisionHandlerPusher, CollisionNode, CollisionPlane,
                            CollisionSphere, CollisionTraverser, Plane, Point3)
class BreachShift(ShowBase):


    def __init__(self):
        super().__init__()

        if self.camera is None:
            raise RuntimeError("The camera has not been initialized.")
        if self.loader is None:
            raise RuntimeError("The loader has not been initialized.")

        self.setBackgroundColor(0.05, 0.05, 0.08)
        self.accept("escape", self.userExit)

        #Camera

        #Player Node
        self.player = self.render.attachNewNode("player")
        self.player.setPos(0, -2, 0)

        #First-person camera
        self.disableMouse()
        self.camera.reparentTo(self.player)
        self.camera.setPos(0, 0, 1.7)
        self.camera.setHpr(0, 0, 0)

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

        #Movement
        self.move_speed = 5.0
        self.clock = ClockObject.getGlobalClock()
        self.taskMgr.add(self.update_movement, "update-movement")

        #Mouse look
        self.mouse_sensitivity = 0.15
        self.camera_pitch = 0.0
        self.mouse_ready = False
        self.mouse_center = (0, 0)

        window = self.win

        if not isinstance(window, GraphicsWindow):
            raise RuntimeError("Mouse look requires a graphics window.")

        properties = WindowProperties()
        properties.setCursorHidden(True)
        properties.setMouseMode(WindowProperties.M_confined)
        window.requestProperties(properties)

        self.taskMgr.add(
            self.update_mouse_look,
            "update-mouse-look",
            sort =- 10,
        )

        #Camera clipping
        if self.camLens is None:
            raise RuntimeError("Camera lens is not initialized.")

        self.camLens.setNear(0.05)

        #Collision setup
        self.setup_collisions()

    def load_single_model(self, path: str) -> NodePath:
            if self.loader is None:
                raise RuntimeError("Model loader is not initialized.")
            model = self.loader.loadModel(path)

            if not isinstance(model, NodePath):
                raise RuntimeError(f"Failed to load model: {path}")

            return model
    def update_movement(self, task):
        keyboard = self.mouseWatcherNode

        if keyboard is None:
            return Task.cont
        direction = Vec3(0, 0, 0)

        if keyboard.isButtonDown(KeyboardButton.asciiKey("w")):
            direction.y += 1

        if keyboard.isButtonDown(KeyboardButton.asciiKey("s")):
            direction.y -= 1

        if keyboard.isButtonDown(KeyboardButton.asciiKey("a")):
            direction.x -= 1

        if keyboard.isButtonDown(KeyboardButton.asciiKey("d")):
            direction.x += 1

        if direction.lengthSquared() > 0:
            direction.normalize()

            dt = min(self.clock.getDt(), 0.05)
            movement = direction * self.move_speed * dt

            self.player.setPos(self.player, movement)
        return Task.cont

    def update_mouse_look(self, task):
        window = self.win
        camera = self.camera

        if not isinstance(window, GraphicsWindow) or camera is None:
            return Task.cont

        if not window.getProperties().getForeground():
            self.mouse_ready = False
            return Task.cont

        center_x = window.getXSize() // 2
        center_y = window.getYSize() // 2
        center = (center_x, center_y)

        #Center the pointer on startup, refocus, or resize.
        if not self.mouse_ready or center != self.mouse_center:
            self.mouse_center = center
            self.mouse_ready = window.movePointer(0, center_x, center_y)
            return Task.cont

        pointer = window.getPointer(0)
        delta_x = pointer.getX() - center_x
        delta_y = pointer.getY() - center_y

        if not window.movePointer(0, center_x, center_y):
            self.mouse_ready = False
            return Task.cont

        #Rotate the player horizontally.
        heading = self.player.getH()
        self.player.setH(heading - delta_x * self.mouse_sensitivity)

        #Rotate only the camera vertically.
        self.camera_pitch -= delta_y * self.mouse_sensitivity
        self.camera_pitch = max(-85.0, min(85.0, self.camera_pitch))
        camera.setP(self.camera_pitch)

        return Task.cont

    def setup_collisions(self):
        collision_mask = BitMask32.bit(1)

        #Use dedicated collision shapes for the visible models.
        self.floor.setCollideMask(BitMask32.allOff())
        self.crate.setCollideMask(BitMask32.allOff())

        self.collision_traverser = CollisionTraverser("world-collisions")
        self.collision_pusher = CollisionHandlerPusher()
        self.collision_pusher.setHorizontal(True)
        
        #Player collision shape
        player_node = CollisionNode("player-collider")
        player_node.addSolid(CollisionSphere(0, 0, 0.9, 0.4))
        player_node.setFromCollideMask(collision_mask)
        player_node.setIntoCollideMask(BitMask32.allOff())

        self.player_collider = self.player.attachNewNode(player_node)
        
        self.collision_pusher.addCollider(
            self.player_collider, self.player
        )
        self.collision_traverser.addCollider(
            self.player_collider, self.collision_pusher
        )

        #Static crate collision shape in world coordinates
        crate_node = CollisionNode("crate-collider")
        crate_node.addSolid(
            CollisionBox(Point3(-1, 5, 0), Point3(1,7,2))
        )
        crate_node.setFromCollideMask(BitMask32.allOff())
        crate_node.setIntoCollideMask(collision_mask)

        self.crate_collider = self.render.attachNewNode(crate_node)
        
        #Arena boundaries, with normals pointing inward
        boundaries_node = CollisionNode("arena-boundaries")
        boundaries_node.setFromCollideMask(BitMask32.allOff())
        boundaries_node.setIntoCollideMask(collision_mask)
        
        for normal, point in(
            (Vec3(1, 0, 0), Point3(-10, 0, 0)),
            (Vec3(-1, 0, 0), Point3(10, 0, 0)),
            (Vec3(0, 1, 0), Point3(0, -5, 0)),
            (Vec3(0, -1, 0), Point3(0, 20, 0))
        ):
            boundaries_node.addSolid(
                CollisionPlane(Plane(normal, point))
            )
        self.arena_boundaries = self.render.attachNewNode(
            boundaries_node
        )

        self.taskMgr.add(
            self.update_collisions,
            "update-collisions",
            sort=10
        )

    def update_collisions(self, task):
        self.collision_traverser.traverse(self.render)
        return Task.cont



if __name__ == "__main__":
    game = BreachShift()
    game.run()

