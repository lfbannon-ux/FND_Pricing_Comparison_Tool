#!/usr/bin/env python3
"""
Phase 4 -- canonical layer.

Maps verbatim filing captions onto canonical rows: ONE continuous row per
economic line item across all periods, with era/basis changes carried as
labelled parallel rows rather than silently merged.

Guards (both fatal by default -- that is the point):
  * COLLISION  two source values land on the same (basis, statement, canonical
               line, period) with DIFFERENT values -> abort. Identical values
               are absorbed as duplicates and logged.
  * LEFTOVER   a source row matches no canonical rule and no explicit EXCLUDE
               -> abort. Extend the map or add a reasoned exclusion.

Usage:
    python3 scripts/canonicalize.py --report      # diagnose: list leftovers/collisions, never abort
    python3 scripts/canonicalize.py               # build: abort on any guard breach
"""
from __future__ import annotations

import argparse
import csv
import re
import sys
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
EXTRACT = ROOT / "extraction"
CANON = ROOT / "canonical"

sys.path.insert(0, str(Path(__file__).resolve().parent))

SRC_FIELDS = [
    "basis", "source_doc", "source_page", "source_url", "statement", "period_label",
    "period_end", "period_type", "section", "line_item", "value", "unit",
    "is_subtotal", "is_comparative", "order_index", "note",
]

# Units are normalised to USD millions where unambiguous. Anything else passes
# through untouched and keeps its own unit.
TO_MILLIONS = {
    "usd_millions": 1.0,
    "usd_thousands": 0.001,
    "usd": 0.000001,
}
PASSTHROUGH = {"usd_per_share", "pct", "shares", "bcf", "count", "text", "cad_millions"}


def load_sources() -> list[dict]:
    rows: list[dict] = []
    files = sorted(EXTRACT.glob("*.csv"))
    if not files:
        sys.exit(f"No extraction CSVs found in {EXTRACT}")
    for path in files:
        with path.open(newline="", encoding="utf-8") as fh:
            rdr = csv.DictReader(fh)
            missing = [c for c in SRC_FIELDS if c not in (rdr.fieldnames or [])]
            if missing:
                print(f"  !! {path.name}: missing columns {missing} -- skipped")
                continue
            for i, r in enumerate(rdr, start=2):
                r["_src_file"] = path.name
                r["_src_line"] = i
                rows.append(r)
    return rows


def norm_value(raw: str, unit: str) -> tuple[float | None, str, str]:
    """Return (value_in_target_unit, target_unit, conversion_note)."""
    raw = (raw or "").strip().replace(",", "").replace("$", "")
    if raw in {"", "-", "--", "–", "—"}:
        return None, unit, ""
    neg = raw.startswith("(") and raw.endswith(")")
    if neg:
        raw = raw[1:-1]
    try:
        v = float(raw)
    except ValueError:
        return None, unit, f"unparseable value {raw!r}"
    if neg:
        v = -v
    if unit in TO_MILLIONS:
        factor = TO_MILLIONS[unit]
        if factor != 1.0:
            return round(v * factor, 6), "usd_millions", f"x{factor} from {unit}"
        return round(v, 6), "usd_millions", ""
    return v, unit, ""


def match_rule(row: dict, rules: list[dict]) -> dict | None:
    """Section-qualified rules match first, then unqualified. First hit wins."""
    stmt = (row.get("statement") or "").strip()
    section = (row.get("section") or "").strip()
    caption = (row.get("line_item") or "").strip()
    for qualified in (True, False):
        for rule in rules:
            if rule.get("statement") and rule["statement"] != stmt:
                continue
            has_sec = bool(rule.get("section"))
            if has_sec != qualified:
                continue
            if has_sec and not re.search(rule["section"], section, re.I):
                continue
            if re.search(rule["pattern"], caption, re.I):
                return rule
    return None


def is_excluded(row: dict, excludes: list[dict]) -> str | None:
    caption = (row.get("line_item") or "").strip()
    stmt = (row.get("statement") or "").strip()
    for ex in excludes:
        if ex.get("statement") and ex["statement"] != stmt:
            continue
        if re.search(ex["pattern"], caption, re.I):
            return ex["reason"]
    return None


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--report", action="store_true",
                    help="diagnose only: list leftovers and collisions, never abort")
    args = ap.parse_args()

    try:
        from canonical_map import RULES, EXCLUDES  # type: ignore
    except ImportError:
        sys.exit("scripts/canonical_map.py not found. Build it from the extraction "
                 "captions first (run with --report once the map exists).")

    CANON.mkdir(parents=True, exist_ok=True)
    rows = load_sources()
    print(f"Loaded {len(rows)} source rows from {len(set(r['_src_file'] for r in rows))} files")

    canonical: dict[tuple, dict] = {}
    caption_map: dict[tuple, set] = defaultdict(set)
    leftovers: list[dict] = []
    collisions: list[str] = []
    duplicates: list[str] = []
    excluded: list[str] = []
    conversions: list[str] = []

    for r in rows:
        reason = is_excluded(r, EXCLUDES)
        if reason:
            excluded.append(f"{r['_src_file']}:{r['_src_line']} {r['line_item']!r} -> {reason}")
            continue
        rule = match_rule(r, RULES)
        if rule is None:
            leftovers.append(r)
            continue

        val, unit, conv = norm_value(r["value"], r["unit"])
        if conv and "unparseable" in conv:
            leftovers.append(r)
            continue
        if conv:
            conversions.append(f"{r['_src_file']}:{r['_src_line']} {r['line_item']!r} {conv}")

        key = (r["basis"], rule["canonical_statement"], rule["canonical"],
               r["period_label"], r["period_type"])
        payload = {
            "basis": r["basis"],
            "statement": rule["canonical_statement"],
            "section": rule["canonical_section"],
            "line": rule["canonical"],
            "order": rule["order"],
            "period_label": r["period_label"],
            "period_end": r["period_end"],
            "period_type": r["period_type"],
            "value": val,
            "unit": unit,
            "is_subtotal": r["is_subtotal"],
            "is_comparative": r["is_comparative"],
            "source_doc": r["source_doc"],
            "source_page": r["source_page"],
            "source_url": r["source_url"],
            "note": r["note"],
        }
        if key in canonical:
            prev = canonical[key]["value"]
            if prev == val:
                duplicates.append(f"{key} == {val} (absorbed, from {r['_src_file']}:{r['_src_line']})")
            else:
                collisions.append(
                    f"COLLISION {key}\n"
                    f"    existing {prev} from doc {canonical[key]['source_doc']} "
                    f"p{canonical[key]['source_page']}\n"
                    f"    incoming {val} from doc {r['source_doc']} p{r['source_page']} "
                    f"({r['_src_file']}:{r['_src_line']})"
                )
        else:
            canonical[key] = payload
        caption_map[(rule["canonical_statement"], rule["canonical"], r["basis"])].add(
            (r["line_item"], r["period_label"], r["source_doc"])
        )

    # ---- guards ----
    print(f"\nMapped   : {len(canonical)} canonical cells")
    print(f"Duplicates absorbed: {len(duplicates)}")
    print(f"Excluded : {len(excluded)}")
    print(f"Unit conversions: {len(conversions)}")
    print(f"LEFTOVERS: {len(leftovers)}")
    print(f"COLLISIONS: {len(collisions)}")

    if leftovers:
        print("\n--- unmapped captions (top 60) ---")
        seen = set()
        for r in leftovers:
            sig = (r["statement"], r["section"], r["line_item"])
            if sig in seen:
                continue
            seen.add(sig)
            print(f"  [{r['statement']}] {r['section']!r} :: {r['line_item']!r}"
                  f"  ({r['_src_file']}:{r['_src_line']})")
            if len(seen) >= 60:
                print(f"  ... and {len(leftovers) - 60}+ more")
                break
    if collisions:
        print("\n--- collisions ---")
        for c in collisions[:40]:
            print("  " + c)

    if not args.report and (leftovers or collisions):
        (CANON / "GUARD_FAILURES.txt").write_text(
            "LEFTOVERS\n" + "\n".join(
                f"[{r['statement']}] {r['section']!r} :: {r['line_item']!r} ({r['_src_file']}:{r['_src_line']})"
                for r in leftovers)
            + "\n\nCOLLISIONS\n" + "\n".join(collisions), encoding="utf-8")
        sys.exit("\nABORT: guard breach. See canonical/GUARD_FAILURES.txt. "
                 "Extend canonical_map.py or add a reasoned EXCLUDE -- never drop rows silently.")

    # ---- outputs ----
    out = CANON / "canonical.csv"
    with out.open("w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=[
            "basis", "statement", "section", "line", "order", "period_label", "period_end",
            "period_type", "value", "unit", "is_subtotal", "is_comparative",
            "source_doc", "source_page", "source_url", "note"])
        w.writeheader()
        for _, payload in sorted(canonical.items(),
                                 key=lambda kv: (kv[1]["basis"], kv[1]["statement"],
                                                 kv[1]["order"], kv[1]["period_end"] or "")):
            w.writerow(payload)

    cm = CANON / "caption_map.csv"
    with cm.open("w", newline="", encoding="utf-8") as fh:
        w = csv.writer(fh)
        w.writerow(["statement", "canonical_line", "basis", "verbatim_caption",
                    "period_label", "source_doc"])
        for (stmt, line, basis), entries in sorted(caption_map.items()):
            for caption, period, doc in sorted(entries):
                w.writerow([stmt, line, basis, caption, period, doc])

    (CANON / "TRANSFORM_LOG.md").write_text(
        "# Canonical transform log\n\n"
        f"- source rows: {len(rows)}\n- canonical cells: {len(canonical)}\n"
        f"- duplicates absorbed: {len(duplicates)}\n- excluded: {len(excluded)}\n"
        f"- unit conversions: {len(conversions)}\n\n"
        "## Duplicates absorbed (identical values, same key)\n" + "\n".join(f"- {d}" for d in duplicates)
        + "\n\n## Explicit exclusions\n" + "\n".join(f"- {e}" for e in excluded)
        + "\n\n## Unit conversions\n" + "\n".join(f"- {c}" for c in conversions) + "\n",
        encoding="utf-8")

    print(f"\nWrote {out}, {cm}, {CANON / 'TRANSFORM_LOG.md'}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
