"""Excel workbook export for merchants who want to slice the data themselves."""

from __future__ import annotations

from pathlib import Path
from typing import List

from . import BASE_RETAILER, RETAILER_LABELS, RETAILERS
from .compare import GroupComparison, build_rollup, rollup_by_category

COMPETITORS = [r for r in RETAILERS if r != BASE_RETAILER]

_MONEY = '"$"#,##0.00'
_PCT = "+0.0%;-0.0%;0.0%"
_INDEX = "0.000"


def _style_header(worksheet, row: int = 1) -> None:
    from openpyxl.styles import Alignment, Font, PatternFill

    fill = PatternFill("solid", fgColor="1F3B57")
    for cell in worksheet[row]:
        cell.font = Font(bold=True, color="FFFFFF")
        cell.fill = fill
        cell.alignment = Alignment(vertical="center", wrap_text=True)
    worksheet.freeze_panes = worksheet.cell(row=row + 1, column=1)


def _autosize(worksheet, limit: int = 46) -> None:
    from openpyxl.utils import get_column_letter

    for idx, column in enumerate(worksheet.columns, start=1):
        width = max((len(str(c.value)) for c in column if c.value is not None), default=8)
        worksheet.column_dimensions[get_column_letter(idx)].width = min(width + 2, limit)


def write_workbook(comparisons: List[GroupComparison], path: Path) -> Path:
    from openpyxl import Workbook
    from openpyxl.styles import Font

    workbook = Workbook()
    overall = build_rollup("All categories", comparisons)

    # --- Summary ---
    sheet = workbook.active
    sheet.title = "Summary"
    sheet.append(["Floor & Decor like-for-like pricing comparison"])
    sheet["A1"].font = Font(bold=True, size=14)
    sheet.append([])
    for label, value, fmt in [
        ("SKU groups in study", overall.groups, "0"),
        ("SKU groups with a comparable competitor offer", overall.compared, "0"),
        ("Wins / ties / losses vs cheapest competitor",
         f"{overall.wins} / {overall.ties} / {overall.losses}", None),
        ("Win rate", overall.win_rate, "0.0%"),
        ("Median gap vs market low", overall.median_gap, _PCT),
        ("Mean gap vs market low", overall.mean_gap, _PCT),
        ("Volume-weighted basket index vs market low", overall.spend_index, _INDEX),
        ("Median gap vs Home Depot", overall.per_retailer_gap.get("home_depot"), _PCT),
        ("Median gap vs Lowe's", overall.per_retailer_gap.get("lowes"), _PCT),
    ]:
        sheet.append([label, value])
        if fmt:
            sheet.cell(row=sheet.max_row, column=2).number_format = fmt
        sheet.cell(row=sheet.max_row, column=1).font = Font(bold=True)

    sheet.append([])
    header_row = sheet.max_row + 1
    sheet.append([
        "Category", "SKUs", "Compared", "Win rate", "Median gap", "Mean gap",
        "Basket index", "Median vs Home Depot", "Median vs Lowe's",
    ])
    for rollup in rollup_by_category(comparisons):
        sheet.append([
            rollup.label, rollup.groups, rollup.compared, rollup.win_rate,
            rollup.median_gap, rollup.mean_gap, rollup.spend_index,
            rollup.per_retailer_gap.get("home_depot"),
            rollup.per_retailer_gap.get("lowes"),
        ])
        row = sheet.max_row
        sheet.cell(row=row, column=4).number_format = "0.0%"
        for col in (5, 6, 8, 9):
            sheet.cell(row=row, column=col).number_format = _PCT
        sheet.cell(row=row, column=7).number_format = _INDEX
    _style_header(sheet, header_row)
    sheet.freeze_panes = f"A{header_row + 1}"
    _autosize(sheet)

    # --- SKU detail ---
    detail = workbook.create_sheet("SKU Detail")
    detail.append([
        "Group", "Category", "Subcategory", "Description", "Basis", "Annual volume",
        "F&D brand", "F&D unit price",
        "Home Depot brand", "Home Depot unit price", "HD delta %", "HD match", "HD counted",
        "Lowe's brand", "Lowe's unit price", "LW delta %", "LW match", "LW counted",
        "Market low", "Gap vs low", "Outcome", "Cheapest", "Flags",
    ])
    for comp in comparisons:
        hd, lw = comp.quotes["home_depot"], comp.quotes["lowes"]
        detail.append([
            comp.group.group_id, comp.group.category, comp.group.subcategory,
            comp.group.description, comp.group.basis, comp.group.annual_volume,
            comp.base.offer.brand if comp.base else "", comp.base_price,
            hd.normalized.offer.brand if hd.normalized else "", hd.unit_price,
            hd.delta_pct, hd.tier, "yes" if hd.included else "no",
            lw.normalized.offer.brand if lw.normalized else "", lw.unit_price,
            lw.delta_pct, lw.tier, "yes" if lw.included else "no",
            comp.market_min, comp.gap_vs_market_min, comp.outcome,
            RETAILER_LABELS.get(comp.cheapest_retailer or "", ""),
            ", ".join(sorted({f.split(":")[0] for f in comp.flags})),
        ])
        row = detail.max_row
        for col in (8, 10, 15, 19):
            detail.cell(row=row, column=col).number_format = _MONEY
        for col in (11, 16, 20):
            detail.cell(row=row, column=col).number_format = _PCT
    _style_header(detail)
    detail.auto_filter.ref = detail.dimensions
    _autosize(detail)

    # --- Offers: the audit trail behind every normalised price ---
    offers = workbook.create_sheet("Offers")
    offers.append([
        "Group", "Retailer", "Retailer SKU", "Brand", "Product", "List price", "UOM",
        "Pack coverage", "Promo price", "Effective price", "Normalised unit price",
        "Conversion", "In stock", "Collected on", "Data source", "URL",
    ])
    for comp in comparisons:
        normalized = ([comp.base] if comp.base else []) + [
            q.normalized for q in comp.quotes.values() if q.normalized
        ]
        for norm in normalized:
            offer = norm.offer
            offers.append([
                offer.group_id, RETAILER_LABELS.get(offer.retailer, offer.retailer),
                offer.retailer_sku, offer.brand, offer.product_name, offer.price,
                offer.uom, offer.pack_coverage, offer.promo_price, offer.effective_price,
                norm.unit_price, norm.conversion, "yes" if offer.in_stock else "no",
                offer.collected_on, offer.data_source, offer.url,
            ])
            row = offers.max_row
            for col in (6, 9, 10, 11):
                offers.cell(row=row, column=col).number_format = _MONEY
    _style_header(offers)
    offers.auto_filter.ref = offers.dimensions
    _autosize(offers)

    # --- Exceptions: what a human needs to look at before acting ---
    exceptions = workbook.create_sheet("Exceptions")
    exceptions.append(["Group", "Category", "Description", "Flag", "Detail"])
    for comp in comparisons:
        for flag in comp.flags:
            name, _, retailer = flag.partition(":")
            exceptions.append([
                comp.group.group_id, comp.group.category, comp.group.description, name,
                RETAILER_LABELS.get(retailer, retailer),
            ])
    _style_header(exceptions)
    exceptions.auto_filter.ref = exceptions.dimensions
    _autosize(exceptions)

    path.parent.mkdir(parents=True, exist_ok=True)
    workbook.save(path)
    return path
