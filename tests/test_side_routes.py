import unittest

from breach_shift.platformer.session import Controls, SideSession
from breach_shift.world.reality import Reality


class SideRouteTests(unittest.TestCase):
    def test_every_authored_route_reaches_core_and_exit_without_teleporting(self):
        """Prove geometry/objective reachability; combat has separate tests."""
        for number in range(1,11):
            with self.subTest(sector=number):
                game = SideSession(level=number,seed=0)
                game.enemies.clear()
                game.director.seal()
                for _ in range(12000):
                    player = game.player
                    roof = any(not solid.one_way and 1.1<solid.z-player.z<1.8
                               and solid.x-1<player.x<solid.right+.5 for solid in game.solids)
                    obstacle = any(not solid.one_way and solid.x-1.2<player.x<solid.x
                                   and .2<solid.top-player.z<2.7 for solid in game.solids)
                    next_floor = any(solid.x<=player.x+1<=solid.right and abs(solid.top-player.z)<.35
                                     for solid in game.solids)
                    ground_ahead = any(solid.x<=player.x+1<=solid.right and solid.top==0
                                       for solid in game.solids)
                    jump = not roof and player.grounded and (obstacle or not next_floor)
                    jump |= (not player.grounded and player.vz<1.8 and game.jumps_used<2
                             and (obstacle or not ground_ahead))
                    shift = (game.reality.state is Reality.NORMAL
                             and player.x>game.level.normal_gate.x-2 and not game.progress.core_collected)
                    shift |= (game.reality.state is Reality.BREACH and game.progress.core_collected
                              and player.x>game.level.breach_gate.x-2)
                    shift &= game.reality.remaining(game.now)==0
                    movement = 1
                    if (game.reality.state is Reality.BREACH and not game.progress.core_collected
                            and player.x>game.level.core[0]-1):
                        movement = -1 if player.x>game.level.core[0]+1 else 0
                    game.step(Controls(move=movement,aim=(player.x+8,player.z+1),jump=jump,
                                       crouch=roof,shift=shift,interact=True),1/120)
                    self.assertTrue(game.health.is_alive,"Route fell into a pit")
                    if game.level.number!=number or game.progress.complete:
                        break
                else:
                    self.fail(f"Sector {number} never reached extraction")


if __name__=="__main__":
    unittest.main()
