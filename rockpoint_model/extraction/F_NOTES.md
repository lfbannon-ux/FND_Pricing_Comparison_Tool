# Agent F — Extraction Notes (SPEC.md §8)
**Scope:** non-IFRS / alternative performance measures, the "Non-IFRS Measures" sections and their
reconciliations, Company-basis financial statements, dividends, operating & commercial KPIs, and
definition changes — across the four Rockpoint earnings releases.

**Deliverables:** `F_earnings_releases.csv` (881 rows), `F_KPI_AND_EVENTS.md`, this file.

---

## 1. Documents and page ranges actually read

| documentId | Document | Filed | Pages read | Result |
|---|---|---|---|---|
| `2235906` | **Q2 FY2026 earnings release** | 2025-11-05 | **1–10 (all)** | **UNREADABLE — 0 rows extracted** |
| `2794952` | Q3 FY2026 earnings release | 2026-02-10 | **1–14 (all)** | 241 rows |
| `3409150` | Q4 + FY2026 earnings release | 2026-05-28 | **1–15 (all)** | 251 rows |
| `3693793` | Q1 FY2027 earnings release | 2026-08-05 | **1–15 (all)** | 223 rows |
| `4064732` | Q2 FY2026 **MD&A** — substitute source | 2025-11-05 | 1–17 (of 23) | 166 rows |

### 1.1 documentId 2235906 could not be extracted — this is a hard gap

`read_document(2235906)` returns **all ten pages with empty text**. Pages 3, 4 and 5 return a bare
newline; pages 1, 2, 6, 7, 8, 9 and 10 return only unresolved table stubs
(`|`, `|`, `[ref:"#/tables/N"]`) with **no table body and no narrative**. The PDF has no usable text
layer in Quartr's extraction. Verified by:
- full-document read (`startPage=1`, all 10 pages) — empty;
- single-page reads at pages 1, 2, 3, 4, 5, 6, 7 — empty (not a truncation or chunking artifact);
- `list_documents(companyId=21558)` — **no alternate copy** of the Q2 FY2026 earnings release exists
  in the feed (only this one `earnings_release_non_us` for eventId 405757).

Direct retrieval of `sourcePdfUrl` was attempted and is **blocked by this environment's network
egress proxy** (`curl` → `CONNECT tunnel failed, response 403`; `WebFetch` → `EGRESS_BLOCKED:
files.quartr.com`). Per SPEC §9 I did not substitute a web search, and per SPEC §10 I did not invent
figures.

**Judgment call (declared).** Rather than deliver a blank quarter, I extracted the Q2 FY2026
non-IFRS reconciliation, supplementary tables, quarterly-results summary and commercial KPIs from
the **companion Q2 FY2026 MD&A, documentId `4064732`, filed the same day (2025-11-05, board-approved
2025-11-04)**. Every one of those 166 rows carries `source_doc=4064732`, its own page and deep-link,
and a `note` beginning:

> `SUBSTITUTE SOURCE: the Q2 FY2026 earnings release (documentId 2235906) returns NO text on any of
> its 10 pages from Quartr read_document, so it could not be extracted. This row comes from the
> companion Q2 FY2026 MD&A filed the same day (2025-11-05, board-approved 2025-11-04), NOT from the
> earnings release.`

Downstream consumers can isolate or drop them with a single filter on `source_doc`.

---

## 2. The column-mapping trap — how each mapping was proven

The PDF extractor mangles every headline and reconciliation header row: the header carries a value
cell, and value rows are offset by one. In all four documents the true layout is **four numeric
columns** in the order `[3M current, 3M prior, long-period current, long-period prior]`, with the
row caption emitted *between* the prior row's values and the current row's first value.

I proved every mapping **twice** — once against the narrative prose and once arithmetically — before
assigning a single value.

### 2.1 Prose cross-checks (SPEC §9 requirement)

| Release | Prose statement | Assignment it fixes |
|---|---|---|
| FY2026 p.1 | *"Net earnings for the fiscal year totaled $207 million and $24 million for the quarter, compared with $209 million and $57 million"* | 206.9 / 24.4 / 209.4 / 57.0 |
| FY2026 p.2 | *"$459 million for the year… $412 million… quarterly results were $129 million, compared to $134 million"* | AGM 459.1 / 412.4 / 128.7 / 134.2 |
| FY2026 p.2 | *"record $386 million and $109 million… compared to $339 million and $113 million"* | Adj EBITDA 385.9 / 109.2 / 338.8 / 112.7 |
| FY2026 p.2 | *"annual record of $252 million and $75 million, compared to $235 million and $78 million"* | DCF 251.6 / 74.8 / 234.5 / 78.0 |
| Q3 FY2026 p.2 | *"$88 million, up 52%… $240 million… 7% increase"* | 88.4/58.1 = +52.2%; 239.5/224.4 = +6.7% |
| Q3 FY2026 p.2 | *"$133 million… $465 million… increased by 18% and 15%"* | 133.3/113.0 = +18.0%; 464.6/405.4 = +14.6% |
| Q3 FY2026 p.2 | *"$116 million… $389 million… 20% and 18%"* | 116.4/96.6 = +20.5%; 389.4/331.1 = +17.6% |
| Q3 FY2026 p.2 | *"$82 million, increasing 34%… $255 million… 4% increase"* | 82.2/61.5 = +33.7%; 254.8/245.0 = +4.0% |
| Q1 FY2027 p.2 | *"$456 million… up from $426 million… quarterly results were $93 million, compared to $96 million"* | AGM 456.3 / 425.8 / 93.0 / 95.8 |
| Q1 FY2027 p.2 | *"higher ToP revenue of $237 million, up from $197 million"* | ToP 236.9 / 197.3 |
| Q1 FY2027 p.2 | *"$253 million and $48 million… compared to $231 million and $47 million"* | DCF 253.4 / 48.4 / 231.4 / 46.6 |
| Q2 FY2026 MD&A p.14 | *"Adjusted EBITDA increased by $17.7 million, or 27%… and by $30.8 million, or 24%"* | 83.2−65.5 = 17.7 (+27.0%); 160.3−129.5 = 30.8 (+23.8%) |

### 2.2 Arithmetic proofs (run from the written CSV, not from my working notes)

A verification script re-read `F_earnings_releases.csv` and recomputed each measure from the
reconciliation rows. **Every check passed** (tolerance ±0.05m):

- **16 / 16** reconciliation columns foot: Net earnings + financing costs + tax + D&A + unrealized
  risk management + other expenses = **printed Adjusted EBITDA**; + operating + G&A + other items =
  **printed Adjusted Gross Margin**; − operating − G&A − interest − mandatory repayments − current
  taxes − cash leases − maintenance capex ± other items = **printed Distributable Cash Flow**.
  (4 columns × 4 documents.)
- **16 / 16** Adjusted Gross Margin component tables foot: ToP + STS = printed Total Fee-for-Service
  gross margin; + Realized Optimization = printed Adjusted Gross Margin.
- **12 / 12** headline Fee-for-Service-% ratios reproduce from the component rows to the printed
  whole percent (including the 102% in Q1 FY2027 and 95%/97%/102% in Q2 FY2026).
- **8 / 8** net-debt tables foot: short-term + long-term = total debt outstanding; + unamortized
  discount − cash = net debt.
- **6 / 6** Company-basis balance sheets foot: TOTAL assets == TOTAL liabilities and equity.
- **4 / 4** Company-basis cash flows tie: O + I + F + FX == printed change in cash, and
  opening + change == printed closing cash.
- **5 / 5** Company-basis income statements tie: current + deferred tax == printed tax subtotal;
  EBT − tax == printed NET EARNINGS; NET EARNINGS + OCI == printed comprehensive earnings.

Because the components sum **exactly** to the printed subtotal in every single column, a mis-assigned
column is arithmetically impossible. **No column mapping in any numeric table is unproven.**

### 2.3 Four header *labels* were destroyed by the extractor and had to be reconstructed

These are label reconstructions, not value assignments. Each is proven; none is a guess.

| Where | What the extractor returned | Reconstruction | Proof |
|---|---|---|---|
| `3409150` p.8 — Company balance sheet | `\| As at July 28, \| (in millions, USD) (1) \|` then `\| 2026 \| 2025 \|` — the words *"As at March 31,"* are missing | col 1 = **As at March 31, 2026**; col 2 = **As at July 28, 2025** | fn1 *"Comparative period is the date of incorporation"* (Rockpoint was incorporated 2025-07-28); and the **Q1 FY2027 release p.8 reprints this identical column, line for line, as its March 31, 2026 comparative** |
| `3693793` p.8 — Company balance sheet | `\| As at March 31, \| (in millions, USD) \|` then `\| 2026 \| 2026 \|` — *"As at June 30,"* missing | col 1 = **As at June 30, 2026**; col 2 = **As at March 31, 2026** | col 2 reproduces `3409150` p.8 exactly (14.8 / 0.5 / 0.1 / 15.4 / 900.9 / 916.3 / 0.5 / 17.1 / 17.6 / 16.8 / 881.9 / 916.3) |
| `3693793` p.15 — net-debt table | same truncated header | same | col 2 reproduces `3409150` p.15 exactly (12.2 / 1,197.3 / 1,209.5 / 24.9 / (42.3) / 1,192.1) |
| `4064732` p.14 — Quarterly Results Summary | `\| Fiscal Year 2025 \| … \| Q2 \| Q1 \| Q4 \| Q3 \|` then `\| Q2 \| Q1 \|` — *"Fiscal Year 2026"* missing | cols = **FY2026 Q2, FY2026 Q1, FY2025 Q4, FY2025 Q3, FY2025 Q2, FY2025 Q1** | FY2026 Q1 column (104.1 / 48.3 / 77.1 / 95.8 / 46.6) matches the Q1 FY2027 release comparatives exactly; FY2025 Q4 and Q3 revenue (128.1 / 112.4) match the FY2026 and Q3 FY2026 releases |
| `4064732` p.13 — net-debt table | `\| As at March 31, 2025 \| (in millions, USD) \|` — *"As at September 30, 2025"* missing | col 1 = **As at September 30, 2025** | cash 30.5 matches the p.15 liquidity narrative: *"As of September 30, 2025… $30.5 million of available cash"* |

**Nothing was left ambiguous. There is no numeric row in the CSV whose period I could not prove.**

---

## 3. Mandatory self-verification results (SPEC §7)

| # | Check | Result |
|---|---|---|
| 1 | Balance sheet foots (per basis, per date) | **PASS** — 6/6 Company-basis balance sheets. `3409150` p.8: 15.4 + 900.9 = **916.3** = 0.5 + 17.1 + 16.8 + 881.9. `2794952` p.7: 29.3 + 935.1 = **964.4** = 42.3 + 29.6 + 892.5. `3693793` p.8: 0.4 + 906.3 = **906.7** = 6.9 + 21.1 + 878.7. The 2025-07-28 comparatives are all zero and foot trivially. |
| 2 | Income statement subtotals reconcile to net earnings | **PASS** — 5/5 Company-basis. e.g. `3409150` p.9 inception-to-date: 31.9 − 1.3 + 3.4 − 1.0 = **33.0**; tax (0.1) + 6.6 = **6.5**; 33.0 − 6.5 = **26.5**; 26.5 + 0.2 = **26.7**. |
| 3 | Cash flow ties (O+I+F+FX == change; opening+change == closing) | **PASS** — 4/4. `3409150` p.10: 0.0 − 489.5 + 489.5 + 0.0 = **0.0**; 0.0 + 0.0 = **0.0**. `3693793` p.10: 0.1 + 12.3 − 12.3 = **0.1**; 0.0 + 0.1 = **0.1**. |
| 4 | Note / reconciliation tables foot to their own printed totals | **PASS** — 16/16 non-IFRS reconciliation columns, 16/16 component tables, 8/8 net-debt tables, 12/12 Fee-for-Service ratios. Detail in §2.2. |
| 5 | Cross-statement: CF closing cash == BS cash at same date | **PASS with one caveat.** `3693793`: CF closing cash **$0.1m** == balance-sheet "Cash and cash equivalents" **$0.1m** at 2026-06-30. `3409150` and `2794952`: CF closing cash is **$ -** (zero) and **neither Company balance sheet carries a "Cash and cash equivalents" line at all** — only *Restricted cash* ($14.8m at 2026-03-31; $29.3m at 2025-12-31), which the cash-flow statement treats as a **working-capital movement**, not as cash. The statements are internally consistent; the caveat is that the check is vacuous for those two dates because the caption does not exist. Recorded, not adjusted. |

**No check failed. No figure was adjusted.**

---

## 4. Caption oddities, sign conventions and footnotes

### 4.1 PDF-extractor artifacts preserved verbatim (SPEC §4: *do not tidy*)
These are almost certainly rendered with a space in the printed PDF; the extractor dropped it. I
recorded the caption **as the extractor returned it** and flagged each in the row's `note`:

| Verbatim as extracted | Where |
|---|---|
| `Fee-for-Service gross margin as a %of Adjusted Gross Margin 1` (`%of`) | headline tables, all three readable releases |
| `LIABILITIESAND EQUITY` / `LIABILITIESAND OWNERS' EQUITY` | `3409150` p.8, `3693793` p.8, statements of financial position |
| `NET EARNINGSAND COMPREHENSIVE EARNINGS` | `3409150` p.9, `3693793` p.9 |
| `EARNINGS PER CLASSA SHARE` / `EARNINGS PER CLASSA SHARE (dollars)` | `3409150` p.9, `3693793` p.9 |
| `Dividends to owners ($0.44 per Class Acommon share)` | `3409150` p.10 |

The Q3 FY2026 release renders the same captions **with** the spaces (`LIABILITIES AND EQUITY`,
`NET EARNINGS AND COMPREHENSIVE EARNINGS`), so the artifact is per-document, not per-issuer.

### 4.2 Subtotal rows printed with **no caption**
The Company-basis statements print unlabelled subtotal rows (current assets, current liabilities,
total income tax). Inventing a caption would breach SPEC §4, and a blank `line_item` would be
unusable. I recorded these as **`[no caption printed]`** with `is_subtotal=1` and a `note` naming
what the row subtotals. Affected: `3409150` p.8 (×2) and p.9 (×1); `2794952` p.7 (×1) and p.8 (×1);
`3693793` p.8 (×2) and p.9 (×1).

### 4.3 Sign / caption oddity — "Note extended to related parties" as a financing **inflow**
`3409150` p.10 and `2794952` p.9 both print, under FINANCING ACTIVITIES:

> `Note extended to related parties  11.7`  — a **positive** (inflow) amount

The caption says the note was *extended* (i.e. lent out), which would be an outflow. The Q3 FY2026
Company balance sheet resolves it: it carries a matching **`Note payable to related party` 11.7**
([2794952 p.7](https://web.quartr.com/companies/21558?companyId=21558&documentId=2794952&documentType=report&eventId=411100&navigation=external&utm_medium=referral&utm_source=mcp&rp=7)),
so the cash effect really is a borrowing and the sign is right — the **caption** is the problem.
Compare the 100%-basis statements, which print the analogous line as a negative
(`Notes extended to related parties (83.0)`, `3409150` p.13). Recorded exactly as printed and
flagged on both rows. **Not corrected.**

### 4.4 Printed dashes
Every em-dash / `-` / `$ -` meaning a reported zero is recorded as `value=0` with
`note=printed_dash_zero`, per SPEC §4. Most numerous in the 2025-07-28 comparative columns (all zero,
the date of incorporation) and in "Current taxes" / "Mandatory debt repayments" rows of the earlier
reconciliations.

### 4.5 Values that look wrong but are not
- **`Fee-for-Service gross margin as a % of Adjusted Gross Margin` = 102%** (Q1 FY2027) and **102%**
  (H1 FY2025, Q2 MD&A). Correct: Realized Optimization gross margin was **negative** in both periods
  (−$2.0m and −$3.5m), so Fee-for-Service margin exceeds total Adjusted Gross Margin.
- **`Realized Optimization gross margin` = $(2.0)m** in Q1 FY2027 — the only negative headline
  component in the four releases.
- **Income tax `(0.7)` / `(0.1)` in `3409150` p.9** — parentheses, so a tax **benefit** in the Current
  line while the Deferred line is an expense; the section is headed *"Income tax (benefit) expense"*.
- **Q3 FY2026 Company income statement prints identical figures in both columns** (three-month and
  inception-to-date) for every line except EPS ($0.56 vs $0.95). Correct: the Company had no
  operations before 2025-10-15, so the quarter *is* the whole post-acquisition period; only the
  weighted-average share count differs. Flagged on all 24 rows.
- **Net debt *rose* while net debt / Adjusted EBITDA stayed at 3.1x** (FY2025 $1,056.3m → FY2026
  $1,192.1m). Correct: cash fell from $204.1m to $42.3m after $456.9m of distributions, while
  Adjusted EBITDA grew from $338.8m to $385.9m.

### 4.6 Footnote text carried into the CSV `note` column
All reconciliation footnotes (1)–(5) of each release are reproduced on the rows they qualify —
including the interest-expense scope, the $19.3m modified-storage-lease exclusion, the "other items"
definition, and the $5.5m maintenance-capex adjustment. Changes across releases are tabulated in
`F_KPI_AND_EVENTS.md` §6.8.

---

## 5. Restatements and reclassifications the filings themselves disclose

1. **Maintenance capital expenditures — fiscal 2025 restated downwards by $5.5 million.**
   First disclosed in the FY2026 release, footnote 5
   ([3409150 p.14](https://web.quartr.com/companies/21558?companyId=21558&documentId=3409150&documentType=report&eventId=554427&navigation=external&utm_medium=referral&utm_source=mcp&rp=14)):
   > *"Fiscal 2025 maintenance capital expenditures were adjusted downwards to reflect $5.5 million in
   > one-time costs associated with historical heat imbalances and cushion gas migration."*

   **No such footnote exists in the Q2 or Q3 FY2026 presentations.** The Q1 FY2027 release re-scopes
   the same adjustment to *"the last twelve months ended June 30, 2025"*. Any prior-year maintenance
   capex or Distributable Cash Flow figure taken from the Q2/Q3 FY2026 releases is on the **pre-restatement**
   basis. Both bases are in the CSV, distinguished by `source_doc`.

2. **Cash lease payments — $19.3 million one-time payment excluded.** Disclosed identically in all
   four documents: a one-time payment made in the three months ended 2025-09-30 that eliminated all
   future payments on modified storage leases in exchange for one upfront payment. It is excluded
   from Distributable Cash Flow in every period presented.

3. **Non-IFRS definition narrowings and broadenings** (Q4 FY2026 and Q1 FY2027) — these change what
   the measures *mean* across the series without the filings labelling them as restatements. Fully
   catalogued in `F_KPI_AND_EVENTS.md` §6.

---

## 6. Inter-filing discrepancies found (recorded as printed, not corrected)

| Measure | Period | Q2 FY2026 MD&A (`4064732` p.14) | Later release | Δ |
|---|---|---|---|---|
| Adjusted Gross Margin | **Q4 FY2025** | **134.1** | **134.2** (`3409150` p.1 and p.14) | 0.1 |
| Adjusted Gross Margin | **Q3 FY2025** | **113.1** | **113.0** (`2794952` p.1 and p.13) | 0.1 |

Both are almost certainly rounding, but the company printed two different numbers for the same
quarter and I did not reconcile them away. Every affected row carries an `INTER-FILING DISCREPANCY`
note. Revenue, Net earnings, Adjusted EBITDA and Distributable Cash Flow agree exactly across all
overlapping columns of all documents.

---

## 7. Verification of the leads supplied in the assignment

| # | Lead as given | Verdict | Evidence |
|---|---|---|---|
| 1 | Warwick Battery Storage ~11 MW ~C$14m | **CONFIRMED** | `3409150` p.2: *"11megawatt battery energy storage system"*, *"expected to cost C$14 million"*. Also: positive FID reached, permits secured, FEED complete, in service **Q2 fiscal 2028**, AESO market participation. Q1 FY2027 p.2 restates 11-MW and says *"remains on budget"* (no C$ figure). |
| 2 | Warwick Gas Storage Expansion up to 5 Bcf | **CONFIRMED, then REFINED** | `3409150` p.2: *"will add **up to 5 Bcf**"*. `3693793` p.3 refines: all approvals received; **≈3.5 Bcf in Q3 fiscal 2027**, rising to **≈5 Bcf** total via fiscal-2028 activity. Both figures are in the CSV as separate rows. |
| 3 | Term Loan repricing 2026-05-07, spread −25bp, ~$3m annual saving, hedged ~5.65% to 2031, cumulative −75bp / $9m | **ALL SIX CONFIRMED** | `3409150` pp.2–3, verbatim. **Additional fact found:** the facility is **$1,234 million**. **Independently corroborated:** the Q2 FY2026 MD&A records a **−50bp** repricing effective **2025-10-29** and a post-repricing all-in rate of **5.90%** (`4064732` pp.6, 16). −50 − 25 = **−75bp**; 5.90% − 0.25% = **5.65%**. |
| 4 | NCIB commenced 2026-03-27, max 5,316,025 class "A" shares, terminates by 2027-03-26 | **ALL THREE CONFIRMED** | `3409150` p.3, verbatim, plus TSX approval. **Additional:** 168,996 shares actually repurchased in Q1 FY2027 at a weighted-average **C$28.60**, ≈**C$4.8m** (`3693793` p.2), = US$3.4m in the cash flow (`3693793` p.10). |
| 5 | Contracted Fee-for-Service revenue backlog | **CONFIRMED — $947 million, +6% y/y** | `3409150` p.3. **Caveat:** disclosed **only once**, in the FY2026 release. **Not** disclosed in Q3 FY2026 or Q1 FY2027. |
| 6 | Take-or-Pay contracting outcomes | **CONFIRMED qualitatively; NO figures given** | `3409150` p.2: fiscal-2027 season concluded, rates and durations in line with expectations, Alberta volume growth robust, California volumes flat on a third consecutive mild winter. **No volume or rate numbers** for the fiscal-2027 season. Fiscal-2026 pricing ($2.32/Dth, +25%; 98.1m Dth allocated, +2%) is available only in the Q2 MD&A. |
| 7 | Storage capacity | **CONFIRMED — ≈280 Bcf, six facilities** | all three readable releases. **More precise figure found:** **279.2 Bcf** with a facility-by-facility split (`4064732` p.3). |
| 8 | Q2 FY2026 release "announces the inaugural dividend" | **CANNOT BE VERIFIED IN THE NAMED DOCUMENT** | documentId 2235906 has no extractable text (§1.1). The **amount, US$0.22 per class "A" common share, is established from two other printed sources** (`F_KPI_AND_EVENTS.md` §1). The **declaration, record and payment dates remain a gap.** |

**Nothing supplied as a lead was contradicted by the source text.** Two were *refined* by later
disclosure (Warwick expansion phasing; the NCIB gained actual purchase data), one is *single-period
only* (backlog), and one could not be checked in its named document (the inaugural dividend).

---

## 8. What is NOT disclosed — explicit list of deliberate blanks

Every item below is absent from the source text. **No row was written for any of them.**

**Because documentId 2235906 has no text layer:**
1. The entire Q2 FY2026 **earnings release** — headline table, Non-IFRS Measures section, Company-basis
   statements, CEO message, outlook, and the inaugural-dividend announcement.
2. **Declaration, record and payment dates of the inaugural dividend.**
3. Whatever Q2-specific KPIs, targets or growth-project statements that release carried.

**Genuinely not reported by the company:**
4. **No non-IFRS measure is presented on the Company (40%) basis** in any release — Adjusted Gross
   Margin, Adjusted EBITDA, Distributable Cash Flow, DCF per share, Fee-for-Service % of Adjusted
   Gross Margin and Net Debt are **100%-basis only**, always.
5. **Distributable Cash Flow per share does not exist for Q2 FY2026** — the measure is neither
   defined nor presented in that period's disclosure.
6. **Adjusted EBITDA Margin exists only for Q2 FY2026** — discontinued in all later releases.
7. **Net Debt to Adjusted EBITDA is not a printed table row** in the Q3 FY2026, Q1 FY2027 or Q2 FY2026
   presentations (3.1x / 3.0x appear in narrative only). It **is** a printed row in the FY2026 release.
8. **Contracted Fee-for-Service revenue backlog:** FY2026 only.
9. **ToP gross-margin contribution percentage (51% / 45%):** FY2026 release only.
10. **LTIF:** FY2026 release only.
11. **15%+ total-shareholder-return target:** Q3 FY2026 release only; not restated later.
12. **$150m / fiscal-2029 brownfield capital envelope and 4x–6x build multiples:** Q1 FY2027 only.
13. **Company-basis figures before 2025-07-28** do not exist (incorporation date); before **2025-10-15**
    the Company held no interest in the Business, and all 2025-07-28 comparative columns print zero.
14. **No Q4-only Company-basis cash flow statement** — the FY2026 release prints only the
    inception-to-date column (`3409150` p.10), although p.9 does give a three-month income statement.
15. **No Company-basis comparative income statement** in the Q1 FY2027 release — single column only.
16. **No FX-translation line** in the Q1 FY2027 Company cash flow.
17. **No shares purchased under the NCIB disclosed in the FY2026 release** (only the permitted maximum);
    the first purchase figure appears in Q1 FY2027.
18. **No segment, regional or facility-level financial split** anywhere in the four releases — Alberta
    and California are discussed only qualitatively.
19. **No reconciliation** of the *"net earnings would have been $259m / $76m / $267m"* Legacy Incentive
    Plan adjustments; they are narrative-only and are not named non-IFRS measures.
20. **No payout-ratio figure** — the policy says *"conservative payout ratio"* without quantifying it.
21. **No weighted-average share counts** are printed in any release, so the EPS and DCF-per-share
    denominators cannot be independently verified.

---

## 9. Judgment calls made, and why

1. **Substituting documentId 4064732 for 2235906.** Rationale, evidence and per-row flagging in §1.1.
   An unflagged blank quarter would have been silently misleading in a four-period series; an
   unflagged substitution would have breached SPEC §3.1. Flagging every row satisfies both.
2. **`period_type=YTD` for LAST TWELVE MONTHS columns.** SPEC §4 offers only `FY | Q | instant | YTD`.
   LTM is none of these. I used `YTD` — the nearest multi-period value — and put an explicit warning
   in the `note` of **every** LTM row: *"period_type YTD used for a LAST TWELVE MONTHS column… This
   release presents LTM, NOT fiscal-year-to-date and NOT a fiscal year."* Affects `2794952` and
   `3693793`. **Do not aggregate LTM rows with fiscal-year rows.**
3. **`[no caption printed]` for unlabelled subtotals.** See §4.2.
4. **Units outside the SPEC enum.** Megawatts, basis points, Bcf/day, decatherms, years, C$ per share
   and the "3.1x" ratio have no enum value. I used `count` (or `usd` for $/Dth, `cad_millions` for the
   C$28.60 per-share price) and stated the real unit explicitly in the `note` — e.g.
   *"unit = basis points; sign negative to denote a reduction"*, *"UNIT NOTE: this is C$ PER SHARE, not
   millions"*. **These `count` and `cad_millions` KPI rows must not be scaled by the canonical layer.**
5. **Sign convention for rate reductions.** The −25bp and −75bp repricing figures are printed as
   positive magnitudes with the word "reducing". I stored them **negative** and said so in the `note`,
   so a downstream sum does not accidentally add basis points.
6. **Dividend growth target stored as `value=5, unit=pct`** with the full *"3-5%"* range in the `note`
   — a range cannot be a single numeric cell, and 5% is the rate actually declared.
7. **The Quarterly Results Summary "Revenue" row** (`4064732` p.14) is an IFRS measure sitting inside a
   non-IFRS table. I kept `statement=non_ifrs` to preserve the table's integrity and flagged it in the
   `note` rather than splitting one printed table across two `statement` values.
8. **Repeated captions within one reconciliation.** "Operating", "General and administrative" and
   "Other items" each appear **twice** (added back to reach Adjusted Gross Margin, then deducted to
   reach Distributable Cash Flow). Both occurrences are kept, distinguished by `order_index` and by a
   `note` reading *"second occurrence of caption, deducted"*.
9. **Extractor artifacts kept, not repaired.** See §4.1. SPEC §4 forbids tidying captions; a silent fix
   would be undetectable downstream, whereas a flagged artifact is auditable.
10. **`get_financials` was never called**, per SPEC §2. Every figure in the CSV comes from document text.

---

## 10. Row census

| | rows |
|---|---|
| **Total** | **881** |
| by document | `3409150` 251 · `2794952` 241 · `3693793` 223 · `4064732` 166 · `2235906` **0** |
| by basis | `business_100` 662 · `company` 219 |
| by statement | `non_ifrs` 608 · `cash_flow` 76 · `balance_sheet` 72 · `kpi` 58 · `income_statement` 51 · `comprehensive_income` 10 · `dividends` 6 |
| rows missing `source_page`, `source_url`, `basis` or `value` | **0** |
| rows whose `source_url` lacks `&rp=` | **0** |
