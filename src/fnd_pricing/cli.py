"""Command line entry point.

    python3 -m fnd_pricing validate
    python3 -m fnd_pricing compare --category "Porcelain Tile"
    python3 -m fnd_pricing report --open-path data/out/pricing_report.html
    python3 -m fnd_pricing export
    python3 -m fnd_pricing template
"""

from __future__ import annotations

import argparse
import csv
import sys
from pathlib import Path
from typing import List, Optional

from . import BASE_RETAILER, RETAILER_LABELS, RETAILERS
from .compare import GroupComparison, build_rollup, compare_all, rollup_by_category
from .loader import PRODUCT_COLUMNS, load_dataset
from .matching import DEFAULT_MIN_TIER, TIER_ORDER
from .models import DataError

ROOT = Path(__file__).resolve().parents[2]
DEFAULT_GROUPS = ROOT / "data/raw/sku_groups.csv"
DEFAULT_PRODUCTS = ROOT / "data/raw/products.csv"
DEFAULT_OUT = ROOT / "data/out"

COMPETITORS = [r for r in RETAILERS if r != BASE_RETAILER]


def _pct(value: Optional[float]) -> str:
    return "     -" if value is None else f"{value * 100:+6.1f}%"


def _load(args) -> List[GroupComparison]:
    groups, offers = load_dataset(Path(args.groups), Path(args.products))
    comparisons = compare_all(groups, offers, min_tier=args.min_tier)
    if getattr(args, "category", None):
        wanted = args.category.lower()
        comparisons = [
            c for c in comparisons if wanted in c.group.category.lower()
        ]
        if not comparisons:
            raise SystemExit(f"no SKU groups match category filter {args.category!r}")
    return comparisons


def _collected_on(args) -> str:
    _, offers = load_dataset(Path(args.groups), Path(args.products))
    dates = sorted({o.collected_on for o in offers if o.collected_on})
    if not dates:
        return ""
    return dates[-1] if len(dates) == 1 else f"{dates[0]} to {dates[-1]}"


def cmd_validate(args) -> int:
    groups, offers = load_dataset(Path(args.groups), Path(args.products))
    comparisons = compare_all(groups, offers, min_tier=args.min_tier)
    missing = [c.group.group_id for c in comparisons if c.base is None]
    sources = {}
    for offer in offers:
        sources[offer.data_source or "unspecified"] = sources.get(offer.data_source or "unspecified", 0) + 1

    print(f"SKU groups          {len(groups)}")
    print(f"Retailer offers     {len(offers)}")
    for retailer in RETAILERS:
        count = sum(1 for o in offers if o.retailer == retailer)
        print(f"  {RETAILER_LABELS[retailer]:<18} {count:>4}  "
              f"({count / len(groups) * 100:.0f}% coverage)")
    print(f"Data sources        " + ", ".join(f"{k}={v}" for k, v in sorted(sources.items())))
    if missing:
        print(f"WARNING: {len(missing)} group(s) have no Floor & Decor offer: "
              f"{', '.join(missing[:8])}{'...' if len(missing) > 8 else ''}")
    print("Validation passed.")
    return 0


def cmd_compare(args) -> int:
    comparisons = _load(args)
    overall = build_rollup("All categories", comparisons)

    print()
    print("FLOOR & DECOR vs HOME DEPOT vs LOWE'S - like-for-like pricing")
    print("=" * 78)
    print(f"SKU groups                {overall.groups}")
    print(f"With comparable offers    {overall.compared}")
    print(f"Win / tie / loss          {overall.wins} / {overall.ties} / {overall.losses}"
          f"   (win rate {(overall.win_rate or 0) * 100:.0f}%)")
    print(f"Median gap vs market low  {_pct(overall.median_gap)}   (negative = F&D cheaper)")
    print(f"Basket index vs low       {overall.spend_index}   (volume-weighted spend)")
    for retailer in COMPETITORS:
        print(f"Median gap vs {RETAILER_LABELS[retailer]:<12}{_pct(overall.per_retailer_gap.get(retailer))}")

    print()
    print(f"{'CATEGORY':<28}{'SKUs':>5}{'CMP':>5}{'WIN':>6}{'MEDIAN':>9}{'INDEX':>8}"
          f"{'vs HD':>9}{'vs LOW':>9}")
    print("-" * 78)
    for rollup in rollup_by_category(comparisons):
        index = "     -" if rollup.spend_index is None else f"{rollup.spend_index:6.3f}"
        print(f"{rollup.label[:27]:<28}{rollup.groups:>5}{rollup.compared:>5}"
              f"{(rollup.win_rate or 0) * 100:>5.0f}%{_pct(rollup.median_gap):>9}{index:>8}"
              f"{_pct(rollup.per_retailer_gap.get('home_depot')):>9}"
              f"{_pct(rollup.per_retailer_gap.get('lowes')):>9}")

    losses = sorted(
        (c for c in comparisons if c.outcome == "loss"),
        key=lambda c: c.gap_vs_market_min or 0, reverse=True,
    )[: args.top]
    if losses:
        print()
        print(f"WIDEST GAPS WHERE FLOOR & DECOR IS BEATEN (top {len(losses)})")
        print("-" * 78)
        for comp in losses:
            print(f"  {comp.group.group_id}  {_pct(comp.gap_vs_market_min)}  "
                  f"{comp.group.category[:22]:<24}{comp.group.description[:34]}")

    if args.csv:
        out = Path(args.csv)
        _write_detail_csv(comparisons, out)
        print(f"\nWrote detail CSV -> {out}")
    return 0


def _write_detail_csv(comparisons: List[GroupComparison], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    columns = [
        "group_id", "category", "subcategory", "description", "basis", "annual_volume",
        "fnd_unit_price", "home_depot_unit_price", "home_depot_delta_pct",
        "home_depot_match_tier", "lowes_unit_price", "lowes_delta_pct",
        "lowes_match_tier", "market_min", "gap_vs_market_min", "outcome",
        "cheapest_retailer", "flags",
    ]
    with open(path, "w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=columns)
        writer.writeheader()
        for comp in comparisons:
            hd, lw = comp.quotes["home_depot"], comp.quotes["lowes"]
            writer.writerow({
                "group_id": comp.group.group_id,
                "category": comp.group.category,
                "subcategory": comp.group.subcategory,
                "description": comp.group.description,
                "basis": comp.group.basis,
                "annual_volume": comp.group.annual_volume,
                "fnd_unit_price": comp.base_price,
                "home_depot_unit_price": hd.unit_price,
                "home_depot_delta_pct": hd.delta_pct,
                "home_depot_match_tier": hd.tier,
                "lowes_unit_price": lw.unit_price,
                "lowes_delta_pct": lw.delta_pct,
                "lowes_match_tier": lw.tier,
                "market_min": comp.market_min,
                "gap_vs_market_min": comp.gap_vs_market_min,
                "outcome": comp.outcome,
                "cheapest_retailer": comp.cheapest_retailer or "",
                "flags": ";".join(sorted(set(comp.flags))),
            })


def cmd_report(args) -> int:
    from .report import render_html

    comparisons = _load(args)
    out = Path(args.out or DEFAULT_OUT / "pricing_report.html")
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(render_html(comparisons, _collected_on(args)), encoding="utf-8")
    print(f"Wrote HTML report -> {out}")
    return 0


def cmd_export(args) -> int:
    try:
        from .excel import write_workbook
    except ImportError:
        raise SystemExit("openpyxl is required for xlsx export: pip install openpyxl")

    comparisons = _load(args)
    out = Path(args.out or DEFAULT_OUT / "pricing_comparison.xlsx")
    write_workbook(comparisons, out)
    print(f"Wrote workbook -> {out}")
    return 0


def cmd_template(args) -> int:
    out = Path(args.out or ROOT / "data/templates/price_collection_template.csv")
    out.parent.mkdir(parents=True, exist_ok=True)
    example = {
        "group_id": "G0001",
        "retailer": "home_depot",
        "retailer_sku": "1005432109",
        "brand": "LifeProof",
        "product_name": "Sterling Oak 22 MIL Rigid Core",
        "price": "89.98",
        "uom": "per_box",
        "pack_coverage": "23.77",
        "promo_price": "",
        "in_stock": "yes",
        "collected_on": "2026-08-14",
        "data_source": "collected",
        "url": "https://www.homedepot.com/p/...",
        "specs": "core=SPC;wear_layer_mil=22;thickness_mm=6.5;width_in=7.2",
    }
    with open(out, "w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=PRODUCT_COLUMNS)
        writer.writeheader()
        writer.writerow(example)
    print(f"Wrote collection template -> {out}")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="fnd_pricing",
        description="Like-for-like pricing comparison across Floor & Decor, "
                    "Home Depot and Lowe's.",
    )
    parser.add_argument("--groups", default=str(DEFAULT_GROUPS), help="sku_groups.csv path")
    parser.add_argument("--products", default=str(DEFAULT_PRODUCTS), help="products.csv path")
    parser.add_argument(
        "--min-tier", default=DEFAULT_MIN_TIER, choices=list(TIER_ORDER),
        help="weakest match tier admitted to the comparison (default: %(default)s)",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    sub = subparsers.add_parser("validate", help="check the input files and report coverage")
    sub.set_defaults(func=cmd_validate)

    sub = subparsers.add_parser("compare", help="print the comparison summary")
    sub.add_argument("--category", help="filter to categories containing this text")
    sub.add_argument("--top", type=int, default=10, help="how many worst gaps to list")
    sub.add_argument("--csv", help="also write the per-SKU detail to this CSV path")
    sub.set_defaults(func=cmd_compare)

    sub = subparsers.add_parser("report", help="write the self-contained HTML report")
    sub.add_argument("--category", help="filter to categories containing this text")
    sub.add_argument("--out", help="output path")
    sub.set_defaults(func=cmd_report)

    sub = subparsers.add_parser("export", help="write the multi-sheet Excel workbook")
    sub.add_argument("--category", help="filter to categories containing this text")
    sub.add_argument("--out", help="output path")
    sub.set_defaults(func=cmd_export)

    sub = subparsers.add_parser("template", help="write a blank price collection CSV")
    sub.add_argument("--out", help="output path")
    sub.set_defaults(func=cmd_template)
    return parser


def main(argv=None) -> int:
    args = build_parser().parse_args(argv)
    try:
        return args.func(args)
    except DataError as exc:
        print(f"data error: {exc}", file=sys.stderr)
        return 2
    except FileNotFoundError as exc:
        print(f"file not found: {exc.filename}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
