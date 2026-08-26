# Agent E — Interim (unaudited) financial statements: extraction notes

Output: `extraction/E_interim_statements.csv` — **1,921 data rows** (plus header).

| source_doc | filing | basis | rows |
|---|---|---|---|
| 4064731 | Q2 FY2026 interim (filed 2025-11-05) | `company` | 19 |
| 4064731 | Q2 FY2026 interim | `business_100` | 669 |
| 4064733 | Q3 FY2026 interim (filed 2026-02-10) | `business_100` | 709 |
| 3693795 | Q1 FY2027 interim (filed 2026-08-05) | `business_100` | 524 |
| | | **total** | **1,921** |

---

## 1. Documents and page ranges actually read

All pages of all three documents were read in full; no read was left truncated.

**documentId 4064731 — "Q2 2026", 24 pages, read pp. 1–24.** This document physically contains **two separate
sets of financial statements**:

* **pp. 1–7 — `company` basis.** "Rockpoint Gas Storage Inc. Unaudited Financial Statements — For the Period
  Beginning July 28, 2025 and ending September 30, 2025." Statements of Financial Position (p.2), Statement of
  Net Earnings and Comprehensive Earnings (p.3), Notes 1–5 (pp. 4–7).
* **pp. 8–24 — `business_100` basis.** "Unaudited Interim Condensed Combined Consolidated Financial Statements
  For the Three and Six Months Ended September 30, 2025." Net earnings/comprehensive earnings (p.9), financial
  position (p.10), changes in owners' equity (p.11), cash flows (p.12), Notes 1–13 (pp. 13–24).

**documentId 4064733 — "Q3 2026", 18 pages, read pp. 1–18.** `business_100` **only**. Net earnings/comprehensive
earnings (p.2), financial position (p.3), changes in equity (p.4), cash flows (p.5), Notes 1–15 (pp. 6–18).

**documentId 3693795 — "Q1 2027", 16 pages, read pp. 1–16.** `business_100` **only**. Financial position (p.2),
net earnings/comprehensive earnings (p.3), changes in equity (p.4), cash flows (p.5), Notes 1–14 (pp. 6–16).

---

## 2. THE BASIS QUESTION — what each filing actually contains

This is the single most important structural finding in my scope, and it is **not** what the SPEC's default
assumption would suggest.

**Q2 FY2026 (doc 4064731) is the only interim filing in my scope that contains any `company`-basis statements —
and every single number in them is nil.**

Rockpoint Gas Storage Inc. was incorporated 2025-07-28 and, as at the 2025-09-30 balance-sheet date, had not yet
completed the IPO (closed 2025-10-15). Note 2 (p.4) states verbatim: *"Separate Statements of Changes in Owners'
Equity and Cash Flows have not been presented as there have been no activities for the Company."* The Company
balance sheet is presented **as at September 30, 2025 and July 28, 2025** and every caption prints an em-dash;
the statement of net earnings covers **the stub period beginning July 28, 2025 and ending September 30, 2025**
and likewise prints an em-dash on every line. I recorded all of these as `value = 0` with `note =
printed_dash_zero`, per SPEC §4.

So the Company basis **exists as a reporting entity from 2025-07-28** (incorporation), but carries **no assets,
no liabilities, no equity and no earnings** until the IPO/Reorganization on 2025-10-15. **Its equity-method
investment in the Business first appears after my scope window closes** (i.e. in the FY2026 annual statements
and the FY2026 earnings release, pp. 8–10, which are another agent's documents).

**Q3 FY2026 (doc 4064733) and Q1 FY2027 (doc 3693795) contain NO Company-basis statements at all.** Both are
purely the combined consolidated statements of the Business on a 100% basis. This means:

* There is **no `company`-basis interim balance sheet, income statement or cash flow statement anywhere in my
  three documents for any date after 2025-09-30.** If the model needs Company-basis interim figures for
  Q3 FY2026 or Q1 FY2027, they are not in these filings and must come from another source (earnings release /
  MD&A / annual statements). I have not invented them.
* Consequently **no growth rate of any kind can be computed on the `company` basis from my data.** The only two
  Company-basis dates I hold (2025-07-28 and 2025-09-30) are both nil, and the stub earnings period is nil.

**No Company-basis "comparative" columns exist in the ordinary sense.** In the Q2 FY2026 Company balance sheet
the second column is dated **2025-07-28 — the date of incorporation**, not a prior fiscal period. I recorded it
with `period_label = "As at Jul 28, 2025 (inception)"`, `period_end = 2025-07-28`, `is_comparative = 1`.

### Composition of "the Business" changes between filings (not a restatement of comparatives)

* **Q2 FY2026 (Note 1, p.13):** the Business = Swan OpCo, BIF OpCo, Warwick Gas Storage LP/Ltd ("WGS LP"),
  BIF II SIM Limited, SIM Energy LP, SIM Energy Limited ("SIM") and Swan Debt Aggregator LP, plus subsidiaries.
  Swan OpCo storage capacity stated as 229.0 Bcf.
* **Q3 FY2026 (Note 1, p.6):** the Business = Swan OpCo and BIF OpCo **and their wholly-owned subsidiaries**.
  WGS LP was acquired by AECO on 2025-10-14 (common control, historical book values); SIM and Swan Debt were
  acquired by Rockpoint Gas Storage Canada Ltd. and **dissolved during December 2025**. Capacity restated to
  250.5 Bcf.
* **Q1 FY2027 (Note 1, p.6):** same definition; Warwick commercially integrated into the AECO Hub 2026-06-01.

Despite the change in legal composition, **the overlapping comparative balances are identical across filings**
(Balance April 1, 2024 = $335.5m in both the Q2 and Q3 filings; Balance April 1, 2025 = $(85.8)m in all three
filings; every line of the March 31, 2025 balance sheet is identical in the Q2 and Q3 filings). **No restatement
of prior-period figures was detected.**

---

## 3. Exactly which period columns each filing presents

### documentId 4064731 — Q2 FY2026

`company` basis (pp. 2–3):

| statement | columns printed |
|---|---|
| Statements of Financial Position | As at **September 30, 2025** \| As at **July 28, 2025** (incorporation date) |
| Statement of Net Earnings and Comprehensive Earnings | one column only: **period beginning July 28, 2025 and ending September 30, 2025** (stub) |
| Changes in owners' equity / cash flows | **not presented** (Note 2: "no activities for the Company") |

`business_100` basis (pp. 9–24) — **four value columns on every period statement**:

| my `period_label` | printed heading | `period_end` | `period_type` | `is_comparative` |
|---|---|---|---|---|
| `Q2 FY2026` | Three Months Ended September 30, 2025 | 2025-09-30 | `Q` | 0 |
| `Q2 FY2025` | Three Months Ended September 30, 2024 | 2024-09-30 | `Q` | 1 |
| `6M FY2026` | Six Months Ended September 30, 2025 | 2025-09-30 | `YTD` | 0 |
| `6M FY2025` | Six Months Ended September 30, 2024 | 2024-09-30 | `YTD` | 1 |

Balance sheet: **As at September 30, 2025** \| As at March 31, 2025 (comparative).
Changes in owners' equity: two blocks — April 1, 2024 → September 30, 2024, and April 1, 2025 →
September 30, 2025.

### documentId 4064733 — Q3 FY2026 (`business_100` only)

| my `period_label` | printed heading | `period_end` | `period_type` | `is_comparative` |
|---|---|---|---|---|
| `Q3 FY2026` | Three Months Ended December 31, 2025 | 2025-12-31 | `Q` | 0 |
| `Q3 FY2025` | Three Months Ended December 31, 2024 | 2024-12-31 | `Q` | 1 |
| `9M FY2026` | Nine Months Ended December 31, 2025 | 2025-12-31 | `YTD` | 0 |
| `9M FY2025` | Nine Months Ended December 31, 2024 | 2024-12-31 | `YTD` | 1 |

Balance sheet: **As at December 31, 2025** \| As at March 31, 2025 (comparative).
Changes in equity: April 1, 2024 → December 31, 2024, and April 1, 2025 → December 31, 2025.

### documentId 3693795 — Q1 FY2027 (`business_100` only)

**Only two value columns. There is no separate YTD column, because Q1 *is* the year to date.** I have recorded
these as `period_type = Q` only; **no `YTD` rows exist for this filing**, and none should be synthesised.

| my `period_label` | printed heading | `period_end` | `period_type` | `is_comparative` |
|---|---|---|---|---|
| `Q1 FY2027` | Three Months Ended June 30, 2026 | 2026-06-30 | `Q` | 0 |
| `Q1 FY2026` | Three Months Ended June 30, 2025 | 2025-06-30 | `Q` | 1 |

Balance sheet: **As at June 30, 2026** \| As at March 31, 2026 (comparative).
Changes in equity: April 1, 2026 → June 30, 2026, and April 1, 2025 → June 30, 2025.

---

## 4. Mandatory self-verification (SPEC §7) — results with numbers

Every check below was run programmatically over the finished CSV with exact decimal arithmetic.
**All checks pass with zero difference. No filing failed to foot.** ($ millions.)

### 4.1 Balance sheet foots (total assets == total liabilities + equity)

| basis | doc | date | current + long-term assets | current + LT liabilities + equity | printed TOTAL | diff |
|---|---|---|---|---|---|---|
| `business_100` | 4064731 | 2025-09-30 | 197.5 + 1,026.1 = **1,223.6** | 85.1 + 1,394.4 + (255.9) = **1,223.6** | 1,223.6 | 0.0 |
| `business_100` | 4064731 | 2025-03-31 | 414.6 + 1,015.6 = **1,430.2** | 112.9 + 1,403.1 + (85.8) = **1,430.2** | 1,430.2 | 0.0 |
| `business_100` | 4064733 | 2025-12-31 | 296.7 + 1,031.6 = **1,328.3** | 95.4 + 1,411.4 + (178.5) = **1,328.3** | 1,328.3 | 0.0 |
| `business_100` | 4064733 | 2025-03-31 | 414.6 + 1,015.6 = **1,430.2** | 112.9 + 1,403.1 + (85.8) = **1,430.2** | 1,430.2 | 0.0 |
| `business_100` | 3693795 | 2026-06-30 | 217.1 + 1,035.7 = **1,252.8** | 68.3 + 1,396.9 + (212.4) = **1,252.8** | 1,252.8 | 0.0 |
| `business_100` | 3693795 | 2026-03-31 | 209.0 + 1,030.7 = **1,239.7** | 79.9 + 1,398.6 + (238.8) = **1,239.7** | 1,239.7 | 0.0 |
| `company` | 4064731 | 2025-09-30 | 0 + 0 = **0** | 0 + 0 = **0** | 0 (printed as "$ –") | 0.0 |
| `company` | 4064731 | 2025-07-28 | 0 + 0 = **0** | 0 + 0 = **0** | 0 (printed as "$ –") | 0.0 |

### 4.2 Income statement ties to printed net earnings

All 10 `business_100` period columns pass both tests (revenues − expenses = printed EBT; EBT − tax = printed
net earnings) with diff 0.0:

| doc | period | total revenues | total expenses | EBT | tax | NET EARNINGS | + OCI | COMPREHENSIVE |
|---|---|---|---|---|---|---|---|---|
| 4064731 | Q2 FY2026 | 103.2 | 56.5 | 46.7 | 0.9 | **45.8** | (0.8) | **45.0** |
| 4064731 | Q2 FY2025 | 83.1 | 56.4 | 26.7 | (22.0) | **48.7** | 0.4 | **49.1** |
| 4064731 | 6M FY2026 | 207.3 | 109.0 | 98.3 | 4.2 | **94.1** | 1.0 | **95.1** |
| 4064731 | 6M FY2025 | 174.8 | 100.2 | 74.6 | (19.7) | **94.3** | 0.1 | **94.4** |
| 4064733 | Q3 FY2026 | 147.2 | 48.7 | 98.5 | 10.1 | **88.4** | 0.7 | **89.1** |
| 4064733 | Q3 FY2025 | 112.4 | 50.1 | 62.3 | 4.2 | **58.1** | (1.8) | **56.3** |
| 4064733 | 9M FY2026 | 354.5 | 157.7 | 196.8 | 14.3 | **182.5** | 1.7 | **184.2** |
| 4064733 | 9M FY2025 | 287.2 | 150.3 | 136.9 | (15.5) | **152.4** | (1.7) | **150.7** |
| 3693795 | Q1 FY2027 | 92.6 | 33.6 | 59.0 | 2.5 | **56.5** | 0.4 | **56.9** |
| 3693795 | Q1 FY2026 | 104.1 | 52.5 | 51.6 | 3.3 | **48.3** | 1.8 | **50.1** |

`company` basis, stub period Jul 28 – Sep 30 2025: 0 − 0 = 0 EBT; 0 − 0 = **0 net earnings and comprehensive
earnings**. Ties (trivially).

### 4.3 Cash flow ties, and reconciles to balance-sheet cash

All 10 `business_100` period columns pass both tests with diff 0.0:

| doc | period | operating | investing | financing | FX | = change | opening | = closing |
|---|---|---|---|---|---|---|---|---|
| 4064731 | Q2 FY2026 | 56.3 | (9.8) | (36.1) | (0.2) | **10.2** | 20.3 | **30.5** |
| 4064731 | Q2 FY2025 | 55.2 | (14.7) | 10.5 | 0.5 | **51.5** | 34.0 | **85.5** |
| 4064731 | 6M FY2026 | 94.0 | (20.7) | (247.7) | 0.8 | **(173.6)** | 204.1 | **30.5** |
| 4064731 | 6M FY2025 | 165.3 | (19.4) | (160.8) | 0.3 | **(14.6)** | 100.1 | **85.5** |
| 4064733 | Q3 FY2026 | 85.0 | (7.4) | (86.0) | 0.1 | **(8.3)** | 30.5 | **22.2** |
| 4064733 | Q3 FY2025 | 75.8 | (10.5) | (5.9) | (1.1) | **58.3** | 85.5 | **143.8** |
| 4064733 | 9M FY2026 | 179.0 | (28.1) | (333.7) | 0.9 | **(181.9)** | 204.1 | **22.2** |
| 4064733 | 9M FY2025 | 241.1 | (29.9) | (166.7) | (0.8) | **43.7** | 100.1 | **143.8** |
| 3693795 | Q1 FY2027 | 70.1 | (4.3) | (38.6) | (0.4) | **26.8** | 42.3 | **69.1** |
| 3693795 | Q1 FY2026 | 37.7 | (10.9) | (211.6) | 1.0 | **(183.8)** | 204.1 | **20.3** |

`company` basis: **no statement of cash flows is presented** (Note 2, p.4). Deliberate blank — nothing extracted,
nothing invented.

### 4.4 Cross-statement reconciliations (all diff 0.0)

| check | value |
|---|---|
| 4064731 CF closing cash (Q2 and 6M) == BS cash at 2025-09-30 | 30.5 == 30.5 |
| 4064731 CF 6M opening cash == BS cash at 2025-03-31 | 204.1 == 204.1 |
| 4064733 CF closing cash (Q3 and 9M) == BS cash at 2025-12-31 | 22.2 == 22.2 |
| 4064733 CF 9M opening cash == BS cash at 2025-03-31 | 204.1 == 204.1 |
| 3693795 CF closing cash == BS cash at 2026-06-30 | 69.1 == 69.1 |
| 3693795 CF opening cash == BS cash at 2026-03-31 | 42.3 == 42.3 |
| 4064731 equity-statement closing total == BS Equity at 2025-09-30 | (255.9) == (255.9) |
| 4064733 equity-statement closing total == BS Owners' Equity at 2025-12-31 | (178.5) == (178.5) |
| 3693795 equity-statement closing total == BS Owners' Equity at 2026-06-30 | (212.4) == (212.4) |
| IS net earnings == CF net earnings == equity-statement net earnings (all 3 filings, primary period) | 94.1 / 182.5 / 56.5 |

### 4.5 Note tables foot to their own printed totals

Every note table was checked both across (components → printed Total column) and down (movements → printed
closing balance). **All pass, 0 failures.**

* **PPE roll-forward (all 3 filings):** 42 row-checks, 0 failures. Cost totals 1,161.4 → 1,186.0 (Q2 filing),
  1,161.4 → 1,189.4 (Q3 filing), 1,189.7 → 1,193.3 (Q1 FY2027 filing). Accumulated depreciation (276.8) →
  (292.3) / (298.7); (301.6) → (309.0). Net book value totals 884.6 → 893.7 / 890.7; 888.1 → 884.3 — each
  agrees to the balance-sheet PPE line.
* **Debt note (all 3 filings):** 12 checks, 0 failures. Total long-term debt, net = 1,204.0 / 1,208.1 /
  1,203.0 / 1,194.1 / 1,197.3 — each agrees to the balance sheet.
* **Lease note (all 3 filings):** 12 checks, 0 failures. Long-term lease liabilities 94.3 / 92.0 / 93.0 agree to
  the balance sheet; portion classified as current 8.0 / 8.4 / 8.5 agrees to the balance sheet.
* **Trade payables note (all 3 filings):** 12 checks, 0 failures; note Total (43.9 / 59.5 / 53.4 / 39.3 / 45.6)
  equals the balance-sheet line in every case.
* **Revenue note (all 3 filings, all 10 period columns):** 30 checks, 0 failures. Geographic components foot to
  the printed fee-revenue total, which equals the income-statement line; the optimization sub-table foots to the
  income-statement "Optimization, net".
* **Fair value — risk management assets/liabilities grid:** 30 row-checks, 0 failures; all four component rows
  agree to the corresponding balance-sheet lines at every date.
* **Fair value hierarchy (Level 1/2/3 → Total):** 59 row-checks, 0 failures. Total liabilities 1,283.0 /
  1,292.8 / 1,282.4 / 1,256.1 / 1,266.5.
* **Commitments note:** 21 row-checks plus column totals, 0 failures. Totals (143.8)/190.2/46.4 (Q2),
  (159.6)/214.0/54.4 (Q3), (99.3)/165.7/66.4 (Q1 FY2027).
* **Supplemental cash flow / non-cash working capital note (all 10 period columns):** 20 checks, 0 failures;
  each note total equals the "Changes in non-cash working capital" line on the cash flow statement.
* **Changes in equity, column arithmetic:** 24 checks (each column of each block), 0 failures; plus row footing
  (components → total column) for every row, 0 failures.

### 4.6 Additional cross-filing consistency checks I ran (not required by SPEC, all pass)

These give independent evidence that the quarter/YTD column assignment is correct and that no columns were
transposed by the PDF extractor:

| check | result |
|---|---|
| 6M FY2026 net earnings 94.1 − Q2 FY2026 45.8 = 48.3 == Q1 FY2026 net earnings printed in the Q1 FY2027 filing | **48.3 == 48.3** |
| 6M FY2026 total revenues 207.3 − Q2 FY2026 103.2 = 104.1 == Q1 FY2026 total revenues in the Q1 FY2027 filing | **104.1 == 104.1** |
| 9M FY2026 net earnings 182.5 − 6M FY2026 94.1 = 88.4 == Q3 FY2026 printed quarter | **88.4 == 88.4** |
| Q1 FY2026 closing cash (Q1 FY2027 filing) 20.3 == Q2 FY2026 opening cash (Q2 filing) | **20.3 == 20.3** |
| Sep 30 2025 BS cash 30.5 == Q3 FY2026 CF opening cash (Q3 filing) | **30.5 == 30.5** |
| 6M FY2026 non-cash WC (15.9) − Q2 FY2026 (1.0) = (14.9) == Q1 FY2026 printed in the Q1 FY2027 filing | **(14.9) == (14.9)** |

---

## 5. Caption oddities, sign conventions and footnotes

### 5.1 Unlabelled subtotal rows — recorded as `line_item = "(unlabelled subtotal)"`

Several printed subtotal rows carry **no caption at all** (a ruled total line under a block). I did **not**
invent a caption. Every such row is written as `line_item = "(unlabelled subtotal)"`, `is_subtotal = 1`, with a
`note` naming what it totals. They are:

* **Income statement** — total expenses (income) block: 56.5 / 56.4 / 109.0 / 100.2 (Q2 filing), 48.7 / 50.1 /
  157.7 / 150.3 (Q3 filing), 33.6 / 52.5 (Q1 FY2027 filing).
* **Income statement** — total income tax expense (benefit): 10.1 / 4.2 / 14.3 / (15.5) (Q3 filing); 2.5 / 3.3
  (Q1 FY2027 filing). In the Q2 FY2026 filing the tax block has only one component ("Deferred") and no subtotal
  row is printed.
* **Balance sheet** — total current assets, total long-term assets, total current liabilities, total long-term
  liabilities in **all three** filings.
* **Note "Optimization, net"** — the final total row (6.5 / 1.7 / 18.4 / 3.8 etc.) has no caption.
* **Note "Risk management assets and liabilities"** — the net total row has no caption.
* **Note "Related party transactions"** — the transactions-table total row has no caption.

### 5.2 Income tax presentation

In the Q2 FY2026 filing the tax block prints as a sub-heading **"Income tax expense (benefit)"** with a single
line **"Deferred"**. The PDF extractor merged the two into one string. I recorded `section = "Income tax expense
(benefit)"`, `line_item = "Deferred"`, with a note. In the Q3 filing the block has **Current** and **Deferred**
plus an unlabelled subtotal; in the Q1 FY2027 filing the heading is renamed **"Income tax expense"** (no
"(benefit)") and again has Current + Deferred + unlabelled subtotal.

### 5.3 Total-assets caption in the Q2 FY2026 filing

In the Q3 FY2026 and Q1 FY2027 filings the balance sheet prints **TOTAL twice** — once for assets and once for
liabilities and owners' equity. In the Q2 FY2026 filing the extractor returned only **one** TOTAL row
(1,223.6 / 1,430.2), positioned after Equity, i.e. the liabilities-and-equity total. I recorded that one row and
did **not** create a second "total assets" row for that filing. Arithmetically the printed long-term-assets
subtotal (1,026.1) plus current assets (197.5) equals 1,223.6, so the balance sheet foots regardless; but I have
not asserted a caption I could not see.

### 5.4 Headers dropped by the PDF extractor — flagged, not guessed

The Quartr PDF extractor consistently drops the **first** header cell of wide tables. Where I could not recover a
column caption, I labelled the column so the gap is visible rather than papering over it:

* **Statements of changes in equity, column 1, all three filings.** Printed header returned as
  "Retained Earnings (Deficit) | Accumulated Other Comprehensive Loss | Owners' Capital (Deficiency)" for a
  four-column table (Q2/Q3), and "Deficit | Accumulated Other Comprehensive Loss | Owners' Deficiency" (Q1
  FY2027). Column 1 is the capital account (it receives "Capital contributions", "Share-based compensation" and
  part of the Warwick distribution, and April 1, 2024 250.7 + 105.6 − 20.8 = 335.5 confirms the ordering).
  Recorded as `section = "Owners' Capital [column header not recovered by extractor]"` with a note on every row.
* **Commitments note, column 1, all three filings.** Header returned as "Unconditional sales obligations | Net |
  For the fiscal year ending:" for a three-column table. Column 1 is the purchase-obligation column: it is
  printed negative and column 1 + column 2 = column 3 on every row and on the total. Narrative on the following
  page confirms *"Purchase obligations consist of forward physical commitments…"*. Recorded as
  `"(column 1 - header not recovered by extractor; purchase obligations)"` with a note.
* **RSU/PSU continuity table, Q1 FY2027 p.13, column 1.** Header returned as "Performance Share Units" only.
  Column 1 is RSUs: the note narrative states 84,951 + 54,246 = **139,197** RSUs, matching column 1 exactly.
  Recorded as `"Restricted Share Units [column header not recovered by extractor]"` with a note.
* **Balance-sheet section heading "LIABILITIES AND OWNERS' EQUITY" in the Q1 FY2027 filing** was not returned.
  The Owners' Equity and closing TOTAL rows carry `section = ""` and a note. (The Q2 and Q3 filings did return
  this heading and it is recorded verbatim there.)
* **Q1 FY2027 Note 9, the "Balance, March 31, 2026" risk-management block (p.11)** was returned by the extractor
  as **loose text lines rather than a table**. I reassembled it (Energy 24.0 / 11.2 / (13.0) / (4.1) / 18.1;
  Currency 0.5 / – / – / – / 0.5; Interest Rate 3.1 / 8.0 / – / – / 11.1; Total 27.6 / 19.2 / (13.0) / (4.1) /
  29.7) and confirmed it against both the March 31, 2026 balance sheet (27.6, 19.2, 13.0, 4.1 — exact) and the
  row and column totals. Every row from that block carries a note recording the reconstruction.

### 5.5 Caption changes between filings (recorded verbatim as printed, with notes)

| Q2 FY2026 caption | Q3 FY2026 caption | Q1 FY2027 caption |
|---|---|---|
| Fee for service revenue | Fee for service revenue | **Fee-for-Service revenue** |
| Gain on gas storage obligations, net | **(Gain) loss on gas storage obligations, net** | Gain on gas storage obligations, net |
| Other expenses | **Other (income) expenses** | Other expenses |
| Equity (balance sheet) | **Owners' Equity** | Owners' Equity |
| Gas storage obligations (long-term only) | **Short-term** / **Long-term gas storage obligations** | Short-term / Long-term gas storage obligations |
| Accrued interest, non-affiliated debt | **Accrued interest** | Accrued interest |
| — | **Current income taxes payable** (new line) | Current income taxes payable |
| Payments of promissory notes (CF) | **Proceeds from (repayments of) affiliated notes** | — (line not presented) |
| Notes extended to related parties (CF) | Notes extended to related parties | **Advances and notes extended to related parties** |
| Payments of term loans (CF) | Payments of term loans | **Payments of term loan** (singular) |
| Lease additions, remeasurements and modifications | Lease additions, remeasurements and modifications | **Lease additions and remeasurements** |
| Tax paid (supplemental CF) | Tax paid | **Income tax cash payments** |
| Take-or-pay contract revenue / Short-term storage service revenue | same | **Take-or-Pay** / **Short-term Storage** (capitalised) |
| Statements of Changes in **Owners' Equity** | Statements of Changes in **Equity** | Statements of Changes in Equity |
| Retained Earnings (Deficit) column | Retained Earnings (Deficit) | **Deficit** |
| Owners' Capital (Deficiency) total column | Owners' Capital (Deficiency) | **Owners' Deficiency** |

Also: the Q2 FY2026 income statement heading reads "OTHER COMPREHENSIVE **(LOSS) INCOME**, NET OF TAX"; Q3 reads
"OTHER COMPREHENSIVE **INCOME (LOSS)**, NET OF TAX"; Q1 FY2027 reads "OTHER COMPREHENSIVE **INCOME**, NET OF
TAX". Recorded as printed.

### 5.6 Sign conventions applied

* Parentheses → negative, everywhere, exactly as printed. No sign was "corrected".
* Expenses in the **EXPENSES (INCOME)** block are printed **positive**; income items inside that block (the gas
  storage obligations gain) print in parentheses and are recorded negative. The block subtotal is therefore a
  positive expense figure that is **subtracted** from total revenues to reach EBT.
* Accumulated depreciation in the PPE note is printed in parentheses → negative.
* Equity deficits, distributions and cash outflows are printed in parentheses → negative.
* Commitments note column 1 (purchase obligations) is printed in parentheses → negative.
* Q1 FY2027 related-party note: **"Management fees recovery (general and administrative)"** prints **(0.2)** —
  a credit. Its table total prints "$ –" (recorded 0 with `printed_dash_zero`), because (0.2) + 0.2 = 0.
* Every em-dash / "–" meaning reported nil is recorded as `value = 0` with `note = printed_dash_zero`.

### 5.7 Two non-USD / non-millions units in the data

The share-option notes print per-share amounts in **both U.S. dollars and Canadian dollars**, and share/unit
counts. Units used:

* `usd_millions` — 1,894 rows (everything on the primary statements and almost all notes).
* `count` — 15 rows (option counts, RSU/PSU counts, weighted average remaining life in years).
* `usd_per_share` — 6 rows.
* **`cad_per_share` — 6 rows. This value is NOT in the SPEC §5 unit enumeration.** I used it deliberately rather
  than mislabel a Canadian-dollar exercise price as `usd_per_share`. **The canonical layer must add
  `cad_per_share` to the enum, or these six rows will fail validation.** Affected rows: doc 4064733 p.15 and doc
  3693795 p.12, section `Share option continuity | Weighted Average Exercise Price C$` /
  `... Canadian Dollars`.
* The "Weighted Average Remaining Life (years)" figure (9.9) is carried as `count`; there is no `years` unit in
  the enum. Flagged here.

---

## 6. Restatements, reclassifications and reorganizations disclosed by the filings themselves

1. **Q3 FY2026 Note 4 (p.8) — Warwick Acquisition.** On 2025-10-14 AECO paid BAIF $135.6m for 100% of WGS LP,
   funded by an affiliate loan. Treated as an **in-substance distribution**: **$93.4m as return of capital** and
   **$42.2m against retained earnings**. Common-control acquisition — assets and liabilities transferred at
   **historical book values**. A **deferred tax liability of $9.7m was recognized directly in retained
   earnings**. A $1.0m capital contribution of security-deposit interests was made in September 2025 (this is
   the "Capital contributions 1.0" line in the Q2 FY2026 equity statement).
2. **Q3 FY2026 Note 4 — SIM / Swan Debt reorganization.** Amounts paid to Brookfield classified as
   **distributions**; **$2.6m of previously disclosed contributed capital was eliminated with an equivalent
   positive offset directly to retained earnings**; a **$0.8m deferred tax asset recognized directly in retained
   earnings**. This is the equity-statement line **"Reorganization of subsidiaries (Note 4)": (2.6) / (6.3) /
   (8.9)**. SIM, Swan Debt Aggregator LP and Rockpoint Canada Inc. were **dissolved during December 2025**.
3. **Cash flow presentation change, Q3 FY2026 onward — comparative re-presented.** The Q2 FY2026 filing shows no
   "Amortization of deferred financing costs" line at all (it sat inside "Other": 6M FY2026 Other = 2.4, 6M
   FY2025 Other = 4.6). From Q3 FY2026 the line is **disaggregated in both the current and the comparative
   column** (9M FY2026: 4.8 amortization + 0.8 Other; 9M FY2025: 5.8 + 0.9). The Q1 FY2027 filing does the same
   for the Q1 FY2026 comparative (1.1 + (0.3)). **The filings do not label this a reclassification**; I flag it
   because a naive quarter-on-quarter comparison of the "Other" line across my three documents is not
   like-for-like. Every affected row carries a note.
4. **Balance sheet, Q3 FY2026 onward:** gas storage obligations split into short-term and long-term. The
   March 31, 2025 comparative shows short-term "–" and long-term 17.4, consistent with the single 17.4 long-term
   line shown in the Q2 FY2026 filing. Non-substantive.
5. **Balance sheet, Q1 FY2027:** the "Due from affiliates" current asset and the "Margin deposits" current
   liability are no longer presented as separate lines (both zero / immaterial at both dates presented).
6. **Q3 FY2026 Note 3 (p.7):** share-based compensation policy adopted for the first time during the three
   months ended December 31, 2025 (PSUs, RSUs, stock options).
7. **Q1 FY2027 Note 3 (p.6):** amendments to IFRS 9 / IFRS 7 adopted — **no material impact**.
8. **Q1 FY2027 share-option opening balance.** The same 132,844 options at C$25.75 are shown at a USD weighted
   average exercise price of **$18.37 at Dec 31, 2025** (Q3 filing) and **$18.12 at Apr 1, 2026** (Q1 FY2027
   filing). This is **FX retranslation of an unchanged C$ price, not a restatement**. Both figures are recorded
   as printed in their own filings.
9. **No restatement of any comparative income-statement, balance-sheet or equity figure was found.** All
   overlapping comparatives agree exactly across filings (see §4.6).

**Subsequent events disclosed (narrative only, no table — not extracted as rows):** Q2 filing Note 13 — IPO
close 2025-10-15 (32,000,000 Class A Shares at C$22.00 / $15.77, gross C$704.0m / $504.6m; over-allotment
4,800,000 shares C$105.6m / $75.7m sold by Brookfield; 79,800,000 Class B Shares issued; 40% interest acquired
for ~$838.8m / C$1,170.4m; 133,000,000 total shares outstanding), new $350.0m Revolving Credit Facility, Term
Loan due 2031 repricing and rehedging. Q3 filing Note 15 — legacy incentive plan partial payment expected to be
**$39.4 million**, funded by Brookfield, to be expensed in the Business when recognized. Q1 FY2027 Note 14 —
**$8.6 million** cash distribution paid 2026-07-02.

---

## 7. What is NOT disclosed in my scope — explicit list of deliberate blanks

Nothing below was estimated, derived or back-solved. Each is genuinely absent from my three documents.

1. **`company`-basis interim statements for Q3 FY2026 and Q1 FY2027 — entirely absent.** Neither doc 4064733 nor
   doc 3693795 contains any Rockpoint Gas Storage Inc. standalone statement.
2. **`company`-basis statement of changes in owners' equity and statement of cash flows for Q2 FY2026 —
   not presented**, explicitly (Note 2, p.4: "no activities for the Company").
3. **`company`-basis equity subtotal row (Q2 FY2026, p.2).** The extractor's output for the Company balance
   sheet is ambiguous as to whether a total-equity line is printed between "Retained earnings" and the closing
   "TOTAL". I recorded Share capital, Retained earnings and TOTAL, and **omitted the possible intermediate
   subtotal** rather than assert a row I cannot prove. All values there are nil, so no figure is lost.
4. **No EPS / earnings-per-share block anywhere in my three documents**, on either basis. The Business is not a
   share-issuing entity, and the Company stub statements show nil earnings and present no per-share data.
5. **No weighted-average share count** on any primary statement in my scope. (Share counts appear only in the
   Q2 filing's subsequent-events narrative and in the option/RSU notes.)
6. **No dividends and no dividends-per-share disclosure** in any of the three filings. Distributions to owners
   are made on the `business_100` basis only, and are presented as an equity movement and a financing cash flow,
   not as a per-share dividend.
7. **No segment note** in any of the three filings. Revenue is disaggregated by geography (U.S. / Canada) and by
   revenue type only.
8. **No income tax rate reconciliation** in any interim filing (condensed disclosure).
9. **No goodwill impairment test disclosure**; goodwill is carried flat at 117.2 at every date.
10. **No right-of-use asset roll-forward table.** ROU assets are embedded in the "Land and storage formations"
    PPE column; only narrative amounts of ROU depreciation are given (Q2: $1.0m / $1.9m; Q3: $1.0m / $2.9m;
    Q1 FY2027: $1.0m).
11. **No Bcf / operational capacity table.** Capacity figures (229.0 → 250.5 Bcf Swan OpCo; 28.7 Bcf BIF OpCo;
    21.5 Bcf WGS LP) appear in Note 1 narrative only, not in a table, and are outside "primary statements and
    note tables". Not extracted.
12. **No non-IFRS measures, no KPI table, no Adjusted EBITDA** in any of the three financial-statement
    documents. Those live in the MD&A / earnings release, which is not my scope. Nothing was written to
    `non_ifrs` or `kpi`.
13. **No decommissioning-obligation roll-forward table** (balance-sheet line only).
14. **No PSU/RSU fair value or Black-Scholes input table** in the Q1 FY2027 filing; only unit counts.
15. **Q1 FY2027 has no YTD column** and none was created. See §3.
16. **No `business_100` balance sheet as at 2025-06-30 or 2024-06-30.** Q1 FY2027's comparative balance-sheet
    date is 2026-03-31, not 2025-06-30. The only 2025-06-30 figures I hold are the two equity-statement closing
    balances (127.0 / (324.7) / (20.8) / (218.5)).

---

## 8. Judgment calls made, and why

1. **`statement` split between `income_statement` and `comprehensive_income`.** The filings present a single
   combined "Statement of Net Earnings and Comprehensive Earnings". I assigned everything through **NET
   EARNINGS** to `income_statement`, and the OCI section plus **NET EARNINGS AND COMPREHENSIVE EARNINGS** to
   `comprehensive_income`, so the canonical layer can pick up either cleanly. The `order_index` runs continuously
   across the two so the printed layout is preserved.
2. **Multi-column note and equity tables encoded via `section`.** The schema has one `value` per row and no
   column field. For grid tables (PPE by asset class, equity by component, fair value by contract type and by
   level, commitments by obligation type, option tables) I put the **column caption into `section`**, pipe-
   separated after the block name — e.g. `Cost | Wells`, `Fair value hierarchy | Liabilities | Level 2`,
   `Risk management assets and liabilities | Energy Contracts`. The row caption stays in `line_item`. This is
   lossless and machine-splittable on `" | "`.
3. **`period_type` for the Company stub period.** "Period beginning July 28, 2025 and ending September 30, 2025"
   is a cumulative since-inception period inside FY2026, not a three-month quarter. I used `YTD` with
   `period_label = "Jul 28 - Sep 30, 2025 (stub)"` and a note recording the stub. It is **not** labelled
   `Q2 FY2026` precisely so that it can never be silently netted against a Business-basis quarter.
4. **Equity-statement movement rows carry the movement period; balance rows carry the instant.** e.g. in the Q3
   filing "Net earnings" is `9M FY2026 / 2025-12-31 / YTD`, while "Balance, April 1, 2025" is
   `As at Apr 1, 2025 / 2025-04-01 / instant`. Opening-balance rows are marked `is_comparative = 1` (they are a
   prior-date carry-forward, not the reporting date).
5. **`is_comparative` on prior-fiscal-year blocks of the equity statement.** The entire April 2024 → September/
   December 2024 block, and (in the Q1 FY2027 filing) the entire April 2025 → June 2025 block, are marked
   `is_comparative = 1`.
6. **Comparative balance-sheet columns marked `is_comparative = 1`** in every filing (March 31, 2025 in the Q2
   and Q3 filings; March 31, 2026 in the Q1 FY2027 filing), since the filing's primary date is the quarter end.
7. **`(unlabelled subtotal)` rather than an invented caption**, and `[column header not recovered by extractor]`
   rather than an invented column name — see §5.1 and §5.4. The alternative (writing "Total expenses" where the
   filing prints nothing) would have been a fabrication.
8. **`cad_per_share` used outside the SPEC enum** — see §5.7. Mislabelling a C$ price as USD would corrupt the
   data; flagging an enum gap does not.
9. **Cross-reference lines kept.** "Commitments and contingencies disclosures — note 11/13/12 —" prints an
   em-dash in both columns in all three filings. I recorded it (value 0, `printed_dash_zero`) with a note
   identifying it as a note cross-reference rather than a real zero balance, so the canonical layer can drop it.
10. **Narrative-only figures were not extracted as rows.** Weighted-average interest rates, letters of credit
    outstanding, borrowing-base collateral, covenant ratios, IPO pricing, the $39.4m legacy-incentive amount and
    the $8.6m July 2026 distribution appear in note prose, not in tables. They are recorded here in §6 for the
    record but are not CSV rows, since SPEC §6 scopes note extraction to tables.
