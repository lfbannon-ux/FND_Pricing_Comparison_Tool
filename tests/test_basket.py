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
               category="LVP", others=None, **offer_kwargs):
    """Build a comparison. `others` prices any additional competitor by name."""
    brands = brands or {}
    offers = [offer(group_id, "floor_and_decor", fnd,
                    brand=brands.get("floor_and_decor", "Mohawk"))]
    if home_depot is not None:
        offers.append(offer(group_id, "home_depot", home_depot,
                            brand=brands.get("home_depot", "Mohawk"), **offer_kwargs))
    if lowes is not None:
        offers.append(offer(group_id, "lowes", lowes,
                            brand=brands.get("lowes", "Mohawk")))
    for retailer, price in (others or {}).items():
        offers.append(offer(group_id, retailer, price,
                            brand=brands.get(retailer, "Mohawk")))
    return compare_group(group(group_id, volume, category), offers)


def everywhere(group_id, fnd, competitor_price, brands=None, volume=1000.0):
    """Priced identically at every competitor in the registry."""
    from fnd_pricing import COMPETITORS

    return comparison(
        group_id, fnd, volume=volume, brands=brands,
        others={r: competitor_price for r in COMPETITORS},
    )


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
        from fnd_pricing import COMPETITORS

        self.competitors = COMPETITORS
        self.comparisons = [
            everywhere("G1", 2.0, 3.0),                          # identical everywhere
            comparison("G2", 2.0, 3.0),                          # Home Depot only
            comparison("G3", 2.0, None, 3.0),                    # Lowe's only
            # Priced everywhere, but one competitor sells a different brand, so
            # it is not an identical SKU and the row leaves the common basket.
            everywhere("G4", 2.0, 3.0, brands={COMPETITORS[-1]: "Style Selections"}),
        ]

    def test_common_basket_is_the_intersection(self):
        common = common_members(self.comparisons)
        self.assertEqual([c.group.group_id for c in common], ["G1"])

    def test_own_baskets_are_wider_than_the_common_one(self):
        basket_set = build_basket_set(self.comparisons)
        self.assertEqual(basket_set.common_skus, 1)
        # Home Depot is identical on G1, G2 and G4; the intersection keeps one.
        self.assertEqual(basket_set.own_baskets["home_depot"].skus, 3)
        self.assertEqual(basket_set.own_baskets["lowes"].skus, 3)
        self.assertEqual(basket_set.own_baskets[self.competitors[-1]].skus, 1)

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


class SignConventionTest(unittest.TestCase):
    """The codebase carries two opposite sign conventions; pin both down."""

    def test_positive_quote_delta_means_floor_and_decor_is_cheaper(self):
        comp = comparison("G1", 2.00, 2.20)
        self.assertAlmostEqual(comp.quotes["home_depot"].delta_pct, 0.10, places=4)
        self.assertEqual(comp.outcome, "win")

    def test_negative_market_gap_means_floor_and_decor_is_cheaper(self):
        comp = comparison("G1", 2.00, 2.20)
        self.assertLess(comp.gap_vs_market_min, 0)

    def test_the_two_conventions_are_opposite_for_the_same_sku(self):
        comp = comparison("G1", 2.00, 2.20)
        self.assertGreater(comp.quotes["home_depot"].delta_pct, 0)
        self.assertLess(comp.gap_vs_market_min, 0)

    def test_a_positive_median_gap_basket_means_floor_and_decor_wins_most_skus(self):
        basket = build_basket([
            comparison("G1", 2.00, 2.20),
            comparison("G2", 2.00, 2.20),
            comparison("G3", 2.00, 1.90),
        ], "home_depot")
        self.assertGreater(basket.median_gap, 0)
        self.assertEqual((basket.wins, basket.losses), (2, 1))


class MultiCompetitorTest(unittest.TestCase):
    """Adding competitors must narrow the common basket, not silently widen it."""

    def test_common_basket_requires_a_match_at_every_competitor(self):
        from fnd_pricing import COMPETITORS

        offers = [offer("G1", "floor_and_decor", 2.0)]
        # Identical at every competitor except the last one, which is absent.
        for retailer in COMPETITORS[:-1]:
            offers.append(offer("G1", retailer, 2.2))
        comp = compare_group(group("G1"), offers)
        self.assertEqual(common_members([comp]), [])

        offers.append(offer("G1", COMPETITORS[-1], 2.2))
        complete = compare_group(group("G1"), offers)
        self.assertEqual(len(common_members([complete])), 1)

    def test_common_share_reports_how_much_of_each_basket_survives(self):
        from fnd_pricing import COMPETITORS

        everywhere = [offer("G1", "floor_and_decor", 2.0)] + [
            offer("G1", r, 2.2) for r in COMPETITORS
        ]
        partial = [offer("G2", "floor_and_decor", 2.0),
                   offer("G2", COMPETITORS[0], 2.2)]
        basket_set = build_basket_set([
            compare_group(group("G1"), everywhere),
            compare_group(group("G2"), partial),
        ])
        self.assertEqual(basket_set.common_skus, 1)
        # The first competitor matched twice; only one survives the intersection.
        self.assertAlmostEqual(basket_set.common_share[COMPETITORS[0]], 0.5, places=4)
        self.assertAlmostEqual(basket_set.common_share[COMPETITORS[1]], 1.0, places=4)

    def test_every_competitor_gets_its_own_basket(self):
        from fnd_pricing import COMPETITORS

        basket_set = build_basket_set([comparison("G1", 2.0, 2.2, 2.3)])
        self.assertEqual(set(basket_set.own_baskets), set(COMPETITORS))
        self.assertEqual(set(basket_set.common_baskets), set(COMPETITORS))


class ActiveSetTest(unittest.TestCase):
    """Narrowing the competitive set changes the answer, so it must be exact."""

    def tearDown(self):
        from fnd_pricing import reset_retailers

        reset_retailers()

    def test_excluding_a_retailer_removes_it_from_every_comparison(self):
        from fnd_pricing import competitors, set_active_retailers

        set_active_retailers(["floor_and_decor", "home_depot", "lowes"])
        self.assertNotIn("tile_shop", competitors())
        comp = comparison("G1", 2.0, 3.0, 3.0, others={"tile_shop": 1.0})
        # The excluded banner cannot set the market low, even priced lowest.
        self.assertNotIn("tile_shop", comp.quotes)
        self.assertEqual(comp.market_min, 3.0)
        self.assertEqual(comp.outcome, "win")

    def test_the_base_retailer_cannot_be_excluded(self):
        from fnd_pricing import BASE_RETAILER, competitors, set_active_retailers

        set_active_retailers(["home_depot"])
        self.assertNotIn(BASE_RETAILER, competitors())
        from fnd_pricing import active_retailers
        self.assertIn(BASE_RETAILER, active_retailers())

    def test_an_unknown_retailer_is_refused(self):
        from fnd_pricing import set_active_retailers

        with self.assertRaises(ValueError):
            set_active_retailers(["home_depot", "menards_wholesale"])

    def test_an_empty_competitive_set_is_refused(self):
        from fnd_pricing import set_active_retailers

        with self.assertRaises(ValueError):
            set_active_retailers(["floor_and_decor"])


class AtLeastBasketTest(unittest.TestCase):
    """`--tier` isolates one grade; `--at-least` asks what we both carry."""

    def setUp(self):
        from fnd_pricing import COMPETITORS

        self.exact = everywhere("G1", 2.0, 2.2)
        # Same specs, different brands -> equivalent, never exact.
        self.equivalent = comparison(
            "G2", 2.0,
            others={r: 2.2 for r in COMPETITORS},
            brands={r: f"Brand{i}" for i, r in enumerate(COMPETITORS)},
        )

    def test_exact_tier_alone_excludes_equivalent_rows(self):
        basket_set = build_basket_set([self.exact, self.equivalent])
        self.assertEqual([c.group.group_id for c in basket_set.common], ["G1"])

    def test_at_least_admits_the_better_tier_too(self):
        basket_set = build_basket_set(
            [self.exact, self.equivalent], tier="equivalent", at_least=True
        )
        self.assertEqual(
            sorted(c.group.group_id for c in basket_set.common), ["G1", "G2"]
        )

    def test_equivalent_tier_alone_excludes_exact_rows(self):
        # Exact-tier equality is what keeps the identical-SKU evidence isolated.
        basket_set = build_basket_set([self.exact, self.equivalent], tier="equivalent")
        self.assertEqual([c.group.group_id for c in basket_set.common], ["G2"])


class BasketDriversTest(unittest.TestCase):
    """Spend concentration and price exposure are different questions."""

    def tearDown(self):
        from fnd_pricing import reset_retailers

        reset_retailers()

    def test_a_high_volume_cheap_sku_dominates_spend_without_being_exposed(self):
        # The item that makes the basket big need not be the item that makes it
        # expensive; ranking by spend alone sends you after the wrong SKU.
        cheap_and_huge = everywhere("G1", 1.00, 1.05, volume=1_000_000)
        dear_and_small = everywhere("G2", 9.00, 6.00, volume=100)

        spend = {
            c.group.group_id: c.base_price * c.group.annual_volume
            for c in (cheap_and_huge, dear_and_small)
        }
        self.assertGreater(spend["G1"], spend["G2"])          # G1 dominates spend

        exposure = {
            c.group.group_id: (c.base_price - c.market_min) * c.group.annual_volume
            for c in (cheap_and_huge, dear_and_small)
        }
        self.assertLess(exposure["G1"], 0)                    # G1 is an advantage
        self.assertGreater(exposure["G2"], 0)                 # G2 is the exposure

    def test_drivers_render_without_error_on_a_real_basket(self):
        import io
        from contextlib import redirect_stdout

        from fnd_pricing.cli import _print_basket_drivers

        rows = [everywhere(f"G{i}", 2.0 + i, 2.5 + i, volume=100 * (i + 1))
                for i in range(4)]
        base_spend = sum(c.base_price * c.group.annual_volume for c in rows)
        buffer = io.StringIO()
        with redirect_stdout(buffer):
            _print_basket_drivers(rows, base_spend, 3)
        output = buffer.getvalue()
        self.assertIn("WHAT MAKES THE BASKET BIG", output)
        self.assertIn("Advantage (F&D cheaper)", output)

    def test_drivers_survive_a_basket_with_no_exposure(self):
        import io
        from contextlib import redirect_stdout

        from fnd_pricing.cli import _print_basket_drivers

        rows = [everywhere("G1", 1.0, 2.0, volume=100)]   # F&D cheaper everywhere
        buffer = io.StringIO()
        with redirect_stdout(buffer):
            _print_basket_drivers(rows, 100.0, 5)
        self.assertNotIn("WHAT MAKES IT EXPENSIVE", buffer.getvalue())
