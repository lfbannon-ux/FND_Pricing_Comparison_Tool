"""Core data structures for the pricing comparison tool."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, Optional


class DataError(ValueError):
    """Raised when an input row cannot be parsed or fails validation."""


# --- Units of measure -------------------------------------------------------
# Retailers sell the same physical good in different units. Every offer is
# normalised onto its SKU group's comparison basis before any price is compared.

BASIS_SQ_FT = "sq_ft"
BASIS_LIN_FT = "lin_ft"
BASIS_LB = "lb"
BASIS_EACH = "each"

BASES = (BASIS_SQ_FT, BASIS_LIN_FT, BASIS_LB, BASIS_EACH)

# uom -> (basis it resolves to, whether `pack_coverage` is required)
UOM_SPEC = {
    "per_sq_ft": (BASIS_SQ_FT, False),
    "per_sq_yd": (BASIS_SQ_FT, False),
    "per_box": (BASIS_SQ_FT, True),
    "per_case": (BASIS_SQ_FT, True),
    "per_carton": (BASIS_SQ_FT, True),
    "per_sheet": (BASIS_SQ_FT, True),
    "per_roll_sqft": (BASIS_SQ_FT, True),
    "per_tile": (BASIS_SQ_FT, True),
    "per_lin_ft": (BASIS_LIN_FT, False),
    "per_piece": (BASIS_LIN_FT, True),
    "per_bundle": (BASIS_LIN_FT, True),
    "per_lb": (BASIS_LB, False),
    "per_bag": (BASIS_LB, True),
    "per_pail": (BASIS_LB, True),
    "per_each": (BASIS_EACH, False),
    "per_kit": (BASIS_EACH, True),
}


@dataclass(frozen=True)
class SkuGroup:
    """A like-for-like comparison unit: one specification, up to three offers."""

    group_id: str
    category: str
    subcategory: str
    basis: str
    description: str
    specs: Dict[str, str] = field(default_factory=dict)
    annual_volume: float = 0.0

    def __post_init__(self) -> None:
        if self.basis not in BASES:
            raise DataError(f"{self.group_id}: unknown comparison basis {self.basis!r}")


@dataclass(frozen=True)
class Offer:
    """One retailer's price for one SKU group."""

    group_id: str
    retailer: str
    retailer_sku: str
    brand: str
    product_name: str
    price: float
    uom: str
    pack_coverage: Optional[float] = None
    promo_price: Optional[float] = None
    in_stock: bool = True
    collected_on: str = ""
    data_source: str = ""
    url: str = ""
    specs: Dict[str, str] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if self.uom not in UOM_SPEC:
            raise DataError(
                f"{self.group_id}/{self.retailer}: unknown unit of measure {self.uom!r}"
            )
        if self.price <= 0:
            raise DataError(f"{self.group_id}/{self.retailer}: price must be positive")
        if self.promo_price is not None and self.promo_price <= 0:
            raise DataError(
                f"{self.group_id}/{self.retailer}: promo price must be positive"
            )
        _, needs_coverage = UOM_SPEC[self.uom]
        if needs_coverage and not self.pack_coverage:
            raise DataError(
                f"{self.group_id}/{self.retailer}: uom {self.uom!r} requires pack_coverage"
            )

    @property
    def effective_price(self) -> float:
        """Shelf price actually payable today (promo wins when present)."""
        return self.promo_price if self.promo_price is not None else self.price

    @property
    def on_promo(self) -> bool:
        return self.promo_price is not None and self.promo_price < self.price
