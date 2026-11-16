import unittest

from breach_shift.combat.weapon import Weapon


class WeaponTests(unittest.TestCase):
    def test_cooldown_rejection_spends_no_ammunition(self):
        weapon = Weapon()
        self.assertTrue(weapon.try_fire(1))
        self.assertFalse(weapon.try_fire(1.1))
        self.assertEqual(weapon.ammo,11)
        self.assertTrue(weapon.try_fire(1.25))

    def test_partial_reload_uses_only_available_reserve(self):
        weapon = Weapon(reserve_ammo=2)
        for time in range(8):
            self.assertTrue(weapon.try_fire(time))
        self.assertTrue(weapon.start_reload())
        self.assertFalse(weapon.try_fire(20))
        weapon.finish_reload()
        self.assertEqual((weapon.ammo,weapon.reserve_ammo),(6,0))
        self.assertFalse(weapon.start_reload())

    def test_empty_magazine_and_cancelled_reload_cannot_create_ammo(self):
        weapon = Weapon(magazine_size=2)
        self.assertTrue(weapon.try_fire(1))
        self.assertTrue(weapon.try_fire(2))
        self.assertFalse(weapon.try_fire(3))
        weapon.start_reload()
        weapon.cancel_reload()
        weapon.finish_reload()
        self.assertEqual(weapon.ammo,0)


if __name__=="__main__":
    unittest.main()
