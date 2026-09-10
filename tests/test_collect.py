import csv
import tempfile
import unittest
from pathlib import Path

from fnd_pricing.collect import (
    Candidate,
    ingest_worksheet,
    worksheet_columns,
    write_canonical,
    write_worksheet,
)
from fnd_pricing.compare import compare_all
from fnd_pricing.loader import load_dataset
from fnd_pricing.models import UOM_SPEC, DataError

ROOT = Path(__file__).resolve().parents[1]
WORKSHEET = ROOT / "data/collection/identical_sku_worksheet.csv"

CANDIDATE = Candidate(
    candidate_id="C001", category="Setting Materials", basis="lb",
    brand="Custom Building Products", product="VersaBond Gray", pack="50 lb bag",
    record_uom="per_bag", specs="chemistry=modified thinset;color_family=gray",
    pack_coverage="50",
)


def fill(row, price_by_prefix, confirmed="y"):
    row["same_product_confirmed"] = confirmed
    row["collected_on"] = "2026-09-08"
    row["annual_volume"] = "1000"
    for prefix, price in price_by_prefix.items():
        row[f"{prefix}_carried"] = "y"
        row[f"{prefix}_price"] = str(price)
        row[f"{prefix}_sku"] = f"{prefix}-1"
    return row


class WorksheetTest(unittest.TestCase):
    def setUp(self):
        self.dir = Path(tempfile.mkdtemp())
        self.path = self.dir / "w.csv"

    def _rows(self):
        return list(csv.DictReader(open(self.path, encoding="utf-8")))

    def _write(self, rows):
        with open(self.path, "w", newline="", encoding="utf-8") as handle:
            writer = csv.DictWriter(handle, fieldnames=worksheet_columns())
            writer.writeheader()
            writer.writerows(rows)

    def test_worksheet_pre_fills_everything_except_the_prices(self):
        write_worksheet([CANDIDATE], self.path)
        row = self._rows()[0]
        self.assertEqual(row["brand"], "Custom Building Products")
        self.assertEqual(row["record_uom"], "per_bag")
        self.assertEqual(row["hd_pack_coverage"], "50")   # expected pack pre-filled
        self.assertEqual(row["hd_price"], "")             # the collector's job
        self.assertEqual(row["same_product_confirmed"], "")

    def test_round_trip_produces_a_loadable_dataset(self):
        write_worksheet([CANDIDATE], self.path)
        rows = self._rows()
        self._write([fill(rows[0], {"fnd": 24.98, "hd": 26.98, "lw": 25.98})])

        report = ingest_worksheet(self.path)
        groups_path, products_path = self.dir / "g.csv", self.dir / "p.csv"
        write_canonical(report, groups_path, products_path)

        groups, offers = load_dataset(groups_path, products_path)
        self.assertEqual(len(groups), 1)
        self.assertEqual(len(offers), 3)
        self.assertTrue(all(o.data_source == "collected" for o in offers))

    def test_an_ingested_row_scores_as_an_exact_match(self):
        # The point of the worksheet: one brand across three rows, identical
        # specs, so the tier comes out `exact` and needs no spec judgement.
        write_worksheet([CANDIDATE], self.path)
        rows = self._rows()
        self._write([fill(rows[0], {"fnd": 24.98, "hd": 26.98, "lw": 25.98})])
        report = ingest_worksheet(self.path)
        write_canonical(report, self.dir / "g.csv", self.dir / "p.csv")

        groups, offers = load_dataset(self.dir / "g.csv", self.dir / "p.csv")
        comparison = compare_all(groups, offers)[0]
        self.assertEqual(comparison.quotes["home_depot"].tier, "exact")
        self.assertEqual(comparison.outcome, "win")

    def test_unconfirmed_identity_is_refused(self):
        write_worksheet([CANDIDATE], self.path)
        rows = self._rows()
        self._write([fill(rows[0], {"fnd": 1.0, "hd": 2.0}, confirmed="")])
        with self.assertRaises(DataError):
            ingest_worksheet(self.path)   # nothing left to ingest

    def test_untouched_rows_are_counted_not_flagged(self):
        write_worksheet([CANDIDATE, CANDIDATE], self.path)
        rows = self._rows()
        rows[1]["candidate_id"] = "C002"
        self._write([fill(rows[0], {"fnd": 1.0, "hd": 2.0}), rows[1]])
        report = ingest_worksheet(self.path)
        self.assertEqual(report.not_started, 1)
        self.assertEqual(report.skipped, [])

    def test_a_started_row_with_no_price_is_flagged(self):
        write_worksheet([CANDIDATE], self.path)
        rows = self._rows()
        rows[0]["fnd_carried"] = "y"          # looked it up, recorded no price
        rows[0]["same_product_confirmed"] = "y"
        self._write(rows)
        with self.assertRaises(DataError):
            ingest_worksheet(self.path)

    def test_only_retailers_marked_carried_become_offers(self):
        write_worksheet([CANDIDATE], self.path)
        rows = self._rows()
        row = fill(rows[0], {"fnd": 24.98, "hd": 26.98})
        row["lw_carried"] = "n"
        self._write([row])
        report = ingest_worksheet(self.path)
        self.assertEqual(len(report.offers), 2)
        self.assertEqual(report.three_way, 0)

    def test_a_malformed_worksheet_is_rejected(self):
        self.path.write_text("candidate_id,brand\nC001,MAPEI\n")
        with self.assertRaises(DataError):
            ingest_worksheet(self.path)


class ShippedWorksheetTest(unittest.TestCase):
    """The shipped candidate list must be internally consistent."""

    @classmethod
    def setUpClass(cls):
        cls.rows = list(csv.DictReader(open(WORKSHEET, encoding="utf-8")))

    def test_it_over_provisions_past_the_forty_sku_target(self):
        self.assertGreaterEqual(len(self.rows), 45)

    def test_every_candidate_uom_reaches_its_declared_basis(self):
        for row in self.rows:
            basis, _ = UOM_SPEC[row["record_uom"]]
            self.assertEqual(
                basis, row["basis"],
                f"{row['candidate_id']}: {row['record_uom']} cannot be compared "
                f"on {row['basis']}",
            )

    def test_pack_uoms_carry_an_expected_pack_size(self):
        for row in self.rows:
            _, needs_coverage = UOM_SPEC[row["record_uom"]]
            if needs_coverage:
                self.assertTrue(
                    row["fnd_pack_coverage"],
                    f"{row['candidate_id']}: {row['record_uom']} needs a pack size",
                )

    def test_no_prices_are_shipped_in_the_worksheet(self):
        # A stray price here would silently become "collected" data.
        for row in self.rows:
            for prefix in ("fnd", "hd", "lw"):
                self.assertEqual(row[f"{prefix}_price"], "")
            self.assertEqual(row["same_product_confirmed"], "")

    def test_candidate_ids_are_unique(self):
        ids = [row["candidate_id"] for row in self.rows]
        self.assertEqual(len(ids), len(set(ids)))


if __name__ == "__main__":
    unittest.main()


class RegistryTest(unittest.TestCase):
    """The worksheet and the retailer registry must stay in step."""

    def test_worksheet_has_a_column_block_per_retailer(self):
        from fnd_pricing import RETAILERS, RETAILER_CODES
        from fnd_pricing.collect import PER_RETAILER_FIELDS, IDENTITY_COLUMNS

        columns = worksheet_columns()
        self.assertEqual(
            len(columns),
            len(IDENTITY_COLUMNS) + len(RETAILERS) * len(PER_RETAILER_FIELDS),
        )
        for retailer in RETAILERS:
            self.assertIn(f"{RETAILER_CODES[retailer]}_price", columns)

    def test_shipped_worksheet_covers_every_retailer(self):
        from fnd_pricing import RETAILER_CODES, RETAILERS

        header = list(csv.DictReader(open(WORKSHEET, encoding="utf-8")).fieldnames)
        for retailer in RETAILERS:
            self.assertIn(f"{RETAILER_CODES[retailer]}_carried", header)

    def test_ingest_handles_a_retailer_that_carries_nothing(self):
        # The Tile Shop does not merchandise laminate; that must ingest cleanly
        # as a missing offer rather than as an error.
        from fnd_pricing import COMPETITORS

        path = Path(tempfile.mkdtemp()) / "w.csv"
        write_worksheet([CANDIDATE], path)
        rows = list(csv.DictReader(open(path, encoding="utf-8")))
        row = fill(rows[0], {"fnd": 24.98, "hd": 26.98})
        for retailer in COMPETITORS[1:]:
            from fnd_pricing import RETAILER_CODES
            row[f"{RETAILER_CODES[retailer]}_carried"] = "n"
        with open(path, "w", newline="", encoding="utf-8") as handle:
            writer = csv.DictWriter(handle, fieldnames=worksheet_columns())
            writer.writeheader()
            writer.writerow(row)
        report = ingest_worksheet(path)
        self.assertEqual(len(report.offers), 2)
        self.assertEqual(report.three_way, 0)


class SpecMatchedStandardTest(unittest.TestCase):
    """The second evidence grade must stay distinguishable from the first."""

    def setUp(self):
        from fnd_pricing.collect import STANDARD_SPEC

        self.dir = Path(tempfile.mkdtemp())
        self.path = self.dir / "w.csv"
        self.candidate = Candidate(
            candidate_id="F001", category="Luxury Vinyl Plank", basis="sq_ft",
            brand="", product="Mid-tier SPC", pack="", record_uom="per_sq_ft",
            specs="core=SPC;wear_layer_mil=20;thickness_mm=6.0;width_in=7",
            match_standard=STANDARD_SPEC,
        )
        write_worksheet([self.candidate], self.path)

    def _rows(self):
        return list(csv.DictReader(open(self.path, encoding="utf-8")))

    def _write(self, rows):
        with open(self.path, "w", newline="", encoding="utf-8") as handle:
            writer = csv.DictWriter(handle, fieldnames=worksheet_columns())
            writer.writeheader()
            writer.writerows(rows)

    def _fill(self, row, brands_specs):
        row["collected_on"] = "2026-09-10"
        row["annual_volume"] = "1000"
        for prefix, (brand, specs, price) in brands_specs.items():
            row[f"{prefix}_carried"] = "y"
            row[f"{prefix}_brand"] = brand
            row[f"{prefix}_specs"] = specs
            row[f"{prefix}_price"] = str(price)
        return row

    def test_a_spec_matched_row_never_scores_as_identical(self):
        # Different brands, same specs -> `equivalent`, never `exact`. An exact
        # tier here would promote a judgement call into a stated fact.
        specs = self.candidate.specs
        row = self._fill(self._rows()[0], {
            "fnd": ("NuCore", specs, 2.99),
            "hd": ("LifeProof", specs, 3.49),
        })
        self._write([row])
        report = ingest_worksheet(self.path)
        write_canonical(report, self.dir / "g.csv", self.dir / "p.csv")

        groups, offers = load_dataset(self.dir / "g.csv", self.dir / "p.csv")
        comparison = compare_all(groups, offers)[0]
        self.assertEqual(comparison.quotes["home_depot"].tier, "equivalent")
        self.assertNotEqual(comparison.quotes["home_depot"].tier, "exact")

    def test_a_worse_spec_is_downgraded_not_hidden(self):
        row = self._fill(self._rows()[0], {
            "fnd": ("NuCore", self.candidate.specs, 2.99),
            "hd": ("LifeProof",
                   self.candidate.specs.replace("wear_layer_mil=20", "wear_layer_mil=6"),
                   2.49),
        })
        self._write([row])
        report = ingest_worksheet(self.path)
        write_canonical(report, self.dir / "g.csv", self.dir / "p.csv")

        groups, offers = load_dataset(self.dir / "g.csv", self.dir / "p.csv")
        quote = compare_all(groups, offers)[0].quotes["home_depot"]
        self.assertIn(quote.tier, ("close", "weak"))
        self.assertIn("wear_layer_mil", quote.match.unmatched_specs)

    def test_missing_per_retailer_specs_is_refused(self):
        row = self._rows()[0]
        row["collected_on"] = "2026-09-10"
        row["fnd_carried"] = "y"
        row["fnd_price"] = "2.99"
        row["fnd_brand"] = "NuCore"      # brand given, specs withheld
        self._write([row])
        with self.assertRaises(DataError):
            ingest_worksheet(self.path)

    def test_each_retailer_keeps_its_own_unit_of_measure(self):
        # Floor & Decor per sq ft, Home Depot per case: the row-level uom must
        # not flatten them, or the case price is compared as a square-foot price.
        row = self._fill(self._rows()[0], {
            "fnd": ("NuCore", self.candidate.specs, 2.99),
            "hd": ("LifeProof", self.candidate.specs, 71.98),
        })
        row["hd_uom"] = "per_case"
        row["hd_pack_coverage"] = "23.77"
        self._write([row])
        report = ingest_worksheet(self.path)
        write_canonical(report, self.dir / "g.csv", self.dir / "p.csv")

        groups, offers = load_dataset(self.dir / "g.csv", self.dir / "p.csv")
        quote = compare_all(groups, offers)[0].quotes["home_depot"]
        self.assertAlmostEqual(quote.unit_price, 71.98 / 23.77, places=3)

    def test_an_unknown_match_standard_is_refused(self):
        row = self._fill(self._rows()[0], {"fnd": ("NuCore", self.candidate.specs, 2.99)})
        row["match_standard"] = "vibes"
        self._write([row])
        with self.assertRaises(DataError):
            ingest_worksheet(self.path)


class FlooringWorksheetTest(unittest.TestCase):
    FLOORING = ROOT / "data/collection/flooring_worksheet.csv"

    @classmethod
    def setUpClass(cls):
        cls.rows = list(csv.DictReader(open(cls.FLOORING, encoding="utf-8")))

    def test_it_covers_lvt_tile_and_hardwood(self):
        categories = {row["category"] for row in self.rows}
        self.assertIn("Luxury Vinyl Plank", categories)
        self.assertIn("Porcelain Tile", categories)
        self.assertIn("Engineered Hardwood", categories)
        self.assertIn("Solid Hardwood", categories)

    def test_most_rows_use_the_spec_matched_standard(self):
        from fnd_pricing.collect import STANDARD_SPEC

        spec_rows = [r for r in self.rows if r["match_standard"] == STANDARD_SPEC]
        self.assertGreaterEqual(len(spec_rows) / len(self.rows), 0.8)

    def test_every_row_declares_a_known_standard(self):
        from fnd_pricing.collect import MATCH_STANDARDS

        for row in self.rows:
            self.assertIn(row["match_standard"], MATCH_STANDARDS)

    def test_every_candidate_carries_a_target_specification(self):
        for row in self.rows:
            self.assertTrue(row["specs"], f"{row['candidate_id']} has no target spec")
            self.assertIn("=", row["specs"])

    def test_no_prices_are_shipped(self):
        from fnd_pricing import RETAILER_CODES, RETAILERS

        for row in self.rows:
            for retailer in RETAILERS:
                self.assertEqual(row[f"{RETAILER_CODES[retailer]}_price"], "")
