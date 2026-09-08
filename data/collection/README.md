# Collecting the 40 identical SKUs

The point of this basket: **no spec judgement**. Every row is the same brand and
model on all three shelves, so the only question is the price. It is the most
defensible number this tool can produce.

## How to run it

1. Open `identical_sku_worksheet.csv` in a spreadsheet. 53 candidates are
   pre-filled with brand, product, pack size and unit of measure — over-provisioned
   so ~40 survive carriage attrition.
2. For each row, search the product at each retailer.
   - **Not carried?** Put `n` in that retailer's `*_carried` and move on.
   - **Carried?** `y`, then record `price` **exactly as the shelf shows it** —
     per bag, per roll, per piece, whatever the tag says. Do not convert. The
     tool converts, and the audit trail survives.
   - Fill `sku` and `url` so anyone can re-check the number later.
   - `promo_price` only if it is on offer today; leave blank otherwise.
3. Check `pack_coverage`. It is pre-filled with the expected pack size (50 for a
   50 lb bag, 54 for a 54 sq ft roll, 8.17 for an 8'2" profile). **If a retailer's
   pack differs, correct it** — that is exactly the trap this tool exists to
   catch, and it is also a signal the products may not be identical.
4. Set `same_product_confirmed=y` only once you are satisfied it is genuinely the
   same product. Ingest refuses the row otherwise, by design.
5. Set `collected_on` (YYYY-MM-DD) and, if you have it, `annual_volume` in the
   row's basis units. Volume is what turns unit prices into a basket cost — the
   comparison still runs without it, but the weighted numbers do not.

Prices are store- and ZIP-specific at all three retailers. **Collect every row
against one store per banner, and note which** — otherwise the comparison mixes
markets.

## Then

```bash
python3 -m fnd_pricing ingest data/collection/identical_sku_worksheet.csv \
    --groups-out data/raw/sku_groups.csv --products-out data/raw/products.csv
python3 -m fnd_pricing validate
python3 -m fnd_pricing basket
```

Partial runs are fine — ingest reports untouched candidates as "not yet
collected" rather than as errors, so you can stop and resume.

Keep every run: copy the finished worksheet to
`data/collection/snapshots/worksheet_YYYY-MM-DD.csv` before the next one.
History cannot be back-filled.

## What this basket is and is not

National-brand three-way overlap concentrates in setting materials, grout,
membrane, profiles and tools. Flooring and tile are private-label on all three
sides, so almost nothing there can be an identical SKU. **This basket therefore
under-weights the categories that carry the spend** — it is a clean audit of
price position, not a picture of the business. The wider 200-SKU study is what
covers the flooring assortment, and it needs spec matching to do it.

`C053` (TrafficMaster) is a deliberate control: it is a Home Depot exclusive and
should fail carriage at the other two. If it does not, check the row.
