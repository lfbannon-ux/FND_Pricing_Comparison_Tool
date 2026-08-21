"""Like-for-like confidence scoring.

A price gap only means something if the two products are genuinely comparable.
Each competitor offer is scored against the Floor & Decor offer in its SKU
group on the attributes that drive price in that category, and the resulting
tier decides whether the gap is trustworthy enough to sit in the headline
index.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Dict, Optional

TIER_EXACT = "exact"            # same brand and model - identical good
TIER_EQUIVALENT = "equivalent"  # different brand, specs align
TIER_CLOSE = "close"            # specs differ on a secondary attribute
TIER_WEAK = "weak"              # not defensible as like-for-like

TIER_ORDER = (TIER_EXACT, TIER_EQUIVALENT, TIER_CLOSE, TIER_WEAK)

# Tiers admitted to the headline price index by default.
DEFAULT_MIN_TIER = TIER_CLOSE

# Attributes weighted by how strongly they move price within a category.
SPEC_WEIGHTS = {
    # resilient / wood
    "wear_layer_mil": 3.0,
    "thickness_mm": 2.5,
    "core": 2.0,
    "species": 2.5,
    "finish": 1.5,
    "width_in": 1.5,
    "length_in": 1.0,
    "waterproof": 2.0,
    "attached_pad": 1.0,
    "ac_rating": 2.0,
    "install": 1.0,
    # tile / stone
    "material": 3.0,
    "size_in": 2.0,
    "pei_rating": 1.5,
    "finish_tile": 1.5,
    "rectified": 1.0,
    "look": 1.5,
    "stone_grade": 2.0,
    # setting materials
    "chemistry": 3.0,
    "grade": 2.0,
    "color_family": 0.5,
    "joint_width": 1.5,
    # trim / tools / other
    "profile": 2.0,
    "length_ft": 1.5,
    "material_trim": 2.0,
    "power": 2.0,
    "capacity": 1.5,
    "tool_type": 3.0,
    # wood / soft surface / underlayment / vanity
    "veneer_mm": 2.5,
    "thickness_in": 2.5,
    "pile_weight_oz": 2.0,
    "backing": 1.5,
    "style": 1.5,
    "pattern": 1.5,
    "chip_size": 1.0,
    "moisture_barrier": 1.5,
    "sound_rating_iic": 1.0,
    "r_value": 1.0,
    "height_mm": 1.5,
    "sink": 2.0,
    "stain_resistant": 1.0,
}
DEFAULT_WEIGHT = 1.0

NUMERIC_SPECS = {
    "wear_layer_mil",
    "thickness_mm",
    "width_in",
    "length_in",
    "pei_rating",
    "ac_rating",
    "length_ft",
    "joint_width",
    "capacity",
    "veneer_mm",
    "thickness_in",
    "pile_weight_oz",
    "sound_rating_iic",
    "r_value",
    "height_mm",
}

# Values that mean the same thing across the three retailers' spec sheets.
_SYNONYMS = {
    "spc": "rigid core",
    "wpc": "rigid core",
    "rigid": "rigid core",
    "yes": "true",
    "no": "false",
    "y": "true",
    "n": "false",
    "matte": "matte",
    "matt": "matte",
    "polished": "polished",
    "click lock": "click",
    "click-lock": "click",
    "glue down": "glue",
    "glue-down": "glue",
}

_NUM_RE = re.compile(r"-?\d+(?:\.\d+)?")


def _canon(value: str) -> str:
    text = " ".join(str(value).strip().lower().split())
    return _SYNONYMS.get(text, text)


def _numeric(value: str) -> Optional[float]:
    match = _NUM_RE.search(str(value))
    return float(match.group()) if match else None


def _dimensions(value: str) -> Optional[tuple]:
    """Parse a size such as '12x24' or '7 in. x 48 in.' into a sorted tuple."""
    nums = [float(n) for n in _NUM_RE.findall(str(value))]
    return tuple(sorted(nums)) if len(nums) >= 2 else None


def _similarity(key: str, left: str, right: str) -> float:
    lhs, rhs = _canon(left), _canon(right)
    if lhs == rhs:
        return 1.0

    dim_l, dim_r = _dimensions(lhs), _dimensions(rhs)
    if dim_l and dim_r and len(dim_l) == len(dim_r):
        ratios = [
            min(a, b) / max(a, b) for a, b in zip(dim_l, dim_r) if max(a, b) > 0
        ]
        return _tolerance_score(min(ratios)) if ratios else 0.0

    if key in NUMERIC_SPECS:
        num_l, num_r = _numeric(lhs), _numeric(rhs)
        if num_l is not None and num_r is not None and max(num_l, num_r) > 0:
            return _tolerance_score(min(num_l, num_r) / max(num_l, num_r))

    # Partial textual overlap, e.g. "hand scraped" vs "hand scraped matte".
    tokens_l, tokens_r = set(lhs.split()), set(rhs.split())
    if tokens_l and tokens_r:
        overlap = len(tokens_l & tokens_r) / len(tokens_l | tokens_r)
        return overlap if overlap >= 0.5 else 0.0
    return 0.0


def _tolerance_score(ratio: float) -> float:
    if ratio >= 0.95:
        return 1.0
    if ratio >= 0.85:
        return 0.6
    if ratio >= 0.70:
        return 0.3
    return 0.0


@dataclass(frozen=True)
class MatchResult:
    score: float
    tier: str
    same_brand: bool
    compared_specs: int
    unmatched_specs: tuple

    @property
    def is_usable(self) -> bool:
        return tier_at_least(self.tier, DEFAULT_MIN_TIER)


def tier_at_least(tier: str, minimum: str) -> bool:
    return TIER_ORDER.index(tier) <= TIER_ORDER.index(minimum)


def score_match(
    base_specs: Dict[str, str],
    base_brand: str,
    cand_specs: Dict[str, str],
    cand_brand: str,
) -> MatchResult:
    """Score a competitor offer against the Floor & Decor offer in its group."""
    keys = sorted(set(base_specs) | set(cand_specs))
    total_weight = sum(SPEC_WEIGHTS.get(k, DEFAULT_WEIGHT) for k in keys) or 1.0

    earned = 0.0
    compared_weight = 0.0
    compared = 0
    unmatched = []

    for key in keys:
        weight = SPEC_WEIGHTS.get(key, DEFAULT_WEIGHT)
        left, right = base_specs.get(key), cand_specs.get(key)
        if left is None or right is None:
            continue  # not stated by both retailers - handled by coverage below
        compared += 1
        compared_weight += weight
        sim = _similarity(key, left, right)
        earned += weight * sim
        if sim < 1.0:
            unmatched.append(key)

    raw = earned / compared_weight if compared_weight else 0.0

    # Specs only one retailer publishes are unverified, so cap confidence by how
    # much of the group's spec weight was actually comparable.
    coverage = compared_weight / total_weight
    score = raw * (0.75 + 0.25 * coverage)

    same_brand = bool(base_brand) and _canon(base_brand) == _canon(cand_brand)

    if same_brand and score >= 0.90:
        tier = TIER_EXACT
    elif score >= 0.85:
        tier = TIER_EQUIVALENT
    elif score >= 0.70:
        tier = TIER_CLOSE
    else:
        tier = TIER_WEAK

    return MatchResult(
        score=round(score, 4),
        tier=tier,
        same_brand=same_brand,
        compared_specs=compared,
        unmatched_specs=tuple(unmatched),
    )
