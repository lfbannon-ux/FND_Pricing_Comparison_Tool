import unittest

from fnd_pricing.compare import compare_group
from fnd_pricing.models import Offer, SkuGroup
from fnd_pricing.spend import (
    MARKET_LOW,
    build_expense,
    expense_by_category,
    total_expense,
)

SPECS = {"core": "SPC", "wear_layer_mil": "20", "thickness_mm": "6.5"}


def group(group_id, category="Luxury Vinyl Plank", basis="sq_ft", volume=1000.0):
    return SkuGroup(
        group_id=group_id, category=category, subcategory="sub", basis=basis,
        description="d", specs=dict(SPECS), annual_volume=volume,
    )


def offer(group_id, retailer, price, uom="per_sq_ft", specs=None, **kwargs):
    return Offer(
        group_id=group_id, retailer=retailer, retailer_sku="X", brand="House",
        product_name="P", price=price, uom=uom,
        specs=specs if specs is not None else dict(SPECS), **kwargs,
    )


def comparison(group_id, fnd, home_depot=None, lowes=None, **group_kwargs):
    offers = [offer(group_id, "floor_and_decor", fnd)]
    if home_depot is not None:
        offers.append(offer(group_id, "home_depot", home_depot))
    if lowes is not None:
        offers.append(offer(group_id, "lowes", lowes))
    return compare_group(group(group_id, **group_kwargs), offers)


class ExpenseTest(unittest.TestCase):
    def test_expense_is_price_times_volume(self):
        expense = build_expense("t", [comparison("G1", 2.50, volume=1000)])
        self.assertEqual(expense.annual_spend, 2500.0)
        self.assertEqual(expense.annual_units, 1000.0)
        self.assertEqual(expense.avg_unit_price, 2.50)

    def test_a_group_without_volume_contributes_no_expense(self):
        expense = build_expense("t", [
            comparison("G1", 2.50, volume=0),
            comparison("G2", 1.00, volume=100),
        ])
        self.assertEqual(expense.annual_spend, 100.0)
        self.assertEqual(expense.priced_skus, 1)
        self.assertEqual(expense.skus, 2)

    def test_index_uses_only_the_skus_the_retailer_covers(self):
        # Home Depot covers only the small SKU. Its index must be computed on
        # that SKU alone - not against the whole $10,000 of Floor & Decor spend,
        # which would read as a huge price advantage that is really no coverage.
        expense = build_expense("t", [
            comparison("G1", 10.0, volume=1000),                 # no competitor
            comparison("G2", 1.0, home_depot=2.0, volume=100),   # covered
        ])
        basket = expense.baskets["home_depot"]
        self.assertEqual(basket.matched_skus, 1)
        self.assertEqual(basket.base_spend, 100.0)
        self.assertEqual(basket.comp_spend, 200.0)
        self.assertEqual(basket.index, 0.5)
        self.assertEqual(basket.delta, -100.0)

    def test_uncovered_spend_is_reported_as_unbenchmarked(self):
        expense = build_expense("t", [
            comparison("G1", 10.0, volume=1000),
            comparison("G2", 1.0, home_depot=2.0, volume=100),
        ])
        self.assertEqual(expense.annual_spend, 10100.0)
        self.assertEqual(expense.benchmarked_spend, 100.0)
        self.assertEqual(expense.unbenchmarked_spend, 10000.0)
        self.assertAlmostEqual(expense.benchmark_coverage, 100 / 10100, places=4)

    def test_an_excluded_quote_stays_out_of_the_basket(self):
        # A weak match must not set a competitor's spend.
        weak = compare_group(group("G1"), [
            offer("G1", "floor_and_decor", 4.0),
            offer("G1", "home_depot", 1.0,
                  specs={"core": "laminate", "wear_layer_mil": "6", "thickness_mm": "7"}),
        ])
        expense = build_expense("t", [weak])
        self.assertEqual(expense.baskets["home_depot"].matched_skus, 0)
        self.assertIsNone(expense.baskets["home_depot"].index)
        self.assertEqual(expense.unbenchmarked_spend, expense.annual_spend)

    def test_out_of_stock_competitor_stays_out_of_the_basket(self):
        comp = compare_group(group("G1"), [
            offer("G1", "floor_and_decor", 4.0),
            offer("G1", "home_depot", 1.0, in_stock=False),
        ])
        self.assertEqual(build_expense("t", [comp]).baskets["home_depot"].matched_skus, 0)

    def test_market_low_basket_takes_the_cheapest_comparable_offer(self):
        expense = build_expense("t", [
            comparison("G1", 3.0, home_depot=4.0, lowes=2.0, volume=100)
        ])
        basket = expense.baskets[MARKET_LOW]
        self.assertEqual(basket.comp_spend, 200.0)   # Lowe's, the cheaper of the two
        self.assertEqual(basket.delta, 100.0)        # positive: F&D costs more
        self.assertEqual(basket.index, 1.5)

    def test_delta_is_negative_when_floor_and_decor_is_cheaper(self):
        expense = build_expense("t", [
            comparison("G1", 2.0, home_depot=3.0, volume=500)
        ])
        self.assertEqual(expense.baskets[MARKET_LOW].delta, -500.0)

    def test_average_unit_price_is_withheld_when_bases_differ(self):
        # $/sq ft and $/each cannot be averaged into a meaningful number.
        mixed = build_expense("t", [
            comparison("G1", 2.0, volume=100),
            comparison("G2", 300.0, basis="each", volume=10),
        ])
        self.assertIsNone(mixed.basis)
        self.assertIsNone(mixed.avg_unit_price)

    def test_categories_are_ranked_by_expense(self):
        rows = expense_by_category([
            comparison("G1", 1.0, category="Small", volume=10),
            comparison("G2", 5.0, category="Big", volume=1000),
            comparison("G3", 2.0, category="Middle", volume=100),
        ])
        self.assertEqual([r.category for r in rows], ["Big", "Middle", "Small"])
        self.assertEqual(rows[0].annual_spend, 5000.0)

    def test_shares_of_total_expense_add_up(self):
        comparisons = [
            comparison("G1", 1.0, category="A", volume=100),
            comparison("G2", 3.0, category="B", volume=100),
        ]
        total = total_expense(comparisons)
        shares = [r.share_of(total.annual_spend) for r in expense_by_category(comparisons)]
        self.assertAlmostEqual(sum(shares), 1.0, places=6)
        self.assertAlmostEqual(shares[0], 0.75, places=6)

    def test_index_is_none_rather_than_a_divide_by_zero(self):
        expense = build_expense("t", [comparison("G1", 2.0, volume=100)])
        self.assertIsNone(expense.baskets["lowes"].index)
        self.assertIsNone(expense.baskets["lowes"].delta_pct)


class ChartTest(unittest.TestCase):
    def test_axis_fills_the_plot_rather_than_over_rounding(self):
        from fnd_pricing.charts import _nice_axis

        maximum, step = _nice_axis(14_499_416)
        self.assertEqual((maximum, step), (15_000_000, 5_000_000))
        self.assertLess(14_499_416 / maximum, 1.01)
        self.assertGreater(14_499_416 / maximum, 0.9)

    def test_bar_end_radius_never_exceeds_the_bar(self):
        from fnd_pricing.charts import _bar_path

        self.assertEqual(_bar_path(100, 100.2, 0, 14), "")   # sub-pixel: no mark
        self.assertIn("M100.0", _bar_path(100, 102, 0, 14))  # tiny bar still draws

    def test_compact_money_keeps_small_values_legible(self):
        from fnd_pricing.charts import compact_money

        self.assertEqual(compact_money(14_499_416), "$14.5M")
        self.assertEqual(compact_money(-2_646), "-$2.6k")
        self.assertEqual(compact_money(985_300), "$985k")
        self.assertEqual(compact_money(0), "$0")


if __name__ == "__main__":
    unittest.main()
