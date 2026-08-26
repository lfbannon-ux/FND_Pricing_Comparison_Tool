# Rockpoint Gas Storage Inc. (TSX: RGSI) — historical financial model

Audit-quality model built from primary filings, every figure as originally reported and
carrying a source document, page and deep link. IFRS, US dollars, fiscal year ending 31 March.

---

## 1. Read this before comparing any two numbers

**The filings present two different sets of figures, and they are not comparable.**

| Basis | What it is | Periods available |
|---|---|---|
| `business_100` | The underlying gas storage Business on a **100% basis** — the combined consolidated financial statements of **Swan Equity Aggregator LP** and **BIF II CalGas (Delaware) LLC**. Audited by **Deloitte LLP** under IFRS. | FY2026 as reported; FY2025 as comparative; four interim periods Q2 FY2026 → Q1 FY2027 |
| `company` | **Rockpoint Gas Storage Inc.** itself, which acquired a **40% interest** from Brookfield on **2025-10-15** (IPO closing). Brookfield retains 60%, held *beside* the Company at OpCo level, not beneath it. | One 246-day stub period only |

They are carried as **parallel, separately labelled blocks** and never merged onto a shared row.

**Rockpoint has essentially one year of reported history.** The IPO closed 15 October 2025 —
*during* FY2026 — so FY2026 is its first annual reporting cycle as a public issuer. There is no
standalone FY2025 annual filing: FY2025 exists only as the comparative column of the FY2026
statements, and is flagged and italicised throughout. **No CAGR in this model would be meaningful**,
and none is presented.

---

## 2. The numbers story (business_100, audited)

US$ millions.

| | FY2026 | FY2025 | Change |
|---|---:|---:|---:|
| Total revenues | 479.4 | 415.3 | **+15.4%** |
| Earnings before income taxes | 223.5 | 198.8 | +12.4% |
| Net earnings | 206.9 | 209.4 | −1.2% |
| Net margin | 43.2% | 50.4% | −7.2 pts |
| Effective tax rate | 7.4% | (5.3)% | — |
| Cash from operations | 190.1 | 313.7 | −39.4% |
| Free cash flow (CFO + capex) | 157.2 | 278.8 | −43.6% |
| Total assets | 1,239.7 | 1,430.2 | −13.3% |
| Cash and cash equivalents | 42.3 | 204.1 | −79.3% |
| Total debt | 1,209.5 | 1,233.9 | −2.0% |
| Net debt | 1,167.2 | 1,029.8 | +13.3% |
| Owners' equity (deficiency) | **(238.8)** | **(85.8)** | — |
| Distributions | (456.9) | (628.9) | — |

Management's own (non-IFRS) measures: Adjusted Gross Margin **459.1** vs 412.4, Adjusted EBITDA
**385.9** vs 338.8, Distributable Cash Flow **251.6** vs 234.5.

**What actually happened.** Revenue grew 15.4% on higher Take-or-Pay rates and strong Optimization
performance. Net earnings nonetheless fell slightly, because FY2026 absorbed a **$51.5m payment
under Brookfield's legacy long-term incentive plans** — funded in full by Brookfield Infrastructure
and offset by an equal capital contribution, so no liquidity impact on Rockpoint or Class A
shareholders. Excluding it, net earnings would have been ~$259m. **Do not read the earnings decline
as operational deterioration.**

Cash fell from 204.1 to 42.3 and net debt rose despite gross debt falling, because 456.9 of
distributions were paid out. Equity is a **deficiency** on both dates — pre-IPO distributions to
Brookfield exceed retained earnings — so **ROE and ROIC are deliberately suppressed** rather than
shown as meaningless negatives.

**Capital structure.** A $1,234.4m senior secured Term Loan B (due Sept 2031, hedged at ~5.65%)
and a $350m revolver (matures Oct 2030, undrawn). The Company is lead borrower and **jointly and
severally liable as guarantor for debt sitting in entities it owns 40% of**.

---

## 3. Structural breaks, in chronological order

Full detail with sources on the **Accounting Notes** tab (28 rows). The ones that change conclusions:

1. **2025-07-28** — Company incorporated. Its reporting period is the 246-day stub
   *"July 28, 2025 to March 31, 2026"*, of which only **168 days carry any economic activity**.
   Not a full year; no annualisation is valid.
2. **2025-10-15** — IPO closes; Company acquires 40%. Trading began **15 October 2025** (widely
   reported secondary sources say 9 October; the AIF is explicit that it was the 15th, and
   "October 9" appears nowhere in the document).
3. **No Company comparatives at all** — the MD&A states outright that none is provided. Q2 FY2026 is
   the only interim filing with Company statements and **every figure in them is nil**; Q3 FY2026 and
   Q1 FY2027 contain none.
4. **FY2025 cash-flow reclassification** (Note 21) — amounts previously shown as "notes extended to
   related parties" moved to "distributions", **with no before/after amounts disclosed**. FY2025
   financing lines therefore will not match FY2025 as originally reported.
5. **Q3 FY2026 onward** — the cash flow splits "Amortization of deferred financing costs" out of
   "Other" in both current and comparative columns, never labelled as a reclassification.
6. **Non-IFRS definitions changed twice** — Q4 FY2026 deleted three adjusting items; Q1 FY2027 added
   equity-settled compensation.
7. **Distributable Cash Flow is not like-for-like** — FY2025 maintenance capex was restated down
   $5.5m, and FY2026 excludes a $19.3m one-time lease payment. The reported **+7% DCF growth
   overstates the true movement**.
8. **DCF-per-share denominator changed twice** (133m hard-coded → dropped → weighted average), with
   the NCIB starting 2026-03-27.
9. **The second headline column changes basis three times** across the releases: 6M YTD → LTM → FY →
   LTM. LTM rows must never be aggregated with FY rows.

---

## 4. Genuine non-disclosures (deliberate blanks, not gaps in the work)

- **No EPS, no share counts, no dividends per share** in the audited Business statements — the
  reporting entity is an LP + LLC combination. Note 12 Share Capital has no table and no numbers.
  Per-share data exists only on the Company basis, for the stub period.
- **No segment analysis** — a single reportable segment. Note 20 is geographical only and splits
  **U.S./Canada, not Alberta/California**. Optimization is not disaggregated geographically.
- **No total-current-liabilities subtotal** in the audited annual statements. The model derives it
  as a labelled in-sheet formula (black, never blue); it reconciles the balance sheet to 0.0000.
- **No year-by-year debt amortisation schedule** — only <1yr / 1–3 / 3–5 / >5 buckets.
- **Facility capacity is disclosed at four-asset level** though six facilities are described: Lodi +
  Kirby Hills (28.7 Bcf combined) and Suffield + Countess (154.0 Bcf combined). Total 279.2 Bcf foots
  exactly, but a six-row capacity table cannot be built.
- **Inaugural dividend dates** could not be verified in any available document.
- **Customer mix: four of five slices unresolved** — the donut chart yields 36/28/20/8/8%, but only
  "Producers 8%" pairs unambiguously in extracted text.

### Not obtained — and why
The **supplemented PREP Prospectus dated 2025-10-08** is the sole source of as-originally-reported
**FY2023–FY2025**. Every filing archive (SEDAR+, the IR site, TSX, `files.quartr.com`) is blocked by
this environment's **network egress policy** — a 403 at the proxy CONNECT stage, which is an
organisation policy denial, not a transient error. `scripts/fetch_primary.py` is written and armed to
run the full download the moment those hosts are allowlisted. See `filings/UNOBTAINED.md`.

Also unavailable: the Q2 FY2026 earnings release (documentId 2235906) **has no text layer** — all 10
pages return empty. Q2 figures were taken from the companion Q2 FY2026 MD&A filed the same day, and
those rows are marked `SUBSTITUTE SOURCE` and separable on `source_doc`.

---

## 5. Verification performed

| Gate | Result |
|---|---|
| Extraction self-verification | Balance sheets foot on both bases at **all 8 dates**; all income-statement columns tie revenues → EBT → net earnings; all cash-flow columns tie and every closing cash agrees to balance-sheet cash |
| Note-table footing | **53 footing checks + 8 cross-statement ties** on the annual notes, ~250 on the interims — **zero failures** |
| Non-IFRS reconciliations | Foot in **all 16 columns** across four documents, through Adjusted EBITDA → Adjusted Gross Margin → Distributable Cash Flow |
| Canonical transform | **4,539 canonical cells + 257 duplicates absorbed + 6 excluded = 4,802 source rows.** LEFTOVERS **0**, COLLISIONS **0** |
| Workbook recalculation | Headless LibreOffice: **zero** formula errors across 28,149 populated cells |
| Integrity checks | **11 of 11 tie at 0.0000** in every period |
| Spot-read | 15 rendered figures read back from the recalculated file and checked against the filings — **0 mismatches** |

The guards did real work. They caught a **map bug of mine** (an unanchored regex folding "Foreign
exchange gain related to investing activities" into the investing subtotal), a **double-count** in a
derived subtotal, and **two genuine inter-filing discrepancies** (Q4 FY2025 Adjusted Gross Margin
134.1 vs 134.2; Q3 FY2025 113.1 vs 113.0) which are preserved side by side rather than silently
collapsed — see `canonical/RESTATEMENTS.md`.

One correction worth stating plainly: **Quartr's standardized financials feed is unusable for this
issuer.** It labels the long-term asset subtotal as "total assets" (1,030.7 when the real figure is
**1,239.7**) and reports total current *assets* as total current *liabilities*, and it mixes the two
reporting bases. Everything in this model comes from filing text instead.

---

## 6. Files

| Path | What it is |
|---|---|
| `build/Rockpoint_Gas_Storage_Historical_Model.xlsx` | The workbook — 29 tabs |
| `SUMMARY.md` | This document |
| `extraction/SPEC.md` | The binding extraction contract |
| `extraction/*.csv`, `*_NOTES.md` | Verbatim extraction + per-agent notes, oddities and non-disclosures |
| `canonical/canonical.csv` | Canonical rows, one per economic line item |
| `canonical/caption_map.csv` | Full audit trail: canonical row ← verbatim caption ← period |
| `canonical/accounting_notes.csv` | The 28 structural breaks |
| `canonical/RESTATEMENTS.md` | Inter-filing discrepancies, both values retained |
| `canonical/TRANSFORM_LOG.md` | Every duplicate absorbed, exclusion and unit conversion |
| `filings/manifest.csv` | The reachable document universe |
| `filings/UNOBTAINED.md` | Every blocked source and the exact remedy |
| `scripts/` | The pipeline: fetch → canonicalize → build → verify |

**Colour code:** blue = hard input exactly as filed (never a formula) · black = formula in the sheet
· green = formula linking to another sheet · italic blue = a comparative.
**Blank = not reported. Dash = reported zero.** Reading a blank as zero is the likeliest way to
misuse this workbook.
