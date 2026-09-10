# Floor & Decor pricing comparison tool

Compares **200 SKUs** across **Floor & Decor**, **Home Depot**, **Lowe's**,
**Menards** and **The Tile Shop** on a like-for-like basis: every price is restated in a common unit, every competitor
item is scored for how genuinely comparable it is, and only defensible pairs are
allowed to move the headline numbers.

```
python3 -m fnd_pricing compare      # console summary
python3 -m fnd_pricing prices       # every price side by side, as quoted
python3 -m fnd_pricing index        # annual expense by category
python3 -m fnd_pricing basket       # price a basket of identical SKUs only
python3 -m fnd_pricing report       # self-contained HTML report
python3 -m fnd_pricing export       # multi-sheet Excel workbook
```

---

## Read this first: where the prices come from

None of the three retailers publish a price API, and all three block automated
collection, so **the prices shipped in this repository are seed estimates, not
collected prices.** Every seed row is stamped `data_source=seed_estimate`. They
are anchored to how these categories are actually merchandised — real price
bands, real pack sizes, real unit-of-measure conventions, real brand line-ups —
so the tool runs end to end and the output is shaped like the real thing. They
are not a substitute for a collection run.

Everything downstream of the data file — normalisation, matching, indexing,
exception handling, reporting — is production logic. Replace the price rows with
collected ones (see [Loading real prices](#loading-real-prices)) and every number
in the report becomes a real number. Nothing else has to change.

## Quickstart

```bash
git clone <this repo> && cd FND_Pricing_Comparison_Tool
pip install -r requirements.txt          # only needed for the xlsx export
export PYTHONPATH=src

python3 -m fnd_pricing validate          # check the data files and coverage
python3 -m fnd_pricing compare --top 10  # summary + widest gaps
python3 -m fnd_pricing index             # expense by category, ranked
python3 -m fnd_pricing report            # -> data/out/pricing_report.html
python3 -m fnd_pricing export            # -> data/out/pricing_comparison.xlsx
```

Filter to one category, or write the per-SKU detail to CSV:

```bash
python3 -m fnd_pricing compare --category "Porcelain Tile"
python3 -m fnd_pricing compare --csv data/out/sku_detail.csv
python3 -m fnd_pricing prices --csv data/out/raw_prices.csv
python3 -m fnd_pricing index --csv data/out/category_expense.csv
python3 -m fnd_pricing basket --csv data/out/exact_match_basket.csv
python3 -m fnd_pricing basket --tier equivalent    # widen to spec-matched goods
python3 -m fnd_pricing report --min-tier equivalent   # tighten the match bar
```

## How the comparison works

**1. SKU groups, not SKUs.** The unit of analysis is a *SKU group*: one
specification with up to three retailer offers against it. Comparing
"Floor & Decor SKU 12345 vs Home Depot SKU 67890" only means something once you
have asserted the two are the same kind of good, so that assertion is the
primary data structure.

**2. Normalisation.** Retailers quote the same goods differently: Floor & Decor
prices most flooring per square foot, Home Depot often prices the identical
product per case, Lowe's sometimes prices per tile or per square yard, and
setting materials come in 25 lb and 50 lb bags. Each group declares a
**comparison basis** (`sq_ft`, `lin_ft`, `lb`, `each`) and every offer is
converted onto it before anything is compared. A unit of measure that resolves
to the wrong basis is a hard error — silently comparing a per-piece trim price
against per-square-foot tile would produce a confident, meaningless number.

**3. Match confidence.** Each competitor offer is scored against the
Floor & Decor offer on the attributes that actually drive price in that category
(wear layer, core, species, PEI rating, stone grade, chemistry, profile…),
weighted by importance. The score yields a tier:

| Tier | Meaning |
|---|---|
| `exact` | Same brand and model — the identical good |
| `equivalent` | Different brand, specifications align |
| `close` | Specs differ on a secondary attribute |
| `weak` | Not defensible as like-for-like — **excluded** |

Attributes only one retailer publishes are unverified, so confidence is capped
by how much of the group's spec weight was actually comparable. `--min-tier`
controls the bar; the default admits `close` and better.

**4. Measurement.** For each group the tool reports each competitor's gap
against Floor & Decor, the market low across comparable in-stock offers, and a
win / tie / loss outcome. Gaps within ±0.5% are called ties rather than wins.

**5. Rollups.** Category and overall rollups report win rate, median and mean
gap, and a **volume-weighted basket index** — Floor & Decor spend divided by
market-low spend on the same basket. That answers "what would this basket
cost us" rather than averaging unit prices, which would let a $0.30 underlayment
outvote a $9 hardwood.

**6. Expense by category.** Gaps and indexes are *rates*; `index` reports the
*level*. Each category's annual expense is Floor & Decor price x annual volume,
ranked largest first, next to what that expense is worth against the market —
because a 20% gap on a category worth $4k/yr is a rounding error beside a 3% gap
on one worth $900k.

Two things make these numbers trustworthy:

- **Matched baskets.** A retailer's index divides Floor & Decor spend by that
  retailer's spend over *only the SKUs that retailer covers*. Dividing total
  Floor & Decor spend by a competitor's spend across a smaller set would compare
  two different baskets and read as a price advantage that is really just
  missing coverage. The consequence is that an index is comparable to 1.0 but
  **not to the other indexes on its row** — they rest on different baskets.
- **Benchmark coverage.** The share of a category's expense sitting on SKUs
  where some competitor offer was comparable enough to use. The rest is reported
  as unbenchmarked spend rather than quietly ignored.

Average unit price is withheld wherever a category mixes comparison bases —
dollars per square foot and dollars per unit cannot be averaged into a number
that means anything.

**7. Identical-SKU basket.** The headline index mixes identical goods with
spec-equivalents. That is the right default — most of the assortment is private
label on both sides, so refusing to compare anything but identical SKUs would
leave almost nothing to measure — but it means the number partly rests on a
judgement that two different products are substitutes. `basket` strips that
judgement out and prices one tier only, normally `exact`: same brand, same
model, both shelves.

It avoids two traps. The SKUs identical at Home Depot are not the SKUs
identical at Lowe's, so the command reports a **common basket** — the SKUs that
qualify at *every* competitor, the only basket on which all three retailers can
be quoted side by side — alongside each competitor's own wider set. And it
reports both the volume-weighted basket cost and the unweighted per-SKU median,
because they answer different questions and can point opposite ways. The promo
effect is broken out separately, so a temporary discount is never mistaken for a
price position.

**8. Exceptions.** Rows that need a human before anyone acts on them are
flagged, not silently dropped: `no_competitor_offer`, `weak_match`,
`competitor_out_of_stock`, `promo_driven_gap` (the gap reverses at list price,
so it is temporary), `extreme_gap` (>40%), `uom_conversion_error`.

## Collecting the identical-SKU basket

The fastest route to a defensible number. `data/collection/identical_sku_worksheet.csv`
ships pre-filled with 53 national-brand candidates — brand, product, pack size and
unit of measure done; only prices and carriage to fill in. Every row is the same
brand and model at all three retailers, so the comparison needs no spec judgement.

```bash
python3 scripts/build_collection_worksheet.py      # regenerate a blank worksheet
# ... fill it in (see data/collection/README.md) ...
python3 -m fnd_pricing ingest data/collection/identical_sku_worksheet.csv
python3 -m fnd_pricing validate && python3 -m fnd_pricing basket
```

Ingest refuses any row where `same_product_confirmed` is not set: an
identical-SKU basket built from unconfirmed identities is just the spec-matched
comparison wearing a better name. Untouched rows are reported as "not yet
collected", so partial runs resume cleanly.

### Collecting both, and merging them

`ingest` takes several worksheets and merges them into one dataset:

```bash
python3 -m fnd_pricing ingest \
    data/collection/identical_sku_worksheet.csv \
    data/collection/flooring_worksheet.csv
```

A candidate id used twice is refused rather than silently overwritten, which is
why the two instruments use different id prefixes. Provenance travels per row:
`data_source` defaults to `collected` but a dry run can stamp `seed_estimate`
and the claim survives into the dataset — ingest no longer asserts that
everything it touches was observed.

The merged dataset needs no extra bookkeeping to stay honest. A spec-matched row
carries a different brand per retailer, so it cannot score `exact`; `--tier
exact` isolates the identical-SKU evidence and `--min-tier equivalent` reads
everything. `data/demo/` holds a full dry run of exactly this, with every row
stamped as an estimate.

### Two worksheets, two grades of evidence

| Worksheet | Rows | Standard | Covers |
|---|---|---|---|
| `identical_sku_worksheet.csv` | 53 | `identical` | setting materials, grout, membrane, profiles, underlayment, tools, sealers |
| `flooring_worksheet.csv` | 46 | 40 `spec_matched` + 6 `identical` attempts | LVT/LVP, porcelain, ceramic, mosaic, stone, engineered and solid hardwood |

The split is not a preference, it is what the market allows. Identical SKUs
exist in install materials because national brands sell the same bag to
everyone. In LVT, tile and hardwood every side is private label, and even
national flooring brands segment collections by retailer to prevent the
comparison, so those rows record each retailer's **own** brand, specs and unit
of measure and let the matching engine score the tier. A `spec_matched` row can
never come out as `exact`, so the identical-SKU basket stays clean; the flooring
rows land at `equivalent` and `close` and are read with `--min-tier`.

## Loading real prices

1. Generate the collection template:
   ```bash
   python3 -m fnd_pricing template   # -> data/templates/price_collection_template.csv
   ```
2. Collect prices for each `group_id` in `data/raw/sku_groups.csv`. Record the
   price **as the shelf shows it** — do not pre-convert. Put the pack size in
   `pack_coverage` (square feet per case, pounds per bag, feet per piece) and let
   the tool do the conversion, so the audit trail survives.
3. Set `data_source=collected` and fill `collected_on` and `url`.
4. Replace `data/raw/products.csv`, then:
   ```bash
   python3 -m fnd_pricing validate && python3 -m fnd_pricing report
   ```

`validate` reports coverage per retailer, flags groups with no Floor & Decor
price, and names the file and line number of any bad row.

To change the assortment under study, edit `data/raw/sku_groups.csv`. To
regenerate the seed dataset from scratch, run
`python3 scripts/generate_seed_data.py` (deterministic — same seed, same file).

### Data format

`data/raw/sku_groups.csv` — one row per comparison unit:

| column | meaning |
|---|---|
| `group_id` | stable id, referenced by every offer |
| `category`, `subcategory` | rollup keys |
| `basis` | `sq_ft`, `lin_ft`, `lb` or `each` |
| `annual_volume` | units per year on the basis; weights the basket index |
| `specs` | `key=value;key=value` — the reference specification |

`data/raw/products.csv` — one row per retailer offer:

| column | meaning |
|---|---|
| `retailer` | `floor_and_decor`, `home_depot` or `lowes` |
| `price`, `uom` | shelf price and how it is quoted (`per_box`, `per_bag`, …) |
| `pack_coverage` | sq ft per case, lb per bag, ft per piece — required for pack uoms |
| `promo_price` | today's promotional price, if any; blank otherwise |
| `in_stock` | out-of-stock offers do not set the market price |
| `data_source` | `collected` or `seed_estimate` — provenance stays with the row |
| `specs` | this retailer's published specification |

## What the seed data shows

On the shipped seed dataset, the shape is the one you would expect from this
competitive set: Floor & Decor leads decisively on hard-surface flooring and
tile, and gives ground on the categories where the home centres are strong.

| | |
|---|---|
| SKU groups compared | 200 of 200 |
| Win rate vs cheapest competitor | 62% (125W / 11T / 64L) |
| Median gap vs market low | −4.9% |
| Basket index vs market low | 0.950 |
| Basket index vs HD / Lowe's / Menards / Tile Shop | 0.882 / 0.879 / 0.893 / 0.813 |

Adding Menards and The Tile Shop moved the headline, which is the point of adding
them: the market low is now the lowest of four banners rather than two, so
Floor & Decor's win rate falls from 68% to 62% and the market-low index rises
from 0.918 to 0.950. A wider competitive set is a harder benchmark.

The identical-goods basket shows the cost of a wider competitive set. Requiring
an identical SKU at **all four** competitors collapses the common basket from 43
(two competitors) to **19 SKUs** — only 34-38% of each big box's own basket
survives the intersection. On that common basket Floor & Decor is cheaper than
every banner: 5.4% vs Home Depot, 5.1% vs Lowe's, 4.6% vs Menards, 7.5% vs The
Tile Shop. The pairwise baskets are wider (50-56 SKUs each) but rest on different
SKU sets, so they are comparable to 1.0 and not to each other.

Note the two sign conventions in the codebase: `Quote.delta_pct` is the
competitor measured against Floor & Decor (**positive = Floor & Decor cheaper**),
while `GroupComparison.gap_vs_market_min` is Floor & Decor measured against the
market (**negative = Floor & Decor cheaper**). Every report that prints either
states its direction inline.

Expense is heavily concentrated: Luxury Vinyl Plank alone is 38% of it ($14.5M),
and the top four categories carry 72%. The expense view also reverses the
priority the rate view implies: Trim & Moulding and Setting Materials look bad on
median gap (+5.2%, +1.7%) but carry $4.5k of exposure between them, while
Vanities & Tops and Installation Tools carry $228k. Grout & Caulk flips sign
outright — a +3.1% median gap, but a small net *advantage* in dollars, because
the SKUs Floor & Decor wins there are the ones with volume behind them.
**Dollars, not percentages, say where to negotiate.**

Strongest: Wall Tile (−16.3%), Ceramic Tile (−10.0%), Solid Hardwood (−10.8%),
LVP (−10.7%). Weakest: Vanities & Tops (+5.1%), Trim & Moulding (+5.2%),
Grout & Caulk (+3.1%), Installation Tools (+0.0% median but a 1.109 basket
index). Treat the direction as illustrative until real prices are loaded.

## Where the raw data lives

Four views of the same numbers, in increasing order of processing:

| File | Shape | What it holds |
|---|---|---|
| `data/raw/products.csv` | long, one row per offer | the canonical input — price exactly as quoted, uom, pack size, promo, stock, provenance |
| `data/out/raw_prices.csv` | wide, one row per SKU | the same data pivoted for reading: every retailer side by side, shelf price next to normalised unit price |
| `data/out/sku_detail.csv` | wide, one row per SKU | the comparison result — unit prices, gaps, match tiers, outcome |
| workbook `Offers` sheet | long, one row per offer | the audit trail, including the conversion applied to each price |

`raw_prices.csv` is the one to open when the question is "what does each retailer
actually charge for this item" — it shows `$88.99 per_box / 29.69 sq ft` beside the
`$3.00/sq ft` the comparison uses, so a conversion can be checked by eye. A retailer
that carries nothing comparable is **blank, never zero**: a zero would price the item
as free and win every comparison it entered.

## Everyday low price vs high-low: read both

Every price in the study is the price payable today, so a promotion on any side
moves the comparison. That is the right default for "what would a customer pay
this week", and it is the wrong default for reading an **everyday-low-price
position**: an EDLP retailer holds a stable shelf price while high-low
competitors dip in and out of promotion, so a promo-inclusive snapshot flatters
whoever happens to be on sale and understates the EDLP one.

`--list-price` prices every offer at its shelf price, ignoring promotions on
**all** sides — symmetric, or it would simply flatter Floor & Decor:

```bash
python3 -m fnd_pricing compare                # as priced today
python3 -m fnd_pricing --list-price compare   # as priced on the shelf
```

The two answer different questions and both are true. `compare` also flags
`promo_driven_gap` on any SKU whose gap reverses between the two, so a temporary
discount is never mistaken for a price position.

**A snapshot cannot measure EDLP properly at all.** EDLP's value is price
*stability*, which is a property of a price series, not of one day. Comparing a
single day catches competitors at a random point in their promotional cycle. The
honest measure is a time-weighted average across repeated collections — which is
the strongest argument for archiving every collection run from the first one.

## Narrowing the competitive set

`--exclude` and `--only` change which banners a run compares, without a second
dataset:

```bash
python3 -m fnd_pricing --exclude tile_shop compare
python3 -m fnd_pricing --only home_depot --only lowes basket
```

Floor & Decor is always included. Every narrowed run prints the active set,
because this is a **methodology change, not a filter**: win rate and the
market-low index are measured against the cheapest comparable competitor, so
results from different competitive sets are not comparable to each other.

`basket --tier` matches a tier exactly, which is what isolates one grade of
evidence — an `exact` basket must not quietly admit spec-matched rows. Add
`--at-least` for the other question, everything comparable at that tier or
better:

```bash
python3 -m fnd_pricing --exclude tile_shop basket                          # identical SKUs only
python3 -m fnd_pricing --exclude tile_shop basket --at-least --tier close  # all comparable
python3 -m fnd_pricing basket --at-least --tier close --top-skus 10        # what drives it
```

`--top-skus` answers the follow-up to every basket number by splitting it in
two: which SKUs make the basket **big** (spend concentration) and which make it
**expensive** (dollars above the market low). They are usually different lists —
a high-volume opening-price-point plank dominates spend while being a price
advantage, and ranking by spend alone sends a merchant after the wrong item.

## Adding or changing a retailer

The comparison engine is retailer-agnostic: `normalize`, `matching`, `compare`,
`spend` and `basket` contain no reference to any specific banner. A retailer is
added in `src/fnd_pricing/__init__.py` — an entry in `RETAILERS`, a display
name, a short code and a compact label — and every table, chart, CSV column and
worksheet column block scales from there.

Two consequences worth planning for:

- **The common identical-SKU basket shrinks with each competitor added**, because
  a SKU must be an identical match at *all* of them to qualify. `basket` reports
  `common_share` — how much of each competitor's own basket survives the
  intersection — so a thin three-way number cannot pass unnoticed.
- **The market low gets lower.** Win rate and the market-low index are defined
  against the cheapest comparable competitor, so they are only comparable across
  runs with the same competitive set. Changing the set is a methodology change,
  not a data refresh.

A specialist does not merchandise everything. The Tile Shop carries no laminate,
wood, carpet, wood trim, underlayment or vanities in the seed data, which is why
its coverage is ~52% against ~93-96% for the full-line boxes. Missing carriage is
recorded as a missing offer, never as a zero.

## Layout

```
src/fnd_pricing/
  models.py      SKU groups, offers, units of measure
  loader.py      CSV ingestion and validation
  normalize.py   unit-of-measure conversion onto the comparison basis
  matching.py    attribute-weighted like-for-like confidence scoring
  compare.py     gaps, outcomes, exception flags, rollups, basket index
  spend.py       annual expense by category on matched baskets
  basket.py      single-tier basket pricing (identical-SKU comparison)
  collect.py     collection worksheet <-> canonical data files
  charts.py      inline SVG bar and diverging charts for the report
  report.py      self-contained HTML report
  excel.py       multi-sheet workbook (Summary / Category Expense / SKU Detail /
                 Offers / Exceptions)
  cli.py         validate | compare | prices | index | basket | report |
                 export | ingest | template
  __init__.py    the retailer registry - add a banner here and it propagates
data/collection/ identical-SKU and flooring worksheets + collection guide
data/demo/       end-to-end dry run on simulated prices (never collected)
data/raw/        sku_groups.csv, products.csv
data/out/        generated reports
scripts/         seed dataset generator
tests/           130 unit tests
```

## Tests

```bash
PYTHONPATH=src python3 -m unittest discover -s tests
```
