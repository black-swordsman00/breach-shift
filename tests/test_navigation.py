import unittest

from level_data import Block, MapBounds, load_levels
from navigation import NavigationGrid
from reality import Reality


class NavigationTests(unittest.TestCase):
    def test_route_avoids_cover_instead_of_walking_through_it(self):
        block = Block(0, 2, 3, 3, 2)
        grid = NavigationGrid((block,), Reality.NORMAL)
        path = grid.find_path((0, -2), (0, 6))
        self.assertTrue(path)
        self.assertTrue(all(not block.overlaps_xy(x, y, 0.55) for x, y in path))
        self.assertTrue(any(abs(x) >= 2 for x, _ in path))

    def test_switching_reality_changes_connectivity(self):
        barrier = Block(0, 8, 19.2, 0.6, 3.5, Reality.NORMAL)
        self.assertFalse(NavigationGrid((barrier,), Reality.NORMAL).find_path((0, 0), (0, 11)))
        self.assertTrue(NavigationGrid((barrier,), Reality.BREACH).find_path((0, 0), (0, 11)))

    def test_spawns_and_objectives_remain_reachable_in_every_map(self):
        for level in load_levels():
            with self.subTest(level=level.name):
                normal = NavigationGrid(level.blocks, Reality.NORMAL)
                breach = NavigationGrid(level.blocks, Reality.BREACH)
                self.assertTrue(breach.find_path((0, -2), level.core))
                self.assertTrue(normal.find_path(level.core, level.exit))
                self.assertFalse(normal.find_path((0, -2), level.core))
                self.assertFalse(breach.find_path(level.core, level.exit))
                for grid in (normal, breach):
                    self.assertTrue(grid.is_free(*level.core))
                    self.assertTrue(grid.is_free(*level.exit))
                    for spawn in level.spawns:
                        self.assertTrue(grid.is_free(spawn.x, spawn.y), spawn)

    def test_nearest_ground_handles_blocked_goals_and_map_edges(self):
        grid = NavigationGrid((Block(0, 0, 2, 2, 2),), Reality.NORMAL)
        point = grid.nearest_free((0, 0))
        self.assertTrue(grid.is_free(*point))
        self.assertFalse(grid.is_free(10, 0))
        self.assertTrue(grid.find_path((30, 30), (0, -2)))

    def test_stationary_route_is_valid(self):
        grid = NavigationGrid((), Reality.NORMAL)
        self.assertEqual(grid.find_path((0, 0), (0, 0)), [(0.0, 0.0)])

    def test_large_map_routes_beyond_the_training_arena(self):
        bounds = MapBounds(-30, 30, -15, 75)
        block = Block(0, 35, 12, 5, 2)
        grid = NavigationGrid((block,), Reality.NORMAL, bounds, cell_size=1)
        path = grid.find_path((0, -10), (0, 70))
        self.assertTrue(path)
        self.assertEqual(path[-1], (0, 70))
        self.assertTrue(all(grid.is_free(x, y) for x, y in path))
        self.assertTrue(any(abs(x) > 6 for x, _ in path))
        self.assertFalse(grid.is_free(30, 70))

    def test_large_full_width_barrier_blocks_routes_until_shift(self):
        bounds = MapBounds(-45, 45, -15, 115)
        barrier = Block(0, 30, 90, 0.6, 3.5, Reality.NORMAL)
        normal = NavigationGrid((barrier,), Reality.NORMAL, bounds, cell_size=1)
        breach = NavigationGrid((barrier,), Reality.BREACH, bounds, cell_size=1)
        self.assertFalse(normal.find_path((-40, 20), (40, 100)))
        self.assertTrue(breach.find_path((-40, 20), (40, 100)))
