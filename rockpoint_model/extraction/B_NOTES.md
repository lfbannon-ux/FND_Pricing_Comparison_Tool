# Agent B — Extraction Notes
**Scope:** Notes to the financial statements only (Agent A holds the primary statements).
**Document:** Quartr documentId **4064735** — "Combined Consolidated Financial Statements For the Fiscal Year Ended March 31, 2026", 44 pages, Rockpoint Gas Storage (companyId 21558, eventId 554427).
**Basis:** `business_100` on every row — combined consolidated FS of Swan Equity Aggregator LP ("Swan OpCo") and BIF II CalGas (Delaware) LLC ("BIF OpCo") and their wholly-owned subsidiaries. No page in this document presents `company`-basis figures.
**Unit:** "Millions of U.S. dollars, unless otherwise noted" is printed on every notes page → `usd_millions` unless the caption itself states otherwise.
**Auditor:** Deloitte LLP, Calgary. Report dated **May 27, 2026**. Unmodified opinion, IFRS as issued by the IASB, Canadian GAAS. No key/critical audit matters section is printed.
**Output:** `B_fy2026_notes.csv` — **1,003 data rows** (1,004 lines incl. header).

---

## 1. Pages read

Whole document read, pages 1–44, in six `read_document` calls (startPage 1, 9, 12, 15, 18, 22, 26, 30, 33, 37, 41). Final call returned `nextPage: null`. No truncation, no substitution.

| Pages | Content | Extracted by me? |
|---|---|---|
| 1–4 | Cover, Independent Auditor's Report | Read, no figures (nothing to extract) |
| 5–8 | Primary statements (SoFP, Net Earnings & CE, Changes in Equity, Cash Flows) | **No — Agent A's scope.** Read only to cross-check note tie-outs |
| 9–18 | Notes 1–3 (Description of Business, Basis of Presentation, Material Accounting Policy Information, Future Accounting Policies) | Policies summarised in §5 below; the only table (useful-life ranges, p.11) is narrative-range text, see §7 |
| 18–19 | Note 4 Reorganization of Businesses | Narrative figures captured under `note_related_party` / cross-referenced |
| 20 | Note 5 Property, Plant and Equipment | ✔ `note_ppe` (138 rows) |
| 21 | Note 6 Goodwill; Note 7 Debt (table + a) Asset Backed Loan) | ✔ `note_other`, `note_debt` |
| 22–24 | Note 7 b)–e) Warwick / Revolving / Term Loan 2026 / Term Loan 2031 | ✔ `note_debt` |
| 24–25 | Note 8 Right of Use Assets and Lease Liabilities; Note 9 Trade Payables | ✔ `note_leases`, `note_other` |
| 26 | Note 10 Gas Storage Obligations; Note 11 Decommissioning Obligations | ✔ `note_other` |
| 27 | Note 12 Share Capital (narrative only); Note 13 Revenues | ✔ `note_revenue` |
| 28 | Note 14 Expenses; Note 15 Financing Costs | ✔ `note_other`, `note_debt` |
| 29–31 | Note 16 Income Taxes | ✔ `note_tax` (139 rows) |
| 31–35 | Note 17 Risk Management Activities and Financial Instruments | ✔ `note_financial_instruments`, `note_commitments` |
| 35–38 | Note 18 Fair Value Measurements | ✔ `note_financial_instruments` |
| 38–39 | Note 19 Share-based Compensation and Pension Plans | ✔ `note_equity` |
| 39 | Note 20 Geographical Information | ✔ `note_segment` |
| 40–42 | Note 21 Related Party Transactions | ✔ `note_related_party` |
| 42–43 | Note 22 Commitments and Contingencies | ✔ `note_commitments` |
| 43 | Note 23 Supplemental Cash Flow Disclosures | ✔ `note_other` |
| 44 | Note 24 Subsequent Events | ✔ `note_other` |

---

## 2. Verification results (SPEC §7.4 — "note tables foot to their own printed totals")

**Every note table in scope foots to its own printed total. 53 footing checks + 8 cross-statement ties, zero failures.** Checks were run programmatically against the written CSV, not against my reading notes.

### 2.1 Note 5 — Property, Plant and Equipment (p.20)
Three sub-tables (cost / accumulated depreciation / net book value). **All 23 printed rows cross-foot across the five classes to the printed `Total` column, and every roll-forward closes vertically.** Examples:

| Check | Components | Printed total |
|---|---|---|
| Cost, Balance April 1, 2024 | 165.6 + 151.6 + 299.9 + 101.4 + 413.6 | **1,132.1** ✓ |
| Cost, Balance March 31, 2025 | 169.4 + 152.5 + 323.3 + 101.1 + 415.1 | **1,161.4** ✓ |
| Cost, Balance March 31, 2026 | 169.8 + 154.8 + 332.6 + 109.6 + 422.9 | **1,189.7** ✓ |
| Cost vertical roll FY2026 | 1,161.4 + 27.3 + 0.9 + 8.5 − 11.4 + 3.0 | **1,189.7** ✓ |
| Acc. dep., Balance March 31, 2026 | 0 − 43.2 − 81.7 − 21.3 − 155.4 | **(301.6)** ✓ |
| Acc. dep. vertical roll FY2026 | (276.8) − 31.0 + 6.9 − 0.7 | **(301.6)** ✓ |
| Net book value 2026 | 1,189.7 − 301.6 | **888.1** ✓ (= SoFP p.5) |
| Net book value 2025 | 1,161.4 − 276.8 | **884.6** ✓ (= SoFP p.5) |

### 2.2 Note 7 — Debt (p.21)
| Period | Check | Result |
|---|---|---|
| FY2026 | 0 + 0 + 0 + 1,234.4 = Total principal | **1,234.4** ✓ |
| FY2026 | 1,234.4 − 12.2 − 24.9 = Total long-term debt, net | **1,197.3** ✓ (= SoFP) |
| FY2025 | 0 + 13.6 + 0 + 1,246.8 = Total principal | **1,260.4** ✓ |
| FY2025 | 1,260.4 − 25.8 − 26.5 = Total long-term debt, net | **1,208.1** ✓ (= SoFP) |

### 2.3 Note 8 — Leases (pp.24–25)
- ROU roll-forward FY2026: 83.9 + 0.1 − 0.1 − 3.9 + 8.4 + 0.1 = **88.5** ✓; by class 87.8 + 0.7 = 88.5 ✓
- ROU roll-forward FY2025: 86.7 + 1.3 − 3.7 − 0.1 − 0.3 = **83.9** ✓; 82.7 + 1.2 = 83.9 ✓
- Lease liabilities FY2026: 108.8 + 10.0 − 17.7 − 10.2 + 0.1 + 8.5 = **99.5** ✓; 99.5 − 8.6 = **90.9** ✓ (= SoFP)
- Lease liabilities FY2025: 106.8 + 10.6 − 0.8 − 8.5 − 0.1 + 0.8 = **108.8** ✓; 108.8 − 9.1 = **99.7** ✓ (= SoFP)
- Undiscounted lease maturity: 8.9 + 8.6 + 8.7 + 9.0 + 9.3 + 302.8 = **347.3** ✓

### 2.4 Note 9 / 10 / 11 (pp.25–26)
- Trade payables FY2026 **45.6** ✓ / FY2025 **59.5** ✓ (both = SoFP)
- Gas storage obligations FY2026: 17.4 − 4.5 + 0.6 = **13.5**; 13.5 − 0.2 = **13.3** ✓ (= SoFP)
- Gas storage obligations FY2025: 19.6 − 1.3 − 0.9 = **17.4** ✓
- Decommissioning FY2026: 5.2 + 0.4 + 0.9 + 0 − 0.1 + 0 = **6.4** ✓ (= SoFP)
- Decommissioning FY2025: 6.8 + 0.6 − 0.1 + 0.1 − 2.0 − 0.2 = **5.2**; 5.2 − 0.2 = **5.0** ✓ (= SoFP)

### 2.5 Note 13 — Revenue (p.27)
- Fee-for-Service by geography FY2026: 204.9 + 28.7 + 60.3 + 94.6 = **388.5** ✓ (= income statement)
- Fee-for-Service by geography FY2025: 163.3 + 21.7 + 77.7 + 104.1 = **366.8** ✓
- Optimization FY2026: 78.8 realized + 12.1 unrealized = **90.9** ✓; FY2025: 56.6 − 8.1 = **48.5** ✓

### 2.6 Notes 14 / 15 — Expenses and Financing Costs (p.28)
Operating **50.8 / 49.5** ✓; G&A **22.2 / 24.2** ✓; Finance costs **89.8 / 93.1** ✓. All three tie to the income statement.

### 2.7 Note 16 — Income Taxes (pp.29–30)
- Rate reconciliation FY2026: 46.9 + 0 − 32.4 + 1.4 + 0 + 0.7 + 0 = **16.6** ✓
- Rate reconciliation FY2025: 41.9 − 24.5 − 29.8 + 1.2 + 0 + 0.5 + 0.1 = **(10.6)** ✓
- Expected tax check: 223.5 × 21.0% = 46.9 ✓ ; 198.8 × 21.1% = 41.9 ✓
- Deferred tax tables foot **in all four columns and in all rows**, e.g. FY2026 net DTL 65.0 + 10.5 + 8.9 = **84.4** ✓ (= SoFP); FY2025 76.2 − 11.2 + 0 = **65.0** ✓ (= SoFP)
- Deferred tax P&L column (net) **10.5 / (11.2)** = the income statement's Deferred income tax expense (benefit) ✓
- Deferred tax "recognized in the balance sheet" column FY2026 = 8.9 = Warwick DTL 9.7 (Note 4) less SIM DTA 0.8 (Note 4) ✓

### 2.8 Notes 17 / 18 — Financial instruments (pp.31–38)
- Contractual obligations table (p.34) foots **in all five buckets and in the Total column** (2,428.6 / 235.0 / 231.9 / 201.5 / 1,760.2) and each row foots across buckets. Debt obligations 12.5 + 25.0 + 25.0 + 1,171.9 = **1,234.4** ✓
- Fair values of risk management assets/liabilities: FY2026 net **29.7**, FY2025 net **9.2**; all four line items tie to the SoFP (27.6 / 19.2 / 13.0 / 4.1 and 19.5 / 9.3 / 13.9 / 5.7) ✓
- Offset/netting tables: FY2026 Net 46.8 − 17.1 = **29.7** ✓; FY2025 28.8 − 19.6 = **9.2** ✓
- Expected realization into earnings: 14.6 + 5.7 + 1.8 + 2.3 + 5.3 = **29.7** ✓ (agrees with the fair-value table)
- FVTPL realized/unrealized table: FY2026 **110.3** ✓, FY2025 **55.8** ✓; and its Optimization-classified lines re-add exactly to Note 13's realized 78.8 / 56.6 and unrealized 12.1 / (8.1) ✓
- Fair value hierarchy: FY2026 Level 2 liabilities 17.1 + 13.5 + 12.5 + 1,223.4 = **1,266.5** ✓; FY2025 **1,292.8** ✓

### 2.9 Notes 19 / 20 / 21 / 22 / 23 (pp.38–43)
- Share options: 0 + 132,844 = **132,844** at March 31, 2026 ✓
- Geographic revenues 274.7 + 204.7 = **479.4** ✓ (= income statement); FY2025 **415.3** ✓
- Geographic non-current assets 465.8 + 539.5 = **1,005.3** ✓ = SoFP long-term assets 1,030.7 less LT risk-management assets 19.2 less other assets 6.2 ✓
- Related party balances **3.1 / 83.0** ✓; related party income-statement amounts **0.6 / 11.0** ✓
- Key management compensation **46.1 / 5.5** ✓
- Purchase/sale obligations: (110.4) + 171.8 = **61.4** ✓, and the purchase column total (110.4) agrees with the contractual-obligations table's Purchase obligations 110.4 ✓
- Changes in non-cash working capital **(45.6) / 71.5** ✓ (= cash flow statement)

### 2.10 Cross-statement ties I confirmed (not required of me, but they validate column assignment)
| Tie | Result |
|---|---|
| Note 5 depreciation 31.0 + Note 5 cushion-gas migration 3.1 = income statement D&A **34.1** | ✓ |
| FY2025: 29.9 + 3.2 = **33.1** | ✓ |
| Note 4: Warwick loan contributed as capital 135.6 + Legacy Incentive contribution 51.5 + BAIF deposit contribution 1.0 = equity statement Capital contributions **188.1** | ✓ |
| Note 4: return of capital 93.4 + against retained earnings 42.2 = Warwick payment **135.6** | ✓ |
| Note 21: principal 224.9 + accrued interest 8.6 = **233.5** paid on the 8.25% Promissory Note | ✓ |
| Note 21: 29.3 + 40.0 + 37.0 = non-cash distributions **106.3**; 17.6 + 11.7 = **29.3** | ✓ |

---

## 3. Column-alignment judgment calls (SPEC §9 — "do NOT guess")

The PDF extractor **dropped the first header cell in six tables** (a systematic defect, not a per-table one). In every case I resolved the identity by arithmetic tie-out to a printed total or to another statement, never by assumption. Each affected row carries the reasoning in its `note` field.

| p. | Table | Missing heading | How proven |
|---|---|---|---|
| 24 | ROU assets by class | col 1 = **Land and storage formations** | Its FY2026 additions 0.1 + remeasurements 8.4 = 8.5 = Note 5's "Lease additions and remeasurements" charged to Land and storage formations (8.5). FY2025 equivalently 1.2 = Note 5's 1.2. |
| 30 | Deferred tax (both years) | col 1 = **As at March 31, 2026** (resp. 2025) — the closing balance | col 4 (As at April 1) + col 2 (P&L) + col 3 (balance sheet) = col 1 for every row; and col 1 non-capital loss DTA 3.2 / 10.6 equals the figures printed in the Note 16 narrative for 2026 / 2025. |
| 35 | Fair values of risk management assets and liabilities | block-1 stub = **Balance, March 31, 2026** | The block-2 stub "Balance, March 31, 2025" is printed; block-1's four line items equal the 2026 SoFP amounts (27.6 / 19.2 / 13.0 / 4.1). |
| 38 | Share options | col 1 = **number of options** | 132,844 matches "Number of Options Outstanding 132,844" in the p.39 table; the other two columns are explicitly headed as prices. |
| 39 | Options outstanding and exercisable | stub col = **exercise price** | The stub value printed is "$18.47 (C$25.75)", matching the p.38 weighted-average exercise prices. |
| 42 | Purchase and sale obligations | col 1 = **Purchase obligations** | Its total (110.4) equals "Purchase obligations (1)" 110.4 in the p.34 contractual-obligations table; and col1 + col2 = col3 (Net) on every row. |

**Rejected as unprovable — nothing extracted:** none. Every table in scope was resolvable.

---

## 4. Caption oddities, sign conventions, footnotes, and things that do NOT agree

### 4.1 Uncaptioned total rows (transcribed as `[uncaptioned total row]` / `[uncaptioned subtotal row]`)
Five tables print a bold total line with **no caption in the stub column**. I did **not** invent a caption; each row carries `note` explaining what it equals.
- p.27 Optimization, net — total row (90.9 / 48.5), equals the income-statement caption "Optimization, net".
- p.30 Deferred tax — the pre-valuation-allowance subtotal (7.9 / 21.9 for FY2026 table; 21.9 / 43.4 for FY2025 table).
- p.31 Hedged inventory volumes — total row (26.0 / 12.4).
- p.35 Fair values of risk management assets/liabilities — net total row (29.7 / 9.2).
- p.37 FVTPL gains/losses — total row (110.3 / 55.8).
- p.40 Related party income-statement amounts — total row (0.6 / 11.0).

### 4.2 Genuine caption defect in the filing (not an extraction artefact)
**p.34, FX sensitivity table.** Both printed rows are captioned **"CAD - 10% increase"**; only the second is further qualified "(other comprehensive income)". There is no decrease scenario and the first row is not labelled as net earnings. Transcribed **verbatim**; flagged on both rows. Values: FY2026 (5.8) and 3.6; FY2025 3.8 and 3.1. Note also the **sign flips between years on the first row** ((5.8) vs 3.8) with no explanation given.

### 4.3 Internal inconsistencies I found and did **not** correct
| # | Item | Figures | Comment |
|---|---|---|---|
| 1 | **Term Loan current portion** | Note 7e narrative: current amounts owing **$12.5m** (2025: $12.5m). Note 7 table / SoFP: "Portion classified as current, net" **(12.2)** (2025: (25.8)). | The table caption says "net"; the 0.3 difference is not explained. FY2025's 25.8 = 12.5 term loan + 13.6 Warwick less 0.3. Both figures captured, cross-flagged in `note`. |
| 2 | **Deferred financing cost amortisation** | Note 15 "Deferred financing costs" **7.3** (FY2026); cash flow statement "Amortization of deferred financing costs" **7.4**. FY2025 both **6.8**. | 0.1 unexplained difference in FY2026 only. Not adjusted. |
| 3 | **Deferred revenue** | Note 13 narrative: deferred revenue related to Fee-for-Service contracts **0.1** (2025: 1.2). SoFP "Deferred revenue": **0.3** (2025: 1.4). | 0.2 gap in both years — presumably non-Fee-for-Service deferred revenue, but the filing does not say so. Flagged on the row. |
| 4 | **Lease cash payments** | Note 23 "Lease cash payments" **34.5** (FY2025: 12.8). Note 8 / cash flow: principal 17.7 + interest 10.2 = 27.9; adding variable lease expense 7.7 gives 35.6. | Neither 27.9 nor 35.6 equals 34.5. FY2025: 0.8 + 8.5 = 9.3, +6.5 = 15.8 vs 12.8. **No reconciliation is disclosed.** Flagged on the row; not derived. |
| 5 | **Decommissioning narrative vs SoFP** | Note 11 narrative: "estimated liability at March 31, 2026 was $6.4 million (March 31, 2025 - **$5.2 million**...)". SoFP "Decommissioning obligations" at 2025: **5.0**. | Narrative quotes the total before the 0.2 current reclassification. Consistent with the table, but the narrative and the SoFP do not use the same number. Flagged. |
| 6 | **Decommissioning roll-forward opening** | FY2026 "Balance, beginning of the year" **5.2** = prior year's "Total decommissioning obligations", *not* prior year's "Balance, end of the year" (5.0). | Internally consistent but the two captions differ in meaning; flagged on the row. |
| 7 | **Margin deposits** | SoFP margin deposits: asset 1.3 / 0.9, liability – / 3.2. Netting table (p.36) "Margin Deposits not Offset": assets (7.9) / (10.1), liabilities (6.0) / (2.2). | Different populations (only deposits not offset). Not reconciled by the filing. Recorded as printed. |

### 4.4 Sign conventions applied
- Parentheses in the source → negative in `value`. Applied throughout.
- Printed em-dash / "-" / "nil" / "no ..." meaning reported zero → `value = 0` with `note` containing `printed_dash_zero`. **168 rows** carry this marker.
- Where a narrative states an amount in words as a **loss** ("a $0.2 million loss", "$1.8 million loss", "$0.6 million of losses"), I recorded it **negative** and flagged `sign applied` in `note`. Six rows: electricity contract realized losses (Note 14, Note 21c), OCI FY2025 (Note 16).
- Accumulated depreciation in Note 5 is printed **negative** (e.g. "$ (43.2)") — kept negative.
- Purchase obligations in the p.42 table are printed **negative**; sales obligations positive. Kept as printed.
- Deferred tax table: the "recognized on the statement of net earnings" column is printed such that a negative reduces the balance for **both** assets and liabilities; the net DTL row nets to +10.5 / (11.2). Kept as printed.

### 4.5 Footnote markers preserved verbatim in `line_item`
- `Purchase obligations (1)` and `Other (2)` (p.34) — footnote text recorded in `note`.
- `Total non-current assets (1)` (p.39) — footnote "(1) Non-current assets exclude financial instruments and post-employment benefit assets" recorded in `note`.

### 4.6 Note references in tables
The SoFP-style "Notes" column in the p.34 contractual-obligations table (7, 8, 10, 11, 22) is preserved in the `note` field as `Notes ref: n` rather than as a separate row.

---

## 5. Material accounting policies that define a caption (Note 3, pp.9–18) — one line each

*(Per instructions these are summarised here, not in the CSV.)*

- **Principles of combination and consolidation** — Swan OpCo and BIF OpCo and their wholly-owned subsidiaries are combined because they are commonly controlled and managed as a single economic entity; all significant intercompany balances and transactions eliminated.
- **Revenue recognition (general)** — recognised when control of a product or service transfers; measured at contract consideration excluding amounts collected for third parties; cash received in advance held as deferred revenue.
- **Fee-for-Service — Take-or-Pay (ToP)** — one performance obligation (injection, storage, withdrawal); fixed monthly demand charges recognised over the contract period to the extent of the right to invoice, regardless of utilisation; a small variable element (fuel, injection/withdrawal fees) recognised over time as volumes move.
- **Fee-for-Service — Short-term Storage (STS)** — one performance obligation combining injection and withdrawal on specified dates; fixed, no customer option to vary volume/timing; generally ≤ 1 year; recognised over time using volume injected/withdrawn as the output measure.
- **Optimization, net** — realised and unrealised gains/losses on natural gas trading; physical contracts recognised at physical delivery, financial contracts at settlement; unrealised = change in derivative fair value; **inventory net-realisable-value adjustments are recorded inside optimization, net** (this is why "Optimization, net" is a net revenue caption, not a gross one).
- **Cash and cash equivalents** — cash on hand plus short-term investments with original maturity ≤ 3 months.
- **Margin deposits** — cash collateral under master netting arrangements not offset against derivative positions; derivatives marked to market daily.
- **Natural gas inventory** — lower of weighted-average cost or net realisable value; write-downs reversible; storage costs expensed to operating in the period incurred (not capitalised into inventory).
- **Property, plant and equipment** — at cost less accumulated depreciation and impairment; cost includes directly attributable costs and estimated decommissioning obligations; componentised; straight-line over useful lives: **Pipelines and interconnects 25–60 yrs; Wells 1–60 yrs; Land and storage formations 3–83 yrs; Facilities and other 3–60 yrs**. Land and pipeline rights of way are **not** depreciated. Major overhauls of engines/compressors depreciated on an hours-used basis (10–20 yr estimated lives).
- **Cushion gas** — a component of the facility with an **indefinite useful life; not amortised**; migration or withdrawal that loses effective pressure support is charged to **depreciation expense** (FY2026 $3.1m; FY2025 $3.2m). This is the bridge between Note 5 depreciation and income-statement D&A.
- **Right-of-use assets** — initial lease liability plus prepayments less incentives plus initial direct costs; depreciated over the shorter of lease term and asset life; **land leases renewable into perpetuity at the Business' option are treated as an acquisition of land and are not depreciated**.
- **Goodwill** — excess of purchase price over fair value of net assets acquired; allocated to CGUs; not amortised; tested annually or on indicator; impairment charged to net earnings and **never reversed**.
- **Impairment of long-lived assets** — recoverable amount = higher of FVLCD and value in use; reversible for all CGUs and individual assets **other than goodwill**.
- **Risk management activities** — natural gas, electricity, interest rate and FX derivatives measured at fair value on a recurring basis through a three-level hierarchy; **not designated as hedges for financial reporting**, so all realised and unrealised gains/losses go to net earnings; classified current/non-current on anticipated settlement date.
- **Netting** — risk management assets/liabilities and certain accrued gas sales/purchases presented net when a determinable amount, a right of offset, an intention to offset, and legal enforceability all exist.
- **Provisions / decommissioning** — best estimate of the consideration to settle, discounted at a credit-adjusted rate; the obligation is added to the carrying amount of the associated asset and amortised; accreted through **financing costs**.
- **Gas storage obligations** — WGS LP's undeliverable forward delivery commitments, accounted for as a **hybrid financial liability with an embedded natural gas derivative at FVTPL** (which is why the caption "Gain on gas storage obligations, net" sits in the income statement).
- **Leases** — IFRS 16 identification and separation judgments; remeasurement rules for term/index/modification changes; short-term lease recognition exemption applied. Perpetually renewable leases measured over a **60-year** estimation horizon.
- **Cost of gas storage services** — amounts paid to counterparties to flow gas into/out of facilities are presented as a **cost, not a reduction of revenue**.
- **Deferred financing costs** — capitalised on debt issuance and amortised to **financing costs** over the debt term using the effective interest method.
- **Foreign currency translation** — reporting currency USD; **WGS LP (and formerly SIM Energy LP / SIM Energy Limited) have a CAD functional currency**; their assets/liabilities at period-end rate, revenues/expenses at average monthly rates, equity at historical rates, translation differences to OCI. All other entities are USD-functional.
- **Current income tax** — measured at amounts expected to be recovered/paid using enacted or substantively enacted rates.
- **Deferred tax** — liability method on temporary differences; standard IAS 12 initial-recognition and investment-in-subsidiary exceptions; DTAs recognised to the extent probable; offset only within the same taxable entity and authority; deferred tax on items outside net earnings follows the underlying transaction to OCI or equity.
- **Tax status** — *critical judgment (d)*: **the Business is predominantly not a taxable entity in the United States** — those taxes are the responsibility of equity holders and are **not recorded**. Only the Canadian corporate subsidiaries bear tax in these statements. This is why the effective rate is far below the 21.0% blended applicable rate ("Earnings of non-taxable entities" (32.4)).
- **Defined contribution pension** — costs expensed as employees earn benefits.
- **Share-based compensation** — PSUs (performance-vesting), RSUs (time-vesting), and stock options (20% per year over five years, ten-year contractual life); valued by reference to Rockpoint's publicly traded Class A common shares; **PSUs/RSUs intended to be cash-settled are liabilities; stock options are equity-settled**, fair-valued at grant using Black-Scholes.
- **Reportable segments** — *critical judgment (i)*: **a single reportable segment, natural gas storage**; CEO and CFO are the CODMs and review combined consolidated information.
- **Future standards** — IFRS 9/IFRS 7 amendments (effective 1 Jan 2026) assessed as **not material**; **IFRS 18** (effective 1 Jan 2027) impact **still being determined**.

---

## 6. Restatements and reclassifications the filing itself discloses

1. **Cash flow reclassification (Note 21, p.41)** — *"Certain amounts previously classified in the statements of cash flows as notes extended to related parties were reclassified to distributions to better reflect the annual nature of the related transactions."* No amount is quantified and no restatement table is given. This affects the FY2025 comparative cash flow statement (Agent A's scope): FY2025 shows "Notes extended to related parties (83.0)" and "Distributions (628.9)", while Note 21 discloses FY2025 advances of $50.0m (June 13, 2024) and $472.2m (September 18, 2024). **The filing does not bridge these.** Flagged for Agent A.
2. **Reorganization of subsidiaries (Note 4, p.19)** — elimination of **$2.6m** of previously disclosed contributed capital on the revised combined consolidation structure, with an equivalent positive offset **directly to retained earnings**; shown on the equity statement as "Reorganization of subsidiaries (Note 4)" (2.6) / (6.3) / (8.9).
3. **Deferred taxes recognised directly in retained earnings (Note 4)** — Warwick DTL **$9.7m** and SIM DTA **$0.8m**, net $8.9m, appearing as the deferred tax note's "recognized in the balance sheet" column (verified above). Not routed through the income statement.
4. **Common-control accounting** — the Warwick Acquisition was recorded at **historical book values**, and the $135.6m payment to BAIF treated as an **in-substance distribution** ($93.4m return of capital / $42.2m against retained earnings), not as a business combination.

---

## 7. What is **NOT** disclosed (deliberate blanks)

These are absences in the filing, not gaps in my extraction.

1. **No segment note and no segment table.** Note 3(i) states there is **one reportable segment, natural gas storage**. There is no segment revenue/EBITDA/asset table anywhere in the statements. Note 20 gives **geographical** information only (revenues and non-current assets, U.S. / Canada). My `note_segment` rows are Note 20 only — 12 rows. **Nothing was recast.**
2. **Revenue disaggregation does not use the labels in my brief.** The filing disaggregates Fee-for-Service by **U.S. / Canada** (not Alberta / California) and by **Take-or-Pay / Short-term Storage service**. There is **no** Alberta or California revenue line, and **no** geographic split of Optimization, net. Alberta and California appear only as facility locations in Notes 1 and 6.
3. **No debt maturity table inside Note 7.** The only maturity profile for debt is the contractual-obligations table in **Note 17e (p.34)**, in Less-than-1-year / 1–3 / 3–5 / More-than-5 buckets — not year by year. I filed it under `note_commitments` with `column=` in `note`. There is **no** year-by-year 2027/2028/2029/2030/2031 debt amortisation schedule.
4. **No current/deferred income tax split table in Note 16.** The tax note contains only the **rate reconciliation** and the **deferred tax component tables**. The Current 6.1 / 0.6 and Deferred 10.5 / (11.2) split is printed **only on the income statement (p.6, Agent A's scope)**.
5. **No disclosure of unrecognised deferred tax assets**, other than the **valuation allowance** line (0.1 / 0.3) in the component table and the non-capital loss narrative ($10.5m / $46.6m of losses; DTA $3.2m / $10.6m; $0.5m expiring end of 2034).
6. **No tax jurisdiction breakdown** of current or deferred tax, no country-by-country reconciliation, no Pillar Two disclosure.
7. **Note 12 "Share Capital" contains no table and no numbers at all** — one narrative paragraph only ("Capital contributions represent the sum of the individual share capital of the combined companies…"). There is **no share count, no share class table, no par value, no authorised capital, and no partners' capital roll-forward** in the notes. The only equity roll-forward is the primary Statement of Changes in Equity (p.7, Agent A's scope). **No EPS is presented anywhere** in these combined consolidated statements.
8. **No PSUs or RSUs have been issued** as of March 31, 2026 (Note 19) — hence no PSU/RSU table.
9. **No option-pricing assumptions disclosed** (no Black-Scholes input table: no volatility, risk-free rate, dividend yield, or expected term). Note 19 says only that the option impact "was not significant during the year ended March 31, 2026" — **the share-based compensation expense amount is not quantified**.
10. **No hedge accounting disclosures** — the Business explicitly does not designate any derivative as a hedge, so there is no cash-flow-hedge reserve, no hedge effectiveness table, and no hedge maturity/notional table other than the hedged-inventory volumes (26.0 / 12.4 million decatherms) and the currency swap net notional (26.0 / 12.5).
11. **No Level 3 fair values** — both hierarchy tables show Level 1 and Level 3 as nil for every line; everything is Level 2. No Level 3 roll-forward, no unobservable-input sensitivity table.
12. **No quantified contingent liability.** Note 22 Contingencies is qualitative; explicitly **no liability recognised** for potential future Legacy Incentive Plan payments.
13. **No goodwill impairment sensitivity table** — only the narrative statement that a 10% fall in operating cash flows and a 5% rise in the discount rate would not cause impairment.
14. **No credit-risk aging of receivables**, no expected-credit-loss matrix, no gross vs net receivable table. Only: no allowance for doubtful accounts, bad debt expense $0.1m each year, and a $1.2m / $0.7m credit-related fair value reduction on retail energy contracts.
15. **No employee headcount, no auditor remuneration, and no directors' remuneration** (directors are compensated by the Company, Note 21d).
16. **No capital commitments for property, plant and equipment** (no committed capex disclosure); the purchase obligations table covers gas and cushion gas only.
17. **No dividends** — nothing is declared or paid at the Business level; equity distributions are shown as "Distributions" in the equity statement (Agent A's scope).
18. **Interest rate on the Revolving Credit Facility is not quantified** — the applicable margin is described only as "determined by a pricing grid based on Rockpoint Gas Storage Partners LP's, or Rockpoint's, corporate debt rating"; the grid itself is not disclosed, nor is the commitment fee rate.
19. **The 60/40 allocation of the Term Loan B between RGSP LP and RGSC is not disclosed in this document.** Note 7e names the borrowers as *Rockpoint Gas Storage Partners LP and its wholly owned subsidiary Rockpoint Gas Storage Canada Ltd. (the "Rockpoint Debt Parties")* but gives **no split of the $1,234.4m between them**. I did not extract a 60/40 allocation because this filing does not print one.
20. **Fiscal years open to income tax examination** are stated as "2019 through 2025" — a text range, not a figure. Recorded here rather than as a CSV row (SPEC §4 requires `value` to be a number).

---

## 8. Other judgment calls

1. **`statement` mapping.** Note 15 Financing Costs was filed as `note_debt` (it is the interest-cost detail for the debt in Note 7). The p.34 contractual-obligations table was filed as `note_commitments` (it is the note's own liquidity-risk commitments table) even though its largest rows are debt — the debt maturity buckets are therefore found under `note_commitments`, not `note_debt`. Notes 9, 10, 11, 14, 23 and 24 have no dedicated enum value and were filed as `note_other`.
2. **Matrix tables → long form.** For multi-column tables (PPE by class, deferred tax by column, fair value by contract type / by level, contractual obligations by bucket), `line_item` carries the **row caption verbatim** and the column identity is carried in `section` or in `note` as `column=<verbatim heading>`. No value was collapsed or summed.
3. **Roll-forward period typing.** Balance rows are `period_type = instant` with the exact balance date in `period_end` (including `2024-04-01` / `2025-04-01` opening balances); movement rows are `period_type = FY` with the year-end date. Opening-balance rows for FY2026 therefore carry `period_end = 2025-04-01` under `period_label = FY2026`.
4. **Narrative figures.** Amounts stated only in note prose (rates, notionals, covenant thresholds, LC balances, subsequent-event rates) were extracted with `note` beginning `narrative` so they can be filtered out of pure table reconstructions. There are 137 such rows.
5. **Stub-plus-subrow tables.** Where an instrument or revenue type is printed as a stub with Realized/Unrealized or U.S./Canada sub-rows (Note 13 revenue, Note 18 FVTPL), I combined them into a single `line_item` of the form `Stub - Subrow` and flagged the construction in `note`. The stubs are otherwise unaddressable in a flat schema; no wording was invented.
6. **`is_comparative`.** All 448 FY2025 rows are marked `1` — every FY2025 figure in this document is a comparative column of a FY2026-primary filing (SPEC §3.1). All 555 FY2026 rows are `0`.
7. **Units not in the SPEC enum.** Million decatherms (hedged volumes) and megawatt-hours (electricity) were recorded as `unit = count` with the real unit named in `note`; ratios ("5.00 to 1.00", "1.10 to 1.00") likewise as `count`; C$ exercise price as `usd_per_share` with `note` flagging that it is **C$ per share, not USD** — do not treat that row as USD in the canonical layer.
8. **Nothing was derived.** Where the filing does not print a number, no row exists. All the sums above are *checks against printed totals*, never a source of a written value.
