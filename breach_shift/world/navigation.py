import heapq
from math import ceil, floor, hypot

from breach_shift.world.levels import Block, MapBounds
from breach_shift.world.reality import Reality


Cell = tuple[int, int]
Position = tuple[float, float]


class NavigationGrid:
    """Find ground routes around the active reality's blockout geometry."""

    def __init__(self, blocks: tuple[Block, ...], reality: Reality,
                 bounds: MapBounds = MapBounds(), cell_size: float = 0.5) -> None:
        if cell_size <= 0:
            raise ValueError("Navigation cell size must be positive.")
        self.bounds = bounds
        self.cell_size = cell_size
        self.blocks = tuple(block for block in blocks if block.active(reality))
        self.free = {
            (x, y)
            for x in range(ceil((bounds.min_x + 0.7) / cell_size), floor((bounds.max_x - 0.7) / cell_size) + 1)
            for y in range(ceil((bounds.min_y + 0.7) / cell_size), floor((bounds.max_y - 0.7) / cell_size) + 1)
            if self.is_free(x * cell_size, y * cell_size)
        }
        self.components: dict[Cell, int] = {}
        self._approach_cache: dict[tuple[int, Cell], Cell] = {}
        for cell in self.free:
            if cell in self.components:
                continue
            component = len(self.components)
            self.components[cell] = component
            pending = [cell]
            while pending:
                x, y = pending.pop()
                for neighbor in ((x + 1, y), (x - 1, y), (x, y + 1), (x, y - 1)):
                    if neighbor in self.free and neighbor not in self.components:
                        self.components[neighbor] = component
                        pending.append(neighbor)

    def is_free(self, x: float, y: float) -> bool:
        return (self.bounds.contains(x, y, margin=0.7)
                and not any(block.overlaps_xy(x, y, 0.55) for block in self.blocks))

    def _cell(self, point: Position) -> Cell:
        return round(point[0] / self.cell_size), round(point[1] / self.cell_size)

    def _position(self, cell: Cell) -> Position:
        return cell[0] * self.cell_size, cell[1] * self.cell_size

    def nearest_free(self, point: Position) -> Position:
        if not self.free:
            raise ValueError("The active map has no navigable ground.")
        cell = self._cell(point)
        if cell not in self.free:
            cell = min(self.free, key=lambda item: hypot(item[0] * self.cell_size - point[0],
                                                       item[1] * self.cell_size - point[1]))
        return self._position(cell)

    def find_path(self, start: Position, goal: Position) -> list[Position]:
        start_point = self.nearest_free(start)
        goal_point = self.nearest_free(goal)
        start_cell = self._cell(start_point)
        goal_cell = self._cell(goal_point)
        if self.components[start_cell] != self.components[goal_cell]:
            return []
        frontier = [(0, start_cell)]
        costs = {start_cell: 0}
        previous: dict[Cell, Cell | None] = {start_cell: None}
        while frontier:
            _, current = heapq.heappop(frontier)
            if current == goal_cell:
                path = []
                cursor: Cell | None = current
                while cursor is not None:
                    path.append(self._position(cursor))
                    cursor = previous[cursor]
                return list(reversed(path))
            for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                neighbor = (current[0] + dx, current[1] + dy)
                cost = costs[current] + 1
                if neighbor not in self.free or cost >= costs.get(neighbor, float("inf")):
                    continue
                costs[neighbor] = cost
                previous[neighbor] = current
                priority = cost + abs(neighbor[0] - goal_cell[0]) + abs(neighbor[1] - goal_cell[1])
                heapq.heappush(frontier, (priority, neighbor))
        return []

    def connected_positions(self, point: Position) -> list[Position]:
        """Return safe ground positions in the point's reachable component."""
        origin = self._cell(self.nearest_free(point))
        component = self.components[origin]
        return [self._position(cell) for cell in self.free if self.components[cell] == component]

    def segment_is_free(self, start: Position, end: Position) -> bool:
        """Sweep the enemy clearance against solid boxes, including thin barriers."""
        if not self.is_free(*start) or not self.is_free(*end):
            return False
        for block in self.blocks:
            interval_start, interval_end = 0.0, 1.0
            for origin, destination, center, extent in (
                    (start[0], end[0], block.x, block.width / 2 + .55),
                    (start[1], end[1], block.y, block.depth / 2 + .55)):
                low, high = center - extent + 1e-6, center + extent - 1e-6
                delta = destination - origin
                if abs(delta) < 1e-9:
                    if not low <= origin <= high:
                        interval_start = 2.0
                        break
                else:
                    first, second = sorted(((low - origin) / delta, (high - origin) / delta))
                    interval_start = max(interval_start, first)
                    interval_end = min(interval_end, second)
                    if interval_start > interval_end:
                        break
            if interval_start <= interval_end:
                return False
        return True

    def pursuit_path(self, start: Position, goal: Position) -> list[Position]:
        """Approach an unreachable player up to the blocking gate instead of idling."""
        start_cell = self._cell(self.nearest_free(start))
        goal_cell = self._cell(self.nearest_free(goal))
        component = self.components[start_cell]
        if self.components[goal_cell] != component:
            key = (component, goal_cell)
            if key not in self._approach_cache:
                if len(self._approach_cache) >= 256:
                    self._approach_cache.clear()
                self._approach_cache[key] = min(
                    (cell for cell in self.free if self.components[cell] == component),
                    key=lambda cell: (cell[0] - goal_cell[0]) ** 2 + (cell[1] - goal_cell[1]) ** 2,
                )
            goal_cell = self._approach_cache[key]
        path = self.find_path(start, self._position(goal_cell))
        # Replanning must not send a moving enemy back to its rounded starting cell.
        if path:
            path.pop(0)
        if path and not self.segment_is_free(start, path[0]):
            path.insert(0, self._position(start_cell))
        return path
