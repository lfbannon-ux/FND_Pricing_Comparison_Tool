"""Basket comparison over a single match tier.

The headline index in `compare` mixes identical goods with spec-equivalents.
That is the right default - most of the assortment is private label on both
sides, so refusing to compare anything but identical SKUs would leave almost
nothing to measure. But it means the number rests partly on a judgement that
two different products are substitutes.

This module strips that judgement out: build a basket from one tier only -
normally `exact`, the same brand and model on both shelves - and price it.
Nothing here depends on a spec-matching opinion.

Two traps it is built to avoid:

- **Different baskets per retailer.** The SKUs identical at one competitor are
  not the SKUs identical at another, so quoting "F&D vs A" on one set against
  "F&D vs B" on another is not a like-for-like comparison between A and B.
  `common_members` restricts to the SKUs that qualify at *every* competitor,
  the only basket on which all of them can be quoted side by side. That
  intersection shrinks with each competitor added - a specialist carries fewer
  national brands than a full-line box - so `common_share` reports how much of
  each competitor's own basket survives it, and the per-competitor `own_baskets`
  stay available for the pairwise view.
- **One summary statistic.** The volume-weighted basket cost and the typical
  per-SKU gap answer different questions and can point opposite ways, so both
  are always reported.
"""

from __future__ import annotations

import statistics
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Sequence

from . import COMPETITORS as _COMPETITORS
from . import BASE_RETAILER, RETAILERS
from .compare import GroupComparison
from .matching import TIER_EXACT

COMPETITORS = list(_COMPETITORS)


def qualifies(comparison: GroupComparison, retailer: str, tier: str) -> bool:
    """Is this SKU eligible for a `tier` basket against `retailer`?"""
    quote = comparison.quotes.get(retailer)
    return bool(
        comparison.base is not None
        and comparison.group.annual_volume > 0
        and quote is not None
        and quote.normalized is not None
        and quote.tier == tier
        and quote.normalized.offer.in_stock
    )


@dataclass
class Basket:
    """Floor & Decor against one competitor over a fixed set of SKUs."""

    retailer: str
    tier: str
    skus: int = 0
    base_spend: float = 0.0
    comp_spend: float = 0.0
    list_base_spend: float = 0.0
    list_comp_spend: float = 0.0
    gaps: List[float] = field(default_factory=list)
    wins: int = 0
    ties: int = 0
    losses: int = 0

    # --- weighted view: what the basket costs -------------------------------
    @property
    def spend_index(self) -> Optional[float]:
        if self.comp_spend <= 0:
            return None
        return round(self.base_spend / self.comp_spend, 4)

    @property
    def spend_advantage(self) -> Optional[float]:
        """Negative = Floor & Decor's basket costs less."""
        index = self.spend_index
        return None if index is None else round(index - 1, 4)

    @property
    def spend_delta(self) -> float:
        return round(self.base_spend - self.comp_spend, 2)

    # --- unweighted view: the typical SKU -----------------------------------
    @property
    def median_gap(self) -> Optional[float]:
        """Competitor vs Floor & Decor on the median SKU. Positive = F&D cheaper."""
        return round(statistics.median(self.gaps), 4) if self.gaps else None

    @property
    def mean_gap(self) -> Optional[float]:
        return round(statistics.fmean(self.gaps), 4) if self.gaps else None

    # --- how much of the gap is a promotion rather than a price -------------
    @property
    def list_spend_index(self) -> Optional[float]:
        if self.list_comp_spend <= 0:
            return None
        return round(self.list_base_spend / self.list_comp_spend, 4)

    @property
    def promo_effect(self) -> Optional[float]:
        """Index movement caused by current promotions on either side."""
        index, list_index = self.spend_index, self.list_spend_index
        if index is None or list_index is None:
            return None
        return round(index - list_index, 4)

    @property
    def win_rate(self) -> Optional[float]:
        return round(self.wins / self.skus, 4) if self.skus else None


def build_basket(
    comparisons: Sequence[GroupComparison],
    retailer: str,
    tier: str = TIER_EXACT,
    tie_band: float = 0.005,
) -> Basket:
    basket = Basket(retailer=retailer, tier=tier)
    for comparison in comparisons:
        if not qualifies(comparison, retailer, tier):
            continue
        quote = comparison.quotes[retailer]
        volume = comparison.group.annual_volume
        basket.skus += 1
        basket.base_spend += comparison.base.unit_price * volume
        basket.comp_spend += quote.unit_price * volume
        basket.list_base_spend += comparison.base.list_unit_price * volume
        basket.list_comp_spend += quote.normalized.list_unit_price * volume
        gap = quote.delta_pct or 0.0
        basket.gaps.append(gap)
        if gap > tie_band:
            basket.wins += 1
        elif gap < -tie_band:
            basket.losses += 1
        else:
            basket.ties += 1

    for attribute in ("base_spend", "comp_spend", "list_base_spend", "list_comp_spend"):
        setattr(basket, attribute, round(getattr(basket, attribute), 2))
    return basket


def common_members(
    comparisons: Sequence[GroupComparison], tier: str = TIER_EXACT
) -> List[GroupComparison]:
    """SKUs that qualify at every competitor - the only true three-way basket."""
    return [
        c for c in comparisons
        if all(qualifies(c, retailer, tier) for retailer in COMPETITORS)
    ]


@dataclass
class BasketSet:
    """A tier basket priced three ways, plus each competitor's own wider set."""

    tier: str
    common: List[GroupComparison]
    common_baskets: Dict[str, Basket]
    own_baskets: Dict[str, Basket]

    @property
    def common_skus(self) -> int:
        return len(self.common)

    @property
    def common_share(self) -> Dict[str, Optional[float]]:
        """What fraction of each competitor's own basket survives the intersection.

        Every competitor added shrinks the common basket, because a SKU must be
        an identical match at all of them to qualify. A low share here is the
        warning that the three-way number rests on very little.
        """
        return {
            retailer: (
                round(len(self.common) / own.skus, 4) if own.skus else None
            )
            for retailer, own in self.own_baskets.items()
        }

    @property
    def cheapest_retailer(self) -> str:
        costs = {BASE_RETAILER: next(iter(self.common_baskets.values())).base_spend}
        costs.update({r: b.comp_spend for r, b in self.common_baskets.items()})
        return min(costs, key=costs.get)


def build_basket_set(
    comparisons: Sequence[GroupComparison], tier: str = TIER_EXACT
) -> BasketSet:
    common = common_members(comparisons, tier)
    return BasketSet(
        tier=tier,
        common=common,
        common_baskets={r: build_basket(common, r, tier) for r in COMPETITORS},
        own_baskets={r: build_basket(comparisons, r, tier) for r in COMPETITORS},
    )
