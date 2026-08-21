"""Self-contained HTML report.

No external assets, no CDN, no build step - the output file can be mailed to a
merchant or opened from a share drive and it still works.
"""

from __future__ import annotations

import html
import json
from typing import Dict, List, Optional

from . import BASE_RETAILER, RETAILER_LABELS, RETAILERS
from .compare import GroupComparison, Rollup, build_rollup, rollup_by_category

COMPETITORS = [r for r in RETAILERS if r != BASE_RETAILER]


def _pct(value: Optional[float], digits: int = 1) -> str:
    return "-" if value is None else f"{value * 100:+.{digits}f}%"


def _money(value: Optional[float]) -> str:
    return "-" if value is None else f"${value:,.2f}"


def _basis_label(basis: str) -> str:
    return {"sq_ft": "/sq ft", "lin_ft": "/lin ft", "lb": "/lb", "each": " ea"}[basis]


def _rows_payload(comparisons: List[GroupComparison]) -> List[dict]:
    rows = []
    for comp in comparisons:
        row = {
            "id": comp.group.group_id,
            "category": comp.group.category,
            "sub": comp.group.subcategory,
            "desc": comp.group.description,
            "basis": _basis_label(comp.group.basis),
            "volume": comp.group.annual_volume,
            "fnd": comp.base_price,
            "fndBrand": comp.base.offer.brand if comp.base else "",
            "outcome": comp.outcome,
            "gap": comp.gap_vs_market_min,
            "cheapest": RETAILER_LABELS.get(comp.cheapest_retailer or "", "-"),
            "flags": sorted({f.split(":")[0] for f in comp.flags}),
        }
        for retailer in COMPETITORS:
            quote = comp.quotes[retailer]
            key = "hd" if retailer == "home_depot" else "lw"
            row[key] = quote.unit_price
            row[key + "Delta"] = quote.delta_pct
            row[key + "Tier"] = quote.tier
            row[key + "Brand"] = quote.normalized.offer.brand if quote.normalized else ""
            row[key + "Promo"] = bool(
                quote.normalized and quote.normalized.offer.on_promo
            )
            row[key + "Included"] = quote.included
            row[key + "Note"] = quote.note
        rows.append(row)
    return rows


def _tiles(overall: Rollup, comparisons: List[GroupComparison]) -> str:
    def basket(retailer: str) -> Optional[float]:
        base_spend = comp_spend = 0.0
        for comp in comparisons:
            quote = comp.quotes[retailer]
            if not quote.included or comp.base_price is None or not comp.group.annual_volume:
                continue
            volume = comp.group.annual_volume
            base_spend += comp.base_price * volume
            comp_spend += quote.unit_price * volume
        return round(base_spend / comp_spend, 4) if comp_spend else None

    def index_tile(value, label, sub):
        tone = "good" if value is not None and value < 1 else "bad"
        text = "-" if value is None else f"{value:.3f}"
        return f"""<div class="tile {tone}"><div class="tile-value">{text}</div>
        <div class="tile-label">{html.escape(label)}</div>
        <div class="tile-sub">{html.escape(sub)}</div></div>"""

    win_rate = overall.win_rate or 0
    tiles = [
        f"""<div class="tile"><div class="tile-value">{overall.compared}</div>
        <div class="tile-label">SKUs compared</div>
        <div class="tile-sub">of {overall.groups} in the study</div></div>""",
        f"""<div class="tile {'good' if win_rate >= 0.5 else 'bad'}">
        <div class="tile-value">{win_rate * 100:.0f}%</div>
        <div class="tile-label">Floor &amp; Decor win rate</div>
        <div class="tile-sub">{overall.wins}W / {overall.ties}T / {overall.losses}L vs cheapest competitor</div></div>""",
        f"""<div class="tile {'good' if (overall.median_gap or 0) < 0 else 'bad'}">
        <div class="tile-value">{_pct(overall.median_gap)}</div>
        <div class="tile-label">Median gap vs market low</div>
        <div class="tile-sub">negative = Floor &amp; Decor is cheaper</div></div>""",
        index_tile(overall.spend_index, "Basket index vs market low", "volume-weighted spend ratio"),
        index_tile(basket("home_depot"), "Basket index vs Home Depot", "volume-weighted spend ratio"),
        index_tile(basket("lowes"), "Basket index vs Lowe's", "volume-weighted spend ratio"),
    ]
    return "\n".join(tiles)


def _category_table(rollups: List[Rollup]) -> str:
    body = []
    for r in rollups:
        gap_class = "pos" if (r.median_gap or 0) > 0 else "neg"
        idx = "-" if r.spend_index is None else f"{r.spend_index:.3f}"
        idx_class = "pos" if (r.spend_index or 0) > 1 else "neg"
        body.append(
            f"<tr><td>{html.escape(r.label)}</td><td class='num'>{r.groups}</td>"
            f"<td class='num'>{r.compared}</td>"
            f"<td class='num'>{(r.win_rate or 0) * 100:.0f}%</td>"
            f"<td class='num {gap_class}'>{_pct(r.median_gap)}</td>"
            f"<td class='num {idx_class}'>{idx}</td>"
            f"<td class='num'>{_pct(r.per_retailer_gap.get('home_depot'))}</td>"
            f"<td class='num'>{_pct(r.per_retailer_gap.get('lowes'))}</td></tr>"
        )
    return "\n".join(body)


def render_html(comparisons: List[GroupComparison], collected_on: str = "") -> str:
    overall = build_rollup("All categories", comparisons)
    categories = rollup_by_category(comparisons)
    payload = json.dumps(_rows_payload(comparisons))
    cat_options = "\n".join(
        f'<option value="{html.escape(c.label)}">{html.escape(c.label)}</option>'
        for c in categories
    )
    subtitle = (
        f"200 SKU groups &middot; Floor &amp; Decor vs Home Depot vs Lowe's"
        + (f" &middot; prices collected {html.escape(collected_on)}" if collected_on else "")
    )

    return f"""<!doctype html>
<html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Pricing Comparison</title>
<style>
:root {{
  --bg:#f6f7f9; --panel:#ffffff; --ink:#16191d; --muted:#5f6873; --line:#e2e5ea;
  --good:#0b7a4b; --bad:#b3261e; --accent:#1a4f8a;
}}
@media (prefers-color-scheme: dark) {{
  :root {{ --bg:#14171a; --panel:#1c2126; --ink:#e8eaed; --muted:#9aa4b0;
           --line:#2b3138; --good:#4ade80; --bad:#f87171; --accent:#7aa7dd; }}
}}
* {{ box-sizing:border-box; }}
body {{ margin:0; background:var(--bg); color:var(--ink);
  font:14px/1.5 -apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,Helvetica,Arial,sans-serif; }}
.wrap {{ max-width:1400px; margin:0 auto; padding:32px 20px 64px; }}
h1 {{ font-size:24px; margin:0 0 4px; letter-spacing:-.01em; }}
.sub {{ color:var(--muted); margin:0 0 28px; }}
h2 {{ font-size:15px; text-transform:uppercase; letter-spacing:.06em;
  color:var(--muted); margin:36px 0 12px; }}
.tiles {{ display:grid; gap:12px; grid-template-columns:repeat(auto-fit,minmax(190px,1fr)); }}
.tile {{ background:var(--panel); border:1px solid var(--line); border-left:3px solid var(--accent);
  border-radius:8px; padding:16px; }}
.tile.good {{ border-left-color:var(--good); }}
.tile.bad {{ border-left-color:var(--bad); }}
.tile-value {{ font-size:26px; font-weight:650; letter-spacing:-.02em; }}
.tile-label {{ font-size:13px; margin-top:2px; }}
.tile-sub {{ font-size:12px; color:var(--muted); margin-top:4px; }}
.panel {{ background:var(--panel); border:1px solid var(--line); border-radius:8px; overflow-x:auto; }}
table {{ border-collapse:collapse; width:100%; font-size:13px; }}
th, td {{ padding:9px 12px; text-align:left; border-bottom:1px solid var(--line); white-space:nowrap; }}
th {{ position:sticky; top:0; background:var(--panel); font-weight:600; font-size:12px;
  text-transform:uppercase; letter-spacing:.04em; color:var(--muted); cursor:pointer; user-select:none; }}
th.num, td.num {{ text-align:right; font-variant-numeric:tabular-nums; }}
tbody tr:hover {{ background:rgba(127,127,127,.07); }}
.neg {{ color:var(--good); }} .pos {{ color:var(--bad); }}
.desc {{ white-space:normal; min-width:220px; color:var(--muted); }}
.pill {{ display:inline-block; padding:1px 7px; border-radius:20px; font-size:11px;
  border:1px solid var(--line); color:var(--muted); }}
.pill.exact {{ color:var(--good); border-color:currentColor; }}
.pill.weak, .pill.none {{ color:var(--bad); border-color:currentColor; }}
.flag {{ display:inline-block; font-size:11px; color:var(--muted); }}
.controls {{ display:flex; gap:10px; flex-wrap:wrap; margin-bottom:12px; }}
input, select {{ padding:8px 10px; border:1px solid var(--line); border-radius:6px;
  background:var(--panel); color:var(--ink); font-size:13px; }}
input {{ min-width:260px; }}
.count {{ color:var(--muted); align-self:center; font-size:13px; }}
footer {{ color:var(--muted); font-size:12px; margin-top:32px; line-height:1.7; }}
</style></head><body><div class="wrap">
<h1>Like-for-like pricing comparison</h1>
<p class="sub">{subtitle}</p>

<div class="tiles">{_tiles(overall, comparisons)}</div>

<h2>By category</h2>
<div class="panel"><table>
<thead><tr><th>Category</th><th class="num">SKUs</th><th class="num">Compared</th>
<th class="num">Win rate</th><th class="num">Median gap</th><th class="num">Basket index</th>
<th class="num">vs Home Depot</th><th class="num">vs Lowe's</th></tr></thead>
<tbody>{_category_table(categories)}</tbody></table></div>

<h2>SKU detail</h2>
<div class="controls">
  <input id="q" type="search" placeholder="Search description, brand or SKU group id">
  <select id="cat"><option value="">All categories</option>{cat_options}</select>
  <select id="out"><option value="">All outcomes</option>
    <option value="win">Wins</option><option value="tie">Ties</option>
    <option value="loss">Losses</option><option value="no_comparison">No comparison</option></select>
  <select id="tier"><option value="">All match tiers</option>
    <option value="exact">Exact only</option>
    <option value="equivalent">Exact + equivalent</option></select>
  <span class="count" id="count"></span>
</div>
<div class="panel"><table id="grid">
<thead><tr>
<th data-k="id">Group</th><th data-k="category">Category</th><th data-k="desc">Description</th>
<th class="num" data-k="fnd">F&amp;D</th>
<th class="num" data-k="hd">Home Depot</th><th class="num" data-k="hdDelta">&Delta;</th>
<th class="num" data-k="lw">Lowe's</th><th class="num" data-k="lwDelta">&Delta;</th>
<th class="num" data-k="gap">Gap vs low</th><th data-k="cheapest">Cheapest</th>
<th data-k="hdTier">Match</th><th data-k="flags">Flags</th>
</tr></thead><tbody></tbody></table></div>

<footer>
<strong>Reading the numbers.</strong> Every price is normalised onto the SKU group's
comparison basis before comparison, so a per-case Home Depot price and a per-square-foot
Floor &amp; Decor price meet on the same unit. &Delta; is the competitor's price against
Floor &amp; Decor: negative means the competitor is cheaper. Gap vs low compares Floor &amp;
Decor against the cheapest comparable competitor offer. The basket index is volume-weighted
spend, so it answers "what would this basket cost" rather than averaging unit prices.
Only offers matched at <em>close</em> tier or better and in stock at collection are counted.
</footer>
</div>
<script>
const ROWS = {payload};
const pct = v => v == null ? '-' : (v*100).toFixed(1).replace(/^(?!-)/,'+') + '%';
const money = v => v == null ? '-' : '$' + v.toFixed(2);
const cls = v => v == null ? '' : (v > 0 ? 'pos' : 'neg');
const TIER_RANK = {{exact:0, equivalent:1, close:2, weak:3, none:4}};
// Open on the widest losses: the rows that need a decision.
let sortKey = 'gap', sortDir = -1;

function visible() {{
  const q = document.getElementById('q').value.toLowerCase();
  const cat = document.getElementById('cat').value;
  const out = document.getElementById('out').value;
  const tier = document.getElementById('tier').value;
  const maxRank = tier ? TIER_RANK[tier] : 99;
  return ROWS.filter(r => {{
    if (cat && r.category !== cat) return false;
    if (out && r.outcome !== out) return false;
    if (tier) {{
      const best = Math.min(TIER_RANK[r.hdTier] ?? 99, TIER_RANK[r.lwTier] ?? 99);
      if (best > maxRank) return false;
    }}
    if (q) {{
      const hay = (r.id + ' ' + r.desc + ' ' + r.category + ' ' + r.sub + ' ' +
                   r.fndBrand + ' ' + r.hdBrand + ' ' + r.lwBrand).toLowerCase();
      if (!hay.includes(q)) return false;
    }}
    return true;
  }});
}}

function render() {{
  const rows = visible().sort((a, b) => {{
    const x = a[sortKey], y = b[sortKey];
    if (x == null) return 1;
    if (y == null) return -1;
    return (typeof x === 'string' ? x.localeCompare(y) : x - y) * sortDir;
  }});
  document.querySelector('#grid tbody').innerHTML = rows.map(r => `
    <tr>
      <td>${{r.id}}</td><td>${{r.category}}</td>
      <td class="desc">${{r.desc}}</td>
      <td class="num">${{money(r.fnd)}}<span class="flag">${{r.basis}}</span></td>
      <td class="num">${{money(r.hd)}}${{r.hdPromo ? ' <span class="flag">promo</span>' : ''}}</td>
      <td class="num ${{cls(r.hdDelta)}}">${{pct(r.hdDelta)}}</td>
      <td class="num">${{money(r.lw)}}${{r.lwPromo ? ' <span class="flag">promo</span>' : ''}}</td>
      <td class="num ${{cls(r.lwDelta)}}">${{pct(r.lwDelta)}}</td>
      <td class="num ${{cls(r.gap)}}">${{pct(r.gap)}}</td>
      <td>${{r.cheapest}}</td>
      <td><span class="pill ${{r.hdTier}}">${{r.hdTier}}</span> <span class="pill ${{r.lwTier}}">${{r.lwTier}}</span></td>
      <td><span class="flag">${{r.flags.join(', ') || '-'}}</span></td>
    </tr>`).join('');
  document.getElementById('count').textContent =
    rows.length + ' of ' + ROWS.length + ' SKU groups';
}}

document.querySelectorAll('#grid th').forEach(th => th.addEventListener('click', () => {{
  const k = th.dataset.k;
  sortDir = (k === sortKey) ? -sortDir : 1;
  sortKey = k;
  render();
}}));
['q','cat','out','tier'].forEach(id =>
  document.getElementById(id).addEventListener('input', render));
render();
</script></body></html>"""
