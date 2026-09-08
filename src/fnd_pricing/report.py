"""Self-contained HTML report.

No external assets, no CDN, no build step - the output file can be mailed to a
merchant or opened from a share drive and it still works.
"""

from __future__ import annotations

import html
import json
from typing import Dict, List, Optional

from . import BASE_RETAILER, RETAILER_LABELS, RETAILER_SHORT, RETAILERS, code
from .charts import compact_money, diverging_bars, magnitude_bars
from .compare import GroupComparison, Rollup, build_rollup, rollup_by_category
from .spend import MARKET_LOW, expense_by_category, total_expense

COMPETITORS = [r for r in RETAILERS if r != BASE_RETAILER]
COMPETITOR_LABELS = [(r, RETAILER_SHORT.get(r, r)) for r in COMPETITORS]


def _pct(value: Optional[float], digits: int = 1) -> str:
    return "-" if value is None else f"{value * 100:+.{digits}f}%"


def _money(value: Optional[float]) -> str:
    return "-" if value is None else f"${value:,.2f}"


def _competitor_headers(prefix: str) -> str:
    return "".join(
        f'<th class="num">{prefix}{html.escape(label)}</th>'
        for _, label in COMPETITOR_LABELS
    )


def _detail_headers() -> str:
    """A price column and a delta column for each competitor."""
    return "".join(
        f'<th class="num" data-k="{code(retailer)}">{html.escape(label)}</th>'
        f'<th class="num" data-k="{code(retailer)}Delta">&Delta;</th>'
        for retailer, label in COMPETITOR_LABELS
    )


def _index(value: Optional[float]) -> str:
    return "-" if value is None else f"{value:.3f}"


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
            key = code(retailer)
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
    ] + [
        index_tile(basket(retailer), f"Basket index vs {label}",
                   "volume-weighted spend ratio")
        for retailer, label in COMPETITOR_LABELS
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
            + "".join(
                f"<td class='num'>{_pct(r.per_retailer_gap.get(retailer))}</td>"
                for retailer in COMPETITORS
            )
            + "</tr>"
        )
    return "\n".join(body)


def _expense_section(comparisons: List[GroupComparison]) -> str:
    """Where the money sits, and how much of it is priced off-market."""
    rows = expense_by_category(comparisons)
    total = total_expense(comparisons)
    if not rows or total.annual_spend <= 0:
        return ""

    spend_rows, delta_rows = [], []
    for row in rows:
        basket = row.baskets[MARKET_LOW]
        share = row.share_of(total.annual_spend) or 0
        index = basket.index
        spend_rows.append((
            row.category, row.annual_spend,
            f"{row.category} - ${row.annual_spend:,.0f} a year, "
            f"{share * 100:.1f}% of total expense, {row.priced_skus} SKUs",
        ))
        delta_rows.append((
            row.category, basket.delta,
            f"{row.category} - {compact_money(abs(basket.delta))} "
            f"{'above' if basket.delta > 0 else 'below'} market low on "
            f"{basket.matched_skus} matched SKUs"
            + (f", index {index:.3f}" if index else ""),
        ))

    body = []
    for row in rows:
        basket = row.baskets[MARKET_LOW]
        index = basket.index
        body.append(
            f"<tr><td>{html.escape(row.category)}</td>"
            f"<td class='num'>{row.priced_skus}</td>"
            f"<td class='num'>{row.annual_spend:,.0f}</td>"
            f"<td class='num'>{(row.share_of(total.annual_spend) or 0) * 100:.1f}%</td>"
            f"<td class='num {'pos' if (index or 1) > 1 else 'neg'}'>{_index(index)}</td>"
            f"<td class='num {'pos' if basket.delta > 0 else 'neg'}'>{basket.delta:,.0f}</td>"
            + "".join(
                f"<td class='num'>{_index(row.baskets[retailer].index)}</td>"
                for retailer in COMPETITORS
            )
            + f"<td class='num'>{(row.benchmark_coverage or 0) * 100:.0f}%</td></tr>"
        )

    market = total.baskets[MARKET_LOW]
    body.append(
        f"<tr class='total'><td>All categories</td>"
        f"<td class='num'>{total.priced_skus}</td>"
        f"<td class='num'>{total.annual_spend:,.0f}</td><td class='num'>100.0%</td>"
        f"<td class='num'>{_index(market.index)}</td>"
        f"<td class='num'>{market.delta:,.0f}</td>"
        + "".join(
            f"<td class='num'>{_index(total.baskets[retailer].index)}</td>"
            for retailer in COMPETITORS
        )
        + f"<td class='num'>{(total.benchmark_coverage or 0) * 100:.0f}%</td></tr>"
    )

    exposure = sum(r.baskets[MARKET_LOW].delta for r in rows
                   if r.baskets[MARKET_LOW].delta > 0)
    top = rows[0]

    return f"""
<h2>Expense by category</h2>
<div class="tiles">
  <div class="tile"><div class="tile-value">{compact_money(total.annual_spend)}</div>
    <div class="tile-label">Annual expense at Floor &amp; Decor prices</div>
    <div class="tile-sub">{total.priced_skus} SKUs carrying a price and a volume</div></div>
  <div class="tile"><div class="tile-value">{(top.share_of(total.annual_spend) or 0) * 100:.0f}%</div>
    <div class="tile-label">Concentrated in {html.escape(top.category)}</div>
    <div class="tile-sub">{compact_money(top.annual_spend)} of {compact_money(total.annual_spend)}</div></div>
  <div class="tile bad"><div class="tile-value">{compact_money(exposure)}</div>
    <div class="tile-label">Annual spend priced above market low</div>
    <div class="tile-sub">across {sum(1 for r in rows if r.baskets[MARKET_LOW].delta > 0)} categories</div></div>
  <div class="tile good"><div class="tile-value">{compact_money(-market.delta)}</div>
    <div class="tile-label">Net annual advantage vs market low</div>
    <div class="tile-sub">on the {market.matched_skus} SKUs with a comparable offer</div></div>
</div>

<h3>Annual expense</h3>
<div class="panel chart-panel viz-root">{magnitude_bars(spend_rows, "Annual expense")}</div>

<h3>Dollars above or below the market low</h3>
<p class="note"><span class="key under"></span>Below market low (advantage)
<span class="key over"></span>Above market low (exposure)</p>
<div class="panel chart-panel viz-root">{diverging_bars(delta_rows, "Annual dollars vs market low")}</div>

<div class="panel"><table>
<thead><tr><th>Category</th><th class="num">SKUs</th><th class="num">Annual expense $</th>
<th class="num">Share</th><th class="num">Index vs low</th><th class="num">$ vs low</th>
{_competitor_headers("Index vs ")}
<th class="num">Benchmarked</th></tr></thead>
<tbody>{"".join(body)}</tbody></table></div>
<p class="note">Each index divides Floor &amp; Decor spend by that retailer's spend over
<em>only the SKUs that retailer covers</em>, so an index is comparable to 1.0 but not to
the other indexes in its row - they rest on different baskets. Benchmarked is the share of
category expense on SKUs where some competitor offer was comparable enough to use.</p>
"""


def render_html(comparisons: List[GroupComparison], collected_on: str = "") -> str:
    overall = build_rollup("All categories", comparisons)
    categories = rollup_by_category(comparisons)
    payload = json.dumps(_rows_payload(comparisons))
    codes = json.dumps([code(r) for r in COMPETITORS])
    first_tier_key = code(COMPETITORS[0]) + "Tier"
    cat_options = "\n".join(
        f'<option value="{html.escape(c.label)}">{html.escape(c.label)}</option>'
        for c in categories
    )
    versus = " vs ".join(["Floor &amp; Decor"] + [l for _, l in COMPETITOR_LABELS])
    subtitle = (
        f"{len(comparisons)} SKU groups &middot; {versus}"
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
  --mark:#2a78d6; --mark-over:#e34948; --grid:#e2e5ea; --zero:#aab2be;
}}
@media (prefers-color-scheme: dark) {{
  :root {{ --bg:#14171a; --panel:#1c2126; --ink:#e8eaed; --muted:#9aa4b0;
           --line:#2b3138; --good:#4ade80; --bad:#f87171; --accent:#7aa7dd;
           --mark:#3987e5; --mark-over:#e66767; --grid:#2b3138; --zero:#4a525c; }}
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
h3 {{ font-size:13px; font-weight:600; margin:26px 0 8px; }}
.note {{ color:var(--muted); font-size:12px; margin:10px 2px 0; max-width:960px; }}
.chart-panel {{ padding:18px 16px 6px; overflow-x:auto; }}
.chart {{ width:100%; min-width:640px; height:auto; display:block; }}
.chart .grid {{ stroke:var(--grid); stroke-width:1; }}
.chart .zero {{ stroke:var(--zero); stroke-width:1; }}
.chart .label {{ fill:var(--muted); font-size:12px; }}
.chart .tick {{ fill:var(--muted); font-size:11px; font-variant-numeric:tabular-nums; }}
.chart .value {{ fill:var(--ink); font-size:12px; font-variant-numeric:tabular-nums; }}
.chart .mark {{ fill:var(--mark); }}
.chart .mark.over {{ fill:var(--mark-over); }}
.chart .hit {{ fill:transparent; }}
.chart .row:hover .hit, .chart .row:focus .hit {{ fill:rgba(127,127,127,.09); }}
.chart .row {{ outline:none; }}
.chart .row:focus .label {{ fill:var(--ink); }}
.key {{ display:inline-block; width:10px; height:10px; border-radius:2px;
  margin:0 6px 0 16px; vertical-align:middle; }}
.key:first-child {{ margin-left:0; }}
.key.under {{ background:var(--mark); }} .key.over {{ background:var(--mark-over); }}
tr.total td {{ font-weight:650; border-top:2px solid var(--line); }}
#tip {{ position:fixed; z-index:20; display:none; max-width:330px; padding:8px 11px;
  background:var(--panel); color:var(--ink); border:1px solid var(--line);
  border-radius:6px; font-size:12px; line-height:1.45; pointer-events:none;
  box-shadow:0 4px 14px rgba(0,0,0,.16); }}
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
{_competitor_headers("vs ")}</tr></thead>
<tbody>{_category_table(categories)}</tbody></table></div>

{_expense_section(comparisons)}

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
{_detail_headers()}
<th class="num" data-k="gap">Gap vs low</th><th data-k="cheapest">Cheapest</th>
<th data-k="{first_tier_key}">Match</th><th data-k="flags">Flags</th>
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
const CODES = {codes};   // competitor short codes, in registry order
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
      const best = Math.min(...CODES.map(c => TIER_RANK[r[c + 'Tier']] ?? 99));
      if (best > maxRank) return false;
    }}
    if (q) {{
      const hay = [r.id, r.desc, r.category, r.sub, r.fndBrand]
        .concat(CODES.map(c => r[c + 'Brand'] || '')).join(' ').toLowerCase();
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
      ${{CODES.map(c => `
        <td class="num">${{money(r[c])}}${{r[c + 'Promo'] ? ' <span class="flag">promo</span>' : ''}}</td>
        <td class="num ${{cls(r[c + 'Delta'])}}">${{pct(r[c + 'Delta'])}}</td>`).join('')}}
      <td class="num ${{cls(r.gap)}}">${{pct(r.gap)}}</td>
      <td>${{r.cheapest}}</td>
      <td>${{CODES.map(c => `<span class="pill ${{r[c + 'Tier']}}" title="${{r[c + 'Note'] || ''}}">${{r[c + 'Tier']}}</span>`).join(' ')}}</td>
      <td><span class="flag">${{r.flags.join(', ') || '-'}}</span></td>
    </tr>`).join('');
  document.getElementById('count').textContent =
    rows.length + ' of ' + ROWS.length + ' SKU groups';
}}

const tip = Object.assign(document.createElement('div'), {{id:'tip'}});
document.body.appendChild(tip);
const showTip = (row, x, y) => {{
  tip.textContent = row.dataset.tip;
  tip.style.display = 'block';
  tip.style.left = Math.min(x + 16, window.innerWidth - 350) + 'px';
  tip.style.top = Math.min(y + 16, window.innerHeight - 90) + 'px';
}};
const hideTip = () => {{ tip.style.display = 'none'; }};
document.querySelectorAll('.chart .row').forEach(row => {{
  row.addEventListener('mousemove', e => showTip(row, e.clientX, e.clientY));
  row.addEventListener('mouseleave', hideTip);
  // Keyboard reaches the same value the pointer does.
  row.addEventListener('focus', () => {{
    const box = row.getBoundingClientRect();
    showTip(row, box.left + 40, box.top);
  }});
  row.addEventListener('blur', hideTip);
}});

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
