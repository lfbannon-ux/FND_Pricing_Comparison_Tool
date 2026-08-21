"""Unit-of-measure normalisation.

Floor & Decor quotes most flooring per square foot, Home Depot and Lowe's
frequently quote the same goods per case or per carton, and setting materials
are sold in 25 lb / 50 lb bags. Nothing may be compared until every offer is
expressed in the same unit, so this module is the gate every price passes
through before it reaches the comparison engine.
"""

from __future__ import annotations

from dataclasses import dataclass

from .models import UOM_SPEC, DataError, Offer

# Multipliers applied after the pack division, to reach the target basis.
_POST_SCALE = {
    "per_sq_yd": 1.0 / 9.0,  # 1 sq yd = 9 sq ft
}


@dataclass(frozen=True)
class NormalizedOffer:
    """An offer restated on its SKU group's comparison basis."""

    offer: Offer
    basis: str
    unit_price: float
    list_unit_price: float
    conversion: str

    @property
    def retailer(self) -> str:
        return self.offer.retailer

    @property
    def promo_discount(self) -> float:
        """Fraction taken off the list unit price by the current promotion."""
        if self.list_unit_price <= 0:
            return 0.0
        return max(0.0, 1.0 - self.unit_price / self.list_unit_price)


def _convert(price: float, offer: Offer) -> float:
    basis, needs_coverage = UOM_SPEC[offer.uom]
    value = price
    if needs_coverage:
        coverage = offer.pack_coverage or 0.0
        if coverage <= 0:
            raise DataError(
                f"{offer.group_id}/{offer.retailer}: pack_coverage must be positive "
                f"for uom {offer.uom!r}"
            )
        value /= coverage
    return value * _POST_SCALE.get(offer.uom, 1.0)


def normalize(offer: Offer, basis: str) -> NormalizedOffer:
    """Restate `offer` on `basis`, raising if the offer's uom cannot get there.

    A uom that resolves to a different basis is a data error, not something to
    silently coerce: comparing a per-piece transition strip against a per-sq-ft
    tile price would produce a confident, meaningless number.
    """
    offer_basis, needs_coverage = UOM_SPEC[offer.uom]
    if offer_basis != basis:
        raise DataError(
            f"{offer.group_id}/{offer.retailer}: uom {offer.uom!r} resolves to "
            f"{offer_basis!r} but the SKU group is compared on {basis!r}"
        )

    unit_price = _convert(offer.effective_price, offer)
    list_unit_price = _convert(offer.price, offer)

    if needs_coverage:
        conversion = f"{offer.uom} / {offer.pack_coverage:g} {basis}"
    elif offer.uom in _POST_SCALE:
        conversion = f"{offer.uom} -> {basis}"
    else:
        conversion = "direct"

    return NormalizedOffer(
        offer=offer,
        basis=basis,
        unit_price=round(unit_price, 4),
        list_unit_price=round(list_unit_price, 4),
        conversion=conversion,
    )
