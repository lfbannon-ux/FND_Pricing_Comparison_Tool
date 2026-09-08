"""Expense by category: where the money actually sits.

The comparison engine measures *rates* - gaps and indexes as percentages. A
merchant also needs the level: which categories carry the spend, how much of it
is priced above or below the market, and how much of it nobody has benchmarked
at all. A 20% gap on a category worth $4k/yr is a rounding error next to a 3%
gap on one worth $900k.

Every index here is computed on a **matched basket**: a retailer is only
compared against the Floor & Decor spend on the SKUs that retailer actually
covers. Dividing total Floor & Decor spend by a competitor's spend over a
smaller set of SKUs would compare two different baskets and read as a price
advantage that is really just missing coverage.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional

from . import COMPETITORS as _COMPETITORS
from . import BASE_RETAILER, RETAILERS
from .compare import GroupComparison

COMPETITORS = list(_COMPETITORS)
MARKET_LOW = "market_low"
BASKETS = COMPETITORS + [MARKET_LOW]


@dataclass(frozen=True)
class Basket:
    """Floor & Decor spend vs one competitor, over the SKUs they both cover."""

    retailer: str
    matched_skus: int
    base_spend: float
    comp_spend: float

    @property
    def index(self) -> Optional[float]:
        """Floor & Decor spend / competitor spend. Below 1.0 = cheaper."""
        if self.comp_spend <= 0:
            return None
        return round(self.base_spend / self.comp_spend, 4)

    @property
    def delta(self) -> float:
        """Dollars per year. Positive = Floor & Decor costs more."""
        return round(self.base_spend - self.comp_spend, 2)

    @property
    def delta_pct(self) -> Optional[float]:
        if self.comp_spend <= 0:
            return None
        return round(self.delta / self.comp_spend, 4)


@dataclass(frozen=True)
class CategoryExpense:
    """One category's annual expense and its price position."""

    category: str
    skus: int
    priced_skus: int
    annual_units: float
    annual_spend: float
    benchmarked_spend: float
    basis: Optional[str]
    baskets: Dict[str, Basket] = field(default_factory=dict)

    @property
    def unbenchmarked_spend(self) -> float:
        """Spend on SKUs where no competitor offer was comparable enough to use."""
        return round(self.annual_spend - self.benchmarked_spend, 2)

    @property
    def benchmark_coverage(self) -> Optional[float]:
        if self.annual_spend <= 0:
            return None
        return round(self.benchmarked_spend / self.annual_spend, 4)

    @property
    def avg_unit_price(self) -> Optional[float]:
        """Only meaningful where the whole category shares one comparison basis."""
        if self.basis is None or self.annual_units <= 0:
            return None
        return round(self.annual_spend / self.annual_units, 4)

    def share_of(self, total_spend: float) -> Optional[float]:
        if total_spend <= 0:
            return None
        return round(self.annual_spend / total_spend, 4)


def _spendable(comparison: GroupComparison) -> bool:
    """A group contributes to expense only with both a price and a volume."""
    return comparison.base_price is not None and comparison.group.annual_volume > 0


def _build_baskets(comparisons: List[GroupComparison]) -> Dict[str, Basket]:
    baskets: Dict[str, Basket] = {}

    for retailer in COMPETITORS:
        matched = base_spend = comp_spend = 0.0
        for comp in comparisons:
            quote = comp.quotes.get(retailer)
            if not _spendable(comp) or quote is None or not quote.included:
                continue
            volume = comp.group.annual_volume
            matched += 1
            base_spend += comp.base_price * volume
            comp_spend += quote.unit_price * volume
        baskets[retailer] = Basket(retailer, int(matched), round(base_spend, 2),
                                   round(comp_spend, 2))

    matched = base_spend = comp_spend = 0.0
    for comp in comparisons:
        if not _spendable(comp) or comp.market_min is None:
            continue
        volume = comp.group.annual_volume
        matched += 1
        base_spend += comp.base_price * volume
        comp_spend += comp.market_min * volume
    baskets[MARKET_LOW] = Basket(MARKET_LOW, int(matched), round(base_spend, 2),
                                 round(comp_spend, 2))
    return baskets


def build_expense(label: str, comparisons: List[GroupComparison]) -> CategoryExpense:
    priced = [c for c in comparisons if _spendable(c)]
    annual_units = sum(c.group.annual_volume for c in priced)
    annual_spend = sum(c.base_price * c.group.annual_volume for c in priced)
    benchmarked = sum(
        c.base_price * c.group.annual_volume
        for c in priced
        if c.market_min is not None
    )
    bases = {c.group.basis for c in comparisons}

    return CategoryExpense(
        category=label,
        skus=len(comparisons),
        priced_skus=len(priced),
        annual_units=round(annual_units, 2),
        annual_spend=round(annual_spend, 2),
        benchmarked_spend=round(benchmarked, 2),
        basis=bases.pop() if len(bases) == 1 else None,
        baskets=_build_baskets(comparisons),
    )


def expense_by_category(comparisons: List[GroupComparison]) -> List[CategoryExpense]:
    """Categories ranked by annual expense, largest first."""
    buckets: Dict[str, List[GroupComparison]] = {}
    for comp in comparisons:
        buckets.setdefault(comp.group.category, []).append(comp)
    rows = [build_expense(name, items) for name, items in buckets.items()]
    return sorted(rows, key=lambda r: r.annual_spend, reverse=True)


def total_expense(comparisons: List[GroupComparison]) -> CategoryExpense:
    return build_expense("All categories", comparisons)
