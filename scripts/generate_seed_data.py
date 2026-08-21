#!/usr/bin/env python3
"""Generate the 200-SKU seed dataset.

The three retailers publish no price API and block automated collection, so
this script builds a deterministic, category-anchored *seed* dataset that lets
the tool run end to end out of the box. Every generated row is stamped
`data_source=seed_estimate`; replace them with rows stamped `collected` (see
data/templates/price_collection_template.csv) and every downstream number
becomes a real number. Price levels, unit-of-measure conventions, pack sizes
and brand line-ups follow how these categories are actually merchandised.

Run:  python3 scripts/generate_seed_data.py
"""

from __future__ import annotations

import csv
import random
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from fnd_pricing.loader import GROUP_COLUMNS, PRODUCT_COLUMNS, format_specs  # noqa: E402
from fnd_pricing.matching import DEFAULT_WEIGHT, SPEC_WEIGHTS  # noqa: E402

SEED = 20260814
COLLECTED_ON = "2026-08-14"
DATA_SOURCE = "seed_estimate"

# Probability knobs, tuned so the generated book of business looks like a real
# collection run rather than a clean lab dataset.
P_NO_OFFER = 0.05        # competitor carries nothing comparable
P_OUT_OF_STOCK = 0.07
P_PROMO_COMPETITOR = 0.16
P_PROMO_FND = 0.10

COLORS = [
    "Alabaster", "Amber Ridge", "Ashford", "Autumn Hollow", "Barnwood", "Bayside",
    "Bergamo", "Bianco", "Blackwater", "Calacatta", "Cambridge", "Carrara",
    "Cedar Point", "Charcoal", "Chelsea", "Coastal Grey", "Copperfield", "Driftwood",
    "Dunmore", "Espresso", "Fieldstone", "Glacier", "Granite Peak", "Greystone",
    "Harbor Oak", "Havana", "Hillcrest", "Ivory", "Juniper", "Kingsport",
    "Linen", "Maplewood", "Marbella", "Meridian", "Millbrook", "Nordic",
    "Oakmont", "Onyx", "Pearl", "Pembroke", "Quarry", "Redmond", "Riverbend",
    "Sandstone", "Saxony", "Sierra", "Slate Creek", "Stonehaven", "Sterling",
    "Sundance", "Thornbury", "Tidewater", "Umber", "Vintage Elm", "Westbury",
    "Whitewash", "Willow Bend", "Windsor", "Yorkshire", "Zermatt",
]


def snap(value: float, rng: random.Random) -> float:
    """Round to a price that would actually appear on a shelf tag."""
    if value < 10:
        return max(0.09, round(int(value * 10) / 10 + 0.09, 2))
    if value < 100:
        return round(int(value) + rng.choice([0.97, 0.98, 0.99]), 2)
    if value < 250:
        return round(int(value / 5) * 5 - 0.02, 2)
    return round(round(value / 10) * 10 - 1, 2)


def snap_unit(value: float) -> float:
    """Per-unit shelf prices (per sq ft, per lin ft) end in 9."""
    return max(0.09, round(int(round(value, 2) * 100) / 100 + 0.005, 2)) if value >= 10 \
        else max(0.09, round(int(value * 10) / 10 + 0.09, 2))


# --- Category definitions ---------------------------------------------------
# fnd_price is the Floor & Decor level on the category's comparison basis.
# comp_index is the competitor's price as a multiple of Floor & Decor's.

CATEGORIES = [
    {
        "category": "Luxury Vinyl Plank",
        "count": 30,
        "basis": "sq_ft",
        "subcats": ["SPC Rigid Core", "WPC Rigid Core", "Glue Down LVP", "Waterproof LVP"],
        "fnd_price": (1.79, 4.99),
        "comp_index": {"home_depot": (1.06, 1.34), "lowes": (1.04, 1.30)},
        "national_prob": 0.20,
        "volume": (12000, 260000),
        "specs": {
            "core": ["SPC", "WPC", "rigid core"],
            "wear_layer_mil": ["6", "12", "20", "22", "28"],
            "thickness_mm": ["4.0", "5.0", "6.0", "6.5", "8.0"],
            "width_in": ["6", "7", "7.2", "9"],
            "length_in": ["48", "60", "72"],
            "waterproof": ["yes"],
            "attached_pad": ["yes", "no"],
            "finish": ["matte", "embossed", "hand scraped", "wire brushed"],
            "look": ["oak", "hickory", "walnut", "maple", "stone"],
            "install": ["click", "glue"],
        },
        "brands": {
            "floor_and_decor": ["NuCore", "DuraLux", "AquaGuard"],
            "home_depot": ["LifeProof", "TrafficMaster", "Home Decorators Collection"],
            "lowes": ["SMARTCORE", "Style Selections", "Origin 21"],
            "national": ["Mohawk", "Shaw", "COREtec", "Pergo"],
        },
        "uom": {
            "floor_and_decor": [("per_sq_ft", None)],
            "home_depot": [("per_box", ("range", 18.0, 30.0)), ("per_sq_ft", None)],
            "lowes": [("per_sq_ft", None), ("per_case", ("range", 16.0, 28.0))],
        },
    },
    {
        "category": "Laminate",
        "count": 18,
        "basis": "sq_ft",
        "subcats": ["Water Resistant Laminate", "Waterproof Laminate", "Standard Laminate"],
        "fnd_price": (0.99, 3.49),
        "comp_index": {"home_depot": (1.05, 1.32), "lowes": (1.03, 1.29)},
        "national_prob": 0.25,
        "volume": (9000, 180000),
        "specs": {
            "ac_rating": ["3", "4", "5"],
            "thickness_mm": ["7", "8", "10", "12"],
            "width_in": ["5", "7", "9"],
            "length_in": ["48", "50", "54"],
            "attached_pad": ["yes", "no"],
            "waterproof": ["yes", "no"],
            "finish": ["matte", "embossed", "hand scraped"],
            "look": ["oak", "hickory", "maple", "tile"],
        },
        "brands": {
            "floor_and_decor": ["AquaGuard", "Sono Eclipse"],
            "home_depot": ["TrafficMaster", "Home Decorators Collection"],
            "lowes": ["Style Selections", "allen + roth"],
            "national": ["Pergo", "Mohawk", "Quick-Step"],
        },
        "uom": {
            "floor_and_decor": [("per_sq_ft", None)],
            "home_depot": [("per_case", ("range", 16.0, 24.0)), ("per_sq_ft", None)],
            "lowes": [("per_sq_ft", None), ("per_case", ("range", 14.0, 22.0))],
        },
    },
    {
        "category": "Engineered Hardwood",
        "count": 16,
        "basis": "sq_ft",
        "subcats": ["Wide Plank Engineered", "Click Engineered", "Glue Down Engineered"],
        "fnd_price": (2.99, 8.99),
        "comp_index": {"home_depot": (1.08, 1.36), "lowes": (1.06, 1.32)},
        "national_prob": 0.20,
        "volume": (4000, 70000),
        "specs": {
            "species": ["white oak", "red oak", "hickory", "maple", "walnut", "birch"],
            "veneer_mm": ["0.6", "2.0", "3.0", "4.0"],
            "thickness_mm": ["9.5", "12.7", "15.0"],
            "width_in": ["5", "6.5", "7.5", "9.5"],
            "finish": ["wire brushed", "smooth", "hand scraped"],
            "install": ["click", "glue", "nail"],
        },
        "brands": {
            "floor_and_decor": ["Sonoma", "Willow Creek", "AquaGuard Wood"],
            "home_depot": ["Malibu Wide Plank", "Home Decorators Collection"],
            "lowes": ["allen + roth", "Villa Barcelona"],
            "national": ["Bruce", "Mohawk", "Shaw", "Mannington"],
        },
        "uom": {
            "floor_and_decor": [("per_sq_ft", None)],
            "home_depot": [("per_case", ("range", 19.0, 31.0)), ("per_sq_ft", None)],
            "lowes": [("per_sq_ft", None), ("per_case", ("range", 18.0, 30.0))],
        },
    },
    {
        "category": "Solid Hardwood",
        "count": 10,
        "basis": "sq_ft",
        "subcats": ["Prefinished Solid", "Unfinished Solid"],
        "fnd_price": (3.49, 9.99),
        "comp_index": {"home_depot": (1.07, 1.33), "lowes": (1.05, 1.30)},
        "national_prob": 0.30,
        "volume": (3000, 45000),
        "specs": {
            "species": ["white oak", "red oak", "hickory", "maple", "birch"],
            "thickness_in": ["0.75", "0.5"],
            "width_in": ["2.25", "3.25", "5"],
            "finish": ["smooth", "hand scraped", "wire brushed", "unfinished"],
            "grade": ["select", "character", "rustic"],
        },
        "brands": {
            "floor_and_decor": ["Founders", "Sonoma"],
            "home_depot": ["Malibu Wide Plank", "Home Decorators Collection"],
            "lowes": ["Villa Barcelona", "allen + roth"],
            "national": ["Bruce", "Somerset", "Mohawk"],
        },
        "uom": {
            "floor_and_decor": [("per_sq_ft", None)],
            "home_depot": [("per_case", ("range", 18.0, 24.0)), ("per_sq_ft", None)],
            "lowes": [("per_sq_ft", None)],
        },
    },
    {
        "category": "Porcelain Tile",
        "count": 26,
        "basis": "sq_ft",
        "subcats": ["Wood Look Plank", "Marble Look", "Concrete Look", "Large Format", "Outdoor Paver"],
        "fnd_price": (0.99, 5.99),
        "comp_index": {"home_depot": (1.09, 1.38), "lowes": (1.07, 1.34)},
        "national_prob": 0.18,
        "volume": (8000, 150000),
        "specs": {
            "material": ["porcelain"],
            "size_in": ["12x24", "24x48", "6x36", "8x48", "12x12", "18x18", "24x24", "6x24"],
            "pei_rating": ["3", "4", "5"],
            "finish_tile": ["matte", "polished", "textured"],
            "rectified": ["yes", "no"],
            "look": ["wood", "marble", "concrete", "stone", "terrazzo"],
            "thickness_mm": ["8", "9", "10", "20"],
        },
        "brands": {
            "floor_and_decor": ["Salerno", "Nova", "Founders", "Sonoma"],
            "home_depot": ["TrafficMaster", "Home Decorators Collection"],
            "lowes": ["Style Selections", "Satori", "allen + roth"],
            "national": ["MSI", "Daltile", "Marazzi", "Emser"],
        },
        "uom": {
            "floor_and_decor": [("per_sq_ft", None)],
            "home_depot": [("per_sq_ft", None), ("per_case", ("range", 12.0, 22.0))],
            "lowes": [("per_sq_ft", None), ("per_tile", ("from_size",))],
        },
    },
    {
        "category": "Ceramic Tile",
        "count": 14,
        "basis": "sq_ft",
        "subcats": ["Field Tile", "Subway Tile", "Floor Ceramic"],
        "fnd_price": (0.69, 2.99),
        "comp_index": {"home_depot": (1.08, 1.35), "lowes": (1.06, 1.31)},
        "national_prob": 0.22,
        "volume": (10000, 160000),
        "specs": {
            "material": ["ceramic"],
            "size_in": ["4x12", "3x6", "12x12", "6x24", "8x10", "4x16"],
            "pei_rating": ["1", "2", "3", "4"],
            "finish_tile": ["glossy", "matte", "crackle"],
            "look": ["solid", "stone", "wood"],
        },
        "brands": {
            "floor_and_decor": ["Salerno", "Nova"],
            "home_depot": ["Daltile", "TrafficMaster"],
            "lowes": ["Style Selections", "Satori"],
            "national": ["Daltile", "Marazzi", "MSI"],
        },
        "uom": {
            "floor_and_decor": [("per_sq_ft", None)],
            "home_depot": [("per_sq_ft", None), ("per_case", ("range", 10.0, 18.0))],
            "lowes": [("per_sq_ft", None), ("per_tile", ("from_size",))],
        },
    },
    {
        "category": "Natural Stone Tile",
        "count": 12,
        "basis": "sq_ft",
        "subcats": ["Marble", "Travertine", "Slate", "Limestone", "Quartzite"],
        "fnd_price": (3.99, 12.99),
        "comp_index": {"home_depot": (1.12, 1.42), "lowes": (1.10, 1.38)},
        "national_prob": 0.10,
        "volume": (2000, 40000),
        "specs": {
            "material": ["marble", "travertine", "slate", "limestone", "quartzite"],
            "size_in": ["12x12", "12x24", "18x18", "16x16", "6x12"],
            "finish_tile": ["honed", "polished", "tumbled", "brushed"],
            "stone_grade": ["premium", "standard", "commercial"],
            "thickness_mm": ["10", "12", "15"],
        },
        "brands": {
            "floor_and_decor": ["Founders", "Sonoma", "Nova"],
            "home_depot": ["MSI", "Home Decorators Collection"],
            "lowes": ["Satori", "allen + roth"],
            "national": ["MSI", "Emser"],
        },
        "uom": {
            "floor_and_decor": [("per_sq_ft", None)],
            "home_depot": [("per_sq_ft", None), ("per_case", ("range", 8.0, 16.0))],
            "lowes": [("per_sq_ft", None), ("per_tile", ("from_size",))],
        },
    },
    {
        "category": "Mosaic & Decorative Tile",
        "count": 10,
        "basis": "sq_ft",
        "subcats": ["Glass Mosaic", "Stone Mosaic", "Porcelain Mosaic", "Decorative Accent"],
        "fnd_price": (7.99, 24.99),
        "comp_index": {"home_depot": (1.10, 1.40), "lowes": (1.08, 1.36)},
        "national_prob": 0.12,
        "volume": (600, 9000),
        "specs": {
            "material": ["glass", "marble", "porcelain", "glass and stone"],
            "pattern": ["herringbone", "penny round", "hexagon", "subway", "picket", "basketweave"],
            "chip_size": ["1x1", "2x2", "1x3", "mixed"],
            "finish_tile": ["polished", "matte", "honed"],
            "size_in": ["12x12", "11.8x11.8", "12x13"],
        },
        "brands": {
            "floor_and_decor": ["Nova", "Founders"],
            "home_depot": ["Home Decorators Collection", "MSI"],
            "lowes": ["Satori", "allen + roth"],
            "national": ["MSI", "Daltile"],
        },
        "uom": {
            "floor_and_decor": [("per_sq_ft", None), ("per_sheet", ("choice", [0.96, 1.0]))],
            "home_depot": [("per_sheet", ("choice", [0.96, 0.97, 1.0]))],
            "lowes": [("per_sheet", ("choice", [0.96, 1.0])), ("per_sq_ft", None)],
        },
    },
    {
        "category": "Wall Tile & Backsplash",
        "count": 8,
        "basis": "sq_ft",
        "subcats": ["Ceramic Wall", "Glass Wall", "Porcelain Wall"],
        "fnd_price": (1.49, 6.99),
        "comp_index": {"home_depot": (1.08, 1.34), "lowes": (1.06, 1.31)},
        "national_prob": 0.20,
        "volume": (1500, 22000),
        "specs": {
            "material": ["ceramic", "porcelain", "glass"],
            "size_in": ["3x6", "4x16", "2.5x8", "4x12"],
            "finish_tile": ["glossy", "matte", "crackle", "beveled"],
            "look": ["solid", "handmade", "marble"],
        },
        "brands": {
            "floor_and_decor": ["Nova", "Salerno"],
            "home_depot": ["Daltile", "Home Decorators Collection"],
            "lowes": ["Satori", "Style Selections"],
            "national": ["Daltile", "Marazzi"],
        },
        "uom": {
            "floor_and_decor": [("per_sq_ft", None)],
            "home_depot": [("per_sq_ft", None), ("per_case", ("range", 8.0, 12.0))],
            "lowes": [("per_sq_ft", None)],
        },
    },
    {
        "category": "Carpet & Carpet Tile",
        "count": 6,
        "basis": "sq_ft",
        "subcats": ["Carpet Tile", "Broadloom"],
        "fnd_price": (1.29, 3.49),
        "comp_index": {"home_depot": (1.04, 1.26), "lowes": (1.03, 1.24)},
        "national_prob": 0.30,
        "volume": (2000, 30000),
        "specs": {
            "material": ["nylon", "polyester", "olefin"],
            "pile_weight_oz": ["20", "26", "32", "40"],
            "backing": ["cushion", "hard back"],
            "style": ["loop", "cut pile", "patterned"],
            "size_in": ["19.7x19.7", "24x24"],
        },
        "brands": {
            "floor_and_decor": ["NuCore Soft", "Sonoma"],
            "home_depot": ["TrafficMaster", "Home Decorators Collection"],
            "lowes": ["STAINMASTER", "Style Selections"],
            "national": ["Shaw", "Mohawk"],
        },
        "uom": {
            "floor_and_decor": [("per_sq_ft", None)],
            "home_depot": [("per_case", ("choice", [21.53, 26.0, 45.0])), ("per_sq_ft", None)],
            "lowes": [("per_sq_ft", None), ("per_sq_yd", None)],
        },
    },
    {
        "category": "Underlayment",
        "count": 8,
        "basis": "sq_ft",
        "subcats": ["Foam Underlayment", "Cork Underlayment", "Felt Underlayment", "Rubber Underlayment"],
        "fnd_price": (0.29, 0.89),
        "comp_index": {"home_depot": (0.95, 1.18), "lowes": (0.94, 1.16)},
        "national_prob": 0.55,
        "volume": (6000, 80000),
        "specs": {
            "material": ["foam", "cork", "felt", "rubber"],
            "thickness_mm": ["2", "3", "6"],
            "moisture_barrier": ["yes", "no"],
            "sound_rating_iic": ["50", "60", "66", "71"],
            "r_value": ["0.5", "1.0", "1.5"],
        },
        "brands": {
            "floor_and_decor": ["FloorMuffler", "Roberts"],
            "home_depot": ["Roberts", "QEP"],
            "lowes": ["Project Source", "Roberts"],
            "national": ["Roberts", "QEP", "MP Global"],
        },
        "uom": {
            "floor_and_decor": [("per_roll_sqft", ("choice", [100.0, 200.0]))],
            "home_depot": [("per_roll_sqft", ("choice", [100.0, 200.0, 630.0]))],
            "lowes": [("per_roll_sqft", ("choice", [100.0, 200.0])), ("per_sq_ft", None)],
        },
    },
    {
        "category": "Setting Materials",
        "count": 8,
        "basis": "lb",
        "subcats": ["Modified Thinset", "Unmodified Thinset", "Large Format Mortar", "Epoxy Mortar"],
        "fnd_price": (0.28, 0.64),
        "comp_index": {"home_depot": (0.92, 1.12), "lowes": (0.91, 1.10)},
        "national_prob": 0.75,
        "volume": (5000, 60000),
        "specs": {
            "chemistry": ["modified thinset", "unmodified thinset", "large format mortar", "epoxy mortar"],
            "grade": ["standard", "premium"],
            "color_family": ["white", "gray"],
            "material": ["cement based", "epoxy"],
        },
        "brands": {
            "floor_and_decor": ["Custom Building Products", "MAPEI"],
            "home_depot": ["Custom Building Products", "MAPEI"],
            "lowes": ["MAPEI", "Custom Building Products"],
            "national": ["Custom Building Products", "MAPEI", "Laticrete", "Bostik"],
        },
        "uom": {
            "floor_and_decor": [("per_bag", ("choice", [50.0, 25.0]))],
            "home_depot": [("per_bag", ("choice", [50.0, 25.0]))],
            "lowes": [("per_bag", ("choice", [50.0, 25.0]))],
        },
    },
    {
        "category": "Grout & Caulk",
        "count": 8,
        "basis": "lb",
        "subcats": ["Sanded Grout", "Unsanded Grout", "Single Component Grout", "Epoxy Grout"],
        "fnd_price": (0.72, 1.60),
        "comp_index": {"home_depot": (0.94, 1.14), "lowes": (0.93, 1.12)},
        "national_prob": 0.70,
        "volume": (3000, 35000),
        "specs": {
            "chemistry": ["sanded", "unsanded", "single component", "epoxy"],
            "joint_width": ["0.125", "0.25", "0.5"],
            "color_family": ["bright white", "delorean gray", "charcoal", "linen"],
            "stain_resistant": ["yes", "no"],
        },
        "brands": {
            "floor_and_decor": ["Custom Building Products", "MAPEI"],
            "home_depot": ["Custom Building Products", "MAPEI"],
            "lowes": ["MAPEI", "TEC"],
            "national": ["Custom Building Products", "MAPEI", "Laticrete", "TEC"],
        },
        "uom": {
            "floor_and_decor": [("per_bag", ("choice", [25.0, 10.0])), ("per_pail", ("choice", [9.0]))],
            "home_depot": [("per_bag", ("choice", [25.0, 10.0])), ("per_pail", ("choice", [9.0]))],
            "lowes": [("per_bag", ("choice", [25.0, 10.0]))],
        },
    },
    {
        "category": "Trim & Moulding",
        "count": 10,
        "basis": "lin_ft",
        "subcats": ["Quarter Round", "T-Molding", "Reducer", "Stair Nose", "Threshold", "Baseboard"],
        "fnd_price": (1.50, 6.00),
        "comp_index": {"home_depot": (0.97, 1.24), "lowes": (0.96, 1.22)},
        "national_prob": 0.35,
        "volume": (2500, 30000),
        "specs": {
            "profile": ["quarter round", "T-molding", "reducer", "stair nose", "threshold", "baseboard"],
            "material_trim": ["MDF", "vinyl", "wood", "aluminum"],
            "length_ft": ["6.5", "7.5", "8.0"],
            "finish": ["matte", "embossed", "smooth"],
        },
        "brands": {
            "floor_and_decor": ["NuCore", "DuraLux", "Sonoma"],
            "home_depot": ["LifeProof", "Zamma", "TrafficMaster"],
            "lowes": ["SMARTCORE", "Project Source", "Style Selections"],
            "national": ["Zamma", "Shaw", "Mohawk"],
        },
        "uom": {
            "floor_and_decor": [("per_piece", ("from_spec", "length_ft"))],
            "home_depot": [("per_piece", ("from_spec", "length_ft"))],
            "lowes": [("per_piece", ("from_spec", "length_ft")), ("per_lin_ft", None)],
        },
    },
    {
        "category": "Tile Trim & Edging",
        "count": 6,
        "basis": "lin_ft",
        "subcats": ["Edge Profile", "Stair Nose Profile", "Transition Profile"],
        "fnd_price": (4.00, 14.00),
        "comp_index": {"home_depot": (0.98, 1.12), "lowes": (0.97, 1.11)},
        "national_prob": 0.80,
        "volume": (800, 9000),
        "specs": {
            "profile": ["square edge", "round edge", "bullnose", "stair nose"],
            "material_trim": ["anodized aluminum", "PVC", "stainless steel", "brushed brass"],
            "height_mm": ["8", "10", "12.5"],
            "length_ft": ["8.0", "8.5"],
        },
        "brands": {
            "floor_and_decor": ["Schluter", "Novalis"],
            "home_depot": ["Schluter", "Custom Building Products"],
            "lowes": ["Schluter", "Blanke"],
            "national": ["Schluter", "Custom Building Products"],
        },
        "uom": {
            "floor_and_decor": [("per_piece", ("from_spec", "length_ft"))],
            "home_depot": [("per_piece", ("from_spec", "length_ft"))],
            "lowes": [("per_piece", ("from_spec", "length_ft"))],
        },
    },
    {
        "category": "Installation Tools",
        "count": 6,
        "basis": "each",
        "subcats": ["Wet Saw", "Snap Cutter", "Hand Tool", "Leveling System"],
        "fnd_price": (12.00, 180.00),
        "comp_index": {"home_depot": (0.93, 1.06), "lowes": (0.92, 1.05)},
        "national_prob": 0.80,
        "volume": (150, 3500),
        "specs": {
            "tool_type": ["wet saw", "snap cutter", "notched trowel", "mixing paddle", "leveling clips", "knee pads"],
            "power": ["electric", "manual"],
            "capacity": ["7", "10", "24", "36"],
            "material": ["steel", "aluminum", "composite"],
        },
        "brands": {
            "floor_and_decor": ["QEP", "Rubi"],
            "home_depot": ["QEP", "Husky", "RIDGID"],
            "lowes": ["QEP", "Kobalt", "Rubi"],
            "national": ["QEP", "Rubi", "DEWALT"],
        },
        "uom": {
            "floor_and_decor": [("per_each", None)],
            "home_depot": [("per_each", None)],
            "lowes": [("per_each", None)],
        },
    },
    {
        "category": "Vanities & Tops",
        "count": 4,
        "basis": "each",
        "subcats": ["Single Sink Vanity", "Double Sink Vanity"],
        "fnd_price": (299.00, 1299.00),
        "comp_index": {"home_depot": (0.82, 1.02), "lowes": (0.81, 1.01)},
        "national_prob": 0.15,
        "volume": (60, 900),
        "specs": {
            "width_in": ["24", "30", "36", "48", "60"],
            "material": ["engineered stone top", "cultured marble top", "quartz top"],
            "sink": ["single", "double"],
            "finish": ["white", "espresso", "grey", "natural oak"],
        },
        "brands": {
            "floor_and_decor": ["Sonoma", "Founders"],
            "home_depot": ["Home Decorators Collection", "Glacier Bay"],
            "lowes": ["allen + roth", "Origin 21"],
            "national": ["Foremost"],
        },
        "uom": {
            "floor_and_decor": [("per_each", None)],
            "home_depot": [("per_each", None)],
            "lowes": [("per_each", None)],
        },
    },
]

RETAILERS = ("floor_and_decor", "home_depot", "lowes")


def sqft_from_size(size_in: str) -> float:
    parts = [float(p) for p in size_in.lower().replace("in", "").split("x")]
    return round(parts[0] * parts[1] / 144.0, 4)


def resolve_coverage(spec, specs, rng):
    if spec is None:
        return None
    kind = spec[0]
    if kind == "range":
        return round(rng.uniform(spec[1], spec[2]), 2)
    if kind == "choice":
        return rng.choice(spec[1])
    if kind == "from_size":
        return sqft_from_size(specs.get("size_in", "12x12"))
    if kind == "from_spec":
        return float(specs[spec[1]])
    raise ValueError(f"unknown coverage spec {spec!r}")


def perturb(specs, pools, rng):
    """Make a competitor's spec sheet differ the way real ones do."""
    out = dict(specs)
    roll = rng.random()
    if roll < 0.45:
        return out

    def keys_with(predicate):
        return [k for k in pools if predicate(SPEC_WEIGHTS.get(k, DEFAULT_WEIGHT)) and len(pools[k]) > 1]

    if roll < 0.75:
        pool_keys = keys_with(lambda w: w <= 1.5)
    elif roll < 0.95:
        pool_keys = keys_with(lambda w: 1.5 < w <= 2.5)
    else:
        pool_keys = keys_with(lambda w: w > 2.5)
    if not pool_keys:
        return out

    key = rng.choice(pool_keys)
    alternatives = [v for v in pools[key] if v != out.get(key)]
    if alternatives:
        out[key] = rng.choice(alternatives)
    return out


def build_rows():
    rng = random.Random(SEED)
    group_rows, product_rows = [], []
    counter = 0

    for cat in CATEGORIES:
        pools = cat["specs"]
        for _ in range(cat["count"]):
            counter += 1
            group_id = f"G{counter:04d}"
            subcat = rng.choice(cat["subcats"])
            base_specs = {key: rng.choice(values) for key, values in pools.items()}

            national = rng.random() < cat["national_prob"]
            national_brand = rng.choice(cat["brands"]["national"]) if national else None
            series = rng.choice(COLORS)

            fnd_unit = rng.uniform(*cat["fnd_price"])
            descriptor = " ".join(
                str(base_specs[k]) for k in list(base_specs)[:2] if base_specs.get(k)
            )
            group_rows.append(
                {
                    "group_id": group_id,
                    "category": cat["category"],
                    "subcategory": subcat,
                    "basis": cat["basis"],
                    "description": f"{subcat} - {series} {descriptor}".strip(),
                    "annual_volume": int(rng.uniform(*cat["volume"])),
                    "specs": format_specs(base_specs),
                }
            )

            for retailer in RETAILERS:
                if retailer != "floor_and_decor" and rng.random() < P_NO_OFFER:
                    continue  # competitor carries nothing comparable

                if retailer == "floor_and_decor":
                    specs = base_specs
                    index = 1.0
                else:
                    specs = base_specs if national else perturb(base_specs, pools, rng)
                    lo, hi = cat["comp_index"][retailer]
                    index = rng.uniform(lo, hi)
                    if national:
                        # Identical branded goods price much closer together.
                        index = 1 + (index - 1) * 0.45

                brand = national_brand or rng.choice(cat["brands"][retailer])
                uom, coverage_spec = rng.choice(cat["uom"][retailer])
                coverage = resolve_coverage(coverage_spec, specs, rng)

                unit_price = fnd_unit * index
                if uom == "per_sq_yd":
                    raw = unit_price * 9
                elif coverage:
                    raw = unit_price * coverage
                else:
                    raw = unit_price
                price = snap(raw, rng) if (coverage or uom == "per_sq_yd" or raw >= 10) else snap_unit(raw)

                promo_prob = P_PROMO_FND if retailer == "floor_and_decor" else P_PROMO_COMPETITOR
                promo = ""
                if rng.random() < promo_prob:
                    discounted = price * (1 - rng.uniform(0.08, 0.25))
                    promo = f"{snap(discounted, rng) if price >= 10 else snap_unit(discounted):.2f}"

                in_stock = "no" if (
                    retailer != "floor_and_decor" and rng.random() < P_OUT_OF_STOCK
                ) else "yes"

                product_rows.append(
                    {
                        "group_id": group_id,
                        "retailer": retailer,
                        "retailer_sku": f"{retailer[:2].upper()}-{rng.randrange(100000, 999999)}",
                        "brand": brand,
                        "product_name": f"{series} {subcat}",
                        "price": f"{price:.2f}",
                        "uom": uom,
                        "pack_coverage": f"{coverage:g}" if coverage else "",
                        "promo_price": promo,
                        "in_stock": in_stock,
                        "collected_on": COLLECTED_ON,
                        "data_source": DATA_SOURCE,
                        "url": "",
                        "specs": format_specs(specs),
                    }
                )

    return group_rows, product_rows


def write_csv(path: Path, columns, rows) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=columns)
        writer.writeheader()
        writer.writerows(rows)


def main() -> None:
    groups, products = build_rows()
    write_csv(ROOT / "data/raw/sku_groups.csv", GROUP_COLUMNS, groups)
    write_csv(ROOT / "data/raw/products.csv", PRODUCT_COLUMNS, products)
    print(f"wrote {len(groups)} SKU groups and {len(products)} retailer offers")


if __name__ == "__main__":
    main()
