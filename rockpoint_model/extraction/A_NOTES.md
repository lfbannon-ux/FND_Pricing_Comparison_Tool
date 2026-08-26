# Agent A — extraction notes
Scope: **primary statements only** of Quartr documentId **4064735**, "Combined Consolidated Financial Statements
For the Fiscal Year Ended March 31, 2026" (Rockpoint Gas Storage; audited by Deloitte LLP; IFRS as issued by the IASB).
Output: `A_fy2026_primary_statements.csv` — **190 rows** (excluding header).

## 1. Documents and pages actually read
- documentId **4064735**, pages **1–44 (all)**, via `mcp__Quartr__read_document`. Page 5 was read twice
  (once in an 8-page chunk, once alone) to confirm the balance-sheet cell stream is stable — it is, byte-identical.
- Rows extracted come from **pages 5, 6, 7, 8** only. Pages 9–44 were read to build `A_NOTE_INDEX.md` and to
  cross-check three primary-statement figures (see §4); no note rows were written — that is Agent B's scope.
- No other document, and no web source, was used.

## 2. Basis
`basis = business_100` on **every** row. Confirmed on p.2 (auditor's report) and p.9 (Note 1): these statements are
the combined consolidated statements of Swan OpCo + BIF OpCo and their wholly-owned subsidiaries. **No page of this
document presents Rockpoint Gas Storage Inc. (`company`) standalone figures.** Rockpoint acquired 40.0% of the
Business on 2025-10-15 (p.9, p.18) but that transaction does not change the reporting entity of this document.

## 3. Unit and column identification
- Every statement header reads "(Millions of U.S. dollars)" → `unit = usd_millions` on all 190 rows. No rescaling done.
- Column headers on pp. 5, 6, 8 are `| Notes | 2026 | 2025 |`. **First numeric column = 2026, second = 2025.**
  Proved independently, not assumed: p.8 "Cash and cash equivalents, end of the year" 42.3 / 204.1 ties to p.5
  "Cash and cash equivalents" 42.3 / 204.1, and p.8 "beginning of the year" 204.1 rolls to the prior column's 204.1.
  All five statements then foot in that orientation (§5) — they would not in the reverse orientation.
- Values printed in parentheses are recorded as negative, per SPEC §4.
- Printed dashes meaning reported-zero are recorded as `0` with `note=printed_dash_zero` (14 such cells).

## 4. Section-7 self-verification — RESULTS WITH NUMBERS
All checks were run **from the written CSV**, not from my reading notes.

### 4.1 Balance sheet foots (p.5) — PASS both dates
| | FY2026 (2026-03-31) | FY2025 (2025-03-31) |
|---|---|---|
| Current-asset items summed | 209.0 | 414.6 |
| …vs printed subtotal | **209.0 OK** | **414.6 OK** |
| Long-term-asset items summed | 1,030.7 | 1,015.6 |
| …vs printed subtotal | **1,030.7 OK** | **1,015.6 OK** |
| Total assets (209.0 + 1,030.7) | 1,239.7 | 1,430.2 |
| Current-liability items summed | 79.9 | 112.9 |
| Long-term-liability items summed vs printed subtotal | 1,398.6 vs **1,398.6 OK** | 1,403.1 vs **1,403.1 OK** |
| Owners' Equity (printed) | (238.8) | (85.8) |
| **L + E = 79.9 + 1,398.6 − 238.8** | **1,239.7** | **112.9 + 1,403.1 − 85.8 = 1,430.2** |
| vs printed "TOTAL" | **1,239.7 → FOOTS EXACTLY** | **1,430.2 → FOOTS EXACTLY** |

Discrepancy: **0.0 on both dates.**

### 4.2 Income statement ties (p.6) — PASS both years
| Check | FY2026 | FY2025 |
|---|---|---|
| Fee-for-Service + Optimization vs "Total revenues" | 388.5 + 90.9 = 479.4 vs **479.4 OK** | 366.8 + 48.5 = 415.3 vs **415.3 OK** |
| Seven expense lines vs printed expense subtotal | 255.9 vs **255.9 OK** | 216.5 vs **216.5 OK** |
| Total revenues − total expenses vs EARNINGS BEFORE INCOME TAXES | 479.4 − 255.9 = 223.5 vs **223.5 OK** | 415.3 − 216.5 = 198.8 vs **198.8 OK** |
| Current + Deferred tax vs printed tax total | 6.1 + 10.5 = 16.6 vs **16.6 OK** | 0.6 + (11.2) = (10.6) vs **(10.6) OK** |
| EBT − tax vs **NET EARNINGS** | 223.5 − 16.6 = **206.9 OK** | 198.8 − (10.6) = **209.4 OK** |
| Net earnings + OCI vs NET EARNINGS AND COMPREHENSIVE EARNINGS | 206.9 + 1.0 = **207.9 OK** | 209.4 + (1.8) = **207.6 OK** |

Discrepancy: **0.0 in every year and every subtotal.**

### 4.3 Cash flow ties and reconciles to balance-sheet cash (p.8 → p.5) — PASS both years
| Check | FY2026 | FY2025 |
|---|---|---|
| Operating items vs "Net cash provided by operating activities" | 190.1 vs **190.1 OK** | 313.7 vs **313.7 OK** |
| Investing items vs "Net cash used in investing activities" | (32.9) vs **(32.9) OK** | (34.9) vs **(34.9) OK** |
| Ten financing items vs "Net cash used in financing activities" | (319.8) vs **(319.8) OK** | (174.2) vs **(174.2) OK** |
| **Op + Inv + Fin + FX vs "Net changes in cash and cash equivalents"** | 190.1 − 32.9 − 319.8 + 0.8 = **(161.8) OK** | 313.7 − 34.9 − 174.2 − 0.6 = **104.0 OK** |
| **Opening + change vs closing** | 204.1 − 161.8 = **42.3 OK** | 100.1 + 104.0 = **204.1 OK** |
| **CF closing cash vs BS "Cash and cash equivalents"** | 42.3 vs **42.3 OK** | 204.1 vs **204.1 OK** |
| CF "Net earnings" vs IS "NET EARNINGS" | 206.9 vs **206.9 OK** | 209.4 vs **209.4 OK** |

Discrepancy: **0.0 everywhere.**

### 4.4 Statement of changes in equity (p.7) — PASS
Every one of the 11 printed rows sums across its three component columns to the printed total column
(Balance April 1 2024 250.7 + 105.6 − 20.8 = 335.5 … Balance March 31 2026 219.1 − 436.3 − 21.6 = (238.8)).
Every one of the four columns rolls forward correctly through both years:
- Owners' Capital: 250.7 → 127.0 → 219.1 **OK**
- Retained Earnings (Deficit): 105.6 → (190.2) → (436.3) **OK**
- Accumulated Other Comprehensive Loss: (20.8) → (22.6) → (21.6) **OK**
- Total: 335.5 → (85.8) → (238.8) **OK**

Cross-statement: equity-statement "Net earnings" 206.9 / 209.4 = income-statement NET EARNINGS **OK**;
equity closing totals (238.8) / (85.8) = balance-sheet "Owners' Equity" **OK**; equity OCI 1.0 / (1.8) =
comprehensive-income "Foreign currency translation adjustment" **OK**.

### 4.5 Note-table checks (out of my scope, used only to validate primary-statement transcription)
- Note 8 (p.25) lease-liability roll-forward prints "Principal repayments **(17.7) / (0.8)**" — this independently
  confirms my cash-flow column assignment for "Payments of lease liabilities" (see §6.3).
- Note 7 (p.21) prints "Total long-term debt, net $1,197.3 / $1,208.1" and "Portion classified as current, net
  (12.2) / (25.8)" — matches the balance sheet.
- Note 16 (p.29) prints "Income tax expense (benefit) $16.6 / $(10.6)" and "Earnings before income taxes
  $223.5 / $198.8" — matches the income statement.
- Note 23 (p.43) prints "Net changes in non-cash working capital $(45.6) / $71.5" — matches the cash flow statement.
- Note 20 (p.39) prints "Total revenues $479.4 / $415.3" — matches the income statement.
- Note 13 (p.27) prints Fee-for-Service $388.5 / $366.8 and Optimization, net $90.9 / $48.5 — matches.

**Nothing in my scope failed to foot. Discrepancy on every check: 0.0.**

## 5. Caption oddities, sign conventions and extraction judgment calls

### 5.1 Unlabelled subtotal rows — `line_item = "[unlabelled subtotal row]"`
The PDF-to-markdown extractor returns each statement as a flat stream of table cells. In that stream **five subtotal
rows arrive as bare number pairs with no caption cell**:

| Statement | Page | Section | FY2026 / FY2025 | What it is (proved arithmetically) |
|---|---|---|---|---|
| balance_sheet | 5 | Current Assets | 209.0 / 414.6 | total current assets |
| balance_sheet | 5 | Long-term Assets | 1,030.7 / 1,015.6 | total long-term assets |
| balance_sheet | 5 | Long-term Liabilities | 1,398.6 / 1,403.1 | total long-term liabilities |
| income_statement | 6 | EXPENSES (INCOME) | 255.9 / 216.5 | total expenses (income) |
| income_statement | 6 | Income tax expense (benefit) | 16.6 / (10.6) | total income tax expense (benefit) |

**Judgment call:** SPEC §4 requires verbatim captions and SPEC §3.2 forbids fabrication, so I did **not** invent
captions such as "Total current assets". Each row carries `line_item = [unlabelled subtotal row]`, `is_subtotal = 1`,
the correct `section`, and a `note` saying the caption was not captured by the extractor and that the row foots
exactly to the items above it. Downstream mapping should key on (`section`, `is_subtotal`), not on `line_item`.
I cannot tell from the returned text whether the underlying PDF prints a caption that the extractor dropped, or
genuinely presents these as ruled, uncaptioned subtotals. **Whoever has the PDF should confirm the five captions.**

### 5.2 Missing lines on the balance sheet — NOT extracted, deliberately blank
Two lines a reader would expect on p.5 do **not** appear anywhere in the returned cell stream:
- **a total current liabilities subtotal.** The seven current-liability items sum to 79.9 (FY2026) / 112.9 (FY2025)
  and that amount is *required* to reach the printed TOTAL, but no such number is printed in the extracted text.
  I did **not** write a derived row. Blank by design.
- **a separate "TOTAL ASSETS" line.** The only "TOTAL" caption in the stream appears at the very end of the table,
  after Owners' Equity, carrying $1,239.7 / $1,430.2. I recorded that single row once, in its printed position,
  with `section = LIABILITIES AND OWNERS' EQUITY` and a note that it also equals total assets
  (209.0 + 1,030.7 = 1,239.7; 414.6 + 1,015.6 = 1,430.2). I did not duplicate it as a total-assets row.

**Warning for the canonical layer:** SPEC §2 cites "total assets 1,030.7 from p.5". That is **not** total assets —
1,030.7 is the *long-term* asset subtotal. **Total assets at 2026-03-31 is 1,239.7** (2025-03-31: 1,430.2).
This is exactly the mis-alignment SPEC §9 warns about, and it is presumably why Quartr's standardized feed does not
foot. Any model built on 1,030.7 as total assets is wrong by 209.0.

### 5.3 Statement of changes in equity — column headers (p.7)
The extractor returned only three header cells for four numeric columns, in a shuffled order:
`Retained Earnings (Deficit)` | `Accumulated Other Comprehensive Loss` | `Owners' Capital (Deficiency)`.
I identified the columns from the row logic, not from the header order:
- **col 1** receives Capital contributions (+188.1), Distributions (−123.7 / −93.4) and Reorganization (−2.6)
  → the **Owners' Capital** column. Its header cell was **not** returned by the extractor; I used
  `section = "Owners' Capital"` and flagged this on every one of those 11 rows in the `note` column.
- **col 2** receives Net earnings → `Retained Earnings (Deficit)` (verbatim).
- **col 3** receives only OCI → `Accumulated Other Comprehensive Loss` (verbatim).
- **col 4** equals col1+col2+col3 on all 11 rows and ties to balance-sheet "Owners' Equity" → the **total** column.
  I used the extractor's third header cell verbatim, `Owners' Capital (Deficiency)`, and noted on each row that it
  is the total column (the printed header is most likely "Total Owners' Capital (Deficiency)", but I did not add
  the word "Total" since I cannot see it).
Columns are carried in the `section` field; `line_item` holds the row caption. Note the deliberate near-collision
between `section = "Owners' Capital"` (component) and `section = "Owners' Capital (Deficiency)"` (total) — read the
`note` field before mapping.

### 5.4 Period assignment on the equity statement
- `Balance, April 1, 2024` → `period_type=instant`, `period_end=2024-04-01`, `period_label=FY2025`, `is_comparative=1`.
- FY2025 movement rows (Net earnings, Other comprehensive loss, Distributions) → `FY`, `2025-03-31`, `is_comparative=1`.
- `Balance, March 31, 2025` → `instant`, `2025-03-31`, `is_comparative=1`.
- FY2026 movement rows → `FY`, `2026-03-31`, `is_comparative=0`. `Balance, March 31, 2026` → `instant`, `2026-03-31`.
`order_index` runs 1–44 in printed reading order (row-major, then column left to right).

### 5.5 Sign conventions and caption quirks recorded verbatim
- `Gain on gas storage obligations, net` is printed **inside** the expense block as (4.5) / (1.3) — an income item
  presented as a negative expense. Section header is literally `EXPENSES (INCOME)`. Recorded as −4.5 / −1.3, flagged.
- `Optimization, net` — the trailing ", net" is part of the printed caption; kept.
- `Operating` and `General and administrative` are printed as bare one-word/short captions (not "Operating expenses");
  kept verbatim.
- `Total finance costs` appears only in Note 15 (p.28); the income statement's own caption is `Financing costs`.
- Cash-flow captions `Net cash used in investing activities` and `Net cash used in financing activities` say "used in"
  in both years and are negative in both — no sign quirk.
- `Net changes in cash and cash equivalents` (plural "changes") is the printed caption; kept.
- `Cash and cash equivalents, beginning of the year` / `, end of the year` — printed with "the"; kept.
- The equity-statement rows carry their own inline note references in the caption
  (`Capital contributions (Notes 4, 21)`, `Distributions (Notes 4, 21)`, `Reorganization of subsidiaries (Note 4)`).
  These are part of the printed caption and were **not** stripped, per SPEC §4.

### 5.6 Row omitted on purpose
p.8 ends with a caption `Supplemental cash flow disclosures` followed by note reference `23` and then only padding
cells. It is a pointer to Note 23, carries no value in either period, and per SPEC §4 ("not reported at all → omit
the row entirely") no row was written.

## 6. Things that look odd but are as printed
1. **`Other expenses` jumps from 6.9 (FY2025) to 55.3 (FY2026)** — an 8x increase. Explained on p.42 (Note 21):
   $51.5 million of Brookfield "Legacy Incentive Plans" payments were made in March 2026 and "recorded to other
   expenses", funded by an offsetting $51.5 million capital contribution from Brookfield. That contribution is the
   `Capital contributions 51.5` line in FY2026 financing activities. So the p.6 expense and the p.8 financing inflow
   are two halves of the same transaction. Recorded as printed; not netted.
2. **`Payments of lease liabilities` (17.7) in FY2026 vs (0.8) in FY2025** — a 22x change on a lease portfolio that
   already existed (lease liabilities were 108.8 at 2025-03-31). This is genuinely as reported: Note 8's lease
   liability roll-forward on p.25 prints "Principal repayments (17.7) / (0.8)" for the same two years, and Note 23
   (p.43) prints "Lease cash payments 34.5 / 12.8". The FY2025 financing section foots to (174.2) only with 0.8 here.
   Recorded as printed and flagged on the row.
3. **Reclassification disclosed by the filing itself (p.41, Note 21):** *"Certain amounts previously classified in the
   statements of cash flows as notes extended to related parties were reclassified to distributions to better reflect
   the annual nature of the related transactions."* This affects the **FY2025 comparative** financing section on p.8
   (`Notes extended to related parties` (83.0) and `Distributions` (628.9)). The filing gives **no** before/after
   amounts, so I recorded the FY2025 column exactly as printed in this filing. **The FY2025 cash-flow financing lines
   in this document are therefore NOT identical to the FY2025 figures as originally reported a year earlier.** Anyone
   comparing to the FY2025 annual statements must expect a difference here.
4. **`Due from affiliates` goes 83.0 → nil.** Note 21 (p.40) explains: settled 2025-08-31 by distributing earnings in
   the form of offsetting promissory notes, and a further $106.3 million of non-cash distributions on 2026-03-31.
   Note the non-cash portion: cash-flow `Distributions` (456.9) is smaller than equity-statement `Distributions`
   (540.1) in FY2026, and the same pattern does not exist in FY2025 (both 628.9). The (540.1) − (456.9) = 83.2 gap is
   consistent with non-cash settlement, but the filing does not print a reconciliation of it, so I derived nothing.
5. **`Reorganization of subsidiaries (Note 4)` (8.9) charged directly to equity in FY2026** — a below-the-line equity
   movement with no income-statement effect. Explained across pp.18–19 (Warwick Acquisition deferred tax of $9.7m
   recognized directly in retained earnings, SIM deferred tax asset of $0.8m, $2.6m contributed-capital elimination).
6. **Decommissioning obligations**: balance sheet p.5 shows 6.4 / 5.0, but Note 11 p.26 shows "Total decommissioning
   obligations 6.4 / **5.2**" with "Portion classified as current − / (0.2)" giving "Balance, end of the year 6.4 / 5.0".
   Not a discrepancy — the 5.2 is pre-reclass. Flagged only because a naive tie-out would flag it. (Note 11 is Agent B's.)

## 7. What is NOT disclosed in my scope — deliberate blanks
- **No earnings-per-share block of any kind.** These are the combined consolidated statements of a limited
  partnership and an LLC; there are no shares of the reporting entity, so no basic EPS, no diluted EPS, no weighted
  average share count, and no per-share amounts appear on pp.5–8. Nothing was written for EPS. Any EPS figures for
  RGSI live in the `company`-basis statements (earnings release pp.8–10 per SPEC §2), not in this document.
- **No share counts and no dividends-per-share** on any primary statement. The only share-count figure anywhere in
  the document is 132,844 stock options at C$25.75 in Note 19 (p.38–39) — Agent B's scope, and it is an option count,
  not a share count. Note 12 "Share Capital" (p.27) is narrative only and prints no numbers.
- **No dividends declared or paid** line — the equity statement and cash flow use `Distributions`, not dividends.
- **No total current liabilities subtotal** and **no separate TOTAL ASSETS line** on p.5 (see §5.2).
- **No non-controlling interest** line anywhere in equity — the Business is presented at 100%.
- **No segment column detail** on the face of any statement (Note 3.i, p.17: single reportable segment).
- **No quarterly columns.** This document is annual only: FY2026 and the FY2025 comparative. Nothing Q-labelled was
  written; Q1–Q4 rows must come from other documents.
- **No `company`-basis rows at all** from this document (see §2).
- **No restatement of prior-period figures** is disclosed other than the cash-flow reclassification in §6.3; the
  filing discloses no correction of error and no change in accounting policy affecting FY2025 amounts.

## 8. Judgment calls, listed
1. Used the flat cell-stream order (not the extractor's broken markdown column alignment) to pair captions with
   values, then **validated every pairing against the statement's own printed subtotals** before writing. Every
   statement foots to 0.0, in both years, in this orientation — and would not in any other pairing.
2. Did not invent captions for the five uncaptioned subtotals (§5.1); used a bracketed placeholder plus a note.
3. Did not write a derived "total current liabilities" or "total assets" row (§5.2).
4. Identified equity columns by row logic and flagged the one column whose header the extractor did not return (§5.3).
5. Put the equity statement's column names in `section` and the row captions in `line_item` — the only way to encode a
   four-column matrix in the long schema.
6. Assigned `statement=comprehensive_income` to the two OCI lines on p.6 and `income_statement` to the rest, even
   though the filing presents them as one continuous statement. `NET EARNINGS` is written **once**, under
   `income_statement`, to avoid double-counting; `NET EARNINGS AND COMPREHENSIVE EARNINGS` sits under
   `comprehensive_income`. Both carry `source_page = 6`.
7. Treated the FY2025 column of all four statements as `is_comparative=1` throughout, including the
   `Balance, April 1, 2024` opening equity row.
