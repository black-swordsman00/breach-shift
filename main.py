from direct.gui.OnscreenText import OnscreenText
from direct.showbase.ShowBase import ShowBase
from direct.task import Task
from panda3d.core import (AmbientLight, ClockObject, DirectionalLight,
                            KeyboardButton, NodePath, Vec3, GraphicsWindow, WindowProperties, BitMask32,
                            CollisionBox, CollisionHandlerPusher, CollisionNode, CollisionPlane,
                            CollisionSphere, CollisionTraverser, Plane, Point3,CardMaker, CollisionRay, CollisionHandlerQueue,
                            TextNode)
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

        if window is None or not isinstance(window, GraphicsWindow):
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

        #Crosshair
        self.create_crosshair()

        #Shooting
        self.setup_shooting()

        #Target health and training controls
        self.setup_target()


    def load_single_model(self, path: str) -> NodePath:
            if self.loader is None:
                raise RuntimeError("Model loader is not initialized.")
            model = self.loader.loadModel(path)

            if not isinstance(model, NodePath):
                raise RuntimeError(f"Failed to load model: {path}")

            return model

    def create_crosshair(self):
        gap = 0.012
        length = 0.022
        thickness = 0.009

        #Create one rectangular arm.
        card = CardMaker("crosshair-arm")
        card.setFrame(
            gap,
            gap + length,
            - thickness / 2,
            thickness / 2
        )
        arm_node = card.generate()

        #Place four white arms around the center.
        self.crosshair = self.aspect2d.attachNewNode("crosshair")
        self.crosshair.setColor(1, 1, 1, 1)

        for rotation in (0, 90, 180, 270):
            arm = self.crosshair.attachNewNode(f"arm-{rotation}")
            arm.setR(rotation)
            arm.attachNewNode(arm_node)

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

        if (window is None or not isinstance(window, GraphicsWindow) or camera is None):
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

    def reset_crate_color(self, task):
        self.crate.setColor(self.crate_default_color)
        return Task.done

    def shoot(self):
        window = self.win
        camera_node = self.camNode

        if(
            window is None
            or not isinstance(window, GraphicsWindow)
            or camera_node is None
        ):
            return

        if not window.getProperties().getForeground():
            return

        #Aim through the center of the screen.
        self.shot_ray.setFromLens(camera_node, 0, 0)
        self.shot_queue.clearEntries()
        self.shot_traverser.traverse(self.render)

        if self.shot_queue.getNumEntries() == 0:
            return

        #Only the nearest collision receives the shot.
        self.shot_queue.sortEntries()
        entry = self.shot_queue.getEntry(0)
        hit_object = entry.getIntoNodePath()

        if hit_object.getNetTag("target") != "crate":
            return

        self.damage_target()


    def setup_shooting(self):
        camera = self.camera
        if camera is None:
            raise RuntimeError("Shooting requires a camera.")

        shot_mask = BitMask32.bit(2)
        self.crate_default_color = self.crate.getColor()

        #Enable shots on the existing colliders.
        for collider in (self.crate_collider, self.arena_boundaries):
            node = collider.node()
            node.setIntoCollideMask(
                node.getIntoCollideMask() | shot_mask
            )
        self.crate_collider.setTag("target","crate")

        #The floor blocks shots.
        floor_node = CollisionNode("shot-floor")
        floor_node.addSolid(
            CollisionPlane(
                Plane(Vec3(0, 0, 1), Point3(0, 0, 0))
            )
        )
        floor_node.setFromCollideMask(BitMask32.allOff())
        floor_node.setIntoCollideMask(shot_mask)
        self.shot_floor = self.render.attachNewNode(floor_node)

        #Create the ray and its collision handler.
        self.shot_ray = CollisionRay()

        ray_node = CollisionNode("shot-ray")
        ray_node.addSolid(self.shot_ray)
        ray_node.setFromCollideMask(shot_mask)
        ray_node.setIntoCollideMask(BitMask32.allOff())

        self.shot_ray_path = camera.attachNewNode(ray_node)
        self.shot_queue = CollisionHandlerQueue()
        self.shot_traverser = CollisionTraverser("shooting")
        self.shot_traverser.addCollider(
            self.shot_ray_path,
            self.shot_queue
        )

        self.accept("mouse1", self.shoot)

    def setup_target(self):
        self.target_max_health = 100
        self.target_health = self.target_max_health
        self.weapon_damage = 25

        self.target_hud = OnscreenText(
            text="",
            parent= self.a2dTopLeft,
            pos=(0.05, -0.10),
            scale= 0.05,
            fg = (1, 1, 1, 1),
            shadow= (0, 0, 0, 1),
            align=TextNode.ALeft,
            mayChange= True
        )

        self.update_target_hud()
        self.accept("r", self.restart_training)

    def update_target_hud(self):
        text = (
            f"Target HP: "
            f"{self.target_health}/{self.target_max_health}"
        )
        if self.target_health == 0:
            text += "\nTarget destroyed!"

        text += "\nR - Restart training"
        self.target_hud.setText(text)

    def damage_target(self):
        if self.target_health <= 0:
            return

        self.target_health = max(
            0,
            self.target_health - self.weapon_damage
        )
        self.update_target_hud()

        self.taskMgr.remove("reset-crate-color")

        if self.target_health == 0:
            self.crate.stash()
            self.crate_collider.stash()
            return

        self.crate.setColor(1.0, 0.85, 0.15, 1.0)

        self.taskMgr.doMethodLater(
            0.15,
            self.reset_crate_color,
            "reset-crate-color"
        )

    def restart_training(self):
        self.taskMgr.remove("reset-crate-color")

        #Reset the player before restoring the target.
        self.player.setPos(0, -2, 0)
        self.player.setH(0)

        self.camera_pitch = 0.0
        camera = self.camera

        if camera is not None:
            camera.setP(0)

        self.mouse_ready = False

        #Restore the target.
        self.target_health = self.target_max_health
        self.crate.setColor(self.crate_default_color)
        self.crate.unstash()
        self.crate_collider.unstash()

        self.update_target_hud()


if __name__ == "__main__":
    game = BreachShift()
    game.run()

