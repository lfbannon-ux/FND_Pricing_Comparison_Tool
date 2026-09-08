import tempfile
import unittest
from pathlib import Path

from fnd_pricing.loader import (
    GROUP_COLUMNS,
    PRODUCT_COLUMNS,
    format_specs,
    load_dataset,
    parse_specs,
)
from fnd_pricing.models import DataError

GROUP_ROW = "G1,Luxury Vinyl Plank,SPC,sq_ft,test,1000,core=SPC;wear_layer_mil=20"
OFFER_ROW = ("G1,floor_and_decor,FD-1,NuCore,Plank,2.79,per_sq_ft,,,yes,"
             "2026-08-14,collected,,core=SPC;wear_layer_mil=20")


class LoaderTest(unittest.TestCase):
    def setUp(self):
        self.dir = Path(tempfile.mkdtemp())

    def write(self, groups=GROUP_ROW, offers=OFFER_ROW):
        (self.dir / "g.csv").write_text(",".join(GROUP_COLUMNS) + "\n" + groups + "\n")
        (self.dir / "p.csv").write_text(",".join(PRODUCT_COLUMNS) + "\n" + offers + "\n")
        return self.dir / "g.csv", self.dir / "p.csv"

    def test_round_trip(self):
        groups, offers = load_dataset(*self.write())
        self.assertEqual(len(groups), 1)
        self.assertEqual(offers[0].specs["core"], "SPC")
        self.assertEqual(groups["G1"].annual_volume, 1000.0)
        self.assertTrue(offers[0].in_stock)

    def test_specs_round_trip_through_the_encoding(self):
        specs = {"core": "rigid core", "size_in": "12x24"}
        self.assertEqual(parse_specs(format_specs(specs)), specs)

    def test_currency_formatting_is_tolerated(self):
        _, offers = load_dataset(*self.write(offers=OFFER_ROW.replace(",2.79,", ',"$2.79",')))
        self.assertEqual(offers[0].price, 2.79)

    def test_offer_for_an_unknown_group_is_rejected(self):
        with self.assertRaises(DataError) as ctx:
            load_dataset(*self.write(offers=OFFER_ROW.replace("G1,", "G9,", 1)))
        self.assertIn("not in sku_groups", str(ctx.exception))

    def test_unknown_retailer_is_rejected(self):
        with self.assertRaises(DataError):
            load_dataset(*self.write(offers=OFFER_ROW.replace("floor_and_decor", "acme_tile")))

    def test_duplicate_offer_for_one_retailer_is_rejected(self):
        with self.assertRaises(DataError) as ctx:
            load_dataset(*self.write(offers=OFFER_ROW + "\n" + OFFER_ROW))
        self.assertIn("duplicate", str(ctx.exception))

    def test_non_numeric_price_is_rejected_with_its_line_number(self):
        with self.assertRaises(DataError) as ctx:
            load_dataset(*self.write(offers=OFFER_ROW.replace(",2.79,", ",call for price,")))
        self.assertIn(":2", str(ctx.exception))

    def test_missing_column_is_reported(self):
        (self.dir / "g.csv").write_text("group_id,category\nG1,LVP\n")
        (self.dir / "p.csv").write_text(",".join(PRODUCT_COLUMNS) + "\n")
        with self.assertRaises(DataError) as ctx:
            load_dataset(self.dir / "g.csv", self.dir / "p.csv")
        self.assertIn("missing column", str(ctx.exception))


if __name__ == "__main__":
    unittest.main()
