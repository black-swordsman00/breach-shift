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
