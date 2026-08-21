"""The report and workbook writers must survive real data."""

import tempfile
import unittest
from pathlib import Path

from fnd_pricing.compare import compare_all
from fnd_pricing.loader import load_dataset
from fnd_pricing.report import render_html

ROOT = Path(__file__).resolve().parents[1]


class OutputTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        groups, offers = load_dataset(
            ROOT / "data/raw/sku_groups.csv", ROOT / "data/raw/products.csv"
        )
        cls.comparisons = compare_all(groups, offers)

    def test_html_report_is_self_contained(self):
        html = render_html(self.comparisons, "2026-08-14")
        self.assertIn("<!doctype html>", html)
        self.assertNotIn("http://", html.replace("http://www.w3.org", ""))
        self.assertNotIn("<script src=", html)
        self.assertIn("Luxury Vinyl Plank", html)

    def test_html_report_embeds_every_sku(self):
        html = render_html(self.comparisons)
        for comp in self.comparisons:
            self.assertIn(f'"{comp.group.group_id}"', html)

    def test_workbook_writes_all_sheets(self):
        from openpyxl import load_workbook

        from fnd_pricing.excel import write_workbook

        out = Path(tempfile.mkdtemp()) / "book.xlsx"
        write_workbook(self.comparisons, out)
        workbook = load_workbook(out)
        self.assertEqual(
            workbook.sheetnames, ["Summary", "SKU Detail", "Offers", "Exceptions"]
        )
        self.assertEqual(workbook["SKU Detail"].max_row, len(self.comparisons) + 1)


if __name__ == "__main__":
    unittest.main()
