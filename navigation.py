import heapq
from math import hypot

from level_data import Block
from reality import Reality


Cell = tuple[int, int]
Position = tuple[float, float]


class NavigationGrid:
    """Find ground routes around the active reality's blockout geometry."""

    def __init__(self, blocks: tuple[Block, ...], reality: Reality) -> None:
        self.blocks = tuple(block for block in blocks if block.active(reality))
        self.free = {
            (x, y) for x in range(-18, 19) for y in range(-8, 39)
            if self.is_free(x / 2, y / 2)
        }

    def is_free(self, x: float, y: float) -> bool:
        return (-9.3 <= x <= 9.3 and -4.3 <= y <= 19.3
                and not any(block.overlaps_xy(x, y, 0.55) for block in self.blocks))

    def nearest_free(self, point: Position) -> Position:
        if not self.free:
            raise ValueError("The active map has no navigable ground.")
        cell = (round(point[0] * 2), round(point[1] * 2))
        if cell not in self.free:
            cell = min(self.free, key=lambda item: hypot(item[0] / 2 - point[0], item[1] / 2 - point[1]))
        return cell[0] / 2, cell[1] / 2

    def find_path(self, start: Position, goal: Position) -> list[Position]:
        start_point = self.nearest_free(start)
        goal_point = self.nearest_free(goal)
        start_cell = (round(start_point[0] * 2), round(start_point[1] * 2))
        goal_cell = (round(goal_point[0] * 2), round(goal_point[1] * 2))
        frontier = [(0, start_cell)]
        costs = {start_cell: 0}
        previous: dict[Cell, Cell | None] = {start_cell: None}
        while frontier:
            _, current = heapq.heappop(frontier)
            if current == goal_cell:
                path = []
                cursor: Cell | None = current
                while cursor is not None:
                    path.append((cursor[0] / 2, cursor[1] / 2))
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
