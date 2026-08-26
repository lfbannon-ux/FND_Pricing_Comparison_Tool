"""
Canonical map: verbatim filing caption -> canonical row.

Discipline (from the brief):
  * Merge across eras/documents ONLY where the filings' own presentation proves
    definitional continuity. The annual (doc 4064735) and interim (docs 4064731/
    4064733/3693795) statements use the same captions and the same statement
    architecture, so they map onto shared canonical rows. That is the merge this
    map performs, and the caption map records every instance of it.
  * The two BASES are never merged. `basis` is a separate dimension carried all
    the way through to separate workbook blocks.
  * Section-qualified rules match before unqualified ones. Section qualification
    is load-bearing here: "Margin deposits" is BOTH a current asset and a current
    liability, and the equity statement is component x movement.
  * Five subtotal captions were not captured by the PDF extractor. They are
    matched on (section + is_subtotal) via the placeholder, never on an invented
    caption, and the canonical name records what the arithmetic proves them to be.

Rule fields:
    statement           source statement value (required)
    section             optional regex qualifying the source section
    pattern             regex matched against the verbatim line_item
    canonical_statement destination statement
    canonical_section   destination section
    canonical           destination canonical row label
    order               display order within the destination statement
    passthrough         if True, keep the verbatim caption/section/order as-is
"""

P = r"\[unlabelled subtotal row\]"
U = r"\[uncaptioned total row\]"

RULES: list[dict] = []


def R(statement, pattern, canonical, section=None, canon_stmt=None,
      canon_sec="", order=0):
    RULES.append({
        "statement": statement, "section": section, "pattern": pattern,
        "canonical_statement": canon_stmt or statement,
        "canonical_section": canon_sec, "canonical": canonical, "order": order,
    })


# ---------------------------------------------------------------- income statement
R("income_statement", r"^Fee-for-Service revenue$",        "Fee-for-Service revenue",        canon_sec="Revenues", order=10)
R("income_statement", r"^Optimization, net$",              "Optimization, net",              canon_sec="Revenues", order=20)
R("income_statement", r"^Total revenues$",                 "Total revenues",                 canon_sec="Revenues", order=30)
R("income_statement", r"^Cost of gas storage services$",   "Cost of gas storage services",   canon_sec="Expenses (income)", order=40)
R("income_statement", r"^Operating$",                      "Operating",                      canon_sec="Expenses (income)", order=50)
R("income_statement", r"^General and administrative$",     "General and administrative",     canon_sec="Expenses (income)", order=60)
R("income_statement", r"^Depreciation and amortization$",  "Depreciation and amortization",  canon_sec="Expenses (income)", order=70)
R("income_statement", r"^Financing costs$",                "Financing costs",                canon_sec="Expenses (income)", order=80)
R("income_statement", r"gas storage obligations",          "Gain on gas storage obligations, net", canon_sec="Expenses (income)", order=90)
R("income_statement", r"^Other expenses$",                 "Other expenses",                 canon_sec="Expenses (income)", order=100)
# subtotal caption absent from the extracted text; proven by 479.4 - 255.9 = 223.5
R("income_statement", P, "Total expenses (income)", section=r"EXPENSES", canon_sec="Expenses (income)", order=110)
R("income_statement", r"EARNINGS BEFORE INCOME TAXES",     "Earnings before income taxes",   canon_sec="Earnings", order=120)
R("income_statement", r"^Current$",  "Income tax expense (benefit) - current",  section=r"Income tax", canon_sec="Income tax", order=130)
R("income_statement", r"^Deferred$", "Income tax expense (benefit) - deferred", section=r"Income tax", canon_sec="Income tax", order=140)
R("income_statement", P, "Total income tax expense (benefit)", section=r"Income tax", canon_sec="Income tax", order=150)
R("income_statement", r"^NET EARNINGS$", "Net earnings", canon_sec="Earnings", order=160)

# -------------------------------------------------------- comprehensive income
R("comprehensive_income", r"[Ff]oreign currency translation", "Foreign currency translation adjustment", canon_sec="Other comprehensive income (loss)", order=10)
R("comprehensive_income", r"NET EARNINGS AND COMPREHENSIVE", "Net earnings and comprehensive earnings", canon_sec="Other comprehensive income (loss)", order=20)

# ------------------------------------------------------------------ balance sheet
BS_CA = r"Current Assets"
BS_LA = r"Long-term Assets"
BS_CL = r"Current Liabilities"
BS_LL = r"Long-term Liabilities"
R("balance_sheet", r"^Cash and cash equivalents$",   "Cash and cash equivalents",   section=BS_CA, canon_sec="Current assets", order=10)
R("balance_sheet", r"Trade and accrued receivables", "Trade and accrued receivables", section=BS_CA, canon_sec="Current assets", order=20)
R("balance_sheet", r"Natural gas inventory",         "Natural gas inventory",       section=BS_CA, canon_sec="Current assets", order=30)
R("balance_sheet", r"Short-term risk management assets", "Short-term risk management assets", section=BS_CA, canon_sec="Current assets", order=40)
R("balance_sheet", r"^Margin deposits$",             "Margin deposits (asset)",     section=BS_CA, canon_sec="Current assets", order=50)
R("balance_sheet", r"Prepaid expenses",              "Prepaid expenses and other current assets", section=BS_CA, canon_sec="Current assets", order=60)
R("balance_sheet", r"Due from affiliates",           "Due from affiliates",         section=BS_CA, canon_sec="Current assets", order=70)
R("balance_sheet", P, "Total current assets", section=BS_CA, canon_sec="Current assets", order=80)
R("balance_sheet", r"Property, plant and equipment", "Property, plant and equipment, net", section=BS_LA, canon_sec="Long-term assets", order=90)
R("balance_sheet", r"^Goodwill$",                    "Goodwill",                    section=BS_LA, canon_sec="Long-term assets", order=100)
R("balance_sheet", r"Long-term risk management assets", "Long-term risk management assets", section=BS_LA, canon_sec="Long-term assets", order=110)
R("balance_sheet", r"^Other assets$",                "Other assets",                section=BS_LA, canon_sec="Long-term assets", order=120)
R("balance_sheet", P, "Total long-term assets", section=BS_LA, canon_sec="Long-term assets", order=130)
R("balance_sheet", r"Trade payables and accrued liabilities", "Trade payables and accrued liabilities", section=BS_CL, canon_sec="Current liabilities", order=140)
R("balance_sheet", r"^Short-term debt$",             "Short-term debt",             section=BS_CL, canon_sec="Current liabilities", order=150)
R("balance_sheet", r"Short-term risk management liabilities", "Short-term risk management liabilities", section=BS_CL, canon_sec="Current liabilities", order=160)
R("balance_sheet", r"Short-term lease liabilities",  "Short-term lease liabilities", section=BS_CL, canon_sec="Current liabilities", order=170)
R("balance_sheet", r"Short-term gas storage obligations", "Short-term gas storage obligations", section=BS_CL, canon_sec="Current liabilities", order=180)
R("balance_sheet", r"^Margin deposits$",             "Margin deposits (liability)", section=BS_CL, canon_sec="Current liabilities", order=190)
R("balance_sheet", r"^Deferred revenue$",            "Deferred revenue",            section=BS_CL, canon_sec="Current liabilities", order=200)
R("balance_sheet", P, "Total current liabilities", section=BS_CL, canon_sec="Current liabilities", order=205)
R("balance_sheet", r"^Long-term debt$",              "Long-term debt",              section=BS_LL, canon_sec="Long-term liabilities", order=210)
R("balance_sheet", r"Long-term risk management liabilities", "Long-term risk management liabilities", section=BS_LL, canon_sec="Long-term liabilities", order=220)
R("balance_sheet", r"Long-term lease liabilities",   "Long-term lease liabilities", section=BS_LL, canon_sec="Long-term liabilities", order=230)
R("balance_sheet", r"Long-term gas storage obligations", "Long-term gas storage obligations", section=BS_LL, canon_sec="Long-term liabilities", order=240)
R("balance_sheet", r"Decommissioning obligations",   "Decommissioning obligations", section=BS_LL, canon_sec="Long-term liabilities", order=250)
R("balance_sheet", r"Other long-term liabilities",   "Other long-term liabilities", section=BS_LL, canon_sec="Long-term liabilities", order=260)
R("balance_sheet", r"Deferred income taxes",         "Deferred income taxes",       section=BS_LL, canon_sec="Long-term liabilities", order=270)
R("balance_sheet", P, "Total long-term liabilities", section=BS_LL, canon_sec="Long-term liabilities", order=280)
R("balance_sheet", r"Owners' Equity",                "Owners' equity (deficiency)", section=r"OWNERS", canon_sec="Equity", order=290)
R("balance_sheet", r"^TOTAL$",                       "Total liabilities and owners' equity", section=r"OWNERS", canon_sec="Equity", order=300)

# -------------------------------------------------------------------- cash flow
CF_OP = r"OPERATING ACTIVITIES"
CF_ADJ = r"Adjustments"
R("cash_flow", r"^Net earnings$", "Net earnings", section=CF_OP, canon_sec="Operating activities", order=10)
R("cash_flow", r"Deferred income tax", "Deferred income tax expense (benefit)", section=CF_ADJ, canon_sec="Operating activities", order=20)
R("cash_flow", r"Unrealized risk management", "Unrealized risk management (gains) losses", section=CF_ADJ, canon_sec="Operating activities", order=30)
R("cash_flow", r"Depreciation and amortization", "Depreciation and amortization", section=CF_ADJ, canon_sec="Operating activities", order=40)
R("cash_flow", r"Amortization of deferred financing", "Amortization of deferred financing costs", section=CF_ADJ, canon_sec="Operating activities", order=50)
R("cash_flow", r"^Other$", "Other", section=CF_ADJ, canon_sec="Operating activities", order=60)
R("cash_flow", r"non-cash working capital", "Changes in non-cash working capital", section=CF_ADJ, canon_sec="Operating activities", order=70)
R("cash_flow", r"^Net cash (provided by|used in) operating activities", "Net cash provided by operating activities", section=CF_OP, canon_sec="Operating activities", order=80)
R("cash_flow", r"Property, plant and equipment expenditures", "Property, plant and equipment expenditures", canon_sec="Investing activities", order=90)
R("cash_flow", r"^Net cash (used in|provided by) investing activities", "Net cash used in investing activities", canon_sec="Investing activities", order=100)
R("cash_flow", r"Proceeds from revolving", "Proceeds from revolving credit facilities", canon_sec="Financing activities", order=110)
R("cash_flow", r"Payments of revolving", "Payments of revolving credit facilities", canon_sec="Financing activities", order=120)
R("cash_flow", r"Proceeds from term loans", "Proceeds from term loans", canon_sec="Financing activities", order=130)
R("cash_flow", r"Payments of term loans", "Payments of term loans", canon_sec="Financing activities", order=140)
R("cash_flow", r"affiliated notes", "Proceeds from (repayments of) affiliated notes", canon_sec="Financing activities", order=150)
R("cash_flow", r"Notes extended to related parties", "Notes extended to related parties", canon_sec="Financing activities", order=160)
R("cash_flow", r"Payments of financing costs", "Payments of financing costs", canon_sec="Financing activities", order=170)
R("cash_flow", r"Payments of lease liabilities", "Payments of lease liabilities", canon_sec="Financing activities", order=180)
R("cash_flow", r"^Capital contributions", "Capital contributions", canon_sec="Financing activities", order=190)
R("cash_flow", r"^Distributions", "Distributions", canon_sec="Financing activities", order=200)
R("cash_flow", r"^Net cash (used in|provided by) financing activities", "Net cash used in financing activities", canon_sec="Financing activities", order=210)
R("cash_flow", r"Effect of translation", "Effect of translation on foreign currency cash and cash equivalents", canon_sec="Net change", order=220)
R("cash_flow", r"Net changes in cash", "Net changes in cash and cash equivalents", canon_sec="Net change", order=230)
R("cash_flow", r"beginning of the (year|period)", "Cash and cash equivalents, beginning of the period", canon_sec="Net change", order=240)
R("cash_flow", r"end of the (year|period)", "Cash and cash equivalents, end of the period", canon_sec="Net change", order=250)

# ------------------------------------------------------------- changes in equity
# 2-D statement: source `section` is the equity COMPONENT, `line_item` the movement.
# Component becomes the canonical section, so movements never collide across columns.
for comp_pat, comp_name, base in [
    (r"^Owners' Capital$",                 "Owners' capital", 100),
    (r"Retained Earnings",                 "Retained earnings (deficit)", 200),
    (r"Accumulated Other Comprehensive",   "Accumulated other comprehensive loss", 300),
    (r"Owners' Capital \(Deficiency\)",    "Total owners' capital (deficiency)", 400),
]:
    R("equity_changes", r"^Balance, April 1, 2024$",   "Balance, beginning",                 section=comp_pat, canon_sec=comp_name, order=base + 1)
    R("equity_changes", r"^Net earnings$",             "Net earnings",                       section=comp_pat, canon_sec=comp_name, order=base + 2)
    R("equity_changes", r"Other comprehensive loss",   "Other comprehensive income (loss)",  section=comp_pat, canon_sec=comp_name, order=base + 3)
    R("equity_changes", r"Other comprehensive income", "Other comprehensive income (loss)",  section=comp_pat, canon_sec=comp_name, order=base + 3)
    R("equity_changes", r"^Capital contributions",     "Capital contributions",              section=comp_pat, canon_sec=comp_name, order=base + 4)
    R("equity_changes", r"^Distributions",             "Distributions",                      section=comp_pat, canon_sec=comp_name, order=base + 5)
    R("equity_changes", r"Reorganization of subsidiaries", "Reorganization of subsidiaries", section=comp_pat, canon_sec=comp_name, order=base + 6)
    R("equity_changes", r"^Balance, March 31, 202\d$", "Balance, end",                       section=comp_pat, canon_sec=comp_name, order=base + 9)

# ============================================================================
# Interim-filing caption variants -> the SAME canonical rows (business_100).
# Merge justified: identical statement architecture across the annual and the
# three interim filings, and Agent E's cross-filing tie-outs prove continuity
# (6M 94.1 - Q2 45.8 = 48.3 = the Q1 comparative printed a filing later;
#  9M 182.5 - 6M 94.1 = 88.4 = the printed Q3 quarter). Every variant remains
# visible in the caption map.
# ============================================================================
V = r"\(unlabelled subtotal\)"
R("income_statement", r"^Fee for service revenue$", "Fee-for-Service revenue", canon_sec="Revenues", order=10)
R("income_statement", V, "Total expenses (income)", section=r"EXPENSES", canon_sec="Expenses (income)", order=110)
R("income_statement", V, "Total income tax expense (benefit)", section=r"Income tax", canon_sec="Income tax", order=150)
# caption refinement only: the parenthetical signals the line may be negative in a
# quarter. Same statement position, same expense-positive convention as the annual.
R("income_statement", r"^Other \(income\) expenses$", "Other expenses", canon_sec="Expenses (income)", order=100)
R("balance_sheet", V, "Total current assets",        section=BS_CA, canon_sec="Current assets", order=80)
R("balance_sheet", V, "Total long-term assets",      section=BS_LA, canon_sec="Long-term assets", order=130)
R("balance_sheet", V, "Total current liabilities",   section=BS_CL, canon_sec="Current liabilities", order=205)
R("balance_sheet", V, "Total long-term liabilities", section=BS_LL, canon_sec="Long-term liabilities", order=280)
R("balance_sheet", r"^Gas storage obligations$", "Long-term gas storage obligations", section=BS_LL, canon_sec="Long-term liabilities", order=240)
# The interim filings print a TOTAL under ASSETS that the annual does not.
R("balance_sheet", r"^TOTAL$", "Total assets", section=r"^ASSETS$", canon_sec="Long-term assets", order=135)
R("balance_sheet", r"^(Owners' )?Equity$", "Owners' equity (deficiency)", section=r"OWNERS|^$", canon_sec="Equity", order=290)
R("balance_sheet", r"^TOTAL$", "Total liabilities and owners' equity", section=r"OWNERS|^$", canon_sec="Equity", order=300)
R("cash_flow", r"^Proceeds from term loans?$", "Proceeds from term loans", canon_sec="Financing activities", order=130)
R("cash_flow", r"^Payments of term loans?$", "Payments of term loans", canon_sec="Financing activities", order=140)
R("cash_flow", r"^Payments of promissory notes$", "Payments of promissory notes", canon_sec="Financing activities", order=175)
R("cash_flow", r"^Net cash \(used in\) provided by financing activities$", "Net cash used in financing activities", canon_sec="Financing activities", order=210)

# ============================================================================
# MD&A SUMMARY blocks -> their own canonical statement, never merged with the
# audited statements. These are 5-to-7 caption management summaries and
# narrative-derived commentary; merging them onto audited rows would be an
# unproven definitional merge. Kept visible, kept separate.
# ============================================================================
for sec_pat in [r"Statements of Financial Position of the Business", r"Assets and Liabilities",
                r"Quarterly Results Summary", r"Results of Operations and Financial Results",
                r"Statements of Cash Flows Summary", r"^Net cash (used in|provided by) "]:
    for stmt in ["income_statement", "balance_sheet", "cash_flow"]:
        RULES.append({
            "statement": stmt, "section": sec_pat, "pattern": r".", "passthrough": True,
            "canonical_statement": "mdna_summary", "canonical_section": "",
            "canonical": "", "order": 0,
        })

# ============================================================================
# COMPANY-BASIS primary statements -> passthrough.
# Rationale, deliberate: the Company (Rockpoint Gas Storage Inc.) is an
# equity-method holder of a 40% interest with a completely different statement
# architecture from the Business, and it has only ONE real reporting period --
# the 246-day stub "July 28, 2025 to March 31, 2026", of which only 168 days
# (from 2025-10-15) carry economic activity. The Q2 FY2026 Company statements
# are entirely nil; Q3 FY2026 and Q1 FY2027 present none at all. With a single
# filing family and effectively one period there is no cross-era merging to do,
# and inventing canonical names would obscure the filing's own vocabulary.
# ============================================================================
for stmt in ["income_statement", "balance_sheet", "cash_flow", "comprehensive_income"]:
    RULES.append({
        "statement": stmt, "basis": "company", "section": None, "pattern": r".",
        "passthrough": True, "canonical_statement": stmt,
        "canonical_section": "", "canonical": "", "order": 0,
    })

# ============================================================================
# Changes in equity -> passthrough on BOTH bases, with the equity component
# taken from the source section and normalised through SECTION_ALIASES below.
# The statement is inherently 2-D (component x movement) and spans eight
# different balance dates across four filings; forcing canonical
# "Balance, beginning"/"Balance, end" rows across those dates would collide.
# The verbatim balance captions are period anchors and are kept as printed.
# ============================================================================
RULES.append({
    "statement": "equity_changes", "section": None, "pattern": r".", "passthrough": True,
    "canonical_statement": "equity_changes", "canonical_section": "", "canonical": "", "order": 0,
})

# ------------------------------------------------------- notes / KPI passthrough
# DELIBERATE DECISION, not a gap. These topics span a single filing family, so no
# cross-era caption merging is required or defensible; inventing canonical names
# would obscure the filing's own vocabulary. Captions pass through verbatim and
# the caption map still records every one.
for stmt in ["note_debt", "note_tax", "note_ppe", "note_segment", "note_revenue",
             "note_leases", "note_equity", "note_financial_instruments",
             "note_related_party", "note_commitments", "note_other",
             "non_ifrs", "kpi", "dividends", "share_data"]:
    RULES.append({
        "statement": stmt, "section": None, "pattern": r".", "passthrough": True,
        "canonical_statement": stmt, "canonical_section": "", "canonical": "", "order": 0,
    })

# ============================================================================
# Equity-component aliases. The four filings drift in how they label the same
# equity column; these are the SAME component, so they are normalised onto one
# canonical section name. Every verbatim variant stays in the caption map.
# ============================================================================
SECTION_ALIASES = {
    "Owners' Capital": "Owners' capital",
    "Owners' Capital [column header not recovered by extractor]": "Owners' capital",
    "Retained Earnings (Deficit)": "Retained earnings (deficit)",
    "Deficit": "Retained earnings (deficit)",
    "Accumulated Other Comprehensive Loss": "Accumulated other comprehensive loss",
    "Owners' Capital (Deficiency)": "Total owners' capital (deficiency)",
    "Owners' Deficiency": "Total owners' capital (deficiency)",
    "Total": "Total owners' capital (deficiency)",
}

# ------------------------------------------------------------------- exclusions
EXCLUDES: list[dict] = [
    {
        "statement": "balance_sheet",
        "pattern": r"^Commitments and contingencies disclosures$",
        "reason": ("Balance-sheet note-pointer line. The interim filings print this "
                   "caption between liabilities and equity as a cross-reference to the "
                   "commitments note; it carries no amount (extracted as 0 with no "
                   "printed figure) and is not an economic line item. Excluding it "
                   "keeps a phantom zero row off the balance sheet. The commitments "
                   "figures themselves are extracted under note_commitments."),
    },
]
