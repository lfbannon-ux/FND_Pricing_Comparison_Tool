import unittest

from fnd_pricing.basket import (
    build_basket,
    build_basket_set,
    common_members,
    qualifies,
)
from fnd_pricing.compare import compare_group
from fnd_pricing.models import Offer, SkuGroup

SPECS = {"core": "SPC", "wear_layer_mil": "20", "thickness_mm": "6.5"}


def group(group_id, volume=1000.0, category="LVP"):
    return SkuGroup(
        group_id=group_id, category=category, subcategory="s", basis="sq_ft",
        description="d", specs=dict(SPECS), annual_volume=volume,
    )


def offer(group_id, retailer, price, brand="Mohawk", **kwargs):
    return Offer(
        group_id=group_id, retailer=retailer, retailer_sku="X", brand=brand,
        product_name="P", price=price, uom="per_sq_ft", specs=dict(SPECS), **kwargs,
    )


def comparison(group_id, fnd, home_depot=None, lowes=None, brands=None, volume=1000.0,
               category="LVP", **offer_kwargs):
    brands = brands or {}
    offers = [offer(group_id, "floor_and_decor", fnd,
                    brand=brands.get("floor_and_decor", "Mohawk"))]
    if home_depot is not None:
        offers.append(offer(group_id, "home_depot", home_depot,
                            brand=brands.get("home_depot", "Mohawk"), **offer_kwargs))
    if lowes is not None:
        offers.append(offer(group_id, "lowes", lowes,
                            brand=brands.get("lowes", "Mohawk")))
    return compare_group(group(group_id, volume, category), offers)


class QualifyTest(unittest.TestCase):
    def test_same_brand_and_specs_qualifies(self):
        self.assertTrue(qualifies(comparison("G1", 2.0, 3.0), "home_depot", "exact"))

    def test_a_different_brand_does_not_qualify_as_exact(self):
        comp = comparison("G1", 2.0, 3.0, brands={"home_depot": "LifeProof"})
        self.assertEqual(comp.quotes["home_depot"].tier, "equivalent")
        self.assertFalse(qualifies(comp, "home_depot", "exact"))

    def test_out_of_stock_does_not_qualify(self):
        comp = comparison("G1", 2.0, 3.0, in_stock=False)
        self.assertFalse(qualifies(comp, "home_depot", "exact"))

    def test_a_sku_without_volume_cannot_join_a_spend_basket(self):
        self.assertFalse(qualifies(comparison("G1", 2.0, 3.0, volume=0), "home_depot", "exact"))

    def test_a_missing_competitor_does_not_qualify(self):
        self.assertFalse(qualifies(comparison("G1", 2.0), "home_depot", "exact"))


class BasketTest(unittest.TestCase):
    def test_spend_index_and_advantage(self):
        basket = build_basket([comparison("G1", 2.0, 2.5, volume=100)], "home_depot")
        self.assertEqual(basket.skus, 1)
        self.assertEqual(basket.base_spend, 200.0)
        self.assertEqual(basket.comp_spend, 250.0)
        self.assertEqual(basket.spend_index, 0.8)
        self.assertEqual(basket.spend_advantage, -0.2)
        self.assertEqual(basket.spend_delta, -50.0)

    def test_weighted_and_unweighted_views_may_disagree(self):
        # Floor & Decor is dearer on both low-volume SKUs but much cheaper on the
        # one that carries the volume. The typical SKU says "dearer"; the basket
        # says "cheaper". Both are true, which is why both are reported.
        comparisons = [
            comparison("G1", 2.20, 2.00, volume=1),
            comparison("G2", 2.20, 2.00, volume=1),
            comparison("G3", 1.00, 2.00, volume=1000),
        ]
        basket = build_basket(comparisons, "home_depot")
        self.assertLess(basket.median_gap, 0)      # median SKU: F&D dearer
        self.assertLess(basket.spend_index, 1.0)   # basket: F&D cheaper
        self.assertEqual((basket.wins, basket.losses), (1, 2))

    def test_tie_band_absorbs_trivial_differences(self):
        basket = build_basket([comparison("G1", 2.000, 2.002)], "home_depot")
        self.assertEqual((basket.wins, basket.ties, basket.losses), (0, 1, 0))

    def test_promotions_are_separated_from_list_price(self):
        # Home Depot's list price is 3.00; it is on promotion at 2.20.
        basket = build_basket(
            [comparison("G1", 2.00, 3.00, volume=100, promo_price=2.20)], "home_depot"
        )
        self.assertAlmostEqual(basket.spend_index, 2.00 / 2.20, places=4)
        self.assertAlmostEqual(basket.list_spend_index, 2.00 / 3.00, places=4)
        self.assertGreater(basket.promo_effect, 0)  # the promo narrows F&D's lead

    def test_an_empty_basket_reports_nothing_rather_than_dividing_by_zero(self):
        basket = build_basket([comparison("G1", 2.0)], "home_depot")
        self.assertEqual(basket.skus, 0)
        self.assertIsNone(basket.spend_index)
        self.assertIsNone(basket.median_gap)
        self.assertIsNone(basket.promo_effect)
        self.assertIsNone(basket.win_rate)


class CommonBasketTest(unittest.TestCase):
    def setUp(self):
        self.comparisons = [
            comparison("G1", 2.0, 3.0, 3.0),                                    # both
            comparison("G2", 2.0, 3.0),                                         # HD only
            comparison("G3", 2.0, None, 3.0),                                   # Lowe's only
            comparison("G4", 2.0, 3.0, 3.0, brands={"lowes": "Style Selections"}),
        ]

    def test_common_basket_is_the_intersection(self):
        common = common_members(self.comparisons)
        self.assertEqual([c.group.group_id for c in common], ["G1"])

    def test_own_baskets_are_wider_than_the_common_one(self):
        basket_set = build_basket_set(self.comparisons)
        self.assertEqual(basket_set.common_skus, 1)
        self.assertEqual(basket_set.own_baskets["home_depot"].skus, 3)
        self.assertEqual(basket_set.own_baskets["lowes"].skus, 2)

    def test_every_common_basket_prices_the_same_floor_and_decor_spend(self):
        # The point of the common basket: one F&D number, quoted three ways.
        basket_set = build_basket_set(self.comparisons)
        spends = {b.base_spend for b in basket_set.common_baskets.values()}
        self.assertEqual(len(spends), 1)

    def test_cheapest_retailer_on_the_common_basket(self):
        basket_set = build_basket_set(self.comparisons)
        self.assertEqual(basket_set.cheapest_retailer, "floor_and_decor")


if __name__ == "__main__":
    unittest.main()
