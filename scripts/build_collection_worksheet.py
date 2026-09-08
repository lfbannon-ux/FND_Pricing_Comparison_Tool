#!/usr/bin/env python3
"""Generate the identical-SKU collection worksheet.

The candidates below are national-brand products expected to be carried by all
three retailers. That expectation is the collector's first job to confirm - the
`*_carried` columns exist precisely so a wrong guess here costs one blank row
rather than a bad comparison.

Over-provisioned to ~52 candidates to land 40 confirmed after attrition.

A deliberate bias to record: national-brand three-way overlap concentrates in
setting materials, grout, membrane, profiles and tools. Flooring and tile are
private-label on all three sides, so almost nothing there can be an identical
SKU. This basket is therefore a clean AUDIT of price position, not a picture of
the business - it under-weights exactly the categories that carry the spend.

Run:  python3 scripts/build_collection_worksheet.py
"""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from fnd_pricing.collect import Candidate, write_worksheet  # noqa: E402

VERIFIED = "carriage verified at all three (Sept 2026 search)"
EXPECTED = "expected at all three - confirm carriage"

CANDIDATES = [
    # --- Setting materials: per_bag, coverage = pounds ---------------------
    ("Setting Materials", "lb", "Custom Building Products", "VersaBond Gray Fortified Thin-Set (MTSG50)", "50 lb bag", "per_bag", "chemistry=modified thinset;color_family=gray;grade=standard", "50", EXPECTED),
    ("Setting Materials", "lb", "Custom Building Products", "VersaBond White Professional Thin-Set (MTSW50)", "50 lb bag", "per_bag", "chemistry=modified thinset;color_family=white;grade=standard", "50", EXPECTED),
    ("Setting Materials", "lb", "Custom Building Products", "VersaBond-LFT Gray Large Format Mortar", "50 lb bag", "per_bag", "chemistry=large format mortar;color_family=gray;grade=premium", "50", EXPECTED),
    ("Setting Materials", "lb", "MAPEI", "Ultraflex 2 Gray Polymer-Modified Mortar", "50 lb bag", "per_bag", "chemistry=modified thinset;color_family=gray;grade=premium", "50", EXPECTED),
    ("Setting Materials", "lb", "MAPEI", "Ultraflex 1 White Mortar", "50 lb bag", "per_bag", "chemistry=modified thinset;color_family=white;grade=standard", "50", EXPECTED),
    ("Setting Materials", "each", "MAPEI", "Type 1 Ceramic Tile Adhesive", "3.5 gal pail", "per_each", "chemistry=mastic;grade=standard", "", EXPECTED),
    ("Setting Materials", "lb", "Laticrete", "254 Platinum Gray Multipurpose Mortar", "50 lb bag", "per_bag", "chemistry=modified thinset;color_family=gray;grade=premium", "50", EXPECTED),
    ("Setting Materials", "each", "Custom Building Products", "AcrylPro Professional Tile Adhesive", "3.5 gal pail", "per_each", "chemistry=mastic;grade=standard", "", EXPECTED),

    # --- Grout & caulk -----------------------------------------------------
    ("Grout & Caulk", "each", "Custom Building Products", "Fusion Pro Single Component Grout", "1 gal pail", "per_each", "chemistry=single component;stain_resistant=yes", "", EXPECTED),
    ("Grout & Caulk", "lb", "Custom Building Products", "Polyblend Plus Sanded Grout", "25 lb bag", "per_bag", "chemistry=sanded;joint_width=0.25", "25", EXPECTED),
    ("Grout & Caulk", "lb", "Custom Building Products", "Polyblend Plus Non-Sanded Grout", "10 lb bag", "per_bag", "chemistry=unsanded;joint_width=0.125", "10", EXPECTED),
    ("Grout & Caulk", "lb", "MAPEI", "Keracolor S Sanded Grout", "25 lb bag", "per_bag", "chemistry=sanded;joint_width=0.25", "25", EXPECTED),
    ("Grout & Caulk", "lb", "MAPEI", "Keracolor U Unsanded Grout", "10 lb bag", "per_bag", "chemistry=unsanded;joint_width=0.125", "10", EXPECTED),
    ("Grout & Caulk", "each", "MAPEI", "Flexcolor CQ Ready-to-Use Grout", "1 gal pail", "per_each", "chemistry=single component;stain_resistant=yes", "", EXPECTED),
    ("Grout & Caulk", "each", "Custom Building Products", "Commercial 100% Silicone Sealant", "10.1 oz tube", "per_each", "chemistry=silicone", "", EXPECTED),
    ("Grout & Caulk", "each", "Custom Building Products", "Polyblend Sanded Ceramic Tile Caulk", "10.5 oz tube", "per_each", "chemistry=sanded caulk", "", EXPECTED),

    # --- Membrane & backer -------------------------------------------------
    ("Membrane & Backer", "sq_ft", "Schluter", "DITRA Uncoupling Membrane (DITRA5M)", "54 sq ft roll", "per_roll_sqft", "material=polyethylene;thickness_mm=3.2;function=uncoupling", "54", VERIFIED),
    ("Membrane & Backer", "sq_ft", "Schluter", "DITRA Uncoupling Membrane", "150 sq ft roll", "per_roll_sqft", "material=polyethylene;thickness_mm=3.2;function=uncoupling", "150", VERIFIED),
    ("Membrane & Backer", "sq_ft", "Schluter", "DITRA-XL Uncoupling Membrane", "175 sq ft roll", "per_roll_sqft", "material=polyethylene;thickness_mm=7;function=uncoupling", "175", VERIFIED),
    ("Membrane & Backer", "sq_ft", "Schluter", "KERDI 200 Waterproofing Membrane", "108 sq ft roll", "per_roll_sqft", "material=polyethylene;function=waterproofing", "108", EXPECTED),
    ("Membrane & Backer", "each", "Schluter", "KERDI-BOARD Building Panel 1/2 in", "32 in x 48 in", "per_each", "material=xps;thickness_in=0.5", "", EXPECTED),
    ("Membrane & Backer", "each", "USG", "Durock Brand Cement Board 1/2 in", "3 ft x 5 ft", "per_each", "material=cement board;thickness_in=0.5", "", EXPECTED),
    ("Membrane & Backer", "each", "James Hardie", "HardieBacker Cement Board 1/4 in", "3 ft x 5 ft", "per_each", "material=cement board;thickness_in=0.25", "", EXPECTED),
    ("Membrane & Backer", "sq_ft", "Schluter", "DITRA-HEAT Membrane", "134 sq ft roll", "per_roll_sqft", "material=polyethylene;function=heat", "134", EXPECTED),

    # --- Tile trim & profiles: per_piece, coverage = length in feet --------
    ("Tile Trim & Edging", "lin_ft", "Schluter", "JOLLY Anodized Aluminum Edge 3/8 in", "8 ft 2 in", "per_piece", "profile=square edge;material_trim=anodized aluminum;height_mm=10", "8.17", EXPECTED),
    ("Tile Trim & Edging", "lin_ft", "Schluter", "RONDEC Anodized Aluminum Edge 3/8 in", "8 ft 2 in", "per_piece", "profile=round edge;material_trim=anodized aluminum;height_mm=10", "8.17", EXPECTED),
    ("Tile Trim & Edging", "lin_ft", "Schluter", "SCHIENE Aluminum Edge 3/8 in", "8 ft 2 in", "per_piece", "profile=square edge;material_trim=aluminum;height_mm=10", "8.17", EXPECTED),
    ("Tile Trim & Edging", "lin_ft", "Schluter", "RENO-U Aluminum Reducer 3/8 in", "8 ft 2 in", "per_piece", "profile=reducer;material_trim=anodized aluminum;height_mm=10", "8.17", EXPECTED),
    ("Tile Trim & Edging", "lin_ft", "Schluter", "DILEX-KSA Movement Joint", "8 ft 2 in", "per_piece", "profile=movement joint;material_trim=stainless steel", "8.17", EXPECTED),
    ("Tile Trim & Edging", "lin_ft", "Schluter", "TREP-SE Stair Nosing", "4 ft 11 in", "per_piece", "profile=stair nose;material_trim=aluminum", "4.92", EXPECTED),

    # --- Underlayment ------------------------------------------------------
    ("Underlayment", "sq_ft", "Roberts", "Super Felt Cushion Underlayment", "100 sq ft roll", "per_roll_sqft", "material=felt;thickness_mm=3;moisture_barrier=no", "100", EXPECTED),
    ("Underlayment", "sq_ft", "Roberts", "Serenity Foam Underlayment", "100 sq ft roll", "per_roll_sqft", "material=foam;thickness_mm=2;moisture_barrier=yes", "100", EXPECTED),
    ("Underlayment", "sq_ft", "MP Global", "QuietWalk Underlayment", "100 sq ft roll", "per_roll_sqft", "material=felt;thickness_mm=3;moisture_barrier=yes", "100", EXPECTED),
    ("Underlayment", "sq_ft", "Roberts", "First Step Underlayment", "630 sq ft roll", "per_roll_sqft", "material=foam;thickness_mm=2;moisture_barrier=yes", "630", EXPECTED),

    # --- Tools -------------------------------------------------------------
    ("Installation Tools", "each", "QEP", "LASH Tile Leveling System Clips (100 ct)", "100 count", "per_each", "tool_type=leveling clips;power=manual", "", EXPECTED),
    ("Installation Tools", "each", "QEP", "LASH Tile Leveling Wedges (48 ct)", "48 count", "per_each", "tool_type=leveling wedges;power=manual", "", EXPECTED),
    ("Installation Tools", "each", "QEP", "7 in Wet Tile Saw", "each", "per_each", "tool_type=wet saw;power=electric;capacity=7", "", EXPECTED),
    ("Installation Tools", "each", "QEP", "24 in Ceramic Tile Cutter", "each", "per_each", "tool_type=snap cutter;power=manual;capacity=24", "", EXPECTED),
    ("Installation Tools", "each", "Rubi", "TX-700 Tile Cutter", "each", "per_each", "tool_type=snap cutter;power=manual;capacity=28", "", EXPECTED),
    ("Installation Tools", "each", "QEP", "1/4 in x 3/8 in Square-Notch Trowel", "each", "per_each", "tool_type=notched trowel;power=manual;material=steel", "", EXPECTED),
    ("Installation Tools", "each", "QEP", "Gum Rubber Grout Float", "each", "per_each", "tool_type=grout float;power=manual", "", EXPECTED),
    ("Installation Tools", "each", "QEP", "Professional Knee Pads", "pair", "per_each", "tool_type=knee pads;power=manual", "", EXPECTED),
    ("Installation Tools", "each", "Marshalltown", "Margin Trowel 5 in x 2 in", "each", "per_each", "tool_type=margin trowel;power=manual;material=steel", "", EXPECTED),

    # --- Sealers, cleaners, finishing -------------------------------------
    ("Sealers & Care", "each", "Custom Building Products", "Aqua Mix Sealer's Choice Gold", "1 qt", "per_each", "chemistry=impregnating sealer", "", EXPECTED),
    ("Sealers & Care", "each", "Custom Building Products", "Aqua Mix Grout Colorant", "8 oz", "per_each", "chemistry=colorant", "", EXPECTED),
    ("Sealers & Care", "each", "Miracle Sealants", "511 Impregnator Sealer", "1 qt", "per_each", "chemistry=impregnating sealer", "", EXPECTED),
    ("Sealers & Care", "each", "Bona", "Hardwood Floor Cleaner", "32 oz spray", "per_each", "chemistry=cleaner;surface=hardwood", "", EXPECTED),
    ("Sealers & Care", "each", "Bona", "Hardwood Floor Cleaner Refill", "128 oz", "per_each", "chemistry=cleaner;surface=hardwood", "", EXPECTED),
    ("Sealers & Care", "each", "DAP", "Alex Plus Acrylic Latex Caulk Plus Silicone", "10.1 oz tube", "per_each", "chemistry=acrylic latex caulk", "", EXPECTED),
    ("Sealers & Care", "each", "Zinsser", "Bulls Eye 1-2-3 Primer", "1 gal", "per_each", "chemistry=primer", "", EXPECTED),

    # --- Transition & moulding (national brand where it exists) ------------
    ("Trim & Moulding", "lin_ft", "M-D Building Products", "Aluminum Carpet Trim / Transition", "36 in", "per_piece", "profile=threshold;material_trim=aluminum", "3", EXPECTED),
    ("Trim & Moulding", "lin_ft", "M-D Building Products", "Vinyl Reducer Transition", "36 in", "per_piece", "profile=reducer;material_trim=vinyl", "3", EXPECTED),
    ("Trim & Moulding", "lin_ft", "TrafficMaster", "Seam Binder Transition", "36 in", "per_piece", "profile=seam binder;material_trim=aluminum", "3", "HD-exclusive brand - likely to fail carriage; kept as a control"),
]


def main() -> None:
    candidates = [
        Candidate(
            candidate_id=f"C{index:03d}", category=category, basis=basis, brand=brand,
            product=product, pack=pack, record_uom=uom, specs=specs,
            pack_coverage=coverage, notes=notes,
        )
        for index, (category, basis, brand, product, pack, uom, specs, coverage, notes)
        in enumerate(CANDIDATES, start=1)
    ]
    out = ROOT / "data/collection/identical_sku_worksheet.csv"
    write_worksheet(candidates, out)
    print(f"wrote {len(candidates)} candidates -> {out}")
    print("target: 40 confirmed three-way rows after carriage attrition")


if __name__ == "__main__":
    main()
