import unittest

from fnd_pricing.models import DataError, Offer
from fnd_pricing.normalize import normalize


def offer(**kwargs):
    base = dict(
        group_id="G1", retailer="home_depot", retailer_sku="1", brand="LifeProof",
        product_name="Test", price=100.0, uom="per_sq_ft",
    )
    base.update(kwargs)
    return Offer(**base)


class NormalizeTest(unittest.TestCase):
    def test_direct_unit_price_passes_through(self):
        self.assertEqual(normalize(offer(price=2.79), "sq_ft").unit_price, 2.79)

    def test_case_price_divides_by_coverage(self):
        result = normalize(offer(price=89.98, uom="per_box", pack_coverage=23.77), "sq_ft")
        self.assertAlmostEqual(result.unit_price, 3.7854, places=4)
        self.assertIn("23.77", result.conversion)

    def test_square_yard_converts_to_square_foot(self):
        result = normalize(offer(price=27.0, uom="per_sq_yd"), "sq_ft")
        self.assertAlmostEqual(result.unit_price, 3.0, places=4)

    def test_promo_price_wins_but_list_price_is_retained(self):
        result = normalize(
            offer(price=50.0, uom="per_bag", pack_coverage=25.0, promo_price=40.0), "lb"
        )
        self.assertAlmostEqual(result.unit_price, 1.60, places=4)
        self.assertAlmostEqual(result.list_unit_price, 2.00, places=4)
        self.assertAlmostEqual(result.promo_discount, 0.20, places=4)

    def test_piece_price_divides_by_length(self):
        result = normalize(offer(price=24.0, uom="per_piece", pack_coverage=8.0), "lin_ft")
        self.assertEqual(result.unit_price, 3.0)

    def test_uom_from_a_different_basis_is_rejected(self):
        # A per-piece trim price must never be compared against per-sq-ft tile.
        with self.assertRaises(DataError):
            normalize(offer(uom="per_piece", pack_coverage=8.0), "sq_ft")

    def test_coverage_is_required_where_the_uom_implies_a_pack(self):
        with self.assertRaises(DataError):
            offer(uom="per_box")


if __name__ == "__main__":
    unittest.main()
