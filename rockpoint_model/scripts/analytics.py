#!/usr/bin/env python3
"""
Analytics & integrity-check blocks appended to each statement sheet, plus the
Key Metrics sheet.

Two hard rules from the brief are enforced here:
  * Growth is BLANK across any non-comparable boundary. Two periods are
    comparable only if they share a period_type and are ~one year apart.
    A stub period, a basis change, or a quarter-vs-year pairing yields blank.
  * Integrity checks are FORMULA rows (never hard values) so they re-evaluate
    on recalculation. They are labelled "CHECK:" so verify_workbook.py finds them.
"""
from __future__ import annotations

from datetime import date
from openpyxl.styles import Alignment, Border, Font, PatternFill, Side
from openpyxl.utils import get_column_letter

F = "Arial"
NAVY = "1F3352"
LIGHT = "DCE3ED"
RULE = "8A97AA"
BLACK = "000000"
GREEN = "007A3D"
GREY = "5A6472"
PCT_CALC = "0.0%"
MONEY = '#,##0.0;(#,##0.0);"-"'
thin = Side(style="thin", color=RULE)


def _font(color=BLACK, bold=False, italic=False, sz=10):
    return Font(name=F, size=sz, bold=bold, italic=italic, color=color)


def _iso(s: str) -> date | None:
    try:
        y, m, d = (int(x) for x in s.split("-"))
        return date(y, m, d)
    except Exception:  # noqa: BLE001
        return None


def comparable(p_prev, p_cur) -> bool:
    """True only if a growth rate between these two periods is meaningful."""
    (_, e_prev, t_prev), (_, e_cur, t_cur) = p_prev, p_cur
    if t_prev != t_cur:
        return False
    d_prev, d_cur = _iso(e_prev), _iso(e_cur)
    if not d_prev or not d_cur:
        return False
    delta = (d_cur - d_prev).days
    return 330 <= delta <= 400


def find_row(line_rows: dict[str, int], *candidates: str) -> int | None:
    """Locate a canonical line by exact match, then by case-insensitive substring."""
    for cand in candidates:
        if cand in line_rows:
            return line_rows[cand]
    low = {k.lower(): v for k, v in line_rows.items()}
    for cand in candidates:
        c = cand.lower()
        if c in low:
            return low[c]
        for k, v in low.items():
            if c in k:
                return v
    return None


def _section(ws, r: int, text: str, ncols: int) -> int:
    for c in range(1, ncols + 2):
        ws.cell(row=r, column=c).fill = PatternFill("solid", fgColor=LIGHT)
    ws.cell(row=r, column=1, value=text).font = _font(NAVY, bold=True)
    return r + 1


def _ratio_row(ws, r, label, periods, num_row, den_row, ncols, fmt=PCT_CALC):
    ws.cell(row=r, column=1, value=label).font = _font(GREY)
    ws.cell(row=r, column=1).alignment = Alignment(indent=1)
    for i in range(len(periods)):
        col = get_column_letter(2 + i)
        cell = ws.cell(row=r, column=2 + i)
        cell.value = (f'=IF(OR(NOT(ISNUMBER({col}{den_row})),{col}{den_row}=0),"",'
                      f'{col}{num_row}/{col}{den_row})')
        cell.number_format = fmt
        cell.font = _font(BLACK)          # black = in-sheet formula
    return r + 1


def _growth_row(ws, r, label, periods, src_row, ncols):
    ws.cell(row=r, column=1, value=label).font = _font(GREY)
    ws.cell(row=r, column=1).alignment = Alignment(indent=1)
    for i in range(len(periods)):
        cell = ws.cell(row=r, column=2 + i)
        if i == 0 or not comparable(periods[i - 1], periods[i]):
            cell.value = None            # blank across a non-comparable boundary
        else:
            cur, prev = get_column_letter(2 + i), get_column_letter(1 + i)
            cell.value = (f'=IF(OR(NOT(ISNUMBER({prev}{src_row})),{prev}{src_row}=0),"",'
                          f'{cur}{src_row}/{prev}{src_row}-1)')
            cell.number_format = PCT_CALC
            cell.font = _font(BLACK)
    return r + 1


def _check_row(ws, r, label, periods, formula_fn, ncols):
    """A CHECK: row. verify_workbook.py asserts every value is ~0."""
    ws.cell(row=r, column=1, value=label).font = _font(GREY, italic=True)
    ws.cell(row=r, column=1).alignment = Alignment(indent=1)
    for i in range(len(periods)):
        col = get_column_letter(2 + i)
        cell = ws.cell(row=r, column=2 + i)
        cell.value = formula_fn(col)
        cell.number_format = MONEY
        cell.font = _font(BLACK)
        cell.border = Border(top=thin)
    return r + 1


def guarded(rows_needed, expr):
    """
    Build =IF(AND(ISNUMBER(r1),ISNUMBER(r2),...),expr,"").

    A check may only assert where EVERY input is actually reported. Excel treats a
    blank cell as zero, which would otherwise turn "not reported" into a false
    failure -- e.g. the audited annual statements print no total-current-liabilities
    subtotal, so an unguarded liabilities check fails by exactly that amount.
    """
    def fn(c):
        conds = ",".join(f"ISNUMBER({c}{rw})" for rw in rows_needed)
        return f'=IF(AND({conds}),{expr(c)},"")'
    return fn


def _computed_row(ws, r, label, periods, expr_fn, ncols, fmt=MONEY, indent=1):
    """A BLACK in-sheet formula row (derived, not filed)."""
    ws.cell(row=r, column=1, value=label).font = _font(BLACK, bold=True)
    ws.cell(row=r, column=1).alignment = Alignment(indent=indent)
    for i in range(len(periods)):
        col = get_column_letter(2 + i)
        cell = ws.cell(row=r, column=2 + i, value=expr_fn(col))
        cell.number_format = fmt
        cell.font = _font(BLACK, bold=True)
        cell.border = Border(top=thin)
    return r + 1


def add_analytics_block(ws, r: int, periods: list, line_rows: dict[str, int],
                        statement: str, ncols: int,
                        cash_sheet_name: str | None = None,
                        cash_row: int | None = None,
                        bs_period_index: list | None = None,
                        sections: dict | None = None):
    """
    Append the Analytics & checks block at the foot of a statement sheet.

    Canonical row names are matched EXACTLY where possible -- the canonical layer
    controls them, so fuzzy matching would only hide a mapping change.
    """
    r += 1
    r = _section(ws, r, "Analytics & checks", ncols)
    F_ = find_row
    sections = sections or {}
    exported: dict[str, int] = {}

    if statement == "income_statement":
        rev = F_(line_rows, "Total revenues")
        exp = F_(line_rows, "Total expenses (income)")
        ebt = F_(line_rows, "Earnings before income taxes")
        tax = F_(line_rows, "Total income tax expense (benefit)")
        ni = F_(line_rows, "Net earnings")
        if rev:
            r = _growth_row(ws, r, "Revenue growth", periods, rev, ncols)
        if rev and ebt:
            r = _ratio_row(ws, r, "Pre-tax margin", periods, ebt, rev, ncols)
        if rev and ni:
            r = _ratio_row(ws, r, "Net margin", periods, ni, rev, ncols)
        if ni:
            r = _growth_row(ws, r, "Net earnings growth", periods, ni, ncols)
        if ebt and tax:
            r = _ratio_row(ws, r, "Effective tax rate", periods, tax, ebt, ncols)
        if rev and exp and ebt:
            r = _check_row(ws, r, "CHECK: total revenues less total expenses less earnings before tax",
                           periods,
                           guarded([rev, exp, ebt],
                                   lambda c: f'{c}{rev}-{c}{exp}-{c}{ebt}'), ncols)
        if ebt and tax and ni:
            r = _check_row(ws, r, "CHECK: earnings before tax less income tax less net earnings",
                           periods,
                           guarded([ebt, tax, ni],
                                   lambda c: f'{c}{ebt}-{c}{tax}-{c}{ni}'), ncols)

    elif statement == "balance_sheet":
        tca = F_(line_rows, "Total current assets")
        tla = F_(line_rows, "Total long-term assets")
        tcl = F_(line_rows, "Total current liabilities")
        # The audited annual statements print no total-current-liabilities subtotal
        # (the interim filings do). Derive it as a labelled in-sheet formula summing
        # the printed current-liability lines -- black, never blue: it is computed
        # here, not filed. Agent A independently proved 79.9 / 112.9 this way.
        cl_span = sections.get("Current liabilities")
        if cl_span:
            lo, hi = cl_span
            # Exclude the printed subtotal row itself from the SUM range, or the
            # interim periods (which DO print it) would double-count.
            if tcl is not None and lo <= tcl <= hi:
                hi = tcl - 1
            if hi >= lo:
                printed = f"{{c}}{tcl}" if tcl else None
                def _tcl_expr(c, lo=lo, hi=hi, tcl=tcl):
                    summed = f'IF(COUNT({c}{lo}:{c}{hi})=0,"",SUM({c}{lo}:{c}{hi}))'
                    if tcl:
                        # prefer the figure the filing printed; fall back to the sum
                        return f'=IF(ISNUMBER({c}{tcl}),{c}{tcl},{summed})'
                    return f'={summed}'
                tcl_row = r
                r = _computed_row(
                    ws, r,
                    "Total current liabilities (printed where given, else sum of "
                    "printed current-liability lines)",
                    periods, _tcl_expr, ncols)
                tcl = tcl_row
                # Downstream (Key Metrics) should use this row rather than the
                # printed one, since it carries a figure in every period.
                exported["Total current liabilities"] = tcl_row
        tll = F_(line_rows, "Total long-term liabilities")
        eq = F_(line_rows, "Owners' equity (deficiency)")
        tle = F_(line_rows, "Total liabilities and owners' equity")
        ta_printed = F_(line_rows, "Total assets")

        ta_row = None
        if tca and tla:
            ta_row = r
            r = _computed_row(ws, r, "Total assets (computed: current + long-term)", periods,
                              guarded([tca, tla], lambda c: f'{c}{tca}+{c}{tla}'), ncols)
        tl_row = None
        if tcl and tll:
            tl_row = r
            r = _computed_row(ws, r, "Total liabilities (computed: current + long-term)", periods,
                              guarded([tcl, tll], lambda c: f'{c}{tcl}+{c}{tll}'), ncols)

        if ta_row and tle:
            r = _check_row(ws, r, "CHECK: computed total assets less printed total liabilities and equity",
                           periods,
                           guarded([ta_row, tle], lambda c: f'{c}{ta_row}-{c}{tle}'), ncols)
        if tl_row and eq and tle:
            r = _check_row(ws, r, "CHECK: total liabilities plus equity less printed total",
                           periods,
                           guarded([tl_row, eq, tle],
                                   lambda c: f'{c}{tl_row}+{c}{eq}-{c}{tle}'), ncols)
        if ta_printed and ta_row:
            r = _check_row(ws, r, "CHECK: printed total assets less computed total assets",
                           periods,
                           guarded([ta_printed, ta_row],
                                   lambda c: f'{c}{ta_printed}-{c}{ta_row}'), ncols)
        if tca and tcl:
            r = _ratio_row(ws, r, "Current ratio", periods, tca, tcl, ncols, fmt='#,##0.00"x"')

    elif statement == "cash_flow":
        cfo = F_(line_rows, "Net cash provided by operating activities")
        cfi = F_(line_rows, "Net cash used in investing activities")
        cff = F_(line_rows, "Net cash used in financing activities")
        fx = F_(line_rows, "Effect of translation on foreign currency cash and cash equivalents")
        chg = F_(line_rows, "Net changes in cash and cash equivalents")
        opening = F_(line_rows, "Cash and cash equivalents, beginning of the period")
        closing = F_(line_rows, "Cash and cash equivalents, end of the period")
        capex = F_(line_rows, "Property, plant and equipment expenditures")

        if cfo and capex:
            r = _computed_row(ws, r, "Free cash flow (computed: CFO + PP&E expenditures)", periods,
                                            guarded([cfo, capex], lambda c: f'{c}{cfo}+{c}{capex}'), ncols)
        if cfo and cfi and cff and chg:
            fx_term = f'+{{c}}{fx}' if fx else ''
            needed = [x for x in (cfo, cfi, cff, fx, chg) if x]
            r = _check_row(
                ws, r, "CHECK: operating + investing + financing + FX less printed change in cash",
                periods,
                guarded(needed, lambda c: (f'{c}{cfo}+{c}{cfi}+{c}{cff}'
                                           + (f'+{c}{fx}' if fx else '')
                                           + f'-{c}{chg}')), ncols)
        if opening and closing and chg:
            r = _check_row(
                ws, r, "CHECK: opening cash plus change less closing cash", periods,
                guarded([opening, chg, closing],
                        lambda c: f'{c}{opening}+{c}{chg}-{c}{closing}'), ncols)
        if closing and cash_sheet_name and cash_row and bs_period_index:
            ws.cell(row=r, column=1,
                    value="CHECK: closing cash less balance-sheet cash (cross-sheet)"
                    ).font = _font(GREY, italic=True)
            ws.cell(row=r, column=1).alignment = Alignment(indent=1)
            ref = f"'{cash_sheet_name}'"
            for i in range(len(periods)):
                col = get_column_letter(2 + i)
                idx = bs_period_index[i]
                bs_col = get_column_letter(2 + idx) if idx is not None else None
                cell = ws.cell(row=r, column=2 + i)
                if bs_col is None:
                    cell.value = None
                else:
                    cell.value = (f'=IF(AND(ISNUMBER({col}{closing}),'
                                  f'ISNUMBER({ref}!{bs_col}{cash_row})),'
                                  f'{col}{closing}-{ref}!{bs_col}{cash_row},"")')
                    cell.number_format = MONEY
                    cell.font = _font(GREEN)
                cell.border = Border(top=thin)
            r += 1

    if exported:
        pass
    ws.cell(row=r, column=1,
            value="Growth is deliberately blank across any non-comparable boundary "
                  "(different period type, stub period, or basis change). "
                  "Black = formula in this sheet; green = formula linking to another sheet."
            ).font = _font(GREY, italic=True, sz=9)
    return exported
