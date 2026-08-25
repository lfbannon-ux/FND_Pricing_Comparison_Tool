"""Inline SVG charts for the HTML report.

Server-rendered, no chart library, no external requests. Colours are taken from
CSS custom properties so light and dark mode are each stepped deliberately
rather than one being an automatic flip of the other.
"""

from __future__ import annotations

import html
import math
from typing import List, Sequence, Tuple

VIEW_W = 940
ROW_H = 30
BAR_H = 14          # thin marks: well under the 24px cap
RADIUS = 4          # rounded data-end, square at the baseline
LABEL_W = 210
AXIS_H = 30


def compact_money(value: float) -> str:
    sign = "-" if value < 0 else ""
    amount = abs(value)
    if amount >= 1_000_000:
        return f"{sign}${amount / 1_000_000:,.1f}M"
    if amount >= 10_000:
        return f"{sign}${amount / 1_000:,.0f}k"
    if amount >= 1_000:
        return f"{sign}${amount / 1_000:,.1f}k"
    return f"{sign}${amount:,.0f}"


def _nice_axis(value: float, target_ticks: int = 4) -> Tuple[float, float]:
    """Pick a clean tick step, then the axis maximum that step implies.

    Choosing the step first is what keeps both the ticks readable and the plot
    full: rounding the maximum up on its own turns a $14.5M bar into a $20M
    axis and throws away a third of the width.
    """
    if value <= 0:
        return 1.0, 1.0
    raw = value / target_ticks
    magnitude = 10.0 ** math.floor(math.log10(raw))
    step = magnitude * 10
    for multiple in (1, 2, 2.5, 5, 10):
        if magnitude * multiple >= raw:
            step = magnitude * multiple
            break
    return math.ceil(value / step) * step, step


def _bar_path(x0: float, x1: float, y: float, height: float) -> str:
    """A bar rounded only at the data-end, square where it meets the baseline."""
    width = abs(x1 - x0)
    radius = min(RADIUS, width)
    if width < 0.5:
        return ""
    if x1 >= x0:  # grows right
        return (f"M{x0:.1f},{y:.1f} H{x1 - radius:.1f} "
                f"Q{x1:.1f},{y:.1f} {x1:.1f},{y + radius:.1f} "
                f"V{y + height - radius:.1f} "
                f"Q{x1:.1f},{y + height:.1f} {x1 - radius:.1f},{y + height:.1f} "
                f"H{x0:.1f} Z")
    return (f"M{x0:.1f},{y:.1f} H{x1 + radius:.1f} "
            f"Q{x1:.1f},{y:.1f} {x1:.1f},{y + radius:.1f} "
            f"V{y + height - radius:.1f} "
            f"Q{x1:.1f},{y + height:.1f} {x1 + radius:.1f},{y + height:.1f} "
            f"H{x0:.1f} Z")


def _ticks(maximum: float, step: float) -> List[float]:
    count = int(round(maximum / step))
    return [step * i for i in range(count + 1)]


def magnitude_bars(
    rows: Sequence[Tuple[str, float, str]], value_label: str
) -> str:
    """Ranked horizontal bars for a single measure. rows = (label, value, tip)."""
    if not rows:
        return ""
    plot_w = VIEW_W - LABEL_W - 90
    axis_max, axis_step = _nice_axis(max(v for _, v, _ in rows))
    height = len(rows) * ROW_H + AXIS_H

    parts = [
        f'<svg class="chart" viewBox="0 0 {VIEW_W} {height}" role="img" '
        f'aria-label="{html.escape(value_label)} by category">'
    ]

    for tick in _ticks(axis_max, axis_step):
        x = LABEL_W + plot_w * tick / axis_max
        parts.append(
            f'<line class="grid" x1="{x:.1f}" y1="0" x2="{x:.1f}" '
            f'y2="{len(rows) * ROW_H:.0f}"/>'
        )
        parts.append(
            f'<text class="tick" x="{x:.1f}" y="{len(rows) * ROW_H + 18:.0f}" '
            f'text-anchor="middle">{compact_money(tick)}</text>'
        )

    for index, (label, value, tip) in enumerate(rows):
        y = index * ROW_H
        bar_y = y + (ROW_H - BAR_H) / 2
        x1 = LABEL_W + plot_w * value / axis_max
        parts.append(f'<g class="row" tabindex="0" data-tip="{html.escape(tip)}">')
        parts.append(
            f'<rect class="hit" x="0" y="{y:.0f}" width="{VIEW_W}" height="{ROW_H}"/>'
        )
        parts.append(
            f'<text class="label" x="{LABEL_W - 12}" y="{y + ROW_H / 2 + 4:.1f}" '
            f'text-anchor="end">{html.escape(label)}</text>'
        )
        parts.append(f'<path class="mark" d="{_bar_path(LABEL_W, x1, bar_y, BAR_H)}"/>')
        parts.append(
            f'<text class="value" x="{x1 + 8:.1f}" y="{y + ROW_H / 2 + 4:.1f}">'
            f'{compact_money(value)}</text>'
        )
        parts.append("</g>")

    parts.append("</svg>")
    return "".join(parts)


def diverging_bars(
    rows: Sequence[Tuple[str, float, str]], value_label: str
) -> str:
    """Bars either side of a zero baseline. rows = (label, value, tip)."""
    if not rows:
        return ""
    plot_w = VIEW_W - LABEL_W - 90
    extent, extent_step = _nice_axis(max(abs(v) for _, v, _ in rows) or 1.0, 2)
    zero_x = LABEL_W + plot_w / 2
    half = plot_w / 2
    height = len(rows) * ROW_H + AXIS_H

    parts = [
        f'<svg class="chart" viewBox="0 0 {VIEW_W} {height}" role="img" '
        f'aria-label="{html.escape(value_label)} by category">'
    ]

    arm = _ticks(extent, extent_step)
    for tick in [-t for t in reversed(arm[1:])] + arm:
        x = zero_x + half * tick / extent
        css = "zero" if tick == 0 else "grid"
        parts.append(
            f'<line class="{css}" x1="{x:.1f}" y1="0" x2="{x:.1f}" '
            f'y2="{len(rows) * ROW_H:.0f}"/>'
        )
        parts.append(
            f'<text class="tick" x="{x:.1f}" y="{len(rows) * ROW_H + 18:.0f}" '
            f'text-anchor="middle">{compact_money(tick)}</text>'
        )

    for index, (label, value, tip) in enumerate(rows):
        y = index * ROW_H
        bar_y = y + (ROW_H - BAR_H) / 2
        x1 = zero_x + half * value / extent
        tone = "over" if value > 0 else "under"
        anchor = "start" if value > 0 else "end"
        offset = 8 if value > 0 else -8
        parts.append(f'<g class="row" tabindex="0" data-tip="{html.escape(tip)}">')
        parts.append(
            f'<rect class="hit" x="0" y="{y:.0f}" width="{VIEW_W}" height="{ROW_H}"/>'
        )
        parts.append(
            f'<text class="label" x="{LABEL_W - 12}" y="{y + ROW_H / 2 + 4:.1f}" '
            f'text-anchor="end">{html.escape(label)}</text>'
        )
        parts.append(
            f'<path class="mark {tone}" d="{_bar_path(zero_x, x1, bar_y, BAR_H)}"/>'
        )
        parts.append(
            f'<text class="value" x="{x1 + offset:.1f}" y="{y + ROW_H / 2 + 4:.1f}" '
            f'text-anchor="{anchor}">{compact_money(value)}</text>'
        )
        parts.append("</g>")

    parts.append("</svg>")
    return "".join(parts)
