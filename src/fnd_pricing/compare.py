"""The comparison engine: normalise, match, then measure the gap."""

from __future__ import annotations

import statistics
from dataclasses import dataclass, field
from typing import Dict, Iterable, List, Optional

from . import BASE_RETAILER, RETAILERS
from .matching import DEFAULT_MIN_TIER, MatchResult, score_match, tier_at_least
from .models import DataError, Offer, SkuGroup
from .normalize import NormalizedOffer, normalize

# Gaps inside this band are called a tie rather than a win or a loss.
TIE_BAND = 0.005
# Gaps beyond this are surfaced for human review before anyone acts on them.
EXTREME_GAP = 0.40

FLAG_NO_MATCH = "no_competitor_offer"
FLAG_WEAK_MATCH = "weak_match"
FLAG_OUT_OF_STOCK = "competitor_out_of_stock"
FLAG_PROMO_DRIVEN = "promo_driven_gap"
FLAG_EXTREME = "extreme_gap"
FLAG_NO_BASE = "no_floor_and_decor_offer"
FLAG_UOM = "uom_conversion_error"


@dataclass
class Quote:
    """One competitor's normalised, match-scored price for a SKU group."""

    retailer: str
    normalized: Optional[NormalizedOffer] = None
    match: Optional[MatchResult] = None
    delta_abs: Optional[float] = None
    delta_pct: Optional[float] = None
    list_delta_pct: Optional[float] = None
    included: bool = False
    note: str = ""

    @property
    def unit_price(self) -> Optional[float]:
        return self.normalized.unit_price if self.normalized else None

    @property
    def tier(self) -> str:
        return self.match.tier if self.match else "none"


@dataclass
class GroupComparison:
    group: SkuGroup
    base: Optional[NormalizedOffer]
    quotes: Dict[str, Quote]
    flags: List[str] = field(default_factory=list)

    @property
    def base_price(self) -> Optional[float]:
        return self.base.unit_price if self.base else None

    @property
    def comparable_quotes(self) -> List[Quote]:
        return [q for q in self.quotes.values() if q.included and q.unit_price]

    @property
    def market_min(self) -> Optional[float]:
        prices = [q.unit_price for q in self.comparable_quotes]
        return min(prices) if prices else None

    @property
    def market_avg(self) -> Optional[float]:
        prices = [q.unit_price for q in self.comparable_quotes]
        return round(statistics.fmean(prices), 4) if prices else None

    @property
    def cheapest_retailer(self) -> Optional[str]:
        candidates = [(q.unit_price, q.retailer) for q in self.comparable_quotes]
        if self.base_price:
            candidates.append((self.base_price, BASE_RETAILER))
        if not candidates:
            return None
        best = min(price for price, _ in candidates)
        within_tie = [r for price, r in candidates if price <= best * (1 + TIE_BAND)]
        # Credit a statistical tie to Floor & Decor rather than to a competitor
        # that happens to be two cents lower.
        return BASE_RETAILER if BASE_RETAILER in within_tie else within_tie[0]

    @property
    def gap_vs_market_min(self) -> Optional[float]:
        """Negative means Floor & Decor undercuts the cheapest competitor."""
        if not self.base_price or not self.market_min:
            return None
        return round((self.base_price - self.market_min) / self.market_min, 4)

    @property
    def outcome(self) -> str:
        gap = self.gap_vs_market_min
        if gap is None:
            return "no_comparison"
        if gap < -TIE_BAND:
            return "win"
        if gap > TIE_BAND:
            return "loss"
        return "tie"


def _build_quote(
    retailer: str,
    offer: Optional[Offer],
    group: SkuGroup,
    base: Optional[NormalizedOffer],
    min_tier: str,
) -> Quote:
    quote = Quote(retailer=retailer)
    if offer is None:
        quote.note = "no comparable item carried"
        return quote

    try:
        quote.normalized = normalize(offer, group.basis)
    except DataError as exc:
        quote.note = str(exc)
        return quote

    if base is None:
        quote.note = "no Floor & Decor offer to score against"
        return quote

    quote.match = score_match(
        base.offer.specs or group.specs,
        base.offer.brand,
        offer.specs or group.specs,
        offer.brand,
    )
    quote.included = tier_at_least(quote.match.tier, min_tier) and offer.in_stock

    if not offer.in_stock:
        quote.note = "out of stock at collection date"
    elif not quote.included:
        quote.note = f"match tier {quote.match.tier} below {min_tier}"

    base_price = base.unit_price
    quote.delta_abs = round(quote.normalized.unit_price - base_price, 4)
    quote.delta_pct = round(quote.delta_abs / base_price, 4) if base_price else None
    if base.list_unit_price:
        quote.list_delta_pct = round(
            (quote.normalized.list_unit_price - base.list_unit_price)
            / base.list_unit_price,
            4,
        )
    return quote


def compare_group(
    group: SkuGroup, offers: Iterable[Offer], min_tier: str = DEFAULT_MIN_TIER
) -> GroupComparison:
    by_retailer = {offer.retailer: offer for offer in offers}
    base_offer = by_retailer.get(BASE_RETAILER)

    base: Optional[NormalizedOffer] = None
    flags: List[str] = []
    if base_offer is not None:
        try:
            base = normalize(base_offer, group.basis)
        except DataError:
            flags.append(FLAG_UOM)
    else:
        flags.append(FLAG_NO_BASE)

    quotes = {
        retailer: _build_quote(
            retailer, by_retailer.get(retailer), group, base, min_tier
        )
        for retailer in RETAILERS
        if retailer != BASE_RETAILER
    }

    comparison = GroupComparison(group=group, base=base, quotes=quotes, flags=flags)

    for quote in quotes.values():
        if quote.normalized is None:
            if quote.note.startswith("no comparable"):
                comparison.flags.append(f"{FLAG_NO_MATCH}:{quote.retailer}")
            else:
                comparison.flags.append(f"{FLAG_UOM}:{quote.retailer}")
            continue
        if quote.match and quote.match.tier == "weak":
            comparison.flags.append(f"{FLAG_WEAK_MATCH}:{quote.retailer}")
        if not quote.normalized.offer.in_stock:
            comparison.flags.append(f"{FLAG_OUT_OF_STOCK}:{quote.retailer}")
        # A gap that only exists because someone is running a promotion is a
        # temporary gap; pricing decisions should not be anchored to it.
        if (
            quote.included
            and quote.delta_pct is not None
            and quote.list_delta_pct is not None
            and (quote.delta_pct > 0) != (quote.list_delta_pct > 0)
        ):
            comparison.flags.append(f"{FLAG_PROMO_DRIVEN}:{quote.retailer}")
        if quote.included and quote.delta_pct is not None and abs(quote.delta_pct) > EXTREME_GAP:
            comparison.flags.append(f"{FLAG_EXTREME}:{quote.retailer}")

    return comparison


def compare_all(
    groups: Dict[str, SkuGroup],
    offers: Iterable[Offer],
    min_tier: str = DEFAULT_MIN_TIER,
) -> List[GroupComparison]:
    grouped: Dict[str, List[Offer]] = {gid: [] for gid in groups}
    for offer in offers:
        grouped[offer.group_id].append(offer)
    return [
        compare_group(groups[gid], grouped[gid], min_tier=min_tier)
        for gid in groups
    ]


# --- Rollups ----------------------------------------------------------------


@dataclass
class Rollup:
    """Aggregate position for a slice of the assortment."""

    label: str
    groups: int = 0
    compared: int = 0
    wins: int = 0
    ties: int = 0
    losses: int = 0
    median_gap: Optional[float] = None
    mean_gap: Optional[float] = None
    spend_index: Optional[float] = None
    per_retailer_gap: Dict[str, Optional[float]] = field(default_factory=dict)

    @property
    def win_rate(self) -> Optional[float]:
        return round(self.wins / self.compared, 4) if self.compared else None


def _spend_index(comparisons: List[GroupComparison]) -> Optional[float]:
    """Volume-weighted basket index: Floor & Decor spend / market-min spend.

    Weighting by annual volume turns a list of unit prices into the number that
    matters commercially - what the same basket costs at each retailer. Below
    1.0 means Floor & Decor is cheaper on the basket.
    """
    base_spend = 0.0
    market_spend = 0.0
    for comp in comparisons:
        volume = comp.group.annual_volume
        if not volume or comp.base_price is None or comp.market_min is None:
            continue
        base_spend += comp.base_price * volume
        market_spend += comp.market_min * volume
    if market_spend <= 0:
        return None
    return round(base_spend / market_spend, 4)


def build_rollup(label: str, comparisons: List[GroupComparison]) -> Rollup:
    rollup = Rollup(label=label, groups=len(comparisons))
    gaps = []
    per_retailer: Dict[str, List[float]] = {
        r: [] for r in RETAILERS if r != BASE_RETAILER
    }

    for comp in comparisons:
        gap = comp.gap_vs_market_min
        if gap is None:
            continue
        rollup.compared += 1
        gaps.append(gap)
        outcome = comp.outcome
        if outcome == "win":
            rollup.wins += 1
        elif outcome == "loss":
            rollup.losses += 1
        else:
            rollup.ties += 1
        for retailer, quote in comp.quotes.items():
            if quote.included and quote.delta_pct is not None:
                per_retailer[retailer].append(quote.delta_pct)

    if gaps:
        rollup.median_gap = round(statistics.median(gaps), 4)
        rollup.mean_gap = round(statistics.fmean(gaps), 4)
    rollup.spend_index = _spend_index(comparisons)
    rollup.per_retailer_gap = {
        retailer: (round(statistics.median(values), 4) if values else None)
        for retailer, values in per_retailer.items()
    }
    return rollup


def rollup_by_category(comparisons: List[GroupComparison]) -> List[Rollup]:
    buckets: Dict[str, List[GroupComparison]] = {}
    for comp in comparisons:
        buckets.setdefault(comp.group.category, []).append(comp)
    return [build_rollup(name, items) for name, items in sorted(buckets.items())]
