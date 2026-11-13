from panda3d.core import(
    BitMask32,
    CollisionBox,
    CollisionNode,
    NodePath,
    Point3
)

class Target:
    """Manage a training target's model, collider, and health."""

    def __init__(self,
                parent: NodePath,
                model: NodePath,
                position: Point3,
                max_health: int = 100,
                name: str = "target"
                ) -> None:
        self.name = name
        self.max_health = max_health
        self.default_color = (0.85, 0.2, 0.12, 1.0)

        #Keep model and collider under one unscaled root.
        self.root = parent.attachNewNode(self.name)
        self.root.setPos(position)

        self.model = model
        self.model.reparentTo(self.root)
        self.model.setPos(0, 0, 0)
        self.model.setScale(2, 2, 2)
        self.model.setTextureOff(1)
        self.model.setCollideMask(BitMask32.allOff())

        collider_node = CollisionNode(f"{self.name}-collider")
        collider_node.addSolid(
            CollisionBox(Point3(0, 0, 0), Point3(2, 2, 2))
        )
        collider_node.setFromCollideMask(BitMask32.allOff())
        collider_node.setIntoCollideMask(BitMask32.bit(1))

        self.collider = self.root.attachNewNode(collider_node)
        self.collider.setTag("target", self.name)

        self.reset()

    def take_damage(self, damage: int) -> bool:
        if self.health <= 0:
            return False

        self.health = max(0, self.health - damage)

        if self.health == 0:
            self.root.stash()

        return True

    def flash_hit(self) -> None:
        self.model.setColor(1.0, 0.85, 0.15, 1.0)

    def restore_color(self) -> None:
        self.model.setColor(self.default_color)

    def reset(self) -> None:
        self.health = self.max_health
        self.restore_color()
        self.root.unstash()