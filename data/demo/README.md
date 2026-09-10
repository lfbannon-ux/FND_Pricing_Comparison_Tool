# Dry run — simulated prices, not collected ones

**Nothing in this directory is a price observation.** Every row is stamped
`data_source=seed_estimate`, and a test enforces it.

The retailers publish no price API and their domains are blocked at this
environment's network egress proxy, so no automated collection is possible.
This directory exists to prove the pipeline end to end — two worksheets, two
evidence grades, five retailers, one merged dataset — before anyone spends a
morning collecting.

## What was run

```bash
python3 scripts/fill_worksheets_demo.py         # simulate prices into data/demo/

python3 -m fnd_pricing ingest \
    data/demo/identical_sku_worksheet_SEED_PRICES.csv \
    data/demo/flooring_worksheet_SEED_PRICES.csv \
    --groups-out data/demo/sku_groups.csv \
    --products-out data/demo/products.csv
```

99 SKUs, 420 offers, 43 priced at all five banners.

Then the whole pipeline against the merged dataset — `validate`, `compare`,
`prices`, `index`, `basket`, `report`, `export`.

## The real run

Identical commands, real worksheets, no code change:

```bash
python3 -m fnd_pricing ingest \
    data/collection/identical_sku_worksheet.csv \
    data/collection/flooring_worksheet.csv
python3 -m fnd_pricing validate && python3 -m fnd_pricing basket
```

Leave `data_source` blank when collecting and it defaults to `collected`.

## What the dry run demonstrates

**The two grades of evidence self-separate.** No extra bookkeeping is needed:
a spec-matched row carries a different brand per retailer, so it cannot score
`exact`. In the dry run every `exact` quote on a flooring row traced back to
F041–F046, the six national-brand rows deliberately declared `identical` — and
zero came from a spec-matched row. So `--tier exact` isolates the
identical-SKU evidence wherever it was collected, and `--min-tier equivalent`
reads everything.

**Merging is guarded.** A candidate id used in two worksheets is refused rather
than silently overwritten, which is why the two instruments use different id
prefixes (`C###` and `F###`).

## What it does not demonstrate

Anything about the actual competitive position. The dry run's numbers come from
the positioning assumptions in `scripts/fill_worksheets_demo.py` — chosen by the
script, not observed — and they differ from the 200-SKU seed dataset's
assumptions, which is why the two produce different answers. That divergence is
the point: **the answer is entirely determined by the input, so the input has to
be real.**
