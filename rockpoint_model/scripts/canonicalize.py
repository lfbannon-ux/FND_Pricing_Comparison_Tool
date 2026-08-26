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
PASSTHROUGH = {"usd_per_share", "cad_per_share", "pct", "shares", "bcf", "count",
               "text", "cad_millions", "years"}



def annotate_blocks(rows: list[dict]) -> None:
    """
    Documented pre-pass for same-caption-twice cases.

    A non-IFRS reconciliation walks UP from net earnings to Adjusted Gross Margin
    and then DOWN again to Adjusted EBITDA, printing the SAME caption twice with
    opposite signs (e.g. "Operating" +50.8 then -50.8). The brief forbids merging
    across a sign-convention flip, so these must stay separate rows.

    Disambiguation is by PRINT ORDER, labelled with the subtotal the row builds
    toward -- which is what the reader actually needs ("...to Adjusted EBITDA")
    rather than an opaque index. Applied ONLY where a genuine duplicate exists.
    """
    groups: dict[tuple, list[dict]] = defaultdict(list)
    for r in rows:
        groups[(r["_src_file"], r["statement"], r["section"],
                r["period_label"], r["period_type"])].append(r)

    for _, grp in groups.items():
        grp.sort(key=lambda x: int(x["order_index"] or 0))
        # nearest following subtotal = the total this row builds toward
        nxt = ""
        for r in reversed(grp):
            r["_block_label"] = nxt
            if r["is_subtotal"] == "1":
                nxt = r["line_item"]
        # only qualify captions that actually repeat with differing values
        by_caption: dict[str, list[dict]] = defaultdict(list)
        for r in grp:
            by_caption[r["line_item"]].append(r)
        for caption, dupes in by_caption.items():
            if len(dupes) > 1 and len({d["value"] for d in dupes}) > 1:
                for d in dupes:
                    d["_needs_block"] = "1"

    # Cross-FILE duplicates: the same canonical cell reported differently by two
    # filings is an inter-filing discrepancy / restatement, not a collision to
    # resolve. Qualify by source document so both survive, and log it.
    xf: dict[tuple, list[dict]] = defaultdict(list)
    for r in rows:
        xf[(r["basis"], r["statement"], r["section"], r["line_item"],
            r["period_label"], r["period_type"])].append(r)
    for _, grp in xf.items():
        if len({d["source_doc"] for d in grp}) > 1 and len({d["value"] for d in grp}) > 1:
            for d in grp:
                d["_needs_doc_qual"] = "1"


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
    raw_original = (raw or "").strip()
    # A text-unit fact (credit rating, target range, maturity date) is a reported
    # value, not a number that failed to parse. Carry it through verbatim.
    if unit in {"text"}:
        return (raw_original or None), unit, ""
    raw = raw_original.replace(",", "").replace("$", "")
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
    basis = (row.get("basis") or "").strip()
    for qualified in (True, False):
        for rule in rules:
            if rule.get("statement") and rule["statement"] != stmt:
                continue
            if rule.get("basis") and rule["basis"] != basis:
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
    annotate_blocks(rows)
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

        canonical_line = (r["line_item"] if rule.get("passthrough") else rule["canonical"])
        canonical_section = (r["section"] if rule.get("passthrough")
                             else rule["canonical_section"])
        # Documented pre-pass: several note tables print IDENTICAL row and column
        # captions across repeated blocks (PP&E cost / accumulated depreciation /
        # net book value) or across roll-forward columns (deferred tax: closing
        # balance, recognised in P&L, recognised in the balance sheet, opening
        # balance). The extracting agent recorded which block or column each row
        # came from as "block=<name>" / "column=<name>" in the note field. Fold
        # that qualifier into the canonical section so those genuinely distinct
        # figures stay separate rows instead of colliding.
        if rule.get("passthrough"):
            from canonical_map import SECTION_ALIASES
            canonical_section = SECTION_ALIASES.get(canonical_section, canonical_section)
            quals = []
            for pat in (r"section stub:\s*([^;]+)", r"\bblock=([^;]+)",
                        r"\bcolumn=([^;]+)"):
                m = re.search(pat, r.get("note", "") or "")
                if m:
                    quals.append(m.group(1).strip().replace("_", " "))
            if r.get("_needs_doc_qual"):
                quals.append(f"per doc {r['source_doc']}")
            if r.get("_needs_block") and r.get("_block_label"):
                quals.append(f"to {r['_block_label']}")
            if quals:
                qual = " / ".join(quals)
                canonical_section = (f"{qual}: {canonical_section}"
                                     if canonical_section else qual)
        canonical_order = (int(r["order_index"] or 0) if rule.get("passthrough")
                           else rule["order"])
        key = (r["basis"], rule["canonical_statement"], canonical_section, canonical_line,
               r["period_label"], r["period_type"])
        payload = {
            "basis": r["basis"],
            "statement": rule["canonical_statement"],
            "section": canonical_section,
            "line": canonical_line,
            "order": canonical_order,
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
        caption_map[(rule["canonical_statement"], canonical_line, r["basis"])].add(
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

    restated = sorted({
        (r["basis"], r["statement"], r["line_item"], r["period_label"],
         r["source_doc"], r["value"])
        for r in rows if r.get("_needs_doc_qual")})
    if restated:
        lines = ["# Inter-filing discrepancies / restatements", "",
                 "The same period reported with a DIFFERENT value by two filings.",
                 "Neither value is overwritten; each is carried on its own canonical row,",
                 "qualified by source document.", ""]
        for b, st, li, per, doc, val in restated:
            lines.append(f"- [{b}] {st} :: {li!r} {per}: **{val}** per doc {doc}")
        (CANON / "RESTATEMENTS.md").write_text("\n".join(lines) + "\n", encoding="utf-8")

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
