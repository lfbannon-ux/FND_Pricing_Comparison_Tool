#!/usr/bin/env python3
"""DRY RUN: fill both worksheets with simulated prices.

This does NOT collect prices. The retailers publish no price API and their
domains are blocked at this environment's network egress proxy, so no automated
collection is possible from here. What this script does is exercise the whole
pipeline - two worksheets, two evidence grades, five retailers, one merged
dataset - so the machinery is proven before anyone spends a morning collecting.

Every row it writes is stamped `data_source=seed_estimate` and the output goes
to data/demo/, never to data/collection/. The real run is the same commands
against the real worksheets; nothing downstream changes.

Run:  python3 scripts/fill_worksheets_demo.py
"""

from __future__ import annotations

import csv
import random
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from fnd_pricing import RETAILER_CODES, RETAILERS  # noqa: E402
from fnd_pricing.collect import (  # noqa: E402
    STANDARD_IDENTICAL,
    worksheet_columns,
)

SEED = 20260910
COLLECTED_ON = "2026-09-10"
DATA_SOURCE = "seed_estimate"

# Floor & Decor price level on each category's comparison basis.
LEVEL = {
    "Setting Materials": (0.30, 0.62),
    "Grout & Caulk": (0.78, 1.55),
    "Membrane & Backer": (1.30, 2.90),
    "Tile Trim & Edging": (4.50, 13.00),
    "Underlayment": (0.32, 0.88),
    "Installation Tools": (14.00, 175.00),
    "Sealers & Care": (9.00, 44.00),
    "Trim & Moulding": (1.60, 5.80),
    "Luxury Vinyl Plank": (1.29, 4.99),
    "Porcelain Tile": (1.19, 5.99),
    "Ceramic Tile": (0.79, 2.99),
    "Mosaic & Decorative Tile": (8.99, 22.99),
    "Natural Stone Tile": (4.49, 11.99),
    "Engineered Hardwood": (3.29, 8.99),
    "Solid Hardwood": (3.99, 7.99),
}

# Competitor position. Identical SKUs price close together; spec-matched
# comparisons spread much wider because the products genuinely differ.
POSITION = {
    "home_depot": (0.99, 1.12),
    "lowes": (0.98, 1.11),
    "menards": (0.94, 1.06),
    "tile_shop": (1.02, 1.18),
}
SPEC_SPREAD = 1.9          # widen the band for spec-matched rows

COMPETITOR_BRANDS = {
    "floor_and_decor": ["NuCore", "AquaGuard", "DuraLux", "Salerno", "Sonoma"],
    "home_depot": ["LifeProof", "TrafficMaster", "Home Decorators Collection"],
    "lowes": ["SMARTCORE", "Style Selections", "allen + roth"],
    "menards": ["Tuscany", "Patrician", "Dakota"],
    "tile_shop": ["Rush River", "Marmi", "Kismet"],
}

# Where each banner does not merchandise the category at all.
ABSENT = {
    "tile_shop": {
        "Engineered Hardwood", "Solid Hardwood", "Trim & Moulding",
        "Underlayment", "Sealers & Care",
    },
}
P_NOT_CARRIED = 0.12
P_PROMO = 0.15


def snap(value: float) -> float:
    if value < 10:
        return max(0.09, round(int(value * 10) / 10 + 0.09, 2))
    if value < 100:
        return round(int(value) + 0.98, 2)
    return round(round(value / 10) * 10 - 1, 2)


def downgrade(specs: str, rng: random.Random) -> str:
    """Make a competitor's spec sheet genuinely differ, as real ones do."""
    parts = [p for p in specs.split(";") if "=" in p]
    if not parts or rng.random() > 0.35:
        return specs
    index = rng.randrange(len(parts))
    key, value = parts[index].split("=", 1)
    if key in {"wear_layer_mil", "veneer_mm", "thickness_mm", "pei_rating"}:
        try:
            parts[index] = f"{key}={float(value) * rng.choice([0.6, 0.75]):g}"
        except ValueError:
            return specs
    elif key in {"finish", "finish_tile"}:
        parts[index] = f"{key}={rng.choice(['matte', 'polished', 'smooth'])}"
    return ";".join(parts)


def fill(path: Path, out: Path, rng: random.Random) -> tuple:
    rows = list(csv.DictReader(open(path, newline="", encoding="utf-8")))
    priced = skipped = 0

    for row in rows:
        category = row["category"]
        low, high = LEVEL.get(category, (5.0, 40.0))
        base = rng.uniform(low, high)
        identical = row["match_standard"] == STANDARD_IDENTICAL
        row["collected_on"] = COLLECTED_ON
        row["data_source"] = DATA_SOURCE
        row["annual_volume"] = str(int(rng.uniform(400, 90000)))
        row["same_product_confirmed"] = "y" if identical else ""

        carried_any = False
        for retailer in RETAILERS:
            code = RETAILER_CODES[retailer]
            if category in ABSENT.get(retailer, set()):
                row[f"{code}_carried"] = "n"
                continue
            if retailer != "floor_and_decor" and rng.random() < P_NOT_CARRIED:
                row[f"{code}_carried"] = "n"
                continue

            if retailer == "floor_and_decor":
                index = 1.0
            else:
                lo, hi = POSITION[retailer]
                if not identical:
                    mid = (lo + hi) / 2
                    lo, hi = mid - (mid - lo) * SPEC_SPREAD, mid + (hi - mid) * SPEC_SPREAD
                index = rng.uniform(lo, hi)

            unit = base * index
            uom = row["record_uom"]
            coverage = row[f"{code}_pack_coverage"]

            # Home centres quote flooring by the case; Floor & Decor by the foot.
            if uom == "per_sq_ft" and retailer in {"home_depot", "menards"} and rng.random() < 0.6:
                uom = "per_case" if retailer == "home_depot" else "per_box"
                coverage = f"{rng.uniform(16.0, 30.0):.2f}"
            price = snap(unit * float(coverage)) if coverage else snap(unit)

            row[f"{code}_carried"] = "y"
            row[f"{code}_sku"] = f"{code.upper()}-{rng.randrange(100000, 999999)}"
            row[f"{code}_price"] = f"{price:.2f}"
            row[f"{code}_uom"] = uom
            row[f"{code}_pack_coverage"] = coverage
            row[f"{code}_url"] = ""
            if rng.random() < P_PROMO:
                row[f"{code}_promo_price"] = f"{snap(price * rng.uniform(0.8, 0.93)):.2f}"
            if not identical:
                # Each retailer brings its own brand and spec sheet.
                row[f"{code}_brand"] = rng.choice(COMPETITOR_BRANDS[retailer])
                row[f"{code}_specs"] = (
                    row["specs"] if retailer == "floor_and_decor"
                    else downgrade(row["specs"], rng)
                )
            carried_any = True

        priced += 1 if carried_any else 0
        skipped += 0 if carried_any else 1

    out.parent.mkdir(parents=True, exist_ok=True)
    with open(out, "w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=worksheet_columns())
        writer.writeheader()
        writer.writerows(rows)
    return priced, skipped


def main() -> None:
    rng = random.Random(SEED)
    total = 0
    for name in ("identical_sku_worksheet", "flooring_worksheet"):
        source = ROOT / f"data/collection/{name}.csv"
        out = ROOT / f"data/demo/{name}_SEED_PRICES.csv"
        priced, _ = fill(source, out, rng)
        total += priced
        print(f"  {priced:>3} rows priced -> {out.relative_to(ROOT)}")
    print(f"\n{total} simulated SKUs. Every row stamped data_source={DATA_SOURCE}.")
    print("These are NOT collected prices.")


if __name__ == "__main__":
    main()
