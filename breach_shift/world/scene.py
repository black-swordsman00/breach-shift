from panda3d.core import BitMask32, CollisionBox, CollisionNode, NodePath, Point3

from breach_shift.world.levels import Block, LevelDefinition
from breach_shift.world.navigation import NavigationGrid
from breach_shift.world.reality import Reality


class CampaignWorld:
    """Render a level blockout and switch its visible and solid geometry together."""

    def __init__(self, parent: NodePath, cube: NodePath, level: LevelDefinition) -> None:
        self.level = level
        self.root = parent.attachNewNode(f"level-{level.number}")
        self.blocks: list[tuple[Block, NodePath]] = []
        cell_size = 1.0 if max(level.bounds.width, level.bounds.depth) > 50 else 0.5
        self.grids = {reality: NavigationGrid(level.blocks, reality, level.bounds, cell_size)
                      for reality in Reality}
        bounds = level.bounds
        center_x = (bounds.min_x + bounds.max_x) / 2
        center_y = (bounds.min_y + bounds.max_y) / 2
        perimeter = (
            Block(bounds.min_x - 0.3, center_y, 0.6, bounds.depth + 1.2, 4.5),
            Block(bounds.max_x + 0.3, center_y, 0.6, bounds.depth + 1.2, 4.5),
            Block(center_x, bounds.min_y - 0.3, bounds.width, 0.6, 4.5),
            Block(center_x, bounds.max_y + 0.3, bounds.width, 0.6, 4.5),
        )
        for block in (*level.blocks, *perimeter):
            node = self.root.attachNewNode("level-block")
            node.setPos(block.x, block.y, 0)
            model = cube.copyTo(node)
            model.setPos(-block.width / 2, -block.depth / 2, 0)
            model.setScale(block.width, block.depth, block.height)
            model.setTextureOff(1)
            model.setCollideMask(BitMask32.allOff())
            color = (0.3, 0.38, 0.4, 1)
            if block.reality is Reality.NORMAL:
                color = (0.15, 0.6, 0.65, 1)
            elif block.reality is Reality.BREACH:
                color = (0.65, 0.15, 0.7, 1)
            model.setColor(color)
            collider = CollisionNode("level-block-collider")
            collider.addSolid(CollisionBox(Point3(-block.width / 2, -block.depth / 2, 0),
                                           Point3(block.width / 2, block.depth / 2, block.height)))
            collider.setFromCollideMask(BitMask32.allOff())
            collider.setIntoCollideMask(BitMask32.bit(1) | BitMask32.bit(2) | BitMask32.bit(3))
            node.attachNewNode(collider)
            self.blocks.append((block, node))

        self.core = self.root.attachNewNode("power-core")
        self.core.setPos(*level.core, 0.4)
        model = cube.copyTo(self.core)
        model.setPos(-0.3, -0.3, 0)
        model.setScale(0.6, 0.6, 0.8)
        model.setTextureOff(1)
        model.setCollideMask(BitMask32.allOff())
        model.setColor(0.9, 0.25, 1, 1)
        self.exit = self.root.attachNewNode("exit")
        self.exit.setPos(*level.exit, 0)
        for position, scale in (((-1, 0, 0), (0.2, 0.3, 2.3)),
                                ((0.8, 0, 0), (0.2, 0.3, 2.3)),
                                ((-1, 0, 2.3), (2, 0.3, 0.2))):
            part = cube.copyTo(self.exit)
            part.setPos(*position)
            part.setScale(*scale)
            part.setTextureOff(1)
            part.setCollideMask(BitMask32.allOff())
        cube.removeNode()
        self.apply(Reality.NORMAL, False)
        self.set_exit_ready(False)

    def destination_safe(self, position: Point3, reality: Reality) -> bool:
        return (self.level.bounds.contains(position.x, position.y, margin=0.4)
                and not any(block.active(reality) and block.blocks_player(position.x, position.y, position.z)
                            for block, _ in self.blocks))

    def apply(self, reality: Reality, core_collected: bool) -> None:
        for block, node in self.blocks:
            node.unstash() if block.active(reality) else node.stash()
        self.core.unstash() if reality is Reality.BREACH and not core_collected else self.core.stash()

    def set_exit_ready(self, ready: bool) -> None:
        self.exit.setColorScale((0.2, 0.9, 0.4, 1) if ready else (0.8, 0.2, 0.15, 1))

    def destroy(self) -> None:
        self.root.removeNode()
