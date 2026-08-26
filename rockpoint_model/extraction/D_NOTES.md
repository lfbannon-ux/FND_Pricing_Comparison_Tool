# D_NOTES.md — Agent D extraction notes (FY2026 Annual Information Form)

Per `SPEC.md` §8. Agent D, scope = the qualitative and structural record.

---

## 1. Documents and page ranges actually read

| Document | Quartr `documentId` | Type | Pages | Read |
|---|---|---|---|---|
| Rockpoint Gas Storage Inc., **FY 2026 Annual Information Form**, dated **May 28, 2026** | **3724816** | report (`eventId=554427`, `companyId=21558`, event title "Q4 2026") | **79 of 79** | **complete** — pp.1–79, in eight `read_document` calls (1–7, 8–12, 13–16, 17–19, 20–23, 24–26, 27–29, 30–32, 33–35, 36–38, 39–41, 42–44, 45–48, 49–53, 54–58, 59–63, 64–69, 70–74, 75–78, 79) |

Source PDF (as reported by Quartr):
`https://files.quartr.com/reports/99c3092a1483525dff4fc4ed416153b4-2026-07-08-10-15-53.pdf`

No other document was consulted. **No web search, no `get_financials`, no external source of any kind was used.**
One `read_document` call returned `Rate limit exceeded`; it was retried and succeeded — no page was skipped or
substituted.

**Page-number convention.** All `source_page` values and all deep-links in `D_aif_qualitative.md` use the **PDF page
number** returned by `read_document` (`pageNumber`), which is what `&rp=<page>` resolves to. The AIF's own printed footer
page number is **PDF page − 2** (PDF p.3 carries the footer "FY2026 Annual Information Form | 1"). Where the AIF's own
table of contents is quoted in the narrative, its printed page numbers are labelled as such and are **not** converted.

---

## 2. Verification results (SPEC §7, adapted)

SPEC §7 checks 1–3 and 5 (balance sheet foots, income statement ties, cash flow ties, cross-statement cash) are
**not applicable** to this document: **the AIF contains no primary financial statements**. It contains no balance sheet,
no income statement, no cash flow statement and no statement of changes in equity. It defines the Annual Financial
Statements ([p.65](https://web.quartr.com/companies/21558?companyId=21558&documentId=3724816&documentType=report&eventId=554427&navigation=external&utm_medium=referral&utm_source=mcp&rp=65))
and points to SEDAR+ for them.

SPEC §7 check 4 ("note tables foot to their own printed totals") **is** applicable and was run on every numeric table in
the AIF. Results:

| # | Check | Result |
|---|---|---|
| 1 | **Facility capacities sum to the stated portfolio total.** 75.0 (Wild Goose) + 28.7 (Lodi Storage Facility) + 154.0 (AECO Hub™) + 21.5 (Warwick) | = **279.2 Bcf**, exactly the printed total at [p.11]. **PASS** |
| 2 | **AECO Hub™ well count.** Suffield 58 + Countess 27 ([p.15]) vs the facility table's 85 | = **85**. **PASS** |
| 3 | **IPO gross proceeds.** 32,000,000 × C$22.00 | = **C$704,000,000**; filing prints "approximately C$704.0 million". **PASS** |
| 4 | **October 2025 Secondary Offering gross proceeds.** 4,800,000 × C$22.00 | = **C$105,600,000**; filing prints "approximately C$105.6 million". **PASS** |
| 5 | **February 2026 Secondary Offering gross proceeds.** 16,400,000 × C$28.00 | = **C$459,200,000**; filing prints "**approximately C$459.0 million**". **MISMATCH of C$0.2m.** The filing's own figure is prefixed "approximately", so this is rounding, not an error. **Recorded exactly as printed (459.0)** with the discrepancy noted on the row. **No adjustment made.** |
| 6 | **Class A share count.** 32,000,000 (IPO) + 21,200,000 (to Selling Shareholders) vs the 53,200,000 outstanding at [p.49] | = **53,200,000**. **PASS** |
| 7 | **The 40/60 split.** 53,200,000 ÷ (53,200,000 + 79,800,000) | = **40.00%**, matching "the public owns … 40% of the aggregate number of outstanding Shares" at [p.5]. **PASS.** *(The 133,000,000 denominator is not printed by the filing — see §5, judgment call J1.)* |
| 8 | **Brookfield's post-IPO 72.3%.** (16,400,000 + 79,800,000) ÷ 133,000,000 | = **72.331%**; filing prints "approximately 72.3%". **PASS** |
| 9 | **Contracting mix table columns foot to 100%** ([p.17]). FY25 Rev 44+44+12; FY26 Rev 49+32+19; LT AGM target 60+25+15; FY25 AGM 45+41+14; FY26 AGM 51+32+17 | **100 / 100 / 100 / 100 / 100.** **PASS** — and this is what established that the extractor's column alignment on that table is correct (see §4, O1). |
| 10 | **Customer mix chart sums to 100%** ([p.22]). 36 + 28 + 20 + 8 + 8 | = **100**. **PASS on the values**; the label→value pairing nonetheless **fails** (see §4, O2). |
| 11 | **Brookfield OpCo percentages.** 36.37% + 23.63% (per OpCo, from the org chart at [p.6]) | = **60.00%**, matching the narrative's 60% at [p.5]. **PASS** |
| 12 | **Lock-up residual.** 16,439,750 (aggregate lock-up) − 16,400,000 (waived 2026-02-17) | = **39,750**, exactly the Class A shares still restricted at 2026-03-31 per [p.52]. **PASS** (the AIF does not print this subtraction). |
| 13 | **Class A restriction percentage.** 39,750 ÷ 53,200,000 | = **0.0747%**; filing prints **0.07%**. **PASS** (rounding). |
| 14 | **D&O ownership percentage.** 40,245 ÷ 53,200,000 | = **0.0756%**; filing prints "**approximately 0.08%**". Rounds to 0.08% only if rounded up from 0.0756 — consistent with "approximately". **PASS (weak)**; both figures recorded as printed, no adjustment. |
| 15 | **Term Loan drawn vs original.** $1,234.4m outstanding vs $1,250.0m original principal | outstanding is **$15.6m below** original — consistent with scheduled TLB amortisation. **No inconsistency.** Note the AIF prints **no amortisation schedule**. |
| 16 | **Lodi pipeline lengths.** Narrative: Lodi Facility 50 km + Kirby Hills 10 km = **60 km**, vs the facility table's **Owned Pipeline 72 km** ([p.13]) | **DOES NOT RECONCILE — 12 km unexplained.** Recorded verbatim on both rows with the discrepancy in `note`. **No adjustment made.** See §4, O5. |
| 17 | **Regulatory compliance spend table** ([p.26]). 4.0 + 5.6 + 1.2 + 0.2 | = **11.0**; the filing prints **no total row**, so there is nothing to foot against. Recorded as four rows; the arithmetic total is flagged in the `note` field as *not printed*. |
| 18 | **Deloitte fee table** ([p.60]). 806,652 + 587,848 | = **1,394,500**; the filing prints **no total row**. Same treatment as #17. |
| 19 | **Trading table internal sanity.** High ≥ Low in all six months | **PASS** in all six rows — this is what confirms the extractor's High/Low/Volume triplet alignment (see §4, O3). |
| 20 | **OpCo Interest Acquisition consideration.** $882.0m aggregate ([p.57]) − $450.4m cash ([p.9], [p.57]) | implies **$431.6m** of share consideration for 21,200,000 Class A Shares ≈ **$20.36/share**, versus the **deemed C$25.00** price — implies an FX of ≈ 0.814 USD/CAD, plausible for October 2025. **CONSISTENT.** The **$431.6m residual is NOT printed by the filing** and is **not** written to the CSV as a value row; it appears only in the `note` field of the $882.0m row. See §5, judgment call J2. |

**Nothing in the AIF was adjusted, corrected, derived or back-solved into a value cell.** Where a figure did not foot
(#5, #16) it was recorded exactly as printed and flagged.

---

## 3. Restatements and reclassifications disclosed by the filing

**None.** The AIF discloses **no restatement, no reclassification, no change in accounting policy and no correction of a
prior-period error.** It contains no financial statements to restate. The only "prior period" content is the FY25 column
in the contracting-mix table at [p.17], which carries no restatement note.

Two changes in *presentation basis* are structural rather than restatements, and are recorded so the modeller does not
mistake them for one:
- The Company **held no interest in the Business before 2025-10-15**; its own audited statements cover a **stub period
  from incorporation (2025-07-28) to 2026-03-31**, with a comparative balance sheet date of **2025-07-28** and **no
  comparative income statement** ([p.65]). This is consistent with `SPEC.md` §2.
- The **Warwick Facility entered the portfolio on 2025-10-14** ([p.9]) via a common-control transfer from a Brookfield
  affiliate. The AIF presents the 279.2 Bcf portfolio total **including** Warwick's 21.5 Bcf, but says nothing about how
  Warwick is presented in the comparative FY2025 Business-basis financials. **Whether FY2025 comparatives include
  Warwick is not disclosed here** — see §6.

---

## 4. Caption oddities, extractor artefacts, sign conventions, footnotes

**O1 — Contracting mix table ([p.17]) column alignment: RESOLVED, high confidence.** The PDF extractor returns the three
row labels, then all five column headers, then the fifteen values in three rows of five. The mapping was **proved** by
column footing (every column = 100%, check #9). No guesswork.

**O2 — Customer mix donut chart ([p.22]) label→value pairing: NOT RESOLVED. Four values deliberately omitted from the
CSV.** The extractor returns:
```
Financial Institutions / Utilities / 28 % / 36 % / Producers 8 % / 8 % / 20 % / Other / Marketers
```
Five labels (Financial Institutions, Utilities, Producers, Other, Marketers) and five values (36, 28, 20, 8, 8) summing
to 100%. **Only "Producers 8 %" appears adjacent to its own value** and is therefore the only pairing that can be
proved; it is the only customer-mix row in `D_aif_facts.csv`. The other four are ambiguous in two independent ways:
- **Financial Institutions vs Utilities** could be 28/36 (extractor reading order: label, label, value, value) or 36/28
  (paired reading order). The narrative — "Financial institutions comprise a **significant portion**"; "utilities
  represent an **important component**" — is suggestive of FI > Utilities but is **not decisive**.
- **Other vs Marketers** for the remaining {20, 8} is likewise unresolved, though 20% Marketers / 8% Other is the more
  natural reading of a chart that lists Marketers as a named customer group and Other as a residual.

Per `SPEC.md` §3 rule 2 and §9, **no guess was written**. The unresolved set is recorded here in full so a later agent
with access to the source PDF image can close it: **{Financial Institutions, Utilities} ↔ {36%, 28%}** and
**{Marketers, Other} ↔ {20%, 8%}**, FY2026 fee-for-service revenue basis.

**O3 — Trading table ([p.52]) triplet alignment: RESOLVED, high confidence.** The extractor emits the six month labels,
then the three column headers, then eighteen values in High/Low/Volume triplets. Every triplet satisfies High ≥ Low and
every third value is a six/seven-digit share count, so the alignment is unambiguous (check #19).

**O4 — Month label garbled.** The first trading month prints as "**October ( 1531 ) 2025 ( 2 )**". "(2)" is the
footnote marker; "(1531)" is extractor noise with no counterpart in the filing. The month is October 2025, established by
footnote (2) ("commenced trading on the TSX on **October 15, 2025**") — note that **1531** contains "15" and the footnote
number, so it is almost certainly a mangled overlay of the footnote marker onto the date. Recorded in the row `note`.

**O5 — Lodi pipeline lengths do not reconcile ([p.13]).** Facility table: **Owned Pipeline 72 km**. Narrative: Lodi
Facility connected "via a **50 km** pipeline"; Kirby Hills "linked to two interconnections west of Rio Vista by a
**10 km** pipeline". 50 + 10 = 60 ≠ 72. **Both figures recorded verbatim; no reconciliation attempted.** The 12 km gap is
unexplained by the filing (it may be intra-complex pipe not described, or an error).

**O6 — Identical compression figure at two different facilities ([p.12], [p.13]).** Wild Goose gas-generated compression
is **27,970 horsepower**; Kirby Hills gas-generated compression is also **27,970 horsepower**. An exact match across two
unrelated facilities is suspicious and may be a filing copy-paste error, but it **is what is printed**. Recorded verbatim
on both rows with the coincidence flagged. **No adjustment made.**

**O7 — Dividend table dates are PAYMENT dates, not quarter ends ([p.48]).** The table's left column reads "Quarter –
Payment Date": "**Second Quarter – December 31, 2025**" and "**Third Quarter – March 31, 2026**". A reader skimming will
mistake these for quarter ends. FY2026 Q2 ended **2025-09-30** and Q3 ended **2025-12-31**; the dividends were *paid*
one quarter in arrears. In the CSV, `period_label` carries the **quarter the dividend relates to** (Q2 FY2026, Q3 FY2026)
and `period_end` carries the **payment date**, with the convention stated in each row's `note`. Practical consequence:
**only $0.44/share was actually paid within FY2026**; the Q4 FY2026 dividend of $0.231 is payable **2026-06-30**, i.e.
in FY2027.

**O8 — Internal date inconsistency on the dividend increase ([p.48], same page).** Body text: "announced an increase to
its quarterly dividend from $0.22 per Class A Share to $0.231 per Class A Share **on May 28, 2026**". Table note (1):
"**On May 27, 2026**, the Board **declared** a quarterly cash dividend of $0.231 per Class A Share". A one-day
discrepancy on the same page. The two verbs differ (announced vs declared), which may reconcile it — declared 27th,
announced 28th (the AIF date) — but **the filing does not say so**. Both recorded verbatim; the CSV row uses the table
note's **2026-05-27** declaration date and flags the body text.

**O9 — Organizational chart at [p.6] is heavily scrambled.** Entity names, jurisdictions, ownership percentages and GP
markers are interleaved out of order and **individual parent–child edges cannot be reliably reconstructed**.
`D_aif_qualitative.md` §1.5 therefore lists **only** the entities, jurisdictions and percentages that are legible, and
explicitly declines to assert edges. The four Brookfield percentages (36.37% / 23.63%, twice) **were** recorded to the
CSV because they are self-verifying (they sum to the 60% stated in the narrative, check #11). The two "40%" edges from
the Company to each OpCo are corroborated verbatim by the narrative at [p.5].

**O10 — `Starks Gas Storage L.L.C.` (Delaware) appears in the org chart at [p.6] and NOWHERE ELSE in the AIF.** It is
not in the [p.5] list of Rockpoint Gas Storage entities, has no facility, no capacity, no description and no glossary
entry. It is presumably a dormant or non-operating entity — but **the AIF does not say**. Recorded here as an open item.

**O11 — Directors table row alignment ([p.54]).** The extractor returns names in one block, appointment dates in
another, and occupations in a third. The mapping in §8.1 of the narrative follows the printed sequence and is
independently corroborated at four points (McKenna's CEO biography matches the officers table at [p.55]; Chhina's
Deloitte partnership matches the Audit Committee bio at [p.59]; Cella's and Devine's bios likewise). Confidence is
**high but not absolute**; no director data was written to the CSV, so this affects the narrative only.

**O12 — "Largest gas storage facilities" chart ([p.21]) — RECONSTRUCTED, medium confidence.** Owners, facility names
and capacities are returned interleaved. The pairings were reconstructed on a **strict descending-capacity rule**: the
extracted text yields 12 western-Canada facility names against 12 values and 9 California names against 9 values, and
**both value sequences are already strictly descending** in the source text, which is how such charts are ordered. The
reconstruction is corroborated by Rockpoint's own four entries, which independently match the facility pages: 154 = AECO
Hub™ (154.0), 75 = Wild Goose (75.0), 29 ≈ Lodi & Kirby Hills (28.7), 22 ≈ Warwick (21.5) — the chart rounds to whole
Bcf. **Every reconstructed row in `D_aif_facts.csv` carries an explicit `note` saying so.** Non-Rockpoint rows should be
treated as **medium confidence** and are not fit for any purpose more demanding than market-context colour.

**O13 — Rounding: chart vs facility pages.** The competitor chart rounds Lodi & Kirby Hills to **29** (vs 28.7) and
Warwick to **22** (vs 21.5). Both roundings are recorded as printed on their respective rows; the CSV therefore contains
two different values for the same asset from two different pages. This is correct per `SPEC.md` §3 rule 1 (as printed)
and is flagged in each row's `note`.

**O14 — TIER carbon prices printed with inconsistent currency symbols ([p.24]).** Within one paragraph the AIF writes
"Alberta froze the TIER price at **C$95**/tonne", then "the headline price … will hold at **$95**/tonne … before
gradually rising to **$140**/tonne by 2040", then "the effective price of carbon will increase to **$130**/tonne", then
"a minimum transfer price for TIER credits starting at **$60** per tonne, which will rise incrementally to
**$110**/tonne in 2040". Since the AIF's currency convention is "$ = US dollars, C$ = Canadian dollars" ([p.3]), the
bare "$" figures would literally read as **USD** — which is almost certainly not intended for an Alberta provincial
carbon price. **Recorded verbatim in the narrative with the symbols exactly as printed** and flagged here. No carbon
prices were written to `D_aif_facts.csv` (out of the CSV scope assigned to this agent), so no unit assignment was forced.

**O15 — "$" in the regulatory compliance spend table ([p.26]) and the Deloitte fee table ([p.60])** is unqualified and
therefore **US dollars** per the AIF's currency convention. Recorded as `usd_millions` and `usd` respectively.

**O16 — "Nil" is an explicit reported zero.** Tax Fees and All Other Fees at [p.60] print "**Nil**", not a dash and not a
blank. Per `SPEC.md` §4 these are reported zeros: recorded as **value 0** with `note=printed as Nil`.

**O17 — Two spellings/short forms in the source.** The AIF writes both "**ToP**" and "**TOP**" for take-or-pay (the
extractor uppercases inconsistently); the glossary defines "**ToP**" means take-or-pay ([p.69]). `line_item` captions in
the CSV use **ToP**, matching the glossary and the body text. Also "AECO Hub™" appears with and without the trademark
symbol; the CSV uses "AECO Hub" without it for CSV-safety, with the trademark retained in the narrative.

**O18 — Sign conventions: not applicable.** Every numeric figure in the AIF is presented positive. There are no
parentheses, no negative values, no credit-balance captions and no em-dash zeros anywhere in this document.

**O19 — Forward-looking section names a development project the business description does not.** [p.62] lists
"the potential brownfield expansion projects at the Wild Goose Facility, the **Kirby Hills Facility** and the Warwick
Facility". But the Description of the Business gives **Development Opportunities** subsections for **Wild Goose**
([p.12]), **AECO Hub™/Countess** ([p.15]) and **Warwick** ([p.16]) only — **there is no Kirby Hills development
subsection and no Kirby Hills brownfield expansion is described anywhere**. Conversely the forward-looking list omits
the Countess battery project despite describing "the battery storage projects at the Countess Facility and the Warwick
Facility" in the same bullet. Recorded as an internal inconsistency; **no Kirby Hills expansion figure exists to
extract**.

**O20 — Footnote markers preserved in captions.** Where a printed caption carries a footnote marker it is retained
verbatim in `line_item` per `SPEC.md` §4 — e.g. `Audit Fees (1)`, `Class A Shares (1) - % of Class`,
`ToP Contracts - Long-Term AGM Target Mix (1)`.

---

## 5. Judgment calls made, and why

**J1 — Wrote one derived value row: total Shares outstanding = 133,000,000 ([p.49]).** `SPEC.md` §3 rule 2 forbids
derivation. I wrote this single row anyway, with `is_subtotal=1` and an explicit `note` reading
"**NOT PRINTED by the filing — derived here only as an audit check that 53.2m/133.0m = 40.0%**". Reason: the 40/60 split
is the load-bearing fact of the entire structure and the denominator that proves it is the one number the AIF never
prints. Flagging it loudly in-row was judged better than burying it in notes. **If the canonical layer enforces
"printed values only", this row should be dropped** — it is the only derived value in the file and it is
self-identifying. Every other value in `D_aif_facts.csv` is printed in the AIF.

**J2 — Did NOT write the $431.6m implied share consideration.** [p.57] prints $882.0m aggregate and $450.4m cash; the
$431.6m residual would be a back-solve, which `SPEC.md` §3 rule 2 forbids. It appears **only** in the `note` field of
the $882.0m row, never as a value. (Contrast with J1, where the derived figure is a pure cross-check of an already-stated
percentage rather than a substantive new consideration amount.)

**J3 — Unit enum extended in three places, all documented.** `SPEC.md` §4 gives a closed unit list that does not cover
this document's contents. Rather than mis-label a figure, three extensions were used:
- **`cad_per_share`** — for C$ share prices (IPO C$22.00, deemed C$25.00, secondary C$28.00, option strike C$25.75,
  monthly trading highs/lows, C$0.000001 Class B liquidation entitlement). Using the enum's `usd_per_share` for a
  Canadian-dollar price would have been a data defect; `SPEC.md` §5 says "State the unit the filing prints".
- **`tcf`** — one row only: the North American market's ~5.6 Tcf ([p.19]). Converting to 5,600 Bcf would have been a
  silent rescale, forbidden by §5.
- **`cad_millions`** — C$704.0m, C$105.6m, C$459.0m gross proceeds and the C$14m Warwick battery cost. This one is
  already in the SPEC enum; noted here only for completeness.

**J4 — Physical units (MMcf/d, km, horsepower, MW, years) recorded as `unit=count` with the real unit in `note`.** The
SPEC enum has no physical-quantity units. Every such row carries `note=printed_unit=<unit>` (e.g.
`printed_unit=MMcf/d`, `printed_unit=km`, `printed_unit=horsepower`, `printed_unit=MW`, `printed_unit=year`). **A
downstream consumer must read the `note` field before using these values** — `count` is a placeholder, not a meaning.
Only **Bcf** capacities use a true unit (`bcf`), since that is in the enum and is the figure the model actually needs.

**J5 — `basis` assignment.** `SPEC.md` §2 requires every row to carry a basis. Assignments:
- **`business_100`** — everything describing the Business itself: facility capacities and statistics, development
  projects, contracting mix, regulatory compliance spend, headcount, and the historical Salt Plains/Tres Palacios/Warwick
  transaction amounts.
- **`company`** — everything at the Rockpoint Gas Storage Inc. level: share counts, share prices, prior sales, transfer
  restrictions, dividends, ownership percentages, credit facilities, audit fees.
- **Industry statistics** (North American / Californian / Alberta market size, competitor capacities, the Tionesta
  compressor retirement) are **neither basis** — they describe third parties. They were assigned **`business_100`**
  because they appear in the Business description, and **every such row carries a `note` marking it a third-party
  industry statistic**, so they can be filtered out. This is a forced choice created by `basis` being mandatory.
- The **Term Loan and Revolving Credit Facility rows are `company`** even though the debt sits in RGSP LP and RGSC (i.e.
  at the Business level), because the AIF presents them under "Capital Structure" as "**the Company's** credit
  facilities" ([p.51]) and because the Company is lead borrower and joint-and-several guarantor ([p.41]). **A modeller
  must not treat $1,234.4m as 40%-attributable Company debt without reading the MD&A** — see §6 gap G7.

**J6 — `period_type` for monthly trading data.** The SPEC enum offers `FY | Q | instant | YTD`; there is no monthly type.
Trading rows use `period_type=instant` with `period_end` = the month end and `period_label` = the month name
(e.g. "October 2025"), and each row's `note` says "monthly range" or "monthly total".

**J7 — `period_label`/`period_end` for point-in-time structural facts.** Facility capacities, share counts and ownership
percentages are stated "as at March 31, 2026" or "as of the date of this Annual Information Form" (2026-05-28). All were
recorded as `FY2026 / 2026-03-31 / instant`, since the AIF's own convention is "presented as of March 31, 2026, except as
indicated otherwise" ([p.3]). Where a fact is explicitly tied to a different date (post-IPO ownership at 2025-10-15,
prior sales dates), `period_label` and `period_end` reflect that date instead.

**J8 — Which prospectus page range maps to which prospectus section is an INFERENCE.** The TOC at [p.2] prints
"149-155 ; 192-198" against the Material Contracts row without labelling either. The narrative's mapping
(149–155 = "Description of Share Capital and OpCo Interests – The OpCos"; 192–198 = "Relationship with Brookfield –
Agreements Between the Company and Brookfield") follows the order in which the AIF text lists the two references at
[p.58] and normal prospectus ordering. **It is not stated by the filing** and is labelled as an inference in
`D_aif_qualitative.md` §9.

**J9 — MD&A page-range attributions in §9 of the narrative are reconstructed from the TOC's two-column layout.** The
extractor returns the TOC's incorporation column as loose numbers ("15-17", a bare "4", a bare "6", "29-30", "21-28",
"149-155 ; 192-198") interleaved with the AIF's own page numbers. Each attribution was **confirmed against the in-text
cross-reference**, which names the incorporated MD&A section explicitly (e.g. [p.4] names "Non-IFRS Measures Utilized by
Our Business"; [p.19] names "Importance of Natural Gas Storage"; [p.26] names "Seasonality of the Business"; [p.51] and
[p.58] name "Liquidity and Capital Resources"). Section names are therefore **certain**; the page ranges attached to
them are **high confidence**.

**J10 — Did not extract the Audit Committee Charter (Appendix B, pp.71–79) line by line.** It is a standard governance
charter with no financial or structural content bearing on the model. It was **read in full**; the model-relevant items
(three-member requirement, independence and financial literacy, the OpCo engagement provision, the quarterly meeting
cadence, and the notably strict Brookfield-inclusive independence definition at [p.79]) are summarised in
`D_aif_qualitative.md` §8.5. Nothing from it is in the CSV.

---

## 6. WHAT THE AIF DOES **NOT** DISCLOSE — explicit list of deliberate blanks

These are the gaps another agent must fill from another document, or leave blank. **None of them was estimated,
interpolated or filled from memory.**

### 6.1 Facility-level splits

- **G1 — The Lodi Storage Facility's 28.7 Bcf is NOT split between the Lodi Facility and the Kirby Hills Facility.** Only
  the combined figure is given ([p.11], [p.13]). Well counts, injection/withdrawal rates, interconnects and owned
  pipeline are likewise **combined only**. Compression is the sole item split (26,600 hp Lodi / 27,970 hp Kirby Hills).
- **G2 — The AECO Hub™'s 154.0 Bcf is NOT split between Suffield and Countess.** Only the combined figure is given
  ([p.14], [p.15]). Wells (58/27), reservoirs (5/2) and compression (36,150/34,500 hp) **are** split, but capacity,
  injection rate, withdrawal rate, interconnects and owned pipeline are **combined only**.
- **G3 — No cushion (base) gas volume is disclosed for any facility**, in aggregate or individually — despite "effective
  working gas storage capacity" being defined by reference to base gas ([p.66]).
- **G4 — No portfolio-level deliverability total is printed.** The four facility tables give per-asset max injection and
  withdrawal; the AIF never sums them.
- **G5 — No facility-level revenue, gross margin, EBITDA, capex, contracted volume, utilisation rate or contract-term
  profile.** The only per-facility financial figure in the entire AIF is **FY26 regulatory compliance spend** ([p.26]).
  There is no segment disclosure of any kind.
- **G6 — No storage rate, tariff, demand charge, injection/withdrawal fee or price per Bcf** for any contract type, any
  facility or any period.

### 6.2 Financials, debt and capital

- **G7 — No financial statements at all.** No income statement, balance sheet, cash flow statement or statement of
  changes in equity, on either basis. No revenue, no Adjusted Gross Margin figure (only the *mix* percentages), no net
  earnings, no total assets, no equity. The AIF defines the Annual Financial Statements ([p.65]) and points to SEDAR+.
- **G8 — No Term Loan pricing.** No margin, no spread over SOFR, no floor, no OID, no all-in rate, no effective hedged
  rate. **No repricing, amendment, refinancing or margin-change event is disclosed anywhere in the AIF.** The AIF gives
  only: original principal $1,250.0m, agreement dated 2024-09-18, maturity September 2031, $1,234.4m outstanding at
  2026-03-31, 60/40 RGSP LP / RGSC allocation, SOFR benchmark, 100% hedged through September 2031, minimum debt service
  coverage ratio covenant — then defers to the MD&A ([p.51]). **The "term loan repricing" I was asked to record is
  simply not in this document.**
- **G9 — No Term Loan amortisation schedule and no maturity ladder.**
- **G10 — No covenant levels.** The AIF names the two financial covenants (minimum debt service coverage ratio; maximum
  total net leverage ratio) but gives **no threshold, no actual ratio and no headroom** ([p.42]).
- **G11 — No Revolving Credit Facility pricing, commitment fee, or letter-of-credit sub-limit.** It also does **not**
  say whether letters of credit were outstanding at 2026-03-31 — only that there were **no cash drawings** ([p.51]),
  which is a carefully narrow statement.
- **G12 — No credit ratings** for the Company or any borrower.
- **G13 — No use-of-proceeds statement for the IPO.**
- **G14 — No NCIB activity.** The NCIB commenced 2026-03-27, four days before year end; the AIF does **not** disclose
  whether any shares were purchased, at what price, or the cost. No post-year-end NCIB update either.
- **G15 — No option plan detail beyond the single 132,844 grant** — no plan maximum, no vesting schedule, no
  outstanding-award reconciliation, no share-based compensation expense. Equity compensation plan securities are
  **deferred to the management information circular** ([p.61]).
- **G16 — No distributions actually received from the OpCos.** The AIF gives the *policy* (OpCos target 50–60% payout,
  40% to the Company) but **no actual distribution amount** for FY2026.

### 6.3 Customers, contracts and operations

- **G17 — No named customer and no quantified customer concentration.** The risk factor says only that the Business
  "relies on **certain key customers** for a significant portion of its revenues" ([p.34]). **No number of major
  customers, no percentage-of-revenue threshold, no named counterparty.** The customer *category* mix at [p.22] is the
  only quantification, and four of its five slices are unresolved (see §4, O2).
- **G18 — No contract backlog, no weighted-average remaining ToP contract term, no contracted-capacity percentage, no
  renewal rate.** ToP terms are described as "typically ranging from one to ten years" and STS as "typically spanning up
  to one storage season with a strong history of contract renewals" ([p.17]) — qualitative only.
- **G19 — No volumetric operating data.** No gas injected, withdrawn, cycled or held in inventory; no utilisation
  percentage; no proprietary optimization inventory volume or value.
- **G20 — No hedge book detail** beyond "100.0% of the principal borrowings under the Term Loan were hedged through
  September 2031" ([p.43]). No notional, no fixed rate achieved, no commodity/FX/power/carbon hedge positions, no
  mark-to-market.
- **G21 — No capital expenditure figures** other than the four regulatory compliance spend amounts and the C$14m Warwick
  battery cost. No maintenance capex total, no growth capex, no five-year plan quantification (the five-year plan is
  mentioned at [p.26] but never quantified).
- **G22 — No decommissioning/abandonment obligation amount**, despite abandonment being a named risk ([p.41]) and
  abandonment costs being a stated component of AECO Hub™ and Warwick compliance spend ([p.26]).
- **G23 — No employee breakdown** by geography, function or union status; only the total of 148 at 2026-03-31 ([p.26]).
- **G24 — No ESG metrics.** No GHG emissions figure, no safety statistic (TRIR/LTIF), no diversity data — only policies
  and programs are described ([p.27]–[p.28]).

### 6.4 Structure and corporate

- **G25 — The org chart's parent–child edges are not recoverable** from the extracted text (see §4, O9). What each
  intermediate holding entity owns is **not** asserted in the narrative.
- **G26 — `Starks Gas Storage L.L.C.` is unexplained** (see §4, O10).
- **G27 — No financial information for the OpCos individually.** Swan OpCo and BIF OpCo are never presented separately;
  the audited Business statements are the **combined** consolidated statements of both.
- **G28 — Warwick's treatment in the FY2025 comparative is not disclosed.** Warwick joined the portfolio 2025-10-14 via
  a common-control transfer; the AIF says nothing about whether FY2025 Business-basis comparatives are restated to
  include it. **This materially affects any FY25→FY26 growth calculation** and must be resolved from the financial
  statements.
- **G29 — Director and officer remuneration and indebtedness, and principal shareholders, are deferred to the
  management information circular** ([p.61]), which is **not yet filed** as at the AIF date.
- **G30 — No individual director or officer shareholdings** — only the group total of 40,245 Class A Shares ([p.55]).
- **G31 — CPUC Application outcome unknown.** Filed 2026-01-12, "**remains under review** by the CPUC as of the date
  hereof" ([p.10]). No expected timeline is given. The Exchange Right becomes exercisable **2026-10-15** but is blocked
  to the extent it would cause a change of control of Wild Goose or Lodi without CPUC Approval — **so the timing of any
  Brookfield exchange is genuinely unknowable from this document.**
- **G32 — No pro-forma or as-if-full-year FY2026 figures** for the Company, despite the Company existing for only part
  of the year.

### 6.5 What the AIF defers to the **IPO Prospectus** (unavailable to us)

The IPO Prospectus is the **supplemented PREP prospectus dated October 8, 2025** ([p.67]). It is incorporated by
reference for **exactly one thing** — the substantive terms of seven material contracts ([p.58]):

| Deferred content | Prospectus section named | TOC page range at [p.2] |
|---|---|---|
| **A&R LPA** (Swan OpCo partnership agreement) and **LLC Agreement** (BIF OpCo) — full rights and obligations of Swan GP, the Swan limited partners and the BIF OpCo members | "**Description of Share Capital and OpCo Interests – The OpCos**" | **149–155** (mapping inferred — see §5, J8) |
| **Business Transfer Agreement**, **Shareholder Agreement**, **Registration Rights Agreement**, **Exchange Agreement**, **Relationship Agreement** — full terms | "**Relationship with Brookfield – Agreements Between the Company and Brookfield**" | **192–198** (mapping inferred — see §5, J8) |

**What this means in practice:** the AIF gives usable *summaries* of the Exchange Right, the One-to-One Ratio
Requirements, the nomination-rights ladder, the OpCo governance arrangements and the transfer restrictions
([p.6]–[p.8], [p.50]–[p.51]) — enough to model the structure. What is **only** in the Prospectus is the operative
detail: **OpCo distribution mechanics and waterfalls, capital account and allocation provisions, tax distribution
provisions, GP removal and consent rights, drag/tag rights, transfer mechanics, and any economic terms of the OpCo
agreements beyond the 40/60 split.** None of that is recoverable from the AIF.

### 6.6 What the AIF defers to the **Annual MD&A**

Six incorporations (see `D_aif_qualitative.md` §9). The model-critical ones:

- **"Liquidity and Capital Resources" (MD&A pp.21–28)** — the **only** stated source for Term Loan and Revolving Credit
  Facility detail: pricing, covenant levels, amortisation, availability, and any repricing. Referenced twice, at [p.51]
  and [p.58].
- **"Non-IFRS Measures Utilized by Our Business" (MD&A pp.15–17)** — the full Adjusted Gross Margin definition and, by
  implication, its **reconciliation to net earnings**. The AIF gives the definition but **no AGM figure and no
  reconciliation** ([p.3]–[p.4]).
- **"Qualitative and Quantitative Disclosures about Market Risk" (MD&A pp.29–30)**, including "**– Interest Rate Risk**"
  — all quantified market risk exposure ([p.33], [p.44]).
- **"Organizational Overview – Business Overview – Importance of Natural Gas Storage" (MD&A p.4)** — further North
  American market data ([p.19]).
- **"Organizational Overview – Seasonality of the Business" (MD&A p.6)** — the substantive seasonality analysis. The
  AIF's own seasonality section is one paragraph that points here; the useful seasonality content in the AIF is in the
  **risk factors** at [p.32] and [p.34], not in the seasonality section ([p.26]).

### 6.7 Referenced but not incorporated

- **Business acquisition report dated December 1, 2025** for the OpCo Interest Acquisition — on SEDAR+ ([p.10]). This is
  where any pro-forma or acquired-business financial information for the 40% OpCo stake would live.
- **Annual Financial Statements** ([p.61], [p.65]).
- **Management information circular** for the next annual meeting — not yet filed ([p.61]).
- **Full text of the nine material contracts** on SEDAR+ ([p.58]).

---

## 7. Contradictions with the brief I was given

| Claim in my instructions | What the AIF actually says | Status |
|---|---|---|
| Trading began **2025-10-09** | "The Class A Shares **commenced trading on the TSX on October 15, 2025**, the closing date of the Initial Public Offering" ([p.52]). The monthly trading table's first row is **October 2025**; there is no earlier month. **October 9, 2025 appears nowhere in the AIF.** | **CONTRADICTED.** Use **2025-10-15** for first trade unless a better source says otherwise. Note that 2025-10-08 (prospectus) and 2025-10-15 (closing and first trade) bracket the 9th, so an October 9 conditional/when-issued date is conceivable — but it is **not in this filing**. |
| **Term loan repricing** | **No repricing, amendment, refinancing or margin change is disclosed anywhere in the AIF.** See §6.2, G8. | **NOT IN THIS DOCUMENT.** Must come from the Annual MD&A "Liquidity and Capital Resources" (pp.21–28). |
| "The **six facilities**" | Correct as to count, but the AIF presents them as **four commercial assets**, two of which are two-site complexes: Wild Goose (1 site), Lodi Storage Facility (Lodi + Kirby Hills), AECO Hub™ (Suffield + Countess), Warwick (1 site). **Capacity is disclosed at the four-asset level, not the six-site level** — see §6.1, G1 and G2. | **Refinement, not a contradiction.** A six-row facility table with individual capacities **cannot** be built from this document. |
| "RGSP LP" listed alongside the Company and the OpCos as part of the ownership structure | **RGSP LP = Rockpoint Gas Storage Partners LP (Delaware)** ([p.68]) is an **operating entity beneath Swan OpCo**, not a holding entity above or beside the Company. Its significance is that it is a **Term Loan and Revolver borrower** ([p.51], [p.68], [p.69]) carrying ~60% of Term Loan principal, and the pre-IPO employer of most current executives ([p.55]). | **Refinement.** |
| Everything else — supplemented PREP prospectus 2025-10-08; closing 2025-10-15; 32,000,000 Class A at C$22.00; ~C$704m gross; NCIB commenced 2026-03-27; Brookfield retains 60%; the Exchange Right; the Business Transfer Agreement; the LLC Agreement | All confirmed verbatim. See `D_aif_qualitative.md` §2.1 for the citation table. | **CONFIRMED** |

---

## 8. Output files written

| File | Contents |
|---|---|
| `D_aif_qualitative.md` | The structured narrative record. **Every** factual claim carries a PDF page reference rendered as a live Quartr deep-link ending `&rp=<page>`. 70 distinct pages of the 79 are cited. |
| `D_aif_facts.csv` | **203 rows**, long format per `SPEC.md` §4, columns in the specified order. Bases used: `business_100`, `company`. Statements used: `kpi`, `share_data`, `dividends`, `note_debt`, `note_other`, `non_ifrs`. Units used: `bcf`, `shares`, `usd_per_share`, `count`, `pct`, `usd`, `usd_millions`, `cad_millions`, plus the two documented extensions `cad_per_share` and `tcf` (§5, J3). No blank-value rows. Every row carries `source_doc`, `source_page` and a `source_url` ending `&rp=<source_page>` (validated programmatically: 0 mismatches). |
| `D_NOTES.md` | This file. |
