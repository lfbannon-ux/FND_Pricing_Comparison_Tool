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

from . import (
    BASE_RETAILER, RETAILER_CODES, RETAILER_LABELS, RETAILER_SHORT, RETAILERS,
    active_retailers, competitors, set_active_retailers,
)
from .compare import GroupComparison, build_rollup, compare_all, rollup_by_category
from .loader import PRODUCT_COLUMNS, load_dataset
from .basket import build_basket_set, qualifies
from .collect import ingest_worksheets, write_canonical
from .matching import DEFAULT_MIN_TIER, TIER_EXACT, TIER_ORDER
from .spend import MARKET_LOW, expense_by_category, total_expense
from .models import DataError

ROOT = Path(__file__).resolve().parents[2]
DEFAULT_GROUPS = ROOT / "data/raw/sku_groups.csv"
DEFAULT_PRODUCTS = ROOT / "data/raw/products.csv"
DEFAULT_OUT = ROOT / "data/out"



def _pct(value: Optional[float]) -> str:
    return "     -" if value is None else f"{value * 100:+6.1f}%"


def _load(args) -> List[GroupComparison]:
    groups, offers = load_dataset(Path(args.groups), Path(args.products))
    comparisons = compare_all(
        groups, offers, min_tier=args.min_tier,
        use_list_price=getattr(args, "list_price", False),
    )
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
    versus = " vs ".join(
        [RETAILER_LABELS[BASE_RETAILER]] + [RETAILER_LABELS[r] for r in competitors()]
    )
    print(f"{versus.upper()} - like-for-like pricing")
    print("=" * 78)
    print(f"SKU groups                {overall.groups}")
    print(f"With comparable offers    {overall.compared}")
    print(f"Win / tie / loss          {overall.wins} / {overall.ties} / {overall.losses}"
          f"   (win rate {(overall.win_rate or 0) * 100:.0f}%)")
    print(f"Median gap vs market low  {_pct(overall.median_gap)}   (negative = F&D cheaper)")
    print(f"Basket index vs low       {overall.spend_index}   (volume-weighted spend)")
    for retailer in competitors():
        print(f"Median gap vs {RETAILER_LABELS[retailer]:<12}{_pct(overall.per_retailer_gap.get(retailer))}")

    print()
    competitor_heads = "".join(
        f"{RETAILER_CODES[r].upper():>9}" for r in competitors()
    )
    width = 60 + 9 * len(competitors())
    print(f"{'CATEGORY':<28}{'SKUs':>5}{'CMP':>5}{'WIN':>6}{'MEDIAN':>9}{'INDEX':>8}"
          f"{competitor_heads}")
    print("-" * width)
    for rollup in rollup_by_category(comparisons):
        index = "     -" if rollup.spend_index is None else f"{rollup.spend_index:6.3f}"
        gaps = "".join(
            f"{_pct(rollup.per_retailer_gap.get(r)):>9}" for r in competitors()
        )
        print(f"{rollup.label[:27]:<28}{rollup.groups:>5}{rollup.compared:>5}"
              f"{(rollup.win_rate or 0) * 100:>5.0f}%{_pct(rollup.median_gap):>9}{index:>8}"
              f"{gaps}")

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
        "fnd_unit_price",
    ] + [
        f"{retailer}_{field}"
        for retailer in competitors()
        for field in ("unit_price", "delta_pct", "match_tier")
    ] + [
        "market_min", "gap_vs_market_min", "outcome", "cheapest_retailer", "flags",
    ]
    with open(path, "w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=columns)
        writer.writeheader()
        for comp in comparisons:
            row = {
                "group_id": comp.group.group_id,
                "category": comp.group.category,
                "subcategory": comp.group.subcategory,
                "description": comp.group.description,
                "basis": comp.group.basis,
                "annual_volume": comp.group.annual_volume,
                "fnd_unit_price": comp.base_price,
                "market_min": comp.market_min,
                "gap_vs_market_min": comp.gap_vs_market_min,
                "outcome": comp.outcome,
                "cheapest_retailer": comp.cheapest_retailer or "",
                "flags": ";".join(sorted(set(comp.flags))),
            }
            for retailer in competitors():
                quote = comp.quotes[retailer]
                row[f"{retailer}_unit_price"] = quote.unit_price
                row[f"{retailer}_delta_pct"] = quote.delta_pct
                row[f"{retailer}_match_tier"] = quote.tier
            writer.writerow(row)


def cmd_index(args) -> int:
    """Rank categories by annual expense and show each one's price position."""
    comparisons = _load(args)
    rows = expense_by_category(comparisons)
    total = total_expense(comparisons)
    if total.annual_spend <= 0:
        raise SystemExit("no annual_volume set on any SKU group - expense cannot be computed")

    def line(label, skus, units, spend, share, basket, coverage):
        index = "        -" if basket.index is None else f"{basket.index:9.3f}"
        return (f"{label[:27]:<28}{skus:>5}{units:>15,.0f}{spend:>16,.0f}"
                f"{share * 100:>7.1f}%{index}{basket.delta:>14,.0f}{coverage * 100:>6.0f}%")

    print()
    print("ANNUAL EXPENSE BY CATEGORY - at Floor & Decor prices")
    print("=" * 111)
    print(f"{'CATEGORY':<28}{'SKUS':>5}{'ANNUAL UNITS':>15}{'ANNUAL SPEND':>16}"
          f"{'SHARE':>8}{'IDX/LOW':>9}{'$ VS LOW':>14}{'BMK':>7}")
    print("-" * 111)
    for row in rows:
        print(line(row.category, row.priced_skus, row.annual_units, row.annual_spend,
                   row.share_of(total.annual_spend) or 0, row.baskets[MARKET_LOW],
                   row.benchmark_coverage or 0))
    print("-" * 111)
    print(line("All categories", total.priced_skus, total.annual_units, total.annual_spend,
               1.0, total.baskets[MARKET_LOW], total.benchmark_coverage or 0))

    exposed = [r for r in rows if r.baskets[MARKET_LOW].delta > 0]
    if exposed:
        print()
        print("PRICED ABOVE THE MARKET LOW - ranked by annual dollars at stake")
        print("-" * 111)
        for row in sorted(exposed, key=lambda r: r.baskets[MARKET_LOW].delta, reverse=True):
            basket = row.baskets[MARKET_LOW]
            print(f"  {row.category[:26]:<28}{basket.delta:>12,.0f} a year on "
                  f"{basket.matched_skus:>3} matched SKUs   index {basket.index:.3f}")

    print()
    print("Note: each index divides Floor & Decor spend by that retailer's spend over only")
    print("the SKUs that retailer covers, so compare an index to 1.0 - not to each other.")
    print("BMK is the share of category expense that has any comparable competitor offer.")

    if args.csv:
        out = Path(args.csv)
        _write_expense_csv(rows, total, out)
        print(f"\nWrote expense CSV -> {out}")
    return 0


def _write_expense_csv(rows, total, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    columns = [
        "category", "skus", "priced_skus", "basis", "annual_units", "avg_unit_price",
        "annual_spend", "share_of_spend", "benchmarked_spend", "unbenchmarked_spend",
        "benchmark_coverage", "matched_skus_vs_low", "index_vs_market_low",
        "dollars_vs_market_low",
    ] + [
        f"{prefix}_vs_{retailer}"
        for retailer in competitors()
        for prefix in ("index", "dollars")
    ]
    with open(path, "w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=columns)
        writer.writeheader()
        for row in list(rows) + [total]:
            low = row.baskets[MARKET_LOW]
            record = {
                "category": row.category, "skus": row.skus,
                "priced_skus": row.priced_skus, "basis": row.basis or "mixed",
                "annual_units": row.annual_units, "avg_unit_price": row.avg_unit_price,
                "annual_spend": row.annual_spend,
                "share_of_spend": row.share_of(total.annual_spend),
                "benchmarked_spend": row.benchmarked_spend,
                "unbenchmarked_spend": row.unbenchmarked_spend,
                "benchmark_coverage": row.benchmark_coverage,
                "matched_skus_vs_low": low.matched_skus,
                "index_vs_market_low": low.index, "dollars_vs_market_low": low.delta,
            }
            for retailer in competitors():
                record[f"index_vs_{retailer}"] = row.baskets[retailer].index
                record[f"dollars_vs_{retailer}"] = row.baskets[retailer].delta
            writer.writerow(record)


def cmd_basket(args) -> int:
    """Price a basket built from a single match tier - identical goods by default."""
    comparisons = _load(args)
    basket_set = build_basket_set(comparisons, tier=args.tier,
                                  at_least=args.at_least)
    common = basket_set.common
    if not common:
        raise SystemExit(
            f"no SKU carries an in-stock {args.tier!r} match at every competitor"
        )

    base_spend = basket_set.common_baskets[competitors()[0]].base_spend
    if args.at_least:
        label = f"ALL COMPARABLE SKUs ({args.tier} match or better)"
    else:
        label = {TIER_EXACT: "IDENTICAL SKUs (same brand and model)"}.get(
            args.tier, f"{args.tier.upper()} MATCHES ONLY")

    print()
    print(f"BASKET: {label}")
    print("=" * 78)
    qualifier = f"{args.tier} match or better" if args.at_least else f"{args.tier} match"
    print(f"{len(common)} SKUs carry an in-stock {qualifier} at ALL "
          f"{len(competitors())} competitors, out of {len(comparisons)} studied.")
    print(f"This is the only basket all {len(active_retailers())} retailers can be quoted on "
          f"side by side. Every competitor added shrinks it - see the pairwise")
    print("baskets below, which are wider but not comparable to each other.")
    print()
    print(f"  {'Floor & Decor':<16}{base_spend:>16,.2f}")
    for retailer in competitors():
        basket = basket_set.common_baskets[retailer]
        print(f"  {RETAILER_LABELS[retailer]:<16}{basket.comp_spend:>16,.2f}")

    print()
    print("HOW MUCH CHEAPER IS FLOOR & DECOR?")
    print("-" * 78)
    for retailer in competitors():
        basket = basket_set.common_baskets[retailer]
        name = RETAILER_LABELS[retailer]
        print(f"  vs {name:<14}"
              f"{-basket.spend_delta:>14,.2f}/yr   {-(basket.spend_advantage or 0) * 100:>6.1f}%"
              f"   basket index {basket.spend_index}")
    print()
    print("  Weighted by annual volume - what the basket costs. The unweighted view")
    print("  below answers a different question and does not have to agree:")
    print()
    print("  (per-SKU figures: POSITIVE = the competitor is dearer = Floor & Decor cheaper)")
    for retailer in competitors():
        basket = basket_set.common_baskets[retailer]
        print(f"  vs {RETAILER_LABELS[retailer]:<14}median SKU {_pct(basket.median_gap)}"
              f"   mean {_pct(basket.mean_gap)}"
              f"   F&D cheaper on {basket.wins}/{basket.skus}"
              f" (tie {basket.ties}, dearer {basket.losses})")

    print()
    print("PROMOTION EFFECT")
    print("-" * 78)
    for retailer in competitors():
        basket = basket_set.common_baskets[retailer]
        print(f"  vs {RETAILER_LABELS[retailer]:<14}today {basket.spend_index}"
              f"   at list price {basket.list_spend_index}"
              f"   promotions move it {basket.promo_effect:+.4f}")

    print()
    print("EACH COMPETITOR'S OWN WIDER BASKET (pairwise - not mutually comparable)")
    print("-" * 78)
    share = basket_set.common_share
    for retailer in competitors():
        basket = basket_set.own_baskets[retailer]
        if not basket.skus:
            print(f"  vs {RETAILER_LABELS[retailer]:<16}no identical SKUs in stock")
            continue
        kept = share.get(retailer)
        print(f"  vs {RETAILER_LABELS[retailer]:<16}{basket.skus:>3} SKUs   "
              f"index {basket.spend_index}   "
              f"{-basket.spend_delta:>12,.0f}/yr in Floor & Decor's favour"
              f"   ({(kept or 0) * 100:.0f}% survive the common basket)")

    print()
    print(f"{'BASKET COMPOSITION':<30}{'SKUS':>6}{'F&D SPEND':>16}{'SHARE':>8}")
    print("-" * 78)
    by_category: dict = {}
    for comparison in common:
        spend = comparison.base_price * comparison.group.annual_volume
        entry = by_category.setdefault(comparison.group.category, [0, 0.0])
        entry[0] += 1
        entry[1] += spend
    for category, (count, spend) in sorted(
        by_category.items(), key=lambda kv: kv[1][1], reverse=True
    ):
        print(f"{category[:29]:<30}{count:>6}{spend:>16,.0f}{spend / base_spend * 100:>7.1f}%")

    if args.top_skus:
        _print_basket_drivers(common, base_spend, args.top_skus)

    if args.csv:
        out = Path(args.csv)
        _write_basket_csv(common, basket_set, out)
        print(f"\nWrote basket members -> {out}")
    return 0


def _print_basket_drivers(common, base_spend: float, limit: int) -> None:
    """What makes the basket big, and what makes it expensive - two lists.

    A SKU can dominate spend because its price is high or because its volume
    is. Ranking by spend alone conflates the two and sends a merchant after the
    wrong items, so the concentration and the exposure are reported separately.
    """
    by_spend = sorted(
        common, key=lambda c: c.base_price * c.group.annual_volume, reverse=True
    )
    print()
    print(f"WHAT MAKES THE BASKET BIG - top {limit} by annual spend")
    print(f"{'ID':<7}{'CATEGORY':<24}{'UNIT':>9}{'VOLUME':>12}{'SPEND':>13}{'CUM':>7}")
    print("-" * 78)
    cumulative = 0.0
    for comparison in by_spend[:limit]:
        spend = comparison.base_price * comparison.group.annual_volume
        cumulative += spend
        print(f"{comparison.group.group_id:<7}{comparison.group.category[:23]:<24}"
              f"{comparison.base_price:>9.2f}{comparison.group.annual_volume:>12,.0f}"
              f"{spend:>13,.0f}{cumulative / base_spend:>6.0%}")

    exposed = [
        ((c.base_price - c.market_min) * c.group.annual_volume, c)
        for c in common if c.market_min is not None
    ]
    exposure = sum(d for d, _ in exposed if d > 0)
    advantage = sum(-d for d, _ in exposed if d < 0)
    exposed.sort(key=lambda pair: pair[0], reverse=True)
    dearer = [pair for pair in exposed if pair[0] > 0][:limit]

    if dearer:
        print()
        print(f"WHAT MAKES IT EXPENSIVE - top {len(dearer)} by dollars above the market low")
        print(f"{'ID':<7}{'CATEGORY':<24}{'F&D':>9}{'MKT LOW':>9}{'GAP':>8}{'$/YR':>13}")
        print("-" * 78)
        for delta, comparison in dearer:
            print(f"{comparison.group.group_id:<7}{comparison.group.category[:23]:<24}"
                  f"{comparison.base_price:>9.2f}{comparison.market_min:>9.2f}"
                  f"{(comparison.gap_vs_market_min or 0) * 100:>7.1f}%{delta:>13,.0f}")
        share = sum(d for d, _ in dearer) / exposure if exposure else 0
        print(f"\n  These {len(dearer)} SKUs are {share:.0%} of all exposure.")

    print()
    print(f"  Exposure  (F&D dearer):  {exposure:>12,.0f}/yr across "
          f"{sum(1 for d, _ in exposed if d > 0)} SKUs")
    print(f"  Advantage (F&D cheaper): {advantage:>12,.0f}/yr across "
          f"{sum(1 for d, _ in exposed if d < 0)} SKUs")
    print(f"  Net:                     {advantage - exposure:>12,.0f}/yr in "
          f"Floor & Decor's favour, against the cheapest competitor on every line")


def _write_basket_csv(common, basket_set, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    columns = [
        "group_id", "category", "description", "brand", "basis", "annual_volume",
        "fnd_unit_price", "fnd_annual_spend",
    ] + [
        f"{retailer}_{field}"
        for retailer in competitors()
        for field in ("unit_price", "annual_spend", "gap_pct")
    ] + ["cheapest_retailer"]
    with open(path, "w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=columns)
        writer.writeheader()
        for comparison in common:
            volume = comparison.group.annual_volume
            record = {
                "group_id": comparison.group.group_id,
                "category": comparison.group.category,
                "description": comparison.group.description,
                "brand": comparison.base.offer.brand,
                "basis": comparison.group.basis,
                "annual_volume": volume,
                "fnd_unit_price": comparison.base_price,
                "fnd_annual_spend": round(comparison.base_price * volume, 2),
                "cheapest_retailer": comparison.cheapest_retailer or "",
            }
            for retailer in competitors():
                quote = comparison.quotes[retailer]
                record[f"{retailer}_unit_price"] = quote.unit_price
                record[f"{retailer}_annual_spend"] = (
                    round(quote.unit_price * volume, 2) if quote.unit_price else ""
                )
                record[f"{retailer}_gap_pct"] = quote.delta_pct
            writer.writerow(record)


def cmd_prices(args) -> int:
    """Every price in the study, side by side, as quoted and as normalised.

    The canonical products.csv is long - one row per offer - which is right for
    the engine and unreadable for a person. This is the same data pivoted wide:
    one row per SKU, one column block per retailer, with the shelf price exactly
    as collected next to the unit price the comparison actually uses.
    """
    comparisons = _load(args)

    columns = ["group_id", "category", "subcategory", "description", "basis",
               "annual_volume"]
    for retailer in active_retailers():
        code = RETAILER_CODES[retailer]
        columns.extend([
            f"{code}_brand", f"{code}_sku", f"{code}_price_as_quoted", f"{code}_uom",
            f"{code}_pack_coverage", f"{code}_promo_price", f"{code}_unit_price",
            f"{code}_match_tier", f"{code}_in_stock", f"{code}_counted",
        ])
    columns.extend(["market_min", "gap_vs_market_min", "outcome", "cheapest_retailer"])

    out = Path(args.csv or DEFAULT_OUT / "raw_prices.csv")
    out.parent.mkdir(parents=True, exist_ok=True)
    with open(out, "w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=columns)
        writer.writeheader()
        for comp in comparisons:
            row = {
                "group_id": comp.group.group_id,
                "category": comp.group.category,
                "subcategory": comp.group.subcategory,
                "description": comp.group.description,
                "basis": comp.group.basis,
                "annual_volume": comp.group.annual_volume,
                "market_min": comp.market_min,
                "gap_vs_market_min": comp.gap_vs_market_min,
                "outcome": comp.outcome,
                "cheapest_retailer": comp.cheapest_retailer or "",
            }
            for retailer in active_retailers():
                code = RETAILER_CODES[retailer]
                if retailer == BASE_RETAILER:
                    normalized, tier, counted = comp.base, "base", "yes"
                else:
                    quote = comp.quotes[retailer]
                    normalized = quote.normalized
                    tier = quote.tier
                    counted = "yes" if quote.included else "no"
                if normalized is None:
                    # Not carried, or the offer could not be converted. Blank
                    # cells, never zeros - a zero would price as free.
                    row.update({f"{code}_{f}": "" for f in (
                        "brand", "sku", "price_as_quoted", "uom", "pack_coverage",
                        "promo_price", "unit_price", "in_stock")})
                    row[f"{code}_match_tier"] = "not carried" if tier == "none" else tier
                    row[f"{code}_counted"] = "no"
                    continue
                offer = normalized.offer
                row.update({
                    f"{code}_brand": offer.brand,
                    f"{code}_sku": offer.retailer_sku,
                    f"{code}_price_as_quoted": offer.price,
                    f"{code}_uom": offer.uom,
                    f"{code}_pack_coverage": offer.pack_coverage or "",
                    f"{code}_promo_price": offer.promo_price or "",
                    f"{code}_unit_price": normalized.unit_price,
                    f"{code}_match_tier": tier,
                    f"{code}_in_stock": "yes" if offer.in_stock else "no",
                    f"{code}_counted": counted,
                })
            writer.writerow(row)

    print(f"Wrote {len(comparisons)} SKUs x {len(RETAILERS)} retailers -> {out}")

    sample = comparisons[: args.show]
    if sample:
        heads = "".join(f"{RETAILER_CODES[r].upper():>22}" for r in active_retailers())
        print()
        print(f"{'GROUP':<8}{'DESCRIPTION':<34}{heads}")
        print("-" * (42 + 22 * len(RETAILERS)))
        for comp in sample:
            cells = ""
            for retailer in active_retailers():
                normalized = (
                    comp.base if retailer == BASE_RETAILER
                    else comp.quotes[retailer].normalized
                )
                if normalized is None:
                    cells += f"{'-':>22}"
                    continue
                offer = normalized.offer
                quoted = f"${offer.effective_price:,.2f} {offer.uom[4:]}"
                cells += f"{quoted:>13}{normalized.unit_price:>9.2f}"
            print(f"{comp.group.group_id:<8}{comp.group.description[:33]:<34}{cells}")
        print()
        print("  Each pair is the shelf price as quoted, then the normalised unit price")
        print(f"  on the SKU's basis. Blank = the retailer carries nothing comparable.")
    return 0


def _promo_intensity(args) -> dict:
    """How much of each retailer's book is on promotion, and how deep."""
    _, offers = load_dataset(Path(args.groups), Path(args.products))
    stats: dict = {}
    for retailer in active_retailers():
        theirs = [o for o in offers if o.retailer == retailer]
        discounted = [o for o in theirs if o.on_promo]
        depth = (
            sum(1 - o.promo_price / o.price for o in discounted) / len(discounted)
            if discounted else 0.0
        )
        stats[retailer] = (len(discounted), len(theirs), depth)
    return stats


def cmd_report(args) -> int:
    from .report import render_html

    comparisons = _load(args)
    # The everyday-low-price section needs the same study priced both ways.
    shelf = None
    if not args.list_price:
        groups, offers = load_dataset(Path(args.groups), Path(args.products))
        shelf = compare_all(
            groups, offers, min_tier=args.min_tier, use_list_price=True
        )
        if args.category:
            wanted = args.category.lower()
            shelf = [c for c in shelf if wanted in c.group.category.lower()]

    out = Path(args.out or DEFAULT_OUT / "pricing_report.html")
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(
        render_html(comparisons, _collected_on(args), shelf, _promo_intensity(args)),
        encoding="utf-8",
    )
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


def cmd_ingest(args) -> int:
    """Convert a filled collection worksheet into the canonical data files."""
    sources = [Path(w) for w in args.worksheet]
    report = ingest_worksheets(sources)

    groups_out = Path(args.groups_out or DEFAULT_GROUPS)
    products_out = Path(args.products_out or DEFAULT_PRODUCTS)
    if not args.force and (groups_out.exists() or products_out.exists()):
        raise SystemExit(
            f"{groups_out} / {products_out} already exist. Pass --force to overwrite, "
            f"or --groups-out/--products-out to write elsewhere so the existing "
            f"dataset is preserved."
        )

    write_canonical(report, groups_out, products_out)
    print(f"Ingested {len(report.groups)} SKU(s) and {len(report.offers)} offer(s) "
          f"from {len(sources)} worksheet(s):")
    for source in sources:
        print(f"  {source}")
    print(f"  priced at every one of the {len(RETAILERS)} retailers: {report.three_way}")
    print(f"  -> {groups_out}")
    print(f"  -> {products_out}")
    if report.not_started:
        print(f"  not yet collected: {report.not_started} candidate(s) still blank")
    if report.skipped:
        print(f"\nNeeds attention - {len(report.skipped)} row(s):")
        for candidate_id, reason in report.skipped[:20]:
            print(f"  {candidate_id}: {reason}")
        if len(report.skipped) > 20:
            print(f"  ... and {len(report.skipped) - 20} more")
    print("\nNext: python3 -m fnd_pricing validate && python3 -m fnd_pricing basket")
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
                    "Home Depot, Lowe's, Menards and The Tile Shop.",
    )
    parser.add_argument("--groups", default=str(DEFAULT_GROUPS), help="sku_groups.csv path")
    parser.add_argument("--products", default=str(DEFAULT_PRODUCTS), help="products.csv path")
    parser.add_argument(
        "--min-tier", default=DEFAULT_MIN_TIER, choices=list(TIER_ORDER),
        help="weakest match tier admitted to the comparison (default: %(default)s)",
    )
    parser.add_argument(
        "--list-price", action="store_true",
        help="price every offer at its shelf price, ignoring promotions on all "
             "sides. Use it to read an everyday-low-price position, which a "
             "promo-inclusive snapshot understates.",
    )
    parser.add_argument(
        "--exclude", action="append", default=[], metavar="RETAILER",
        help="drop a competitor from this run, e.g. --exclude tile_shop. "
             "Repeatable. This changes what the market low is measured "
             "against, so results are not comparable to a run with a different set.",
    )
    parser.add_argument(
        "--only", action="append", default=[], metavar="RETAILER",
        help="compare against only these competitors (Floor & Decor is always "
             "included). Repeatable; overrides --exclude.",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    sub = subparsers.add_parser("validate", help="check the input files and report coverage")
    sub.set_defaults(func=cmd_validate)

    sub = subparsers.add_parser("compare", help="print the comparison summary")
    sub.add_argument("--category", help="filter to categories containing this text")
    sub.add_argument("--top", type=int, default=10, help="how many worst gaps to list")
    sub.add_argument("--csv", help="also write the per-SKU detail to this CSV path")
    sub.set_defaults(func=cmd_compare)

    sub = subparsers.add_parser(
        "index", help="rank categories by annual expense and price position")
    sub.add_argument("--category", help="filter to categories containing this text")
    sub.add_argument("--csv", help="also write the category expense table to this CSV path")
    sub.set_defaults(func=cmd_index)

    sub = subparsers.add_parser(
        "basket", help="price a basket built from one match tier (default: identical SKUs)")
    sub.add_argument("--tier", default=TIER_EXACT, choices=list(TIER_ORDER),
                     help="match tier the basket is built from (default: %(default)s)")
    sub.add_argument("--at-least", action="store_true",
                     help="include this tier OR BETTER, rather than only this tier - "
                          "the 'everything we both carry' basket")
    sub.add_argument("--category", help="filter to categories containing this text")
    sub.add_argument("--top-skus", type=int, default=0, metavar="N",
                     help="also list the N SKUs driving the basket's size and its "
                          "exposure above the market low")
    sub.add_argument("--csv", help="also write the basket members to this CSV path")
    sub.set_defaults(func=cmd_basket)

    sub = subparsers.add_parser(
        "prices", help="every price side by side, as quoted and as normalised")
    sub.add_argument("--category", help="filter to categories containing this text")
    sub.add_argument("--csv", help="output path (default data/out/raw_prices.csv)")
    sub.add_argument("--show", type=int, default=8,
                     help="how many rows to preview on screen")
    sub.set_defaults(func=cmd_prices)

    sub = subparsers.add_parser("report", help="write the self-contained HTML report")
    sub.add_argument("--category", help="filter to categories containing this text")
    sub.add_argument("--out", help="output path")
    sub.set_defaults(func=cmd_report)

    sub = subparsers.add_parser("export", help="write the multi-sheet Excel workbook")
    sub.add_argument("--category", help="filter to categories containing this text")
    sub.add_argument("--out", help="output path")
    sub.set_defaults(func=cmd_export)

    sub = subparsers.add_parser(
        "ingest", help="convert a filled collection worksheet into the data files")
    sub.add_argument("worksheet", nargs="+",
                     help="one or more filled collection worksheet CSVs; several are "
                          "merged into a single dataset")
    sub.add_argument("--groups-out", help="where to write sku_groups.csv")
    sub.add_argument("--products-out", help="where to write products.csv")
    sub.add_argument("--force", action="store_true",
                     help="overwrite existing data files")
    sub.set_defaults(func=cmd_ingest)

    sub = subparsers.add_parser("template", help="write a blank price collection CSV")
    sub.add_argument("--out", help="output path")
    sub.set_defaults(func=cmd_template)
    return parser


def _apply_retailer_filter(args) -> None:
    if args.only:
        set_active_retailers(list(args.only) + [BASE_RETAILER])
    elif args.exclude:
        keep = [r for r in RETAILERS if r not in set(args.exclude)]
        unknown = [r for r in args.exclude if r not in RETAILERS]
        if unknown:
            raise SystemExit(
                f"unknown retailer(s): {', '.join(unknown)}. "
                f"Known: {', '.join(RETAILERS)}"
            )
        set_active_retailers(keep)


def main(argv=None) -> int:
    args = build_parser().parse_args(argv)
    try:
        _apply_retailer_filter(args)
        if args.list_price:
            print("[pricing at list: promotions ignored on all sides]")
        if set(active_retailers()) != set(RETAILERS):
            dropped = [RETAILER_LABELS[r] for r in RETAILERS
                       if r not in set(active_retailers())]
            print(f"[active set: {len(active_retailers())} retailers; "
                  f"excluded {', '.join(dropped)}]")
        return args.func(args)
    except ValueError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2
    except DataError as exc:
        print(f"data error: {exc}", file=sys.stderr)
        return 2
    except FileNotFoundError as exc:
        print(f"file not found: {exc.filename}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
