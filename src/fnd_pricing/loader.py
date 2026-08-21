"""CSV ingestion and validation.

Two files drive the tool:

  sku_groups.csv  one row per like-for-like comparison unit (200 of them)
  products.csv    one row per retailer offer against a group (up to 3 each)

Specs travel in a single `specs` column encoded as `key=value;key=value`, which
keeps both files rectangular no matter how differently a vanity and a bag of
thinset are specified.
"""

from __future__ import annotations

import csv
from pathlib import Path
from typing import Dict, Iterable, List, Tuple

from . import RETAILERS
from .models import DataError, Offer, SkuGroup

GROUP_COLUMNS = [
    "group_id",
    "category",
    "subcategory",
    "basis",
    "description",
    "annual_volume",
    "specs",
]

PRODUCT_COLUMNS = [
    "group_id",
    "retailer",
    "retailer_sku",
    "brand",
    "product_name",
    "price",
    "uom",
    "pack_coverage",
    "promo_price",
    "in_stock",
    "collected_on",
    "data_source",
    "url",
    "specs",
]

_TRUTHY = {"1", "true", "yes", "y", "t"}
_FALSY = {"0", "false", "no", "n", "f", ""}


def parse_specs(raw: str) -> Dict[str, str]:
    specs: Dict[str, str] = {}
    for chunk in (raw or "").split(";"):
        chunk = chunk.strip()
        if not chunk:
            continue
        if "=" not in chunk:
            raise DataError(f"malformed spec {chunk!r}; expected key=value")
        key, value = chunk.split("=", 1)
        specs[key.strip()] = value.strip()
    return specs


def format_specs(specs: Dict[str, str]) -> str:
    return ";".join(f"{k}={v}" for k, v in specs.items())


def _float(row: dict, key: str, where: str, required: bool = True):
    raw = (row.get(key) or "").strip()
    if not raw:
        if required:
            raise DataError(f"{where}: missing required numeric column {key!r}")
        return None
    try:
        return float(raw.replace("$", "").replace(",", ""))
    except ValueError as exc:
        raise DataError(f"{where}: {key}={raw!r} is not a number") from exc


def _bool(row: dict, key: str, where: str, default: bool = True) -> bool:
    raw = (row.get(key) or "").strip().lower()
    if raw == "":
        return default
    if raw in _TRUTHY:
        return True
    if raw in _FALSY:
        return False
    raise DataError(f"{where}: {key}={raw!r} is not a boolean")


def _require_columns(header: Iterable[str], expected: List[str], path: Path) -> None:
    missing = [c for c in expected if c not in set(header or ())]
    if missing:
        raise DataError(f"{path}: missing column(s): {', '.join(missing)}")


def load_groups(path: Path) -> Dict[str, SkuGroup]:
    groups: Dict[str, SkuGroup] = {}
    with open(path, newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        _require_columns(reader.fieldnames, GROUP_COLUMNS, path)
        for line, row in enumerate(reader, start=2):
            where = f"{path}:{line}"
            group_id = (row["group_id"] or "").strip()
            if not group_id:
                raise DataError(f"{where}: blank group_id")
            if group_id in groups:
                raise DataError(f"{where}: duplicate group_id {group_id!r}")
            try:
                groups[group_id] = SkuGroup(
                    group_id=group_id,
                    category=row["category"].strip(),
                    subcategory=row["subcategory"].strip(),
                    basis=row["basis"].strip(),
                    description=row["description"].strip(),
                    specs=parse_specs(row["specs"]),
                    annual_volume=_float(row, "annual_volume", where, required=False) or 0.0,
                )
            except DataError as exc:
                raise DataError(f"{where}: {exc}") from exc
    if not groups:
        raise DataError(f"{path}: no SKU groups found")
    return groups


def load_offers(path: Path, groups: Dict[str, SkuGroup]) -> List[Offer]:
    offers: List[Offer] = []
    seen: set = set()
    with open(path, newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        _require_columns(reader.fieldnames, PRODUCT_COLUMNS, path)
        for line, row in enumerate(reader, start=2):
            where = f"{path}:{line}"
            group_id = (row["group_id"] or "").strip()
            retailer = (row["retailer"] or "").strip()
            if group_id not in groups:
                raise DataError(f"{where}: group_id {group_id!r} not in sku_groups.csv")
            if retailer not in RETAILERS:
                raise DataError(
                    f"{where}: retailer {retailer!r} must be one of {', '.join(RETAILERS)}"
                )
            key = (group_id, retailer)
            if key in seen:
                raise DataError(f"{where}: duplicate offer for {group_id}/{retailer}")
            seen.add(key)
            try:
                offers.append(
                    Offer(
                        group_id=group_id,
                        retailer=retailer,
                        retailer_sku=row["retailer_sku"].strip(),
                        brand=row["brand"].strip(),
                        product_name=row["product_name"].strip(),
                        price=_float(row, "price", where),
                        uom=row["uom"].strip(),
                        pack_coverage=_float(row, "pack_coverage", where, required=False),
                        promo_price=_float(row, "promo_price", where, required=False),
                        in_stock=_bool(row, "in_stock", where),
                        collected_on=row["collected_on"].strip(),
                        data_source=row["data_source"].strip(),
                        url=row["url"].strip(),
                        specs=parse_specs(row["specs"]),
                    )
                )
            except DataError as exc:
                raise DataError(f"{where}: {exc}") from exc
    if not offers:
        raise DataError(f"{path}: no offers found")
    return offers


def load_dataset(
    groups_path: Path, products_path: Path
) -> Tuple[Dict[str, SkuGroup], List[Offer]]:
    groups = load_groups(groups_path)
    return groups, load_offers(products_path, groups)
