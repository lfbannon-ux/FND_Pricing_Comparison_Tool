#!/usr/bin/env python3
"""
Phase 5 -- workbook build. Everything is generated from canonical/canonical.csv
by script; no figure is ever typed by hand.

House style (from the brief):
  Arial; dark-navy title/header bands with white text; one ~50-wide label column
  plus one column per period; sections as light-filled bold rows; bold subtotals;
  no gridlines; freeze panes below the header.
  Units: USD millions. Blank = not reported. Dash = reported zero.
  Colour code: BLUE = hard input exactly as filed (never a formula)
               BLACK = formula within the sheet
               GREEN = formula linking to another sheet
"""
from __future__ import annotations

import csv
import sys
from collections import defaultdict, OrderedDict
from datetime import date
from pathlib import Path

from openpyxl import Workbook
from openpyxl.styles import Alignment, Border, Font, PatternFill, Side
from openpyxl.utils import get_column_letter

sys.path.insert(0, str(Path(__file__).resolve().parent))
from analytics import add_analytics_block, find_row  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
CANON = ROOT / "canonical"
BUILD = ROOT / "build"

NAVY = "1F3352"
LIGHT = "DCE3ED"
RULE = "8A97AA"
BLUE = "0000CC"      # hard input as filed
BLACK = "000000"     # in-sheet formula
GREEN = "007A3D"     # cross-sheet formula
GREY = "5A6472"

F = "Arial"
MONEY = '#,##0.0;(#,##0.0);"-"'
PERSHARE = '$#,##0.00;($#,##0.00);"-"'
PCT_PRINTED = '0.0"%"'      # percentages as printed in the filing
PCT_CALC = '0.0%'           # true computed ratios
NUMBER = '#,##0;(#,##0);"-"'

thin = Side(style="thin", color=RULE)


def title_font(sz=11, color="FFFFFF", bold=True):
    return Font(name=F, size=sz, bold=bold, color=color)


def body_font(color=BLACK, bold=False, italic=False, sz=10):
    return Font(name=F, size=sz, bold=bold, italic=italic, color=color)



def cell_value(raw: str, unit: str):
    """Numeric where numeric; verbatim string for text-unit facts."""
    if raw in ("", None):
        return None
    if unit == "text":
        return raw
    try:
        return float(raw)
    except (TypeError, ValueError):
        return raw


def load_canonical() -> list[dict]:
    path = CANON / "canonical.csv"
    if not path.exists():
        sys.exit(f"{path} not found -- run scripts/canonicalize.py first.")
    with path.open(newline="", encoding="utf-8") as fh:
        return list(csv.DictReader(fh))


def period_sort_key(p: tuple[str, str, str]) -> tuple:
    label, end, ptype = p
    rank = {"FY": 0, "YTD": 1, "Q": 2, "instant": 0}.get(ptype, 3)
    return (end or "9999-99-99", rank, label)


def style_sheet(ws, ncols: int) -> None:
    ws.sheet_view.showGridLines = False
    ws.column_dimensions["A"].width = 52
    for c in range(2, ncols + 2):
        ws.column_dimensions[get_column_letter(c)].width = 15


def band(ws, row: int, text: str, ncols: int, sub: str = "") -> int:
    ws.cell(row=row, column=1, value=text).font = title_font(13)
    for c in range(1, ncols + 2):
        ws.cell(row=row, column=c).fill = PatternFill("solid", fgColor=NAVY)
        ws.cell(row=row, column=c).font = title_font(13)
    ws.row_dimensions[row].height = 22
    if sub:
        ws.cell(row=row + 1, column=1, value=sub).font = body_font(GREY, italic=True, sz=9)
        return row + 2
    return row + 1


def header_row(ws, row: int, periods: list, ncols: int) -> None:
    for c in range(1, ncols + 2):
        cell = ws.cell(row=row, column=c)
        cell.fill = PatternFill("solid", fgColor=NAVY)
        cell.font = title_font(10)
        cell.border = Border(bottom=thin)
    ws.cell(row=row, column=1, value="US$ millions unless stated")
    ws.cell(row=row, column=1).alignment = Alignment(horizontal="left")
    for i, (label, end, ptype) in enumerate(periods):
        cell = ws.cell(row=row, column=2 + i, value=label)
        cell.alignment = Alignment(horizontal="right")
        cell.font = title_font(10)


def section_row(ws, row: int, text: str, ncols: int) -> None:
    for c in range(1, ncols + 2):
        ws.cell(row=row, column=c).fill = PatternFill("solid", fgColor=LIGHT)
    ws.cell(row=row, column=1, value=text).font = body_font(NAVY, bold=True)


def write_statement_sheet(wb, sheet_name: str, rows: list[dict], basis: str,
                          statement: str, subtitle: str):
    """One statement, one basis. Periods as columns, canonical rows down."""
    data = [r for r in rows if r["basis"] == basis and r["statement"] == statement]
    if not data:
        return None

    periods = sorted({(r["period_label"], r["period_end"], r["period_type"]) for r in data},
                     key=period_sort_key)
    ncols = len(periods)
    pidx = {p[0]: i for i, p in enumerate(periods)}

    ws = wb.create_sheet(sheet_name[:31])
    style_sheet(ws, ncols)

    r = band(ws, 1, f"Rockpoint Gas Storage Inc.  |  {subtitle}", ncols,
             sub=f"Basis: {basis}.  As originally reported; comparatives flagged.  "
                 f"Blank = not reported.  Dash = reported zero.")
    header_row(ws, r, periods, ncols)
    ws.freeze_panes = ws.cell(row=r + 1, column=2)
    r += 1

    # group by canonical section, preserving canonical order
    by_section: "OrderedDict[str, list]" = OrderedDict()
    for row in sorted(data, key=lambda x: int(x["order"] or 0)):
        by_section.setdefault(row["section"] or "", []).append(row)

    line_rows: dict[str, int] = {}
    section_ranges: dict[str, tuple[int, int]] = {}
    for section, srows in by_section.items():
        if section:
            section_row(ws, r, section, ncols)
            r += 1
        sec_start = r
        seen: "OrderedDict[str, list]" = OrderedDict()
        for row in srows:
            seen.setdefault(row["line"], []).append(row)
        for line, cells in seen.items():
            is_sub = any(c["is_subtotal"] == "1" for c in cells)
            lab = ws.cell(row=r, column=1, value=line)
            lab.font = body_font(bold=is_sub)
            lab.alignment = Alignment(indent=0 if is_sub else 1)
            if is_sub:
                lab.border = Border(top=thin)
            for c in cells:
                if c["period_label"] not in pidx:
                    continue
                col = 2 + pidx[c["period_label"]]
                if c["value"] in ("", None):
                    continue
                v = cell_value(c["value"], c["unit"])
                if v is None:
                    continue
                cell = ws.cell(row=r, column=col, value=v)
                unit = c["unit"]
                cell.number_format = (
                    "General" if unit == "text" else
                    PERSHARE if unit in ("usd_per_share", "cad_per_share") else
                    PCT_PRINTED if unit == "pct" else
                    NUMBER if unit in ("shares", "count") else
                    MONEY)
                # BLUE: hard input exactly as filed
                cell.font = body_font(BLUE, bold=is_sub)
                if is_sub:
                    cell.border = Border(top=thin)
                if c["is_comparative"] == "1":
                    cell.font = body_font(BLUE, bold=is_sub, italic=True)
            line_rows[line] = r
            r += 1
        if section:
            section_ranges[section] = (sec_start, r - 1)
        r += 1
    return ws, periods, line_rows, r, section_ranges


def main() -> int:
    rows = load_canonical()
    BUILD.mkdir(parents=True, exist_ok=True)
    wb = Workbook()
    wb.remove(wb.active)

    bases = sorted({r["basis"] for r in rows})
    statements = [
        ("income_statement", "Income Statement"),
        ("balance_sheet", "Balance Sheet"),
        ("cash_flow", "Cash Flow"),
        ("equity_changes", "Changes in Equity"),
        ("comprehensive_income", "Comprehensive Income"),
    ]

    # ---- Cover & Basis ----
    ws = wb.create_sheet("Cover & Basis")
    style_sheet(ws, 4)
    r = band(ws, 1, "Rockpoint Gas Storage Inc. (TSX: RGSI)", 4,
             sub="Historical financial model -- as originally reported")
    facts = [
        ("Basis of preparation", ""),
        ("Reporting framework", "IFRS Accounting Standards as issued by the IASB"),
        ("Auditor", "Deloitte LLP (Calgary) -- audit under Canadian GAAS"),
        ("Presentation currency", "US dollars (USD)"),
        ("Units in this workbook", "US$ millions unless a row states otherwise"),
        ("Fiscal year end", "31 March. FY2026 = year ended 2026-03-31."),
        ("Quarters", "Q1 = Jun-30, Q2 = Sep-30, Q3 = Dec-31, Q4 = Mar-31"),
        ("", ""),
        ("The two reporting bases -- READ BEFORE COMPARING ANY TWO FIGURES", ""),
        ("business_100",
         "The underlying gas storage Business on a 100% basis: the combined consolidated "
         "financial statements of Swan Equity Aggregator LP and BIF II CalGas (Delaware) LLC "
         "and their wholly-owned subsidiaries. This is what the audited annual statements cover."),
        ("company",
         "Rockpoint Gas Storage Inc. itself, which acquired a 40% interest in the Business from "
         "Brookfield on 2025-10-15 (IPO closing). Brookfield retains 60%. The Company held NO "
         "interest in the Business before 2025-10-15, so Company-basis figures do not exist "
         "before that date."),
        ("Why this matters",
         "The two bases are NOT comparable and are never merged onto a single row in this "
         "workbook. They are carried as parallel, separately labelled sections."),
        ("", ""),
        ("Colour legend", ""),
        ("Blue", "Hard input, exactly as filed. Never a formula."),
        ("Black", "Formula computed within the sheet."),
        ("Green", "Formula linking to another sheet."),
        ("Italic blue", "A comparative column -- reported in a later filing, not as originally reported."),
        ("", ""),
        ("Conventions", ""),
        ("Blank cell", "Not reported in that period. Deliberate; see Accounting Notes."),
        ("Dash", "Reported as zero."),
        ("Growth rates", "Suppressed across any non-comparable boundary."),
        ("", ""),
        ("Sources", ""),
        ("Channel", "Quartr MCP connector, which serves filing text with per-page deep links."),
        ("Every figure", "Carries source document id, page, and a deep link -- see Caption Map."),
        ("NOT obtained", "The supplemented PREP Prospectus dated 2025-10-08 -- the sole source of "
                         "as-originally-reported FY2023-FY2025 history. Blocked by network egress "
                         "policy. See filings/UNOBTAINED.md."),
        ("Built", date.today().isoformat()),
    ]
    for label, val in facts:
        if label and not val:
            section_row(ws, r, label, 4)
            ws.cell(row=r, column=1).font = body_font(NAVY, bold=True)
        else:
            ws.cell(row=r, column=1, value=label).font = body_font(bold=False)
            c = ws.cell(row=r, column=2, value=val)
            c.font = body_font(GREY)
            c.alignment = Alignment(wrap_text=True, vertical="top")
        r += 1
    for col in "BCD":
        ws.column_dimensions[col].width = 40

    # ---- statement sheets, one per basis ----
    # Build first, then append analytics; the cash-flow sheet needs the balance
    # sheet's cash row to exist before it can link to it.
    built: dict[tuple, dict] = {}
    for basis in bases:
        for stmt, nice in statements:
            name = f"{nice} ({'B100' if basis == 'business_100' else 'Co'})"
            res = write_statement_sheet(wb, name, rows, basis, stmt, nice)
            if res:
                ws_s, periods_s, line_rows_s, end_r, sec_ranges = res
                built[(basis, stmt)] = {
                    "ws": ws_s, "name": ws_s.title, "periods": periods_s,
                    "line_rows": line_rows_s, "end": end_r, "sections": sec_ranges,
                }

    for (basis, stmt), info in built.items():
        kwargs = {}
        if stmt == "cash_flow":
            bs = built.get((basis, "balance_sheet"))
            if bs:
                cash_row = find_row(bs["line_rows"], "Cash and cash equivalents", "Cash")
                if cash_row:
                    bs_labels = [p[0] for p in bs["periods"]]
                    kwargs = {
                        "cash_sheet_name": bs["name"],
                        "cash_row": cash_row,
                        "bs_period_index": [
                            bs_labels.index(p[0]) if p[0] in bs_labels else None
                            for p in info["periods"]
                        ],
                    }
        new_rows = add_analytics_block(info["ws"], info["end"], info["periods"],
                                       info["line_rows"], stmt, len(info["periods"]),
                                       sections=info["sections"], **kwargs)
        if new_rows:
            info["line_rows"].update(new_rows)

    # ---- note / topic sheets ----
    topic_sheets = [
        ("note_debt", "Debt Schedule"),
        ("note_tax", "Tax Reconciliation"),
        ("note_ppe", "PP&E"),
        ("note_revenue", "Revenue Detail"),
        ("note_segment", "Segments"),
        ("note_equity", "Equity Roll-Forward"),
        ("note_leases", "Leases"),
        ("note_financial_instruments", "Financial Instruments"),
        ("note_related_party", "Related Party"),
        ("note_commitments", "Commitments"),
        ("note_other", "Other Notes"),
        ("mdna_summary", "MD&A Summary"),
        ("non_ifrs", "Adjusted (Non-IFRS)"),
        ("kpi", "Operating KPIs"),
        ("dividends", "Dividends"),
        ("share_data", "Share Data"),
    ]
    for stmt, nice in topic_sheets:
        data = [r for r in rows if r["statement"] == stmt]
        if not data:
            continue
        periods = sorted({(r["period_label"], r["period_end"], r["period_type"]) for r in data},
                         key=period_sort_key)
        ncols = len(periods)
        pidx = {p[0]: i for i, p in enumerate(periods)}
        ws = wb.create_sheet(nice[:31])
        style_sheet(ws, ncols)
        rr = band(ws, 1, f"Rockpoint Gas Storage Inc.  |  {nice}", ncols,
                  sub="As reported. Bases shown as separate labelled blocks and never merged.")
        header_row(ws, rr, periods, ncols)
        ws.freeze_panes = ws.cell(row=rr + 1, column=2)
        rr += 1
        for basis in sorted({r["basis"] for r in data}):
            section_row(ws, rr, f"Basis: {basis}", ncols)
            rr += 1
            sub = [r for r in data if r["basis"] == basis]
            by_sec: "OrderedDict[str, list]" = OrderedDict()
            for row in sorted(sub, key=lambda x: int(x["order"] or 0)):
                by_sec.setdefault(row["section"] or "", []).append(row)
            for section, srows in by_sec.items():
                if section:
                    ws.cell(row=rr, column=1, value=section).font = body_font(NAVY, bold=True)
                    rr += 1
                seen: "OrderedDict[str, list]" = OrderedDict()
                for row in srows:
                    seen.setdefault(row["line"], []).append(row)
                for line, cells in seen.items():
                    is_sub = any(c["is_subtotal"] == "1" for c in cells)
                    lab = ws.cell(row=rr, column=1, value=line)
                    lab.font = body_font(bold=is_sub)
                    lab.alignment = Alignment(indent=0 if is_sub else 1)
                    for c in cells:
                        if c["period_label"] not in pidx or c["value"] in ("", None):
                            continue
                        v = cell_value(c["value"], c["unit"])
                        if v is None:
                            continue
                        cell = ws.cell(row=rr, column=2 + pidx[c["period_label"]], value=v)
                        unit = c["unit"]
                        cell.number_format = (
                            "General" if unit == "text" else
                            PERSHARE if unit in ("usd_per_share", "cad_per_share") else
                            PCT_PRINTED if unit == "pct" else
                            NUMBER if unit in ("shares", "count") else
                            '#,##0.0' if unit == "bcf" else MONEY)
                        cell.font = body_font(BLUE, bold=is_sub,
                                              italic=(c["is_comparative"] == "1"))
                    rr += 1
                rr += 1

    # ---- Accounting Notes: every structural break, one row each ----
    an_path = CANON / "accounting_notes.csv"
    if an_path.exists():
        ws = wb.create_sheet("Accounting Notes")
        ws.sheet_view.showGridLines = False
        rr = band(ws, 1, "Accounting Notes -- read before comparing any two periods", 6,
                  sub="Every structural break, restatement, definition change and genuine "
                      "non-disclosure. One row each.")
        with an_path.open(newline="", encoding="utf-8") as fh:
            rdr = csv.reader(fh)
            head = next(rdr)
            for i, h in enumerate(head):
                c = ws.cell(row=rr, column=1 + i, value=h.replace("_", " ").title())
                c.font = title_font(10)
                c.fill = PatternFill("solid", fgColor=NAVY)
                c.alignment = Alignment(vertical="center")
            ws.freeze_panes = ws.cell(row=rr + 1, column=1)
            rr += 1
            for row in rdr:
                for i, v in enumerate(row):
                    c = ws.cell(row=rr, column=1 + i, value=v)
                    c.font = body_font(sz=9, bold=(i == 0))
                    c.alignment = Alignment(wrap_text=True, vertical="top")
                ws.row_dimensions[rr].height = 58
                rr += 1
        for i, w in enumerate([7, 24, 20, 13, 72, 62, 34]):
            ws.column_dimensions[get_column_letter(1 + i)].width = w

    # ---- Key Metrics: formulas only, linking to the statement tabs (green) ----
    ismeta = built.get(("business_100", "income_statement"))
    bsmeta = built.get(("business_100", "balance_sheet"))
    cfmeta = built.get(("business_100", "cash_flow"))
    if ismeta and bsmeta and cfmeta:
        from analytics import find_row as _fr
        fy = [p for p in ismeta["periods"] if p[2] == "FY"]
        if fy:
            ws = wb.create_sheet("Key Metrics")
            style_sheet(ws, len(fy))
            rr = band(ws, 1, "Rockpoint Gas Storage Inc.  |  Key Metrics", len(fy),
                      sub="Basis: business_100, full years only. Every cell is a formula "
                          "linking to a statement tab (green). Nothing here is typed.")
            header_row(ws, rr, fy, len(fy))
            ws.freeze_panes = ws.cell(row=rr + 1, column=2)
            rr += 1

            def ref(meta, line, period_label):
                """Cross-sheet A1 reference, or None if that line/period is absent."""
                row_no = _fr(meta["line_rows"], line)
                labels = [p[0] for p in meta["periods"]]
                if row_no is None or period_label not in labels:
                    return None
                return f"'{meta['name']}'!{get_column_letter(2 + labels.index(period_label))}{row_no}"

            def metric(label, fn, fmt=MONEY, section=None):
                nonlocal rr
                if section:
                    section_row(ws, rr, section, len(fy))
                    rr += 1
                ws.cell(row=rr, column=1, value=label).font = body_font()
                ws.cell(row=rr, column=1).alignment = Alignment(indent=1)
                for i, per in enumerate(fy):
                    f = fn(per[0])
                    cell = ws.cell(row=rr, column=2 + i)
                    if f:
                        cell.value = f
                        cell.number_format = fmt
                        cell.font = body_font(GREEN)   # green = cross-sheet formula
                rr += 1

            def ratio(num, den, line, fmt=PCT_CALC, stmt_n=None, stmt_d=None, section=None):
                def fn(per):
                    a = ref(stmt_n, num, per)
                    b = ref(stmt_d, den, per)
                    return f'=IF(AND(ISNUMBER({a}),ISNUMBER({b}),{b}<>0),{a}/{b},"")' if a and b else None
                metric(line, fn, fmt, section)

            metric("Total revenues", lambda p: (lambda a: f"={a}" if a else None)(
                ref(ismeta, "Total revenues", p)), section="Scale and growth")
            def rev_growth(per):
                labels = [x[0] for x in fy]
                i = labels.index(per)
                if i == 0:
                    return None
                from analytics import comparable
                if not comparable(fy[i - 1], fy[i]):
                    return None
                a, b = ref(ismeta, "Total revenues", per), ref(ismeta, "Total revenues", labels[i - 1])
                return f'=IF(AND(ISNUMBER({a}),ISNUMBER({b}),{b}<>0),{a}/{b}-1,"")' if a and b else None
            metric("Revenue growth", rev_growth, PCT_CALC)
            metric("Net earnings", lambda p: (lambda a: f"={a}" if a else None)(
                ref(ismeta, "Net earnings", p)))

            ratio("Earnings before income taxes", "Total revenues", "Pre-tax margin",
                  stmt_n=ismeta, stmt_d=ismeta, section="Margins and returns")
            ratio("Net earnings", "Total revenues", "Net margin", stmt_n=ismeta, stmt_d=ismeta)
            ratio("Total income tax expense (benefit)", "Earnings before income taxes",
                  "Effective tax rate", stmt_n=ismeta, stmt_d=ismeta)
            ws.cell(row=rr, column=1,
                    value="Return on equity / ROIC -- deliberately not shown: owners' equity is a "
                          "DEFICIENCY ((238.8) at FY2026, (85.8) at FY2025), so equity-based "
                          "returns are meaningless. See Accounting Notes N08."
                    ).font = body_font(GREY, italic=True, sz=9)
            rr += 2

            def debt_fn(per):
                st = ref(bsmeta, "Short-term debt", per)
                lt = ref(bsmeta, "Long-term debt", per)
                return f'=IF(AND(ISNUMBER({st}),ISNUMBER({lt})),{st}+{lt},"")' if st and lt else None
            metric("Total debt", debt_fn, section="Leverage and liquidity")
            def netdebt_fn(per):
                st = ref(bsmeta, "Short-term debt", per)
                lt = ref(bsmeta, "Long-term debt", per)
                ca = ref(bsmeta, "Cash and cash equivalents", per)
                return (f'=IF(AND(ISNUMBER({st}),ISNUMBER({lt}),ISNUMBER({ca})),{st}+{lt}-{ca},"")'
                        if st and lt and ca else None)
            metric("Net debt", netdebt_fn)
            ratio("Total current assets", "Total current liabilities", "Current ratio",
                  '#,##0.00"x"', stmt_n=bsmeta, stmt_d=bsmeta)
            def cover_fn(per):
                ebt = ref(ismeta, "Earnings before income taxes", per)
                fin = ref(ismeta, "Financing costs", per)
                return (f'=IF(AND(ISNUMBER({ebt}),ISNUMBER({fin}),{fin}<>0),({ebt}+{fin})/{fin},"")'
                        if ebt and fin else None)
            metric("Interest coverage (EBT + financing costs) / financing costs", cover_fn,
                   '#,##0.00"x"')

            metric("Net cash provided by operating activities",
                   lambda p: (lambda a: f"={a}" if a else None)(
                       ref(cfmeta, "Net cash provided by operating activities", p)),
                   section="Cash generation")
            metric("Property, plant and equipment expenditures",
                   lambda p: (lambda a: f"={a}" if a else None)(
                       ref(cfmeta, "Property, plant and equipment expenditures", p)))
            def fcf_fn(per):
                o = ref(cfmeta, "Net cash provided by operating activities", per)
                cx = ref(cfmeta, "Property, plant and equipment expenditures", per)
                return f'=IF(AND(ISNUMBER({o}),ISNUMBER({cx})),{o}+{cx},"")' if o and cx else None
            metric("Free cash flow (CFO + PP&E expenditures)", fcf_fn)
            metric("Distributions", lambda p: (lambda a: f"={a}" if a else None)(
                ref(cfmeta, "Distributions", p)))

            ws.cell(row=rr + 1, column=1,
                    value="Per-share metrics are not shown on this basis: the audited Business "
                          "statements are an LP + LLC combination and print no EPS and no share "
                          "counts (Accounting Notes N19). No share split has occurred -- the "
                          "Company listed on 2025-10-15. Per-share data exists only on the "
                          "Company basis, for the 246-day stub period."
                    ).font = body_font(GREY, italic=True, sz=9)

    # ---- Caption Map: the full audit trail ----
    cm_path = CANON / "caption_map.csv"
    if cm_path.exists():
        ws = wb.create_sheet("Caption Map")
        ws.sheet_view.showGridLines = False
        r = band(ws, 1, "Caption Map -- canonical row <- verbatim caption <- period", 5,
                 sub="Every merge is visible here. This is the audit trail.")
        with cm_path.open(newline="", encoding="utf-8") as fh:
            rdr = csv.reader(fh)
            head = next(rdr)
            for i, h in enumerate(head):
                c = ws.cell(row=r, column=1 + i, value=h)
                c.font = title_font(10)
                c.fill = PatternFill("solid", fgColor=NAVY)
            ws.freeze_panes = ws.cell(row=r + 1, column=1)
            r += 1
            for row in rdr:
                for i, v in enumerate(row):
                    ws.cell(row=r, column=1 + i, value=v).font = body_font(sz=9)
                r += 1
        for i, w in enumerate([22, 38, 14, 52, 14, 12]):
            ws.column_dimensions[get_column_letter(1 + i)].width = w

    # Reading order: basis and caveats first, then the statements, then detail.
    desired = ["Cover & Basis", "Accounting Notes", "Key Metrics"]
    for i, name in enumerate(desired):
        if name in wb.sheetnames:
            wb.move_sheet(name, offset=-(wb.sheetnames.index(name) - i))
    for name in ("Caption Map",):
        if name in wb.sheetnames:
            wb.move_sheet(name, offset=len(wb.sheetnames) - 1 - wb.sheetnames.index(name))

    out = BUILD / "Rockpoint_Gas_Storage_Historical_Model.xlsx"
    wb.save(out)
    print(f"Wrote {out}")
    print(f"Sheets: {', '.join(wb.sheetnames)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
