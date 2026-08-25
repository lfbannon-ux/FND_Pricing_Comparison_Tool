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

    def test_expense_section_is_rendered_with_both_charts(self):
        html = render_html(self.comparisons)
        self.assertIn("Expense by category", html)
        self.assertIn("Annual expense at Floor &amp; Decor prices", html)
        self.assertEqual(html.count('<svg class="chart"'), 2)
        self.assertIn("Below market low", html)   # legend, so colour is never alone

    def test_charts_carry_a_hover_and_keyboard_target_per_row(self):
        from fnd_pricing.spend import expense_by_category

        html = render_html(self.comparisons)
        categories = len(expense_by_category(self.comparisons))
        self.assertEqual(html.count('<g class="row" tabindex="0"'), categories * 2)

    def test_workbook_writes_all_sheets(self):
        from openpyxl import load_workbook

        from fnd_pricing.excel import write_workbook

        out = Path(tempfile.mkdtemp()) / "book.xlsx"
        write_workbook(self.comparisons, out)
        workbook = load_workbook(out)
        self.assertEqual(
            workbook.sheetnames,
            ["Summary", "Category Expense", "SKU Detail", "Offers", "Exceptions"],
        )
        self.assertEqual(workbook["SKU Detail"].max_row, len(self.comparisons) + 1)


if __name__ == "__main__":
    unittest.main()
