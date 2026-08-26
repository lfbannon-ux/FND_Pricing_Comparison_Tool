# Rockpoint Gas Storage Inc. — Extraction Specification
Contract for all extraction agents. Read fully before extracting a single number.

## 1. Company & filing identity
- Issuer: **Rockpoint Gas Storage Inc.** ("Rockpoint", "the Company"); TSX: **RGSI** (class "A" common shares).
- HQ Calgary, Alberta. Auditor: **Deloitte LLP** (Calgary).
- Reporting framework: **IFRS Accounting Standards as issued by the IASB**. Audit under Canadian GAAS.
- Presentation currency: **USD**. (Some capital-cost figures are quoted in C$ in narrative — keep the currency as printed and mark unit `cad` when so.)
- Fiscal year end: **March 31**. FY labels follow the company's own convention:
  - FY2025 = year ended 2025-03-31
  - FY2026 = year ended 2026-03-31
  - FY2027 = year ending 2027-03-31 (in progress)
  - Quarters: Q1 = Jun-30, Q2 = Sep-30, Q3 = Dec-31, Q4 = Mar-31.

## 2. THE CENTRAL STRUCTURAL TRAP — two reporting bases
This company prints **two different sets of numbers**. Never mix them. Every extracted row MUST carry a `basis` value.

- **`business_100`** — the underlying gas storage/marketing Business on a **100% basis**, being the
  *combined consolidated financial statements of Swan Equity Aggregator LP and BIF II CalGas (Delaware) LLC
  and their wholly-owned subsidiaries*. This is what the **audited annual financial statements** cover
  (FY2026 with FY2025 comparative). Management leads its MD&A discussion with this basis.
- **`company`** — **Rockpoint Gas Storage Inc.** itself, which acquired a **40% interest** in the Business from
  Brookfield on **2025-10-15** (IPO closing). Brookfield retains 60%. The Company held **no interest in the
  Business prior to 2025-10-15**, so Company-basis figures do not exist before that date.
  In the FY2026 earnings release the Company-basis financials appear on **pages 8–10**.

Quartr's standardized `get_financials` feed **silently merges the two bases** (FY2026: total assets 1,030.7
from p.5 vs total liabilities-and-equity 916.3 from p.8 — they do not foot). **Do not use `get_financials`
as a source.** It may be used only as a loose smell-test. All values come from document text.

## 3. Golden rules (priority order)
1. **As originally reported.** Every figure comes from the filing's own printed column for that period.
   A FY2025 figure taken from the FY2026 filing's comparative column is a **comparative**, not an
   as-originally-reported figure — set `is_comparative=1` and name the source doc.
2. **Never fabricate.** A line not reported in a period stays **blank**. Never derive, interpolate, sum,
   back-solve, or "fix". If a printed table does not foot, or a caption looks wrong, or a sign is odd —
   record it **verbatim** and flag it in your notes file. Do not correct it.
3. **Everything auditable.** Every row carries `source_doc`, `source_page`, and `source_url`
   (the Quartr page deep-link, which ends `&rp=<page>`). No row without a page reference.
4. **Verify before trusting.** Self-verify (section 7) before writing your CSV.

## 4. Output schema — long CSV, one row per printed figure
File: `extraction/<agent_id>_<topic>.csv`. UTF-8, comma-separated, quote fields containing commas.

Columns, in this exact order:

    basis, source_doc, source_page, source_url, statement, period_label, period_end, period_type,
    section, line_item, value, unit, is_subtotal, is_comparative, order_index, note

- `basis` — `business_100` | `company` (section 2). Mandatory.
- `source_doc` — Quartr documentId, e.g. `4064735`.
- `source_page` — printed page number as returned by `read_document` (`pageNumber`).
- `source_url` — the page `url` field from `read_document` (already carries `&rp=`).
- `statement` — `income_statement` | `balance_sheet` | `cash_flow` | `equity_changes` | `comprehensive_income`
  | `note_debt` | `note_tax` | `note_ppe` | `note_segment` | `note_revenue` | `note_leases` | `note_equity`
  | `note_financial_instruments` | `note_related_party` | `note_commitments` | `note_other`
  | `non_ifrs` | `kpi` | `dividends` | `share_data`.
- `period_label` — as the company labels it: `FY2026`, `FY2025`, `Q1 FY2027`, `Q3 FY2026`.
- `period_end` — ISO date of period end, e.g. `2026-03-31`.
- `period_type` — `FY` | `Q` | `instant` (balance-sheet / point-in-time) | `YTD`.
- `section` — the filing's own sub-heading (e.g. `Current assets`, `Operating activities`). Verbatim.
- `line_item` — **verbatim caption exactly as printed**, including capitalisation and any footnote marker.
  Do not tidy, expand abbreviations, or normalise.
- `value` — the number **exactly as printed**, sign as printed. Use `-` only as a minus sign.
  Strip thousands separators and currency symbols. A printed value in parentheses is **negative**.
  A printed em-dash / en-dash / "-" meaning "reported zero" → value `0` and `note=printed_dash_zero`.
  Not reported at all → **omit the row entirely** (do not write a blank-value row).
- `unit` — `usd_millions` | `usd_thousands` | `usd` | `cad_millions` | `usd_per_share` | `pct` | `shares`
  | `bcf` | `count` | `text`. State the unit the filing prints; do NOT convert here.
- `is_subtotal` — `1` if the filing presents it as a subtotal/total row, else `0`.
- `is_comparative` — `1` if this period is a comparative column in a filing whose primary period is a
  different period; else `0`.
- `order_index` — integer, ascending in printed order within (statement, basis, period). Preserves layout.
- `note` — free text: caption oddity, footnote reference, sign quirk, "does not foot", etc. Else blank.

## 5. Unit discipline
Record the unit **as the filing prints it**. The statements are generally in USD millions or thousands —
read the column header ("in millions of United States dollars", "$ thousands") and set `unit` accordingly.
Never silently rescale. Conversion to a common unit happens later, in the canonical layer, by script.

## 6. Scope rules
- Extract **every line** of every primary statement: all captions, all subtotals, EPS block, share counts,
  dividends per share, and the comprehensive-income section.
- For notes: extract the full table, every row, including the note's own totals.
- Where a note table is presented for both FY2026 and FY2025, extract **both** columns as separate rows.
- Do not skip a line because it looks unimportant or is zero.

## 7. Mandatory self-verification before writing
Run these and record the result in your notes file:
1. **Balance sheet foots** — total assets == total liabilities + total equity, per basis, per date.
2. **Income statement ties** — the printed subtotals reconcile to printed net earnings.
3. **Cash flow ties** — operating + investing + financing + FX == change in cash; and
   opening cash + change == closing cash.
4. **Note tables foot** to their own printed totals.
5. **Cross-statement** — CF closing cash == BS cash at same date.
If a check fails, **do not adjust the data**. Re-read the page to confirm you transcribed correctly; if the
filing genuinely does not foot, record it in notes with the discrepancy amount and set `note` on the rows.

## 8. Mandatory notes file
File: `extraction/<agent_id>_NOTES.md`. Must contain:
- Documents and page ranges actually read.
- The verification results from section 7, with numbers.
- Every caption oddity, sign convention, and footnote.
- Every restatement or reclassification the filing itself discloses.
- **What is NOT disclosed** in your scope (explicit list of deliberate blanks).
- Any judgment call you made, and why.

## 9. Reading mechanics
- Read documents with the Quartr MCP tool `read_document(documentId, startPage, maxPages)`.
  Long documents return in chunks: when `nextPage` is non-null, call again with `startPage: nextPage`.
  Never stop early because a read was truncated; never substitute a web search for a truncated read.
- `structuredContent.pages[]` gives `pageNumber`, `text`, and `url` — use these for `source_page`/`source_url`.
- Tables arrive as markdown pipe rows. **Column headers are frequently mis-aligned by the PDF extractor**
  (a header row may carry a value, and value rows may be offset). Read the surrounding narrative text to
  confirm which column is which period before assigning values. When alignment is genuinely ambiguous,
  do NOT guess — record what you can prove and flag the ambiguity in notes.
- Checkpoint to disk as you go. Append rows to your CSV per page block; never hold everything to the end.

## 10. Non-negotiable
Never invent a documentId, page number, URL, or figure. If you cannot obtain something, say so in your
notes file and leave it out. An honest gap is a deliverable; a fabricated number is a defect.
