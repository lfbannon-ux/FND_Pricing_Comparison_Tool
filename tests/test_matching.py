import unittest

from fnd_pricing.matching import TIER_ORDER, score_match, tier_at_least

BASE = {
    "core": "SPC",
    "wear_layer_mil": "20",
    "thickness_mm": "6.5",
    "width_in": "7",
    "finish": "matte",
}


class MatchingTest(unittest.TestCase):
    def test_same_brand_and_specs_is_exact(self):
        result = score_match(BASE, "Mohawk", dict(BASE), "Mohawk")
        self.assertEqual(result.tier, "exact")
        self.assertEqual(result.score, 1.0)

    def test_same_specs_different_brand_is_equivalent(self):
        result = score_match(BASE, "NuCore", dict(BASE), "LifeProof")
        self.assertEqual(result.tier, "equivalent")
        self.assertFalse(result.same_brand)

    def test_cosmetic_difference_stays_comparable(self):
        candidate = dict(BASE, finish="embossed")
        self.assertTrue(tier_at_least(score_match(BASE, "A", candidate, "B").tier, "close"))

    def test_material_difference_is_not_like_for_like(self):
        candidate = dict(BASE, core="laminate", wear_layer_mil="6")
        result = score_match(BASE, "A", candidate, "B")
        self.assertEqual(result.tier, "weak")
        self.assertFalse(result.is_usable)

    def test_wear_layer_gap_downgrades_the_match(self):
        strong = score_match(BASE, "A", dict(BASE), "B")
        weaker = score_match(BASE, "A", dict(BASE, wear_layer_mil="12"), "B")
        self.assertLess(weaker.score, strong.score)
        self.assertIn("wear_layer_mil", weaker.unmatched_specs)

    def test_near_identical_numbers_are_treated_as_equal(self):
        result = score_match({"thickness_mm": "6.5"}, "A", {"thickness_mm": "6.4"}, "A")
        self.assertEqual(result.score, 1.0)

    def test_dimensions_parse_regardless_of_notation(self):
        result = score_match({"size_in": "12x24"}, "A", {"size_in": "12 in. x 24 in."}, "A")
        self.assertEqual(result.score, 1.0)

    def test_synonyms_are_reconciled(self):
        result = score_match({"core": "rigid"}, "A", {"core": "rigid core"}, "A")
        self.assertEqual(result.score, 1.0)

    def test_unverified_specs_cap_confidence(self):
        # Only one attribute is published by both retailers, so even a perfect
        # agreement on it should not produce full confidence.
        sparse = score_match(BASE, "A", {"core": "SPC"}, "B")
        self.assertLess(sparse.score, 1.0)
        self.assertEqual(sparse.compared_specs, 1)

    def test_tier_ordering_is_strongest_first(self):
        self.assertEqual(TIER_ORDER[0], "exact")
        self.assertTrue(tier_at_least("exact", "close"))
        self.assertFalse(tier_at_least("weak", "close"))


if __name__ == "__main__":
    unittest.main()
