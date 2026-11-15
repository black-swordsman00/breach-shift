from random import Random
import unittest

from breach_shift.combat.arsenal import Arsenal
from breach_shift.combat.catalog import WEAPON_ORDER, WEAPON_SPECS, WeaponKind
from breach_shift.combat.loot import roll_ammo
from breach_shift.enemies.catalog import ZOMBIE_ORDER, ZOMBIE_SPECS


class ArsenalTests(unittest.TestCase):
    def test_all_enemy_health_values_are_unique_and_increase_toward_the_boss(self):
        health = [ZOMBIE_SPECS[kind].health for kind in ZOMBIE_ORDER]
        self.assertEqual(len(set(health)), 10)
        self.assertEqual(health, sorted(health))
        self.assertEqual((health[0], health[-1]), (75, 800))

    def test_four_weapons_have_distinct_damage_and_independent_ammunition(self):
        arsenal = Arsenal()
        self.assertEqual(len(arsenal.weapons), 4)
        self.assertEqual(len({weapon.damage for weapon in arsenal.weapons.values()}), 4)
        self.assertTrue(arsenal.active.try_fire(1))
        arsenal.select(WeaponKind.SMG)
        self.assertTrue(arsenal.active.try_fire(1))
        self.assertEqual(arsenal.active.ammo, 29)
        arsenal.select(WeaponKind.PISTOL)
        self.assertEqual(arsenal.active.ammo, 11)

    def test_switching_cancels_reload_without_refilling_or_resetting_fire_cooldown(self):
        arsenal = Arsenal()
        pistol = arsenal.active
        pistol.try_fire(1)
        self.assertTrue(pistol.start_reload())
        arsenal.select(WeaponKind.RIFLE)
        self.assertFalse(pistol.is_reloading)
        pistol.finish_reload()
        arsenal.select(WeaponKind.PISTOL)
        self.assertEqual((pistol.ammo, pistol.reserve_ammo), (11, 36))
        self.assertFalse(pistol.try_fire(1.1))

    def test_ammo_is_added_to_its_weapon_even_when_another_is_equipped(self):
        arsenal = Arsenal()
        arsenal.add_ammo(WeaponKind.SHOTGUN, 4)
        self.assertEqual(arsenal.weapons[WeaponKind.SHOTGUN].reserve_ammo, 22)
        self.assertEqual(arsenal.active.reserve_ammo, 36)
        with self.assertRaises(ValueError):
            arsenal.add_ammo(WeaponKind.PISTOL, 0)

    def test_checkpoint_resets_every_weapon_and_preserves_the_selected_slot(self):
        arsenal = Arsenal()
        for kind in WEAPON_ORDER:
            arsenal.select(kind).try_fire(1)
            arsenal.active.reserve_ammo = 0
        arsenal.reset()
        self.assertIs(arsenal.selected, WeaponKind.SHOTGUN)
        for kind, weapon in arsenal.weapons.items():
            self.assertEqual(weapon.ammo, WEAPON_SPECS[kind].magazine_size)
            self.assertEqual(weapon.reserve_ammo, WEAPON_SPECS[kind].reserve_ammo)

    def test_seeded_random_loot_covers_all_weapons_with_valid_bundle_sizes(self):
        rng = Random(42)
        rewards = [roll_ammo(rng) for _ in range(200)]
        self.assertEqual({reward.kind for reward in rewards}, set(WEAPON_ORDER))
        for reward in rewards:
            low, high = WEAPON_SPECS[reward.kind].ammo_bundle
            self.assertGreaterEqual(reward.rounds, low)
            self.assertLessEqual(reward.rounds, high)
