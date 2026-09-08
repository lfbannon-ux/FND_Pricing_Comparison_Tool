# Floor & Decor pricing comparison tool

Compares **200 SKUs** across **Floor & Decor**, **Home Depot** and **Lowe's** on a
like-for-like basis: every price is restated in a common unit, every competitor
item is scored for how genuinely comparable it is, and only defensible pairs are
allowed to move the headline numbers.

```
python3 -m fnd_pricing compare      # console summary
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
| SKU groups compared | 196 of 200 |
| Win rate vs cheapest competitor | 68% (134W / 15T / 47L) |
| Median gap vs market low | −7.7% |
| Basket index vs market low | 0.918 |
| Annual expense at Floor & Decor prices | $38.2M |
| Net annual advantage vs market low | $3.4M |
| Annual expense priced above market low | $233k across 4 categories |

On the 43-SKU identical-goods basket the advantage **narrows but does not
reverse**: the basket costs 4.6% less than Home Depot and 2.9% less than Lowe's,
against ~13% and ~11% across all match tiers, and Floor & Decor is still cheaper
on the median identical SKU (by 2.0% and 3.7%) and on 23 and 28 of the 43 SKUs
respectively. Most of the *size* of the headline advantage lives in private-label
spec-equivalents; the direction holds on identical goods too.

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
  charts.py      inline SVG bar and diverging charts for the report
  report.py      self-contained HTML report
  excel.py       multi-sheet workbook (Summary / Category Expense / SKU Detail /
                 Offers / Exceptions)
  cli.py         validate | compare | index | basket | report | export |
                 template
data/raw/        sku_groups.csv, products.csv
data/out/        generated reports
scripts/         seed dataset generator
tests/           78 unit tests
```

## Tests

```bash
PYTHONPATH=src python3 -m unittest discover -s tests
```
