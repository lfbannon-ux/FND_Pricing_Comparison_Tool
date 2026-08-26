# Agent C — Extraction Notes (per SPEC.md §8)

**Deliverable CSV:** `extraction/C_annual_mdna.csv` — **604 rows** (534 `business_100`, 70 `company`).

---

## 1. Documents and page ranges actually read

| Quartr documentId | Document | Pages read |
|---|---|---|
| `4064736` | Rockpoint Gas Storage Inc. — *Management's Discussion and Analysis For the Fiscal Year Ended March 31, 2026* (MD&A dated **May 27, 2026**; filed 2026-05-28; Quartr eventTitle "Q4 2026") | **1–39 of 39 — complete document, read in 8 sequential `read_document` calls until `nextPage` was null** |

No other document was read. `get_financials` was **not** used (SPEC §2). No web search was used.
Source PDF referenced by Quartr: `https://files.quartr.com/reports/bf881d6b4d9544729ee5cb9a6d61e945-2026-08-22-21-08-00.pdf`.

Pages that produced CSV rows: 3, 4, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 17, 18, 19, 20, 21, 22, 23, 24, 25, 26,
27, 28, 29, 30, 33. Pages 1–2, 5, 16, 31–32, 34–39 are definitional / policy / forward-looking-disclaimer text
and produced no numeric rows (the p.16 definitions are transcribed verbatim into `C_NONIFRS_DEFINITIONS.md`).

---

## 2. THE BASIS QUESTION — how every row was tagged

The MD&A itself states the split explicitly (p.2):

> "This Management's Discussion and Analysis ('MD&A') is dated May 27, 2026 and discusses the financial position of
> **the Business** as at March 31, 2026 and March 31, 2025, and results of operations of **the Business** for the
> three and twelve months ended March 31, 2026 and 2025, as well as the results of operations of **the Company**
> for the three months ended March 31, 2026, and for the period beginning **July 28, 2025 and ended March 31,
> 2026**."

> "The Company was formed on July 28, 2025. Therefore, **no comparative financial information is provided in
> respect of the Company**."

Tagging applied:

- **`company`** — everything under the MD&A heading *"Results of Operations, Financial Results and Financial
  Position of Rockpoint Gas Storage Inc."* (pp.14–15), *"Cash Flows of the Company"* (pp.24–25), *"Share Capital
  of Rockpoint Gas Storage Inc."* (pp.27–28), the offering/IPO/share-issuance facts (pp.7–8), the
  Company-side related-party items (pp.28–29), and the Company's dividends. 70 rows.
- **`business_100`** — everything else, i.e. the Business's results, financial position, cash flows, all
  non-IFRS measures, backlog, contract KPIs, debt/covenants, contractual obligations, capex, risk-management
  derivatives, segment. 534 rows.

### Basis flags raised (not guessed away)

1. **p.21 "Sources of Liquidity" table** — the introduction reads *"The following table presents the **combined
   available liquidity for the Business and the Company**"*, yet the p.7 narrative attributes the identical
   $361.2 million to *"our Business"*. This is the one genuinely mixed-basis table in the document.
   **Decision:** tagged `business_100`, with the ambiguity written into the `note` field of all six rows.
   Rationale: the same $42.3m cash / $318.9m undrawn / $361.2m total figures are used in the p.17
   `business_100` Net Debt reconciliation, and the Company's own unrestricted cash is nil (p.24 Company cash
   flow summary nets to zero). **Do not treat these rows as additive across bases.**

2. **p.22 Revolving Credit Facility** — the borrowers include *both* Rockpoint and Swan OpCo subsidiaries, and
   the covenant compliance statement is *"the Business **and the Company** were in compliance"*. The $350.0m
   commitment / $175.0m LC sub-limit / 5.00x covenant / 1.10x DSCR rows are tagged `business_100` because
   *"borrowings to date under the Revolving Credit Facility have all been made by the subsidiaries of Swan
   OpCo"* (p.22) and the covenant figures *"are derived from the Business"* (p.23). Flagged here.

3. **p.7 leverage target and credit ratings** — "the Business is currently rated 'BB' … 'B1'". Tagged
   `business_100`. The 50–60% payout target (p.6) is a *shareholder* payout and is tagged `company`.

---

## 3. How the Company-basis period is labelled

The MD&A labels the Company's inaugural annual period, verbatim:

> **"July 28, 2025 to March 31, 2026"** (column header, p.14 table)
> **"the period beginning July 28, 2025 and ended March 31, 2026"** (narrative, pp.2, 14, 15, 24, 25, 28, 29)

The other Company column is **"Three Months Ended March 31, 2026"**.

**Encoding in the CSV (judgment call, see §7):**

| MD&A label | `period_label` | `period_end` | `period_type` |
|---|---|---|---|
| July 28, 2025 to March 31, 2026 | `July 28, 2025 to March 31, 2026` (verbatim) | `2026-03-31` | `FY` |
| Three Months Ended March 31, 2026 | `Q4 FY2026` | `2026-03-31` | `Q` |
| quarter ended December 31, 2025 (EPS only) | `Q3 FY2026` | `2025-12-31` | `Q` |

Every Company income-statement, cash-flow, EPS and investment row carries this note:
*"Company inaugural reporting period from incorporation 2025-07-28 to 2026-03-31 (246 days, not a full 12
months); Company held no interest in the Business before 2025-10-15; no comparative period is presented for the
Company (p.2)."*

**Critical downstream warning:** the period label spans 2025-07-28 → 2026-03-31, but the Company was
*"effectively dormant … until September 30, 2025"* (p.14) and only acquired its 40% interest on
**2025-10-15**. Economic activity therefore covers **2025-10-15 → 2026-03-31 (168 days)** only. Do **not**
annualise the $26.5m net earnings or the $0.73 EPS by 12/8 or any other naive factor.

---

## 4. SPEC §7 mandatory self-verification — results

All checks were run programmatically against the written CSV. **Every printed subtotal in this document foots.**

### 7.1 Balance sheet foots — **CANNOT BE TESTED as specified; not a failure**

The MD&A prints only *summaries*, not complete statements of financial position.

| Basis | Date | Total assets | Total **long-term** liabilities | Equity | LTL + Equity | Residual (= current liabilities, **not disclosed**) |
|---|---|---|---|---|---|---|
| business_100 | 2026-03-31 | 1,239.7 | 1,398.6 | (238.8) | 1,159.8 | 79.9 |
| business_100 | 2025-03-31 | 1,430.2 | 1,403.1 | (85.8) | 1,317.3 | 112.9 |
| business_100 | 2024-03-31 | 1,331.0 | 892.7 | 335.5 | 1,228.2 | 102.8 |
| company | 2026-03-31 | 916.3 | 16.8 | **not disclosed** | — | — |

The p.12 table has exactly five captions (Total assets, PP&E net, Long-term debt, Total long-term liabilities,
Equity) — **current assets and current liabilities are never printed**, so assets ≠ liabilities + equity by
construction. This is a disclosure limitation of the MD&A, **not** a footing failure. The audited statements
(a different document) are the place to run SPEC §7.1.

Consistency confirmed: `business_100` long-term debt 1,197.3 on p.12 == 1,197.3 in the p.17 net-debt table.
Company total assets 916.3 (p.15) matches the value SPEC §2 cites from p.8 of the FY2026 earnings release.

### 7.2 Income statement ties — **PASS (all four columns)**

`business_100`, p.9:

| Column | FFS + Opt = Total rev | Total rev − 7 expense lines = EBT | EBT − current − deferred = NET EARNINGS |
|---|---|---|---|
| Q4 FY2026 | 103.0 + 21.9 = 124.9 ✔ | 26.7 ✔ | 24.4 ✔ |
| Q4 FY2025 | 109.4 + 18.7 = 128.1 ✔ | 61.9 ✔ | 57.0 ✔ |
| FY2026 | 388.5 + 90.9 = 479.4 ✔ | 223.5 ✔ | 206.9 ✔ |
| FY2025 | 366.8 + 48.5 = 415.3 ✔ | 198.8 ✔ | 209.4 ✔ |

Tax cross-check: current + deferred (p.9) == the p.12 income-tax total in all four columns
(2.3 / 4.9 / 16.6 / −10.6) ✔.

`company`, p.14:

| Column | 4 income/expense lines = EBT | EBT − current − deferred = NET EARNINGS |
|---|---|---|
| Q4 FY2026 | 4.4 − 0.6 + 0 − 1.0 = 2.8 ✔ | 2.8 + 0.7 − 2.1 = 1.4 ✔ |
| July 28, 2025 to March 31, 2026 | 31.9 − 1.3 + 3.4 − 1.0 = 33.0 ✔ | 33.0 + 0.1 − 6.6 = 26.5 ✔ |

### 7.3 Cash flow ties — **PARTIAL PASS, one $0.8m unexplained gap (flagged, not corrected)**

`business_100`, p.23 — the operating-activities build foots in both years:
FY2026 206.9 + 10.5 − 25.0 + 34.1 + 7.4 + 1.8 − 45.6 = **190.1** ✔;
FY2025 209.4 − 11.2 + 4.0 + 33.1 + 6.8 + 0.1 + 71.5 = **313.7** ✔.

**But the summary table prints no foreign-exchange-on-cash line and no opening/closing cash line**, so
"O + I + F + FX = change in cash" cannot be closed from this document:

- FY2026: 190.1 − 32.9 − 319.8 = **−162.6**. Actual cash movement (p.17 net-debt table): 204.1 → 42.3 =
  **−161.8**. The p.13 and p.21 narratives both state the decrease was **$161.8 million**.
  **Unexplained difference: $0.8 million.** Most plausibly the effect of exchange rate changes on cash and/or a
  restricted-cash reclassification, neither of which is printed. **No adjustment made.** The three cash-flow
  subtotal rows carry a `note` recording the omitted line.
- FY2025: 313.7 − 34.9 − 174.2 = **+104.6**; opening cash at 2024-03-31 is not disclosed in this MD&A, so no
  test is possible.

`company`, p.24: 0 − 489.5 + 489.5 = **0** ✔ (nil unrestricted closing cash — consistent with p.24:
*"Cash expenses of the Company were paid on its behalf by a subsidiary of Swan OpCo"*). The $14.8m the Company
held at 2026-03-31 is **restricted** cash and is properly outside this total.

### 7.4 Note / supplementary tables foot — **PASS, every one**

| Table | Page | Result |
|---|---|---|
| Fee-for-Service revenue disaggregation (ToP + STS = FFS) | 9 | ✔ all 4 columns |
| Optimization disaggregation (realized + unrealized = net) | 10 | ✔ all 4 columns |
| **Adjusted EBITDA / Adjusted Gross Margin / DCF reconciliation to net earnings** | 17 | **✔ all 3 subtotals × all 4 columns = 12/12** |
| **Net debt reconciliation to total debt outstanding** | 17 | **✔ both dates; and Net debt ÷ Adjusted EBITDA reproduces the printed 3.1x for both years** |
| California backlog roll-forward | 18 | ✔ both years |
| Alberta backlog roll-forward | 18 | ✔ both years |
| ToP/STS by geography → ToP total = Take-or-Pay revenue (p.9); STS total = STS net of cost of gas storage services | 19 | ✔ both years |
| Supplementary Adjusted Gross Margin / EBITDA / DCF build-up, incl. both printed % ratios | 20 | ✔ all 4 columns; and identical to the p.17 values |
| Quarterly Results Summary — 4 quarters sum to each fiscal-year total, all 5 metrics | 21 | **✔ 10/10** |
| Available liquidity (cash + undrawn = total) | 21 | ✔ both dates |
| Contractual obligations — 7 rows × buckets, and 5 columns × line items | 25 | **✔ 12/12** |
| Capital expenditures (growth + maintenance = total) | 26 | ✔ both years |
| Risk management realized / unrealized components → printed nets | 30 | **✔ 8/8** |
| Facility capacities sum to portfolio total (154.0 + 21.5 + 75.0 + 28.7 = 279.2 Bcf) | 3 | ✔ |
| Company equity-investment roll-forward (892.2 + 32.1 − 23.4 = 900.9; and 504.6 + 377.4 + 10.2 = 892.2) | 15 | ✔ |

### 7.5 Cross-statement — **PASS where testable**

- Cash at 2026-03-31: **42.3** in the p.17 net-debt table == **42.3** in the p.21 liquidity table ✔
  (2025-03-31: **204.1** == **204.1** ✔).
- FY2026 net unrealized risk-management gains **25.0** (p.30) == the −25.0 add-back in the p.23 cash flow ✔
  (FY2025: −4.0 vs +4.0 ✔).
- The p.17 add-back *"Unrealized risk management losses (gains) (1)"* reproduces exactly as
  −(p.30 net unrealized − p.30 interest rate swaps) in **all four columns** (6.2 / 11.7 / −16.8 / 6.9) ✔,
  confirming footnote 1.
- FY2026/FY2025 total revenues and net earnings on p.10's three-year table match p.9 exactly ✔.
- **CF closing cash == BS cash:** the MD&A prints neither a closing-cash line in the cash-flow summary nor a cash
  line in the balance-sheet summary, so this specific SPEC §7.5 test is **not testable from this document**.

---

## 5. Caption oddities, sign conventions, footnotes

**Sign convention used throughout the CSV:** value exactly as printed, parentheses → negative. Concretely:
- Expenses on the p.9 income statement are printed **positive** (the column is headed `EXPENSES (INCOME)` and is
  deducted); they are stored positive. Only *(Gain) loss on gas storage obligations, net* is printed in
  parentheses where it is a gain and is stored negative (−1.4 / −4.5 for Q4 FY2026 / FY2026).
- On the p.14 Company table the column is headed `INCOME (EXPENSES)`; expenses are printed in parentheses and are
  stored **negative** (G&A −0.6/−1.3, Other expenses −1.0/−1.0, current tax benefits −0.7/−0.1). Note the
  **opposite sign convention between the Business table and the Company table for the same kind of item.**
- In the p.17 DCF section, the deduction rows below Adjusted Gross Margin are printed in parentheses and stored
  negative; the add-back rows above it are stored positive. The same caption *"Operating"* and
  *"General and administrative"* therefore appears **twice per column with opposite signs**, distinguished by
  `order_index` and by an explicit `note`. Likewise *"Other items (2)"* appears twice, equal and opposite.

**Printed-dash zeros** (`note=printed_dash_zero`, value `0`): p.9 Current tax Q4 FY2025; p.14 Company Foreign
exchange gains Q4 FY2026; p.17 Current taxes Q4 FY2025; p.24 Company net cash from operating activities;
p.25 several contractual-obligation buckets; p.30 Currency contracts (unrealized) FY2025.

**Verbatim caption quirks preserved:**
- `"Fee-for-Service as a %of Adjusted Gross Margin"` (p.20) — missing space in "%of". **Not tidied.**
- `"Fee-for- Service Gross Margin (in millions of $)"` (p.19 column header) — spurious space inside the hyphenated
  word as returned by the extractor. **Not tidied.**
- `AECO Hub™` is stored as `AECO Hub(TM)` for CSV safety; noted here.
- p.9 heading `EXPENSES (INCOME)`, p.14 heading `INCOME (EXPENSES)` — retained as printed `section` values.

**Composite line_items (documented departure, always flagged in `note`):** three tables in this MD&A are
matrices where a single printed row caption carries several metric columns, or a maturity-bucket layout. For
these, `line_item` = `<printed row caption> - <printed column header>`, both verbatim:
- p.19 ToP/STS by geography (e.g. `California - Contract Rate ($/Dth (1))`).
- p.25 contractual obligations (e.g. `Debt obligations - Less than 1 year`).
The `note` on every such row says so.

**Unlabelled total rows:** the p.19 table's two total rows (233.6 / 185.0 for ToP; 146.7 / 170.8 for STS) carry
**no printed caption**. Stored as `[unlabelled total row] - Fee-for- Service Gross Margin (in millions of $)`,
`is_subtotal=1`, with a note. Their identity was proven arithmetically (they equal Take-or-Pay contract revenue,
and STS revenue net of cost of gas storage services, respectively).

**Geography labels on the p.18 backlog tables** come from the sentence introducing each table
(*"…changes in our **California** contracted Fee-for-Service revenue backlog…"* / *"…our **Alberta**…"*); the
extracted tables themselves carry no geography caption. Encoded in `section` as
`Contracted Fee-for-Service Revenue Backlog - California` / `- Alberta`, with the provenance in `note`.

**PDF-extractor column mis-alignment (SPEC §9).** *Every* table in this document came back from
`read_document` with its header row shifted into the first data row and values offset. **No column assignment was
guessed.** Each table's alignment was reconstructed and then **independently proven by arithmetic** — each
printed subtotal had to foot on the reconstructed assignment, and the p.21 quarterly table had to sum to the
p.9/p.17 fiscal-year totals. All 12 checks in §4 above passed on the first reconstruction, which is decisive
evidence the assignment is correct. Every affected row carries a `note` recording this.

**Two specific alignment traps worth recording:**
- The p.21 quarterly table lost its fiscal-year header labels entirely (the extractor returned
  `Fiscal 2025 | (in millions, USD) | Q4 | Q3 | Q2 | Q1 | Q4 | Q3 | Q2 | Q1`). The first four columns are
  **fiscal 2026** Q4→Q1 and the last four **fiscal 2025** Q4→Q1 — confirmed because each set of four sums exactly
  to its printed fiscal-year total for all five metrics.
- The p.30 risk-management table returned only a `Fiscal Years Ended March 31,` header for four value columns.
  Assignment (Q4 FY2026, Q4 FY2025, FY2026, FY2025) is confirmed by footnote-1 arithmetic against the p.17
  add-backs and by the FY totals matching the p.23 cash-flow line.

---

## 6. Restatements, reclassifications and definition changes the MD&A discloses

**No restatement of any previously issued financial statement is disclosed.** What *is* disclosed:

1. **Non-IFRS measurement adjustment to a comparative (p.17 footnote 5).**
   > "Fiscal 2025 maintenance capital expenditures were adjusted downwards to reflect $5.5 million in one-time
   > costs associated with historical heat imbalances and cushion gas migration."
   Confirmed numerically: p.26 capex table FY2025 maintenance = **26.8**; p.17 DCF reconciliation FY2025
   maintenance = **21.3**; 26.8 − 5.5 = 21.3. **FY2025 Distributable Cash Flow of $234.5m is $5.5m higher than it
   would be without this adjustment.** FY2026 carries no equivalent adjustment (26.4 in both tables).

2. **Non-IFRS measurement exclusion in the current year (p.17 footnote 4).**
   > "Excludes a one-time payment of $19.3 million made during the three months ended September 30, 2025 related
   > to modified storage leases."
   FY2026 Distributable Cash Flow of $251.6m excludes $19.3m of cash actually paid in Q2 FY2026.

3. **New accounting policy first applied in FY2026 (p.31, Business; p.35, Company): Share-based Compensation.**
   > "We applied, for the first time, certain accounting policies that became applicable to the Business during
   > the fiscal year ended March 31, 2026." — PSUs, RSUs, (Company only: DSUs) and stock options vesting 20% per
   > year over five years. No transitional restatement is described.

4. **Classification judgment on the Legacy Incentive Plans (p.12).**
   > "As the costs of these plans were not related to ordinary course operations, they have been classified as
   > other expenses." — $51.5 million, Q4 FY2026, `business_100`. Funded by an equal Brookfield capital
   > contribution, so no net liquidity effect; 40% of it ($20.6m) flows through the Company's equity earnings.

5. **Legal structure reorganization with no restatement effect (p.8).**
   > "The assets and liabilities of these entities were assumed by Rockpoint Gas Storage Canada Ltd. **with no
   > impact on the Business' consolidated balances**." (SIM entities, Swan Debt and Rockpoint Canada Inc.
   > dissolved during December 2025.)

6. **Term Loan due 2031 excess-cash-flow prepayment condition amended (p.23)** — sweep reduced from 75%/50%/25%/0%
   to 50%/25%/0% against the First Lien Net Leverage Ratio grid. *"This change is not anticipated to have a
   material impact on cash flows."*

7. **Future standards not yet adopted (pp.33, 37):** IFRS 9 / IFRS 7 amendments (effective 2026-01-01) — assessed
   as not material for both the Business and the Company. **IFRS 18** (effective 2027-01-01) — impact *"in the
   process of"* being determined by both. IFRS 18 will affect the FY2028 presentation and will require disclosure
   of management-defined performance measures.

8. **Subsequent events affecting FY2027 (pp.23, 25, 28, 30):** Term Loan due 2031 repriced effective 2026-05-07
   (SOFR + 2.25%, base + 1.25%; all-in hedged rate down from **5.90% to 5.65%**, ≈ **$3.0m/yr** interest saving);
   quarterly dividend raised to **$0.2310/Class A Share** approved 2026-05-27; the Company's $14.8m restricted
   cash and offsetting related-party payable settled. These rows are tagged with `note` containing
   "SUBSEQUENT EVENT".

---

## 7. Judgment calls made, and why

1. **`period_type = FY` for the Company's stub period.** The label `July 28, 2025 to March 31, 2026` is stored
   verbatim in `period_label`, `period_end = 2026-03-31`. `YTD` was the alternative. `FY` was chosen because the
   filing presents it as the Company's *annual* reporting period (its audited annual financial statements cover
   exactly this period), which keeps it groupable with `FY2026` in the canonical layer. Every such row carries a
   note stating it is 246 days, not 12 months, with only 168 days of economic activity.

2. **`Q4 FY2026` / `Q4 FY2025` for "Three Months Ended March 31, 2026 / 2025"**, per SPEC §1's quarter convention.

3. **`is_comparative`.** Set to `1` for FY2025, FY2024, all fiscal-2025 quarters, and all 2025-03-31 / 2024-03-31
   instants — these are prior-period columns in a filing whose primary period is FY2026. Set to `0` for FY2026,
   Q4 FY2026, other fiscal-2026 quarters, the Company stub period and 2026-03-31 instants.

4. **The p.9 Business income statement and the p.12 balance-sheet summary were extracted even though the
   primary-statement extraction is another agent's scope.** These are the *MD&A's own summary tables*, they are
   the arithmetic anchor for the revenue disaggregation and non-IFRS reconciliations that are squarely in my
   scope, and their inclusion lets every non-IFRS check tie inside a single file. They are clearly tagged
   `source_page` 9/12 of doc 4064736, so a duplicate against the audited statements is trivially detectable and
   is *a cross-check, not a conflict*.

5. **Forward-looking targets are in the CSV but explicitly quarantined** — Adjusted EBITDA growth 4–5%, DCF
   growth 5–6%, incremental DCF growth 4–5%, 85% Fee-for-Service cash flows, 50–60% payout, ≤3.5x leverage, the
   Warwick 11 MW battery project and the up-to-5 Bcf Warwick expansion. Each carries
   `note` beginning "TARGET / forward-looking outlook, NOT a reported result". Range targets are stored as
   `unit=text` with the range verbatim rather than being split into two fabricated numbers.

6. **Units outside SPEC §5's enumerated list** were stored using the nearest permitted token with the true unit
   spelled out in `note`, never converted:
   - $/Dth (decatherm) → `unit=usd`, note "per decatherm".
   - MMDth (million decatherms) → `unit=count`, note "MMDth".
   - Ratios printed as "3.1x", "5.00 to 1.00", "1.10 to 1.00" → `unit=count`, note carries the printed form.
   - Years (3.5-year contract life, 54-year decommissioning horizon) and megawatts → `unit=count` with note.
   - C$ amounts (C$22.00 IPO price, C$704.0m gross proceeds, C$105.6m, C$37.5m Warwick facility) → kept in CAD
     per SPEC §1, `unit=cad_millions` / note. The USD equivalents the filing also prints ($15.66, $501.2m) are
     separate rows.

7. **Nothing was derived, summed or back-solved into the CSV.** Two figures that a reader might expect are
   therefore absent — see §8 items 1 and 2.

---

## 8. WHAT IS NOT DISCLOSED (deliberate blanks in my scope)

**Company basis (`company`) — the material gaps:**

1. **Dividends *paid* as a cash-flow line.** The Company's financing activities total $489.5m. The narrative
   (pp.24–25) names only two inflows: $501.2m IPO proceeds and an $11.7m advance from the Business = $512.9m.
   The $23.4m residual is arithmetically the dividends paid (2 × $0.22 × 53,200,000 shares = $23.408m, and p.15
   prints "distributions received to date totaling $23.4 million"). **This $23.4m is NOT printed as a
   dividends-paid line and has NOT been written to the CSV.** Only the printed per-share amounts ($0.22, $0.22,
   $0.2310) and the printed p.15 "distributions received to date" of $23.4m are recorded.
2. **Total dividends declared per share for FY2026** ($0.44) is **not printed** as a total; only the two
   individual $0.22 declarations are. Not aggregated.
3. **The Company's equity / shareholders' equity balance** at 2026-03-31 — not disclosed in the MD&A (only total
   assets $916.3m and total long-term liabilities $16.8m).
4. **The Company's current assets, current liabilities, cash balance, or any balance-sheet detail** beyond the
   investment ($900.9m), restricted cash ($14.8m), total assets and total long-term liabilities.
5. **Weighted-average share counts** (basic or diluted) for either Company period — only EPS is given.
6. **Any Company-basis non-IFRS measure**, including Distributable Cash Flow per share (see
   `C_NONIFRS_DEFINITIONS.md` §10).
7. **Any Company comparative period** — the MD&A states outright that none is provided (p.2).
8. **Q1/Q2 FY2026 Company results** — the Company was *"effectively dormant"* to 2025-09-30; no figures printed.
9. **Company statement of changes in equity / comprehensive income** — not presented in the MD&A. (OCI exists:
   p.15 refers to "share of net income and other comprehensive earnings since that date totaling $32.1 million",
   but the income and OCI components of that $32.1m are not split out.)
10. **Company income tax rate reconciliation** — not presented.

**Business basis (`business_100`) — gaps within my scope:**

11. **Current assets and current liabilities**, and hence a footing balance sheet (see §4/7.1).
12. **Opening and closing cash lines, and any FX-on-cash line, in the cash-flow summary** — hence the
    unexplained $0.8m in FY2026 (§4/7.3).
13. **Adjusted EBITDA, Adjusted Gross Margin or Distributable Cash Flow split by geography or by facility.**
    Only **Fee-for-Service gross margin** is split California/Alberta (p.19), and only for full fiscal years —
    **there is no quarterly geographic split**.
14. **Revenue split by geography.** Not printed. (ToP revenue can be reached geographically via the p.19 gross
    margin rows, but **STS is only available net of cost of gas storage services**, and **optimization, net is
    not split by geography at all**.)
15. **A combined California + Alberta backlog total** — not printed.
16. **Backlog by contract type (ToP vs STS separately)** — the backlog roll-forwards combine both.
17. **Backlog run-off schedule by year** — not printed; only the 3.5-year weighted-average remaining ToP contract
    life.
18. **Utilisation rates / injection-withdrawal volumes / deliverability** — **no volumetric operating statistics
    of any kind are disclosed.** The only volumetric measures are capacity (279.2 Bcf portfolio, and per-facility
    154.0 / 21.5 / 75.0 / 28.7 Bcf) and contracted ToP capacity (98.6 MMDth FY2026, 96.1 MMDth FY2025 —
    the FY2025 total is itself unprinted, appearing only as the CA 68.9 + AB 27.2 components).
19. **STS contract rate and STS working-gas-capacity contribution** — the p.19 table gives these two metrics for
    ToP only; the STS block carries gross margin alone.
20. **Capacity by facility as at a stated date** — the p.3 figures are narrative portfolio descriptions with no
    as-at date; dated to 2026-03-31 by extractor judgment, flagged in `note` on every such row.
21. **Segment disclosure** — a single reportable segment (natural gas storage, p.33); no disaggregated segment
    table exists.
22. **Growth vs maintenance capex split by geography or facility**, and **capex guidance amounts for FY2027**
    (only a qualitative project list on pp.26–27).
23. **Drawn balance on the Revolving Credit Facility at 2026-03-31** — stated as nil for cash drawings
    ("no cash drawings outstanding", p.25); the letters-of-credit utilisation at 2026-03-31 is **not** given
    (only the $37.2m transferred on 2025-10-15 and the $318.9m undrawn-and-available residual).
24. **The actual computed values of the covenant ratios** (Consolidated Total Net Debt/EBITDA vs the 5.00x limit;
    Debt Service Coverage Ratio vs the 1.10x floor) — only the thresholds and a statement of compliance.
25. **Short-term debt composition** — $12.2m at 2026-03-31 / $25.8m at 2025-03-31 appear only in the net-debt
    reconciliation, with no breakdown.
26. **A full statement of changes in equity for the Business** — not in the MD&A; only the single "Equity" line.
27. **Cost of gas storage services split between ToP and STS** — the p.20 presentation charges all of it against
    STS, which is a presentation choice, not an allocation disclosure.

---

## 9. Other things worth flagging to the model builder

- **The two bases must never be summed.** The Business's FY2026 net earnings of $206.9m and the Company's $26.5m
  overlap: the Company's $31.9m equity income *is* 40% of the Business's post-2025-10-15 earnings, adjusted for
  acquisition-date fair-value basis differences. A naive 40% × (Q3 88.4 + Q4 24.4) = $45.1m does **not** equal the
  printed $31.9m — the gap is the 2025-10-01→10-14 stub plus the fair-value basis amortisation described on p.36
  (*"Basis Adjustments Related to Equity Accounting"*). Do not model the Company's equity income as a flat 40% of
  Business net earnings.
- **The Company's EPS figures are not additive across quarters** ($0.03 + $0.56 = $0.59 ≠ $0.73) because the
  weighted-average share count differs by period (the denominator for the stub period is diluted by the pre-IPO
  weeks). Both are printed; both are recorded; neither is derived.
- **FY2024 net earnings of $253.9m include $115.3m from discontinued operations** (Tres Palacios and Salt Plains
  disposals — $114.7m net gain + $0.6m residual income, p.11). Net earnings from continuing operations were
  $138.6m. Using the $253.9m headline in a growth series would be misleading.
- **FY2026 net earnings fell ($206.9m vs $209.4m) while Adjusted EBITDA rose 14%** — the difference is the $51.5m
  Legacy Incentive Plan charge in other expenses, which Adjusted EBITDA adds back in full.
- **Q4 FY2026 income tax total is 2.3, but its components are current 3.0 and deferred (0.7)** — the p.9 income
  statement prints components while p.12 prints the net. Both are in the CSV; they reconcile.
- The MD&A is dated **May 27, 2026** while the filing date given in my task is 2026-05-28. The document's own
  date (May 27, 2026) is what is recorded here.
