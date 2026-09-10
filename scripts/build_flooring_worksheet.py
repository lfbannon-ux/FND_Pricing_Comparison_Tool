#!/usr/bin/env python3
"""Generate the LVT / Tile / Hardwood collection worksheet.

These three categories carry roughly 70% of the assortment's spend and almost
none of its identical SKUs. Private label runs on every side, and even the
national flooring brands segment their collections by retailer - Bruce's Lowe's
line is "America's Best Choice" with Lowe's-only model codes - specifically so
that a shelf-to-shelf price comparison cannot be made.

So these rows use the second evidence grade. Each candidate is a
**specification to match**, not a product to find: the collector picks each
retailer's closest comparable at the same market position and records that
product's own brand and specs. The matching engine then scores the tier, so the
comparison carries its own confidence rather than an assumed identity.

Two disciplines make or break this collection:

1. **Match the market position, not just the spec.** Compare Floor & Decor's
   mid-tier 20 mil SPC against each competitor's mid-tier 20 mil SPC. Picking a
   competitor's premium line against Floor & Decor's opening price point
   produces a large, meaningless gap.
2. **Record what you actually found, not what you were looking for.** If the
   closest product is 12 mil rather than 20, write 12. The matcher will
   downgrade the tier, which is the system working - a `close` match honestly
   labelled beats an `equivalent` one that is wrong.

Run:  python3 scripts/build_flooring_worksheet.py
"""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from fnd_pricing.collect import (  # noqa: E402
    STANDARD_IDENTICAL,
    STANDARD_SPEC,
    Candidate,
    write_worksheet,
)

SPEC_NOTE = "record each retailer's own brand + actual specs"
TIER_NOTE = "match the market position, not only the spec"

# (category, basis, product, pack, uom, specs, notes)
LVT = [
    ("Luxury Vinyl Plank", "Opening price point SPC", "core=SPC;wear_layer_mil=6;thickness_mm=4.0;width_in=6;length_in=48;attached_pad=no;install=click;waterproof=yes;look=oak"),
    ("Luxury Vinyl Plank", "Value SPC", "core=SPC;wear_layer_mil=12;thickness_mm=5.0;width_in=7;length_in=48;attached_pad=yes;install=click;waterproof=yes;look=oak"),
    ("Luxury Vinyl Plank", "Mid-tier SPC", "core=SPC;wear_layer_mil=20;thickness_mm=6.0;width_in=7;length_in=48;attached_pad=yes;install=click;waterproof=yes;look=oak"),
    ("Luxury Vinyl Plank", "Premium SPC wide plank", "core=SPC;wear_layer_mil=22;thickness_mm=6.5;width_in=9;length_in=60;attached_pad=yes;install=click;waterproof=yes;look=oak"),
    ("Luxury Vinyl Plank", "Heavy commercial SPC", "core=SPC;wear_layer_mil=28;thickness_mm=8.0;width_in=9;length_in=60;attached_pad=yes;install=click;waterproof=yes;look=oak"),
    ("Luxury Vinyl Plank", "Mid-tier WPC", "core=WPC;wear_layer_mil=20;thickness_mm=6.5;width_in=7;length_in=48;attached_pad=yes;install=click;waterproof=yes;look=hickory"),
    ("Luxury Vinyl Plank", "Premium WPC wide plank", "core=WPC;wear_layer_mil=28;thickness_mm=8.0;width_in=9;length_in=72;attached_pad=yes;install=click;waterproof=yes;look=walnut"),
    ("Luxury Vinyl Plank", "Glue-down LVT plank", "core=flexible;wear_layer_mil=20;thickness_mm=2.5;width_in=6;length_in=48;install=glue;waterproof=yes;look=oak"),
    ("Luxury Vinyl Plank", "Glue-down LVT stone look", "core=flexible;wear_layer_mil=20;thickness_mm=2.0;width_in=12;length_in=24;install=glue;waterproof=yes;look=stone"),
    ("Luxury Vinyl Plank", "Commercial glue-down LVT", "core=flexible;wear_layer_mil=28;thickness_mm=3.0;width_in=6;length_in=36;install=glue;waterproof=yes;look=oak"),
    ("Luxury Vinyl Plank", "Rigid core, cork back", "core=SPC;wear_layer_mil=20;thickness_mm=7.0;width_in=7;length_in=48;attached_pad=cork;install=click;waterproof=yes;look=oak"),
    ("Luxury Vinyl Plank", "Rigid core tile format", "core=SPC;wear_layer_mil=20;thickness_mm=5.0;width_in=12;length_in=24;install=click;waterproof=yes;look=stone"),
    ("Luxury Vinyl Plank", "Entry waterproof wood look", "core=SPC;wear_layer_mil=12;thickness_mm=5.0;width_in=7;length_in=48;attached_pad=no;install=click;waterproof=yes;look=hickory"),
    ("Luxury Vinyl Plank", "Long-plank premium", "core=SPC;wear_layer_mil=22;thickness_mm=6.5;width_in=7.2;length_in=72;attached_pad=yes;install=click;waterproof=yes;look=oak"),
]

TILE = [
    ("Porcelain Tile", "Wood-look plank 6x36", "material=porcelain;size_in=6x36;finish_tile=matte;pei_rating=4;look=wood;rectified=no;thickness_mm=9"),
    ("Porcelain Tile", "Wood-look plank 8x48 rectified", "material=porcelain;size_in=8x48;finish_tile=matte;pei_rating=4;look=wood;rectified=yes;thickness_mm=9"),
    ("Porcelain Tile", "Marble-look 12x24 polished", "material=porcelain;size_in=12x24;finish_tile=polished;pei_rating=3;look=marble;rectified=yes;thickness_mm=10"),
    ("Porcelain Tile", "Marble-look 24x48 large format", "material=porcelain;size_in=24x48;finish_tile=polished;pei_rating=3;look=marble;rectified=yes;thickness_mm=10"),
    ("Porcelain Tile", "Concrete-look 24x24 matte", "material=porcelain;size_in=24x24;finish_tile=matte;pei_rating=4;look=concrete;rectified=yes;thickness_mm=9"),
    ("Porcelain Tile", "Concrete-look 12x24 matte", "material=porcelain;size_in=12x24;finish_tile=matte;pei_rating=4;look=concrete;rectified=no;thickness_mm=9"),
    ("Porcelain Tile", "Opening price point 12x12", "material=porcelain;size_in=12x12;finish_tile=matte;pei_rating=3;look=stone;rectified=no;thickness_mm=8"),
    ("Porcelain Tile", "2cm outdoor paver 24x24", "material=porcelain;size_in=24x24;finish_tile=textured;pei_rating=5;look=stone;rectified=yes;thickness_mm=20"),
    ("Ceramic Tile", "Subway 3x6 glossy white", "material=ceramic;size_in=3x6;finish_tile=glossy;pei_rating=1;look=solid"),
    ("Ceramic Tile", "Subway 4x12 glossy", "material=ceramic;size_in=4x12;finish_tile=glossy;pei_rating=1;look=solid"),
    ("Ceramic Tile", "Floor tile 12x12", "material=ceramic;size_in=12x12;finish_tile=matte;pei_rating=3;look=stone"),
    ("Ceramic Tile", "Wall tile 4x16 matte", "material=ceramic;size_in=4x16;finish_tile=matte;pei_rating=1;look=solid"),
    ("Mosaic & Decorative Tile", "Porcelain hex mosaic 2in", "material=porcelain;pattern=hexagon;chip_size=2x2;finish_tile=matte;size_in=12x12"),
    ("Mosaic & Decorative Tile", "Glass subway mosaic sheet", "material=glass;pattern=subway;chip_size=1x3;finish_tile=polished;size_in=12x12"),
    ("Natural Stone Tile", "Marble 12x24 honed", "material=marble;size_in=12x24;finish_tile=honed;stone_grade=standard;thickness_mm=10"),
    ("Natural Stone Tile", "Travertine 18x18 tumbled", "material=travertine;size_in=18x18;finish_tile=tumbled;stone_grade=standard;thickness_mm=12"),
]

WOOD = [
    ("Engineered Hardwood", "White oak 7.5in, 3mm veneer", "species=white oak;veneer_mm=3.0;thickness_mm=15.0;width_in=7.5;finish=wire brushed;install=click"),
    ("Engineered Hardwood", "White oak 6.5in, 2mm veneer", "species=white oak;veneer_mm=2.0;thickness_mm=12.7;width_in=6.5;finish=wire brushed;install=click"),
    ("Engineered Hardwood", "White oak 5in, entry veneer", "species=white oak;veneer_mm=0.6;thickness_mm=9.5;width_in=5;finish=smooth;install=click"),
    ("Engineered Hardwood", "Hickory 6.5in, 3mm veneer", "species=hickory;veneer_mm=3.0;thickness_mm=12.7;width_in=6.5;finish=hand scraped;install=glue"),
    ("Engineered Hardwood", "Maple 5in, 2mm veneer", "species=maple;veneer_mm=2.0;thickness_mm=12.7;width_in=5;finish=smooth;install=nail"),
    ("Solid Hardwood", "Red oak 2.25in select", "species=red oak;thickness_in=0.75;width_in=2.25;finish=smooth;grade=select"),
    ("Solid Hardwood", "Red oak 3.25in select", "species=red oak;thickness_in=0.75;width_in=3.25;finish=smooth;grade=select"),
    ("Solid Hardwood", "White oak 5in character", "species=white oak;thickness_in=0.75;width_in=5;finish=smooth;grade=character"),
    ("Solid Hardwood", "Hickory 5in hand scraped", "species=hickory;thickness_in=0.75;width_in=5;finish=hand scraped;grade=character"),
    ("Solid Hardwood", "Maple 3.25in select", "species=maple;thickness_in=0.75;width_in=3.25;finish=smooth;grade=select"),
]

# National-brand rows worth TRYING at the identical standard. Flooring brands
# segment collections by retailer, so most of these will fail; when the model
# codes differ, switch the row to spec_matched rather than forcing it.
IDENTICAL_ATTEMPTS = [
    ("Solid Hardwood", "Bruce", "Solid oak 2.25in - match the model code exactly",
     "species=red oak;thickness_in=0.75;width_in=2.25;finish=smooth;grade=select"),
    ("Engineered Hardwood", "Bruce", "Engineered oak - match the model code exactly",
     "species=red oak;veneer_mm=2.0;thickness_mm=12.7;width_in=5;finish=smooth;install=click"),
    ("Luxury Vinyl Plank", "Pergo", "Pergo rigid core - collections differ by banner",
     "core=SPC;wear_layer_mil=20;thickness_mm=6.0;width_in=7;install=click;waterproof=yes"),
    ("Luxury Vinyl Plank", "COREtec", "COREtec plank - check the collection name",
     "core=WPC;wear_layer_mil=20;thickness_mm=8.0;width_in=7;install=click;waterproof=yes"),
    ("Porcelain Tile", "MSI", "MSI porcelain - collections vary by banner",
     "material=porcelain;size_in=12x24;finish_tile=matte;pei_rating=4;look=concrete"),
    ("Ceramic Tile", "Marazzi", "Marazzi ceramic - check the series name",
     "material=ceramic;size_in=4x12;finish_tile=glossy;pei_rating=1;look=solid"),
]


def main() -> None:
    candidates = []
    index = 0

    for category, product, specs in LVT + TILE + WOOD:
        index += 1
        candidates.append(Candidate(
            candidate_id=f"F{index:03d}", category=category, basis="sq_ft",
            brand="", product=product, pack="", record_uom="per_sq_ft",
            specs=specs, pack_coverage="", match_standard=STANDARD_SPEC,
            notes=f"{SPEC_NOTE}; {TIER_NOTE}",
        ))

    for category, brand, product, specs in IDENTICAL_ATTEMPTS:
        index += 1
        candidates.append(Candidate(
            candidate_id=f"F{index:03d}", category=category, basis="sq_ft",
            brand=brand, product=product, record_uom="per_sq_ft", pack="",
            specs=specs, pack_coverage="", match_standard=STANDARD_IDENTICAL,
            notes="identical only if the model code matches; else switch to spec_matched",
        ))

    out = ROOT / "data/collection/flooring_worksheet.csv"
    write_worksheet(candidates, out)
    spec_rows = sum(1 for c in candidates if c.match_standard == STANDARD_SPEC)
    print(f"wrote {len(candidates)} candidates -> {out}")
    print(f"  {spec_rows} spec-matched, {len(candidates) - spec_rows} identical attempts")
    print("  LVT 14 | Tile 16 | Hardwood 10 | national-brand attempts 6")


if __name__ == "__main__":
    main()
