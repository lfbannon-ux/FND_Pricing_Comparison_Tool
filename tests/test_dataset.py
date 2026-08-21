"""Integrity checks on the shipped dataset itself."""

import unittest
from pathlib import Path

from fnd_pricing import BASE_RETAILER
from fnd_pricing.compare import compare_all
from fnd_pricing.loader import load_dataset
from fnd_pricing.models import BASES, UOM_SPEC

ROOT = Path(__file__).resolve().parents[1]


class DatasetTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.groups, cls.offers = load_dataset(
            ROOT / "data/raw/sku_groups.csv", ROOT / "data/raw/products.csv"
        )
        cls.comparisons = compare_all(cls.groups, cls.offers)

    def test_the_study_covers_two_hundred_skus(self):
        self.assertEqual(len(self.groups), 200)

    def test_every_group_has_a_floor_and_decor_price(self):
        missing = [c.group.group_id for c in self.comparisons if c.base is None]
        self.assertEqual(missing, [], "groups without a base price cannot be compared")

    def test_every_offer_uses_a_uom_that_reaches_its_group_basis(self):
        for offer in self.offers:
            basis = UOM_SPEC[offer.uom][0]
            self.assertEqual(
                basis, self.groups[offer.group_id].basis,
                f"{offer.group_id}/{offer.retailer}: {offer.uom} cannot be compared",
            )

    def test_bases_are_known(self):
        self.assertTrue(all(g.basis in BASES for g in self.groups.values()))

    def test_most_groups_have_at_least_one_competitor_price(self):
        comparable = sum(1 for c in self.comparisons if c.market_min is not None)
        self.assertGreaterEqual(comparable / len(self.comparisons), 0.90)

    def test_every_price_is_positive_and_promos_are_below_list(self):
        for offer in self.offers:
            self.assertGreater(offer.price, 0)
            if offer.promo_price is not None:
                self.assertLessEqual(offer.promo_price, offer.price)

    def test_seed_rows_are_labelled_as_estimates(self):
        # The provenance stamp is what stops seed numbers being mistaken for
        # collected ones once this file is edited by hand.
        self.assertTrue(all(o.data_source for o in self.offers))

    def test_no_retailer_appears_twice_in_one_group(self):
        seen = set()
        for offer in self.offers:
            key = (offer.group_id, offer.retailer)
            self.assertNotIn(key, seen)
            seen.add(key)

    def test_base_retailer_is_floor_and_decor(self):
        self.assertEqual(BASE_RETAILER, "floor_and_decor")


if __name__ == "__main__":
    unittest.main()
