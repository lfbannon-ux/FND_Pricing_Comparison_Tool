"""Collection worksheet: the bridge between a human with three browser tabs
and the tool's canonical data files.

Collecting prices is manual - the retailers publish no price API and block
automated access - so the format has to suit a person working down a list, not
a parser. That means one row per product with all three retailers side by side,
which is the opposite shape from the long, one-row-per-offer files the engine
reads. This module owns both the wide worksheet and the conversion.

The worksheet also carries the *identity claim*: each row asserts "this is the
same product at all three retailers". `ingest` will not accept a row until a
human has confirmed that claim, because an identical-SKU basket built from
unconfirmed identities is just the spec-matched comparison wearing a better
name.
"""

from __future__ import annotations

import csv
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Tuple

from . import RETAILER_CODES, RETAILERS
from .loader import GROUP_COLUMNS, PRODUCT_COLUMNS, parse_specs
from .models import DataError

# Short prefixes keep the wide worksheet readable in a spreadsheet.
RETAILER_PREFIX = dict(RETAILER_CODES)

# Two grades of evidence, kept apart on purpose.
STANDARD_IDENTICAL = "identical"       # same brand and model on every shelf
STANDARD_SPEC = "spec_matched"         # closest comparable, scored by the matcher
MATCH_STANDARDS = (STANDARD_IDENTICAL, STANDARD_SPEC)

IDENTITY_COLUMNS = [
    "candidate_id",
    "category",
    "basis",
    "match_standard",
    "brand",
    "product",
    "pack",
    "record_uom",
    "specs",
    "annual_volume",
    "same_product_confirmed",
    "collected_on",
    "notes",
]

PER_RETAILER_FIELDS = [
    # `uom` is per retailer, not per row: a 50 lb bag is a 50 lb bag everywhere,
    # but Floor & Decor quotes flooring per square foot while a home centre
    # quotes the identical product per case. Blank inherits the row's
    # `record_uom`.
    "carried", "sku", "brand", "price", "uom", "pack_coverage", "promo_price",
    "specs", "url",
]


def worksheet_columns() -> List[str]:
    columns = list(IDENTITY_COLUMNS)
    for retailer in RETAILERS:
        prefix = RETAILER_PREFIX[retailer]
        columns.extend(f"{prefix}_{field}" for field in PER_RETAILER_FIELDS)
    return columns


@dataclass(frozen=True)
class Candidate:
    """A product believed to be carried, identically, by all three retailers."""

    candidate_id: str
    category: str
    basis: str
    brand: str
    product: str
    pack: str
    record_uom: str
    specs: str
    pack_coverage: str = ""
    notes: str = ""
    match_standard: str = STANDARD_IDENTICAL


def write_worksheet(candidates: List[Candidate], path: Path) -> Path:
    """Write a worksheet pre-filled with everything except the prices."""
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=worksheet_columns())
        writer.writeheader()
        for candidate in candidates:
            row = {
                "candidate_id": candidate.candidate_id,
                "category": candidate.category,
                "basis": candidate.basis,
                "match_standard": candidate.match_standard,
                "brand": candidate.brand,
                "product": candidate.product,
                "pack": candidate.pack,
                "record_uom": candidate.record_uom,
                "specs": candidate.specs,
                "annual_volume": "",
                "same_product_confirmed": "",
                "collected_on": "",
                "notes": candidate.notes,
            }
            for retailer in RETAILERS:
                prefix = RETAILER_PREFIX[retailer]
                row[f"{prefix}_carried"] = ""
                row[f"{prefix}_sku"] = ""
                # Left blank on an identical row: the brand and specs are the
                # row's, by definition. Required on a spec-matched row, where
                # each retailer sells a different product.
                row[f"{prefix}_brand"] = ""
                row[f"{prefix}_specs"] = ""
                row[f"{prefix}_price"] = ""
                row[f"{prefix}_uom"] = ""
                # Pre-fill the expected pack size; the collector corrects it if
                # the shelf disagrees, and a disagreement is itself a finding.
                row[f"{prefix}_pack_coverage"] = candidate.pack_coverage
                row[f"{prefix}_promo_price"] = ""
                row[f"{prefix}_url"] = ""
            writer.writerow(row)
    return path


def _yes(value: str) -> bool:
    return (value or "").strip().lower() in {"y", "yes", "true", "1"}


@dataclass
class IngestReport:
    groups: List[dict]
    offers: List[dict]
    skipped: List[Tuple[str, str]]
    not_started: int = 0
    """Rows nobody has touched yet - the normal state during a collection run,
    reported as a count rather than as a list of problems."""

    @property
    def three_way(self) -> int:
        counts: Dict[str, int] = {}
        for offer in self.offers:
            counts[offer["group_id"]] = counts.get(offer["group_id"], 0) + 1
        return sum(1 for n in counts.values() if n == len(RETAILERS))


def ingest_worksheet(path: Path) -> IngestReport:
    """Turn a filled worksheet into canonical group and offer rows."""
    groups: List[dict] = []
    offers: List[dict] = []
    skipped: List[Tuple[str, str]] = []
    not_started = 0

    with open(path, newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        missing = [c for c in worksheet_columns() if c not in (reader.fieldnames or ())]
        if missing:
            raise DataError(f"{path}: missing column(s): {', '.join(missing)}")

        for line, row in enumerate(reader, start=2):
            candidate_id = (row["candidate_id"] or "").strip()
            if not candidate_id:
                continue

            touched = any(
                (row[f"{RETAILER_PREFIX[r]}_{field}"] or "").strip()
                for r in RETAILERS
                for field in ("carried", "price")
            )
            priced = [
                r for r in RETAILERS
                if (row[f"{RETAILER_PREFIX[r]}_price"] or "").strip()
                and _yes(row[f"{RETAILER_PREFIX[r]}_carried"])
            ]
            if not priced:
                if touched:
                    skipped.append((candidate_id, "carried somewhere but no price recorded"))
                else:
                    not_started += 1
                continue

            standard = (row["match_standard"] or STANDARD_IDENTICAL).strip()
            if standard not in MATCH_STANDARDS:
                skipped.append((candidate_id, f"unknown match_standard {standard!r}"))
                continue

            if standard == STANDARD_IDENTICAL:
                if not _yes(row["same_product_confirmed"]):
                    # The identity claim is the whole point of that basket.
                    skipped.append((candidate_id, "same_product_confirmed not set"))
                    continue
            else:
                # A spec-matched row must carry each retailer's own brand and
                # spec sheet, or the matcher would score every row as identical
                # and quietly promote a judgement call into a fact.
                incomplete = [
                    RETAILER_PREFIX[r] for r in priced
                    if not (row[f"{RETAILER_PREFIX[r]}_brand"] or "").strip()
                    or not (row[f"{RETAILER_PREFIX[r]}_specs"] or "").strip()
                ]
                if incomplete:
                    skipped.append((
                        candidate_id,
                        f"spec_matched needs brand and specs per retailer; missing: "
                        f"{', '.join(incomplete)}",
                    ))
                    continue

            specs = parse_specs(row["specs"])
            groups.append({
                "group_id": candidate_id,
                "category": row["category"].strip(),
                "subcategory": row["brand"].strip() or standard,
                "basis": row["basis"].strip(),
                "description": f"{row['brand'].strip()} {row['product'].strip()} "
                               f"{row['pack'].strip()}".strip(),
                "annual_volume": (row["annual_volume"] or "").strip(),
                "specs": row["specs"].strip(),
            })

            for retailer in priced:
                prefix = RETAILER_PREFIX[retailer]
                # On an identical row the brand and specs are the row's - that
                # shared identity is what scores the match as `exact`. On a
                # spec-matched row each retailer brings its own, and the matcher
                # decides the tier from how far apart they are.
                brand = (row[f"{prefix}_brand"] or "").strip() or row["brand"].strip()
                offer_specs = (row[f"{prefix}_specs"] or "").strip() or row["specs"].strip()
                offer_uom = (row[f"{prefix}_uom"] or "").strip() or row["record_uom"].strip()
                parse_specs(offer_specs)   # fail fast on a malformed spec string
                offers.append({
                    "group_id": candidate_id,
                    "retailer": retailer,
                    "retailer_sku": row[f"{prefix}_sku"].strip(),
                    "brand": brand,
                    "product_name": row["product"].strip(),
                    "price": row[f"{prefix}_price"].strip(),
                    "uom": offer_uom,
                    "pack_coverage": row[f"{prefix}_pack_coverage"].strip(),
                    "promo_price": row[f"{prefix}_promo_price"].strip(),
                    "in_stock": "yes",
                    "collected_on": (row["collected_on"] or "").strip(),
                    "data_source": "collected",
                    "url": row[f"{prefix}_url"].strip(),
                    "specs": offer_specs,
                })
            _ = specs  # parsed above purely to fail fast on malformed specs

    if not groups:
        raise DataError(
            f"{path}: nothing to ingest - fill in prices and set "
            f"same_product_confirmed=y on at least one row"
        )
    return IngestReport(
        groups=groups, offers=offers, skipped=skipped, not_started=not_started
    )


def write_canonical(report: IngestReport, groups_path: Path, products_path: Path) -> None:
    groups_path.parent.mkdir(parents=True, exist_ok=True)
    with open(groups_path, "w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=GROUP_COLUMNS)
        writer.writeheader()
        writer.writerows(report.groups)
    with open(products_path, "w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=PRODUCT_COLUMNS)
        writer.writeheader()
        writer.writerows(report.offers)
