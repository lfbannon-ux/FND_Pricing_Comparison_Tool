import unittest

from fnd_pricing.compare import (
    FLAG_NO_MATCH,
    FLAG_PROMO_DRIVEN,
    compare_group,
    build_rollup,
)
from fnd_pricing.models import Offer, SkuGroup

SPECS = {"core": "SPC", "wear_layer_mil": "20", "thickness_mm": "6.5"}


def group(group_id="G1", basis="sq_ft", volume=1000.0):
    return SkuGroup(
        group_id=group_id, category="Luxury Vinyl Plank", subcategory="SPC",
        basis=basis, description="test plank", specs=dict(SPECS), annual_volume=volume,
    )


def offer(retailer, price, uom="per_sq_ft", specs=None, **kwargs):
    return Offer(
        group_id=kwargs.pop("group_id", "G1"), retailer=retailer,
        retailer_sku="X", brand=kwargs.pop("brand", "House"), product_name="P",
        price=price, uom=uom, specs=specs if specs is not None else dict(SPECS),
        **kwargs,
    )


class CompareTest(unittest.TestCase):
    def test_cheaper_floor_and_decor_is_a_win(self):
        comp = compare_group(group(), [
            offer("floor_and_decor", 2.79),
            offer("home_depot", 3.49),
            offer("lowes", 3.29),
        ])
        self.assertEqual(comp.outcome, "win")
        self.assertEqual(comp.market_min, 3.29)
        self.assertEqual(comp.cheapest_retailer, "floor_and_decor")
        self.assertAlmostEqual(comp.gap_vs_market_min, (2.79 - 3.29) / 3.29, places=3)

    def test_more_expensive_floor_and_decor_is_a_loss(self):
        comp = compare_group(group(), [
            offer("floor_and_decor", 3.99),
            offer("home_depot", 3.49),
        ])
        self.assertEqual(comp.outcome, "loss")
        self.assertEqual(comp.cheapest_retailer, "home_depot")

    def test_prices_inside_the_tie_band_are_a_tie(self):
        comp = compare_group(group(), [
            offer("floor_and_decor", 3.00),
            offer("home_depot", 3.01),
        ])
        self.assertEqual(comp.outcome, "tie")
        self.assertEqual(comp.cheapest_retailer, "floor_and_decor")

    def test_units_are_reconciled_before_comparing(self):
        # $89.98 per 23.77 sq ft case = $3.785/sq ft, which beats $3.99/sq ft.
        comp = compare_group(group(), [
            offer("floor_and_decor", 3.99),
            offer("home_depot", 89.98, uom="per_box", pack_coverage=23.77),
        ])
        self.assertEqual(comp.outcome, "loss")
        self.assertAlmostEqual(comp.quotes["home_depot"].unit_price, 3.7854, places=3)

    def test_a_weak_match_is_excluded_from_the_market_price(self):
        comp = compare_group(group(), [
            offer("floor_and_decor", 3.99),
            offer("home_depot", 1.29, specs={"core": "laminate", "wear_layer_mil": "6",
                                             "thickness_mm": "7"}),
        ])
        self.assertFalse(comp.quotes["home_depot"].included)
        self.assertIsNone(comp.market_min)
        self.assertEqual(comp.outcome, "no_comparison")

    def test_out_of_stock_competitor_does_not_set_the_market_price(self):
        comp = compare_group(group(), [
            offer("floor_and_decor", 3.99),
            offer("home_depot", 2.99, in_stock=False),
        ])
        self.assertFalse(comp.quotes["home_depot"].included)
        self.assertIsNone(comp.market_min)

    def test_missing_competitor_offer_is_flagged(self):
        comp = compare_group(group(), [offer("floor_and_decor", 3.99)])
        self.assertIn(f"{FLAG_NO_MATCH}:home_depot", comp.flags)
        self.assertIn(f"{FLAG_NO_MATCH}:lowes", comp.flags)

    def test_gap_that_only_exists_because_of_a_promotion_is_flagged(self):
        # List price says Home Depot is dearer; today's promo flips it.
        comp = compare_group(group(), [
            offer("floor_and_decor", 3.50),
            offer("home_depot", 3.99, promo_price=2.99),
        ])
        self.assertIn(f"{FLAG_PROMO_DRIVEN}:home_depot", comp.flags)

    def test_basket_index_is_weighted_by_volume(self):
        cheap_but_rare = compare_group(group("G1", volume=10), [
            offer("floor_and_decor", 1.00, group_id="G1"),
            offer("home_depot", 2.00, group_id="G1"),
        ])
        dear_and_common = compare_group(group("G2", volume=1000), [
            offer("floor_and_decor", 2.00, group_id="G2"),
            offer("home_depot", 1.00, group_id="G2"),
        ])
        rollup = build_rollup("t", [cheap_but_rare, dear_and_common])
        # 10*1 + 1000*2 = 2010 spent vs 10*2 + 1000*1 = 1020 at market low.
        self.assertAlmostEqual(rollup.spend_index, 2010 / 1020, places=3)
        self.assertEqual(rollup.wins, 1)
        self.assertEqual(rollup.losses, 1)

    def test_rollup_counts_only_comparable_groups(self):
        rollup = build_rollup("t", [
            compare_group(group("G1"), [offer("floor_and_decor", 2.0, group_id="G1")]),
            compare_group(group("G2"), [
                offer("floor_and_decor", 2.0, group_id="G2"),
                offer("home_depot", 3.0, group_id="G2"),
            ]),
        ])
        self.assertEqual(rollup.groups, 2)
        self.assertEqual(rollup.compared, 1)


if __name__ == "__main__":
    unittest.main()


class ListPriceModeTest(unittest.TestCase):
    """Everyday-low-price positions need a promo-free view to be visible."""

    def test_list_price_mode_ignores_a_competitor_promotion(self):
        # Shelf: F&D 2.00, HD 2.50 - F&D is cheaper every day. Today HD is on
        # promotion at 1.80, so a promo-inclusive snapshot calls it a loss.
        offers = [
            offer("floor_and_decor", 2.00),
            offer("home_depot", 2.50, promo_price=1.80),
        ]
        today = compare_group(group(), offers)
        self.assertEqual(today.outcome, "loss")

        shelf = compare_group(group(), offers, use_list_price=True)
        self.assertEqual(shelf.outcome, "win")
        self.assertEqual(shelf.quotes["home_depot"].unit_price, 2.50)

    def test_list_price_mode_also_ignores_the_base_retailer_promotion(self):
        # It must be symmetric, or it just flatters Floor & Decor.
        offers = [
            offer("floor_and_decor", 2.50, promo_price=1.80),
            offer("home_depot", 2.00),
        ]
        self.assertEqual(compare_group(group(), offers).outcome, "win")
        self.assertEqual(
            compare_group(group(), offers, use_list_price=True).outcome, "loss"
        )

    def test_a_gap_unaffected_by_promotions_is_identical_in_both_modes(self):
        offers = [offer("floor_and_decor", 2.00), offer("home_depot", 2.50)]
        today = compare_group(group(), offers)
        shelf = compare_group(group(), offers, use_list_price=True)
        self.assertEqual(today.gap_vs_market_min, shelf.gap_vs_market_min)

    def test_the_promo_driven_flag_marks_exactly_these_reversals(self):
        offers = [
            offer("floor_and_decor", 2.00),
            offer("home_depot", 2.50, promo_price=1.80),
        ]
        comp = compare_group(group(), offers)
        self.assertIn(f"{FLAG_PROMO_DRIVEN}:home_depot", comp.flags)
        # The flag and the list-price mode must agree about which SKU it is.
        self.assertNotEqual(
            comp.outcome, compare_group(group(), offers, use_list_price=True).outcome
        )

    def test_list_price_is_preserved_in_both_modes(self):
        offers = [
            offer("floor_and_decor", 2.00),
            offer("home_depot", 2.50, promo_price=1.80),
        ]
        for use_list in (False, True):
            comp = compare_group(group(), offers, use_list_price=use_list)
            self.assertEqual(comp.quotes["home_depot"].normalized.list_unit_price, 2.50)
