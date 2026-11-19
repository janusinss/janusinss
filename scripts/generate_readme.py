#!/usr/bin/env python3
"""
Vibrant Multi-Reference GitHub Profile README SVG generator for Janus Dominic (@janusinss).
Blends:
  - screen-gd & ripgrim: luminous colored dithered wave header + split bento telemetry grid
  - Canitas (Sequela02): Bayer-dithered commit-cadence project cards (forensic-dgp & skill v2)
  - pursurer-inspired full-width ASCII koi pond visual banner (assets/banner-koi.png)
  - Kevin-Liu-01: crisp categorized tech stack with color-coded technology badges
  - Official Lucide (ISC) & Simple Icons (CC0) SVGs for link icons

Zero external dependencies (Python 3 standard library only).
"""

from __future__ import annotations

import argparse
import datetime as dt
import json
import math
import os
import urllib.request
from pathlib import Path
from typing import Any
from xml.sax.saxutils import escape

BAYER_4X4 = [
    [0 / 16, 8 / 16, 2 / 16, 10 / 16],
    [12 / 16, 4 / 16, 14 / 16, 6 / 16],
    [3 / 16, 11 / 16, 1 / 16, 9 / 16],
    [15 / 16, 7 / 16, 13 / 16, 5 / 16],
]

BG_CARD = "#0a0d12"
BG_PANEL = "#080b10"
BORDER = "#242b35"
HAIRLINE = "#1c222b"
TEXT_PRIMARY = "#f0f6fc"
TEXT_BODY = "#c9d1d9"
TEXT_MUTED = "#7d8590"
TEXT_DIM = "#545d68"
DOT_BG = "#161b24"

FONT_SANS = "-apple-system, BlinkMacSystemFont, 'Segoe UI', Helvetica, Arial, sans-serif"
FONT_MONO = "ui-monospace, SFMono-Regular, 'SF Mono', Menlo, Consolas, 'Liberation Mono', monospace"

THEMES: dict[str, dict[str, str]] = {
    "cyan": {
        "dim": "#0c4a6e",
        "mid": "#0284c7",
        "high": "#38bdf8",
        "peak": "#e0f2fe",
        "spark": "#facc15",
        "accent": "#38bdf8",
        "glow": "#0ea5e9",
    },
    "amber": {
        "dim": "#713f12",
        "mid": "#d97706",
        "high": "#facc15",
        "peak": "#fef9c3",
        "spark": "#fb923c",
        "accent": "#facc15",
        "glow": "#eab308",
    },
}


def wrap_text(text: str, max_chars: int, max_lines: int = 2) -> list[str]:
    words = text.split()
    lines: list[str] = []
    current = ""
    i = 0
    while i < len(words):
        word = words[i]
        candidate = f"{current} {word}".strip()
        if len(candidate) <= max_chars:
            current = candidate
            i += 1
        else:
            if not current:
                current = word[: max_chars - 3] + "..."
                i += 1
            lines.append(current)
            current = ""
            if len(lines) == max_lines:
                break
    if current and len(lines) < max_lines:
        lines.append(current)
    if i < len(words) and lines:
        tail = lines[-1]
        if len(tail) > max_chars - 3:
            tail = tail[: max_chars - 3].rstrip()
        lines[-1] = tail.rstrip(".,;:") + "..."
    return lines


def hero_dither_color(intensity: float, gx: int, gy: int, cols: int) -> str | None:
    threshold = BAYER_4X4[gy % 4][gx % 4]
    if intensity <= 0.04:
        if (gx % 3 == 0) and (gy % 3 == 0):
            return DOT_BG
        return None
    if intensity < threshold:
        if (gx + gy) % 4 == 0 and intensity > 0.14:
            return DOT_BG
        return None

    x_norm = gx / max(cols - 1, 1)
    h = ((gx * 73856093) ^ (gy * 19349663)) & 0xFF

    warm_zone = x_norm > 0.62 and (intensity > 0.58 or (x_norm > 0.78 and intensity > 0.36))
    if warm_zone:
        if intensity > 0.84:
            return "#fef9c3"
        if intensity > 0.58:
            return "#facc15"
        return "#d97706"

    if intensity > 0.84:
        return "#f0f9ff"
    if intensity > 0.60:
        return "#facc15" if h < 18 else "#38bdf8"
    if intensity > 0.34:
        return "#0284c7"
    return "#1e3a8a"


def card_dither_color(intensity: float, gx: int, gy: int, theme: dict[str, str], seed: int) -> str | None:
    threshold = BAYER_4X4[gy % 4][gx % 4]
    if intensity <= 0.04:
        if (gx % 3 == 0) and (gy % 3 == 0):
            return DOT_BG
        return None
    if intensity < threshold:
        if (gx + gy) % 4 == 0 and intensity > 0.14:
            return DOT_BG
        return None
    h = ((gx * 73856093) ^ (gy * 19349663) ^ (seed * 83492791)) & 0xFF
    if intensity > 0.82:
        return theme["spark"] if h < 20 else theme["peak"]
    if intensity > 0.54:
        return theme["high"]
    if intensity > 0.28:
        return theme["mid"]
    return theme["dim"]


def build_hero_svg(
    profile: dict[str, Any],
    wave_series: list[float],
    years: list[str],
    left_meta: str,
    right_meta: str,
    active_dot: bool = True,
) -> str:
    w, h = 860, 326
    topbar_h = 34
    banner_y = topbar_h
    banner_h = 136
    body_y = banner_y + banner_h
    split_x = 532

    cell = 3.8
    pad_x = 14
    cols = int((w - pad_x * 2) // cell)
    rows = 24
    grid_y0 = banner_y + 22

    if not wave_series:
        wave_series = [0.3] * cols
    n = len(wave_series)
    resampled: list[float] = []
    for c in range(cols):
        idx = c * (n - 1) / max(cols - 1, 1)
        lo = int(math.floor(idx))
        hi = min(lo + 1, n - 1)
        frac = idx - lo
        val = wave_series[lo] * (1 - frac) + wave_series[hi] * frac
        resampled.append(max(0.0, min(1.0, val)))

    dots_svg: list[str] = []
    mid_row = (rows - 1) / 2.0
    for gx in range(cols):
        amp = resampled[gx]
        half_span = 1.4 + amp * (rows * 0.45)
        for gy in range(rows):
            dist = abs(gy - mid_row)
            if dist <= half_span:
                norm = 1.0 - (dist / max(half_span, 0.01))
                spine = 0.28 if dist < 1.15 else 0.0
                intensity = min(1.0, (norm ** 1.1) * (0.42 + 0.58 * amp) + spine)
            else:
                overflow = dist - half_span
                intensity = max(0.0, 0.18 - overflow * 0.05) * amp
            color = hero_dither_color(intensity, gx, gy, cols)
            if color:
                px = round(pad_x + gx * cell, 1)
                py = round(grid_y0 + gy * cell, 1)
                dots_svg.append(f'<rect x="{px}" y="{py}" width="2.4" height="2.4" fill="{color}"/>')

    year_svg: list[str] = []
    if years:
        step = (w - 140) / max(len(years), 1)
        for i, yr in enumerate(years):
            yx = int(70 + i * step)
            year_svg.append(
                f'<text x="{yx}" y="{banner_y + 15}" fill="{TEXT_DIM}" font-family="{FONT_MONO}" '
                f'font-size="10">{escape(str(yr))}</text>'
            )

    dot_color = "#4ade80" if active_dot else TEXT_DIM
    name = escape(profile.get("hero_title") or profile["name"])
    username = escape(profile["username"])
    handle = escape(profile["handle"])
    status_badge = escape(profile.get("status_badge", "BUILDING"))
    headline = escape(profile["headline"])
    now_text = escape(profile.get("now", "building web apps & forensic AI"))
    working_at = escape(profile.get("working_at", "MIHA Technologies"))
    focus = escape(profile.get("focus", "full-stack & AI"))
    status = escape(profile.get("status", "building"))
    location = escape(profile.get("location", "Zamboanga, PH"))

    mid_y = body_y + (h - body_y) // 2
    right_mid_x = split_x + (w - split_x) // 2

    return f'''<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" viewBox="0 0 {w} {h}" role="img" aria-label="{name} GitHub profile banner">
  <defs>
    <radialGradient id="cyanGlow" cx="34%" cy="50%" r="48%">
      <stop offset="0%" stop-color="#0ea5e9" stop-opacity="0.26"/>
      <stop offset="100%" stop-color="#0ea5e9" stop-opacity="0"/>
    </radialGradient>
    <radialGradient id="goldGlow" cx="80%" cy="50%" r="36%">
      <stop offset="0%" stop-color="#eab308" stop-opacity="0.22"/>
      <stop offset="100%" stop-color="#eab308" stop-opacity="0"/>
    </radialGradient>
  </defs>
  <rect x="0.5" y="0.5" width="{w - 1}" height="{h - 1}" rx="6" fill="{BG_CARD}" stroke="{BORDER}"/>
  <text x="18" y="21" fill="{TEXT_PRIMARY}" font-family="{FONT_MONO}" font-size="11.5" font-weight="700">{username}</text>
  <rect x="94" y="13" width="3" height="3" fill="#38bdf8"/>
  <rect x="98" y="13" width="3" height="3" fill="#0284c7"/>
  <rect x="94" y="17" width="3" height="3" fill="#facc15"/>
  <rect x="98" y="17" width="3" height="3" fill="#38bdf8"/>
  <text x="108" y="21" fill="{TEXT_BODY}" font-family="{FONT_MONO}" font-size="10.5" letter-spacing="1.2">{status_badge}</text>
  <text x="{w - 18}" y="21" text-anchor="end" fill="{TEXT_MUTED}" font-family="{FONT_MONO}" font-size="11">github.com/{username}</text>
  <line x1="1" y1="{topbar_h}" x2="{w - 1}" y2="{topbar_h}" stroke="{HAIRLINE}"/>

  <rect x="1" y="{banner_y + 1}" width="{w - 2}" height="{banner_h - 1}" fill="{BG_PANEL}"/>
  <rect x="1" y="{banner_y + 1}" width="{w - 2}" height="{banner_h - 1}" fill="url(#cyanGlow)"/>
  <rect x="1" y="{banner_y + 1}" width="{w - 2}" height="{banner_h - 1}" fill="url(#goldGlow)"/>
  {"".join(year_svg)}
  <g>
    {"".join(dots_svg)}
  </g>
  <text x="18" y="{body_y - 9}" fill="{TEXT_MUTED}" font-family="{FONT_MONO}" font-size="10.5">{escape(left_meta)}</text>
  <text x="{w - 28}" y="{body_y - 9}" text-anchor="end" fill="{TEXT_MUTED}" font-family="{FONT_MONO}" font-size="10.5">{escape(right_meta)}</text>
  <rect x="{w - 21}" y="{body_y - 15}" width="5" height="5" fill="{dot_color}"/>
  <line x1="1" y1="{body_y}" x2="{w - 1}" y2="{body_y}" stroke="{HAIRLINE}"/>

  <text x="24" y="{body_y + 46}" fill="{TEXT_PRIMARY}" font-family="{FONT_SANS}" font-size="36" font-weight="700" letter-spacing="-0.9">{name}</text>
  <text x="24" y="{body_y + 70}" fill="{TEXT_BODY}" font-family="{FONT_SANS}" font-size="13.5">{headline}</text>

  <text x="24" y="{body_y + 106}" fill="{TEXT_DIM}" font-family="{FONT_MONO}" font-size="10.5" letter-spacing="0.8">NOW</text>
  <text x="92" y="{body_y + 106}" fill="{TEXT_PRIMARY}" font-family="{FONT_MONO}" font-size="11.5">{now_text}</text>
  <text x="24" y="{body_y + 128}" fill="{TEXT_DIM}" font-family="{FONT_MONO}" font-size="10.5" letter-spacing="0.8">HANDLE</text>
  <text x="92" y="{body_y + 128}" fill="#38bdf8" font-family="{FONT_MONO}" font-size="11.5" font-weight="600">{handle}</text>

  <line x1="{split_x}" y1="{body_y}" x2="{split_x}" y2="{h - 1}" stroke="{HAIRLINE}"/>
  <line x1="{right_mid_x}" y1="{body_y}" x2="{right_mid_x}" y2="{h - 1}" stroke="{HAIRLINE}"/>
  <line x1="{split_x}" y1="{mid_y}" x2="{w - 1}" y2="{mid_y}" stroke="{HAIRLINE}"/>

  <text x="{split_x + 18}" y="{body_y + 26}" fill="{TEXT_DIM}" font-family="{FONT_MONO}" font-size="9.5" letter-spacing="0.9">WORKING AT</text>
  <text x="{split_x + 18}" y="{body_y + 52}" fill="{TEXT_PRIMARY}" font-family="{FONT_MONO}" font-size="12.5" font-weight="600">{working_at}</text>

  <text x="{right_mid_x + 18}" y="{body_y + 26}" fill="{TEXT_DIM}" font-family="{FONT_MONO}" font-size="9.5" letter-spacing="0.9">FOCUS</text>
  <text x="{right_mid_x + 18}" y="{body_y + 52}" fill="#facc15" font-family="{FONT_MONO}" font-size="12.5" font-weight="600">{focus}</text>

  <text x="{split_x + 18}" y="{mid_y + 26}" fill="{TEXT_DIM}" font-family="{FONT_MONO}" font-size="9.5" letter-spacing="0.9">STATUS</text>
  <circle cx="{split_x + 22}" cy="{mid_y + 48}" r="3.5" fill="#4ade80"/>
  <text x="{split_x + 32}" y="{mid_y + 52}" fill="{TEXT_PRIMARY}" font-family="{FONT_MONO}" font-size="12.5" font-weight="600">{status}</text>

  <text x="{right_mid_x + 18}" y="{mid_y + 26}" fill="{TEXT_DIM}" font-family="{FONT_MONO}" font-size="9.5" letter-spacing="0.9">BASED IN</text>
  <text x="{right_mid_x + 18}" y="{mid_y + 52}" fill="{TEXT_PRIMARY}" font-family="{FONT_MONO}" font-size="12.5" font-weight="600">{location}</text>
</svg>
'''


def build_project_card_svg(
    repo_name: str,
    owner: str,
    description: str,
    language: str,
    lang_color: str,
    cta_label: str,
    chart_left: str,
    chart_right: str,
    curve: list[float],
    theme_name: str = "cyan",
    seed: int = 1,
) -> str:
    theme = THEMES.get(theme_name, THEMES["cyan"])
    w, h = 424, 254
    header_h = 36
    chart_h = 114
    chart_y0 = header_h
    body_y0 = header_h + chart_h
    footer_y0 = h - 38

    cell = 3.5
    pad_x = 12
    cols = int((w - pad_x * 2) // cell)
    rows = 23
    grid_y0 = chart_y0 + 30

    if not curve:
        curve = [0.2] * cols
    n = len(curve)
    resampled: list[float] = []
    for c in range(cols):
        idx = c * (n - 1) / max(cols - 1, 1)
        lo = int(math.floor(idx))
        hi = min(lo + 1, n - 1)
        frac = idx - lo
        val = curve[lo] * (1 - frac) + curve[hi] * frac
        resampled.append(max(0.0, min(1.0, val)))

    dots_svg: list[str] = []
    for gx in range(cols):
        amp = resampled[gx]
        height_rows = max(1.0, amp * (rows - 1.5))
        for gy in range(rows):
            from_bottom = (rows - 1) - gy
            if from_bottom <= height_rows:
                crest_dist = abs(height_rows - from_bottom)
                if crest_dist < 1.3:
                    intensity = min(1.0, 0.78 + 0.22 * amp)
                else:
                    ratio = from_bottom / max(height_rows, 0.1)
                    intensity = 0.26 + 0.60 * (ratio ** 0.7) * (0.5 + 0.5 * amp)
            else:
                intensity = 0.02
            color = card_dither_color(intensity, gx, gy, theme, seed=seed)
            if color:
                px = round(pad_x + gx * cell, 1)
                py = round(grid_y0 + gy * cell, 1)
                dots_svg.append(f'<rect x="{px}" y="{py}" width="2.1" height="2.1" fill="{color}"/>')

    desc_lines = wrap_text(description, max_chars=52, max_lines=2)
    desc_svg = []
    for i, line in enumerate(desc_lines):
        dy = body_y0 + 25 + i * 19
        desc_svg.append(
            f'<text x="16" y="{dy}" fill="{TEXT_BODY}" font-family="{FONT_SANS}" font-size="13">{escape(line)}</text>'
        )

    grad_id = f"cardGlow{seed}"

    return f'''<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" viewBox="0 0 {w} {h}" role="img" aria-label="{escape(repo_name)} project card">
  <defs>
    <radialGradient id="{grad_id}" cx="45%" cy="75%" r="60%">
      <stop offset="0%" stop-color="{theme["glow"]}" stop-opacity="0.22"/>
      <stop offset="100%" stop-color="{theme["glow"]}" stop-opacity="0"/>
    </radialGradient>
  </defs>
  <rect x="0.5" y="0.5" width="{w - 1}" height="{h - 1}" rx="6" fill="{BG_CARD}" stroke="{BORDER}"/>
  <text x="16" y="22.5" fill="{TEXT_PRIMARY}" font-family="{FONT_MONO}" font-size="12.5" font-weight="600">{escape(repo_name)}</text>
  <text x="{w - 16}" y="22.5" text-anchor="end" fill="{TEXT_MUTED}" font-family="{FONT_MONO}" font-size="11">{escape(owner)}</text>
  <line x1="1" y1="{header_h}" x2="{w - 1}" y2="{header_h}" stroke="{HAIRLINE}"/>

  <rect x="1" y="{chart_y0 + 1}" width="{w - 2}" height="{chart_h - 1}" fill="{BG_PANEL}"/>
  <rect x="1" y="{chart_y0 + 1}" width="{w - 2}" height="{chart_h - 1}" fill="url(#{grad_id})"/>
  <text x="16" y="{chart_y0 + 18}" fill="{TEXT_MUTED}" font-family="{FONT_MONO}" font-size="10">{escape(chart_left)}</text>
  <text x="{w - 16}" y="{chart_y0 + 18}" text-anchor="end" fill="{theme["accent"]}" font-family="{FONT_MONO}" font-size="10">{escape(chart_right)}</text>
  <g>
    {"".join(dots_svg)}
  </g>
  <line x1="1" y1="{body_y0}" x2="{w - 1}" y2="{body_y0}" stroke="{HAIRLINE}"/>

  {"".join(desc_svg)}

  <line x1="1" y1="{footer_y0}" x2="{w - 1}" y2="{footer_y0}" stroke="{HAIRLINE}"/>
  <circle cx="20" cy="{footer_y0 + 19}" r="3.5" fill="{lang_color}"/>
  <text x="30" y="{footer_y0 + 23}" fill="{TEXT_BODY}" font-family="{FONT_MONO}" font-size="11.5">{escape(language)}</text>
  <text x="{w - 16}" y="{footer_y0 + 23}" text-anchor="end" fill="{theme["accent"]}" font-family="{FONT_MONO}" font-size="11" font-weight="600" letter-spacing="0.5">{escape(cta_label)} &#8599;</text>
</svg>
'''


def build_stack_svg(stack_rows: list[dict[str, Any]]) -> str:
    w = 860
    row_h = 68
    h = row_h * len(stack_rows) + 2
    rows_svg: list[str] = []

    for idx, row in enumerate(stack_rows):
        y_top = 1 + idx * row_h
        if idx > 0:
            rows_svg.append(f'<line x1="1" y1="{y_top}" x2="{w - 1}" y2="{y_top}" stroke="{HAIRLINE}"/>')
        rows_svg.append(
            f'<text x="20" y="{y_top + 22}" fill="{TEXT_MUTED}" font-family="{FONT_MONO}" font-size="11.5" font-weight="600">{escape(row["category"])}</text>'
        )

        cx = 20
        cy = y_top + 32
        for item in row["items"]:
            name = item["name"]
            badge = item["badge"]
            bg = item["color"]
            fg = item["text"]
            chip_w = 34 + len(name) * 7.6 + 10
            rows_svg.append(
                f'<rect x="{cx:.1f}" y="{cy}" width="{chip_w:.1f}" height="24" rx="4" fill="#11161f" stroke="#222936"/>'
                f'<rect x="{cx + 4:.1f}" y="{cy + 4}" width="16" height="16" rx="3" fill="{bg}"/>'
                f'<text x="{cx + 12:.1f}" y="{cy + 15.5}" text-anchor="middle" fill="{fg}" font-family="{FONT_MONO}" font-size="8.5" font-weight="800">{escape(badge)}</text>'
                f'<text x="{cx + 26:.1f}" y="{cy + 16}" fill="{TEXT_PRIMARY}" font-family="{FONT_SANS}" font-size="12" font-weight="500">{escape(name)}</text>'
            )
            cx += chip_w + 10

    return f'''<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" viewBox="0 0 {w} {h}" role="img" aria-label="Tech Stack">
  <rect x="0.5" y="0.5" width="{w - 1}" height="{h - 1}" rx="6" fill="{BG_CARD}" stroke="{BORDER}"/>
  {"".join(rows_svg)}
</svg>
'''


def external_icon_svg(icon: str, color: str) -> str:
    """Official open-source SVG icons sourced verbatim from Lucide (ISC) & Simple Icons (CC0 1.0)."""
    if icon == "globe":
        return (
            f'<svg x="12" y="10.5" width="15" height="15" viewBox="0 0 24 24" fill="none" '
            f'stroke="{color}" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">'
            f'<circle cx="12" cy="12" r="10"/>'
            f'<path d="M12 2a14.5 14.5 0 0 0 0 20 14.5 14.5 0 0 0 0-20M2 12h20"/>'
            f'</svg>'
        )
    if icon == "building-2":
        return (
            f'<svg x="12" y="10.5" width="15" height="15" viewBox="0 0 24 24" fill="none" '
            f'stroke="{color}" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">'
            f'<path d="M6 22V4a2 2 0 0 1 2-2h8a2 2 0 0 1 2 2v18Zm0-10H4a2 2 0 0 0-2 2v6a2 2 0 0 0 2 2h2M18 9h2a2 2 0 0 1 2 2v9a2 2 0 0 1-2 2h-2M10 6h4m-4 4h4m-4 4h4m-4 4h4"/>'
            f'</svg>'
        )
    return (
        f'<svg x="12" y="10.5" width="15" height="15" viewBox="0 0 24 24">'
        f'<path fill="{color}" d="M12 .297c-6.63 0-12 5.373-12 12c0 5.303 3.438 9.8 8.205 11.385c.6.113.82-.258.82-.577c0-.285-.01-1.04-.015-2.04c-3.338.724-4.042-1.61-4.042-1.61C4.422 18.07 3.633 17.7 3.633 17.7c-1.087-.744.084-.729.084-.729c1.205.084 1.838 1.236 1.838 1.236c1.07 1.835 2.809 1.305 3.495.998c.108-.776.417-1.305.76-1.605c-2.665-.3-5.466-1.332-5.466-5.93c0-1.31.465-2.38 1.235-3.22c-.135-.303-.54-1.523.105-3.176c0 0 1.005-.322 3.3 1.23c.96-.267 1.98-.399 3-.405c1.02.006 2.04.138 3 .405c2.28-1.552 3.285-1.23 3.285-1.23c.645 1.653.24 2.873.12 3.176c.765.84 1.23 1.91 1.23 3.22c0 4.61-2.805 5.625-5.475 5.92c.42.36.81 1.096.81 2.22c0 1.606-.015 2.896-.015 3.286c0 .315.21.69.825.57C20.565 22.092 24 17.592 24 12.297c0-6.627-5.373-12-12-12"/>'
        f'</svg>'
    )


def build_pill_svg(label: str, icon: str = "globe", color: str = "#38bdf8", width: int = 232) -> str:
    h = 36
    return f'''<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{h}" viewBox="0 0 {width} {h}" role="img" aria-label="{escape(label)}">
  <rect x="0.5" y="0.5" width="{width - 1}" height="{h - 1}" rx="5" fill="{BG_CARD}" stroke="{BORDER}"/>
  {external_icon_svg(icon, color)}
  <text x="35" y="22.5" fill="{TEXT_PRIMARY}" font-family="{FONT_MONO}" font-size="11.5">{escape(label)}</text>
  <text x="{width - 15}" y="22" text-anchor="end" fill="{color}" font-family="{FONT_MONO}" font-size="12">&#8599;</text>
</svg>
'''


def synthetic_wave(seed: int, points: int = 96, mode: str = "hero") -> list[float]:
    vals: list[float] = []
    for i in range(points):
        t = i / max(points - 1, 1)
        if mode == "hero":
            base = 0.20 + 0.56 * (t ** 1.55)
            mod = 0.20 * math.sin(t * 21.0 + seed) + 0.14 * math.cos(t * 47.0 + seed * 2)
            spike = 0.26 if (i % 15 == (seed % 7)) else 0.0
            v = base + mod + spike
        elif seed == 1:
            v = 0.82 * math.exp(-t * 4.2) + 0.34 * math.exp(-((t - 0.55) / 0.16) ** 2) + 0.16 * (0.5 + 0.5 * math.sin(t * 28))
        else:
            v = 0.24 + 0.62 * math.exp(-((t - 0.62) / 0.11) ** 2) + 0.48 * math.exp(-((t - 0.80) / 0.09) ** 2) + 0.26 * math.exp(-((t - 0.28) / 0.12) ** 2) + 0.08 * math.sin(t * 35)
        vals.append(max(0.06, min(1.0, v)))
    return vals


def github_graphql(query: str, variables: dict[str, Any], token: str) -> dict[str, Any]:
    req = urllib.request.Request(
        "https://api.github.com/graphql",
        data=json.dumps({"query": query, "variables": variables}).encode("utf-8"),
        headers={
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
            "User-Agent": "janusinss-readme-generator",
        },
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=25) as resp:
        payload = json.loads(resp.read().decode("utf-8"))
        if "errors" in payload:
            raise RuntimeError(f"GraphQL error: {payload['errors']}")
        return payload["data"]


def fetch_live_github_data(username: str, token: str) -> dict[str, Any]:
    query = """
    query($login: String!) {
      user(login: $login) {
        contributionsCollection {
          contributionCalendar {
            totalContributions
            weeks {
              contributionDays {
                date
                contributionCount
              }
            }
          }
        }
        repositories(first: 20, ownerAffiliations: OWNER, isFork: false, orderBy: {field: PUSHED_AT, direction: DESC}) {
          nodes {
            name
            nameWithOwner
            url
            description
            stargazerCount
            pushedAt
            primaryLanguage { name }
            defaultBranchRef {
              target {
                ... on Commit {
                  history(first: 100) {
                    nodes { committedDate }
                  }
                }
              }
            }
          }
        }
      }
    }
    """
    return github_graphql(query, {"login": username}, token)["user"]


def format_pushed_date(iso_str: str | None) -> str:
    if not iso_str:
        return "recently"
    try:
        parsed = dt.datetime.fromisoformat(iso_str.replace("Z", "+00:00"))
        return f"pushed {parsed.strftime('%b %d').replace(' 0', ' ')}"
    except Exception:
        return "recently"


def generate_all(config_path: Path, out_dir: Path, mode: str) -> None:
    config = json.loads(config_path.read_text(encoding="utf-8"))
    assets_dir = out_dir / "assets"
    assets_dir.mkdir(parents=True, exist_ok=True)
    for old_f in ("project-3.svg", "project-4.svg", "creative-signal.svg", "creative-pulse.svg"):
        old_p = assets_dir / old_f
        if old_p.exists():
            old_p.unlink()

    token = os.environ.get("GITHUB_TOKEN", "").strip()
    use_live = mode == "live" and bool(token)

    profile = config["profile"]
    username = profile["username"]
    projects_cfg = config["featured_projects"]
    banner_cfg = config["banner_image"]
    stack_rows = config["stack"]
    links_cfg = config["links"]

    now_year = dt.date.today().year
    years = [str(now_year - 3), str(now_year - 2), str(now_year - 1), str(now_year)]
    hero_wave = synthetic_wave(seed=42, points=120, mode="hero")
    hero_left = "activity timeline · syncs daily via GitHub Actions"
    hero_right = "active in Zamboanga City"
    active_today = True

    live_repos_by_name: dict[str, dict[str, Any]] = {}
    if use_live:
        try:
            user_data = fetch_live_github_data(username, token)
            cal = user_data["contributionsCollection"]["contributionCalendar"]
            days = [d for w in cal["weeks"] for d in w["contributionDays"]]
            max_day = max((d["contributionCount"] for d in days), default=1) or 1
            hero_wave = [min(1.0, (d["contributionCount"] / max_day) ** 0.62) for d in days]
            total = cal["totalContributions"]
            hero_left = f"{total:,} contributions in the last year"
            last_day_count = days[-1]["contributionCount"] if days else 0
            active_today = last_day_count > 0
            hero_right = "contributed today" if active_today else f"active {format_pushed_date(days[-1]['date'])}"
            for repo in user_data["repositories"]["nodes"]:
                live_repos_by_name[repo["name"].lower()] = repo
        except Exception as exc:
            print(f"[warn] Live GitHub API fetch failed ({exc}); falling back to static config.")
            use_live = False

    (assets_dir / "hero.svg").write_text(
        build_hero_svg(profile, hero_wave, years, hero_left, hero_right, active_dot=active_today),
        encoding="utf-8",
    )

    rendered_cards: list[dict[str, str]] = []
    for idx, proj in enumerate(projects_cfg[:2], start=1):
        slug = proj["repo"]
        live_repo = live_repos_by_name.get(slug.lower())
        if use_live and live_repo:
            repo_name = live_repo["name"]
            owner = live_repo["nameWithOwner"].split("/")[0]
            desc = live_repo.get("description") or proj["description"]
            lang = (live_repo.get("primaryLanguage") or {}).get("name") or proj["language"]
            url = live_repo.get("url") or proj["url"]
            commits = (((live_repo.get("defaultBranchRef") or {}).get("target") or {}).get("history") or {}).get("nodes", [])
            counts_by_day: dict[str, int] = {}
            for c in commits:
                day_key = c["committedDate"][:10]
                counts_by_day[day_key] = counts_by_day.get(day_key, 0) + 1
            today = dt.date.today()
            span_days = 60
            series = [counts_by_day.get((today - dt.timedelta(days=span_days - 1 - d)).isoformat(), 0) for d in range(span_days)]
            peak = max(series) if series else 0
            total_c = sum(series)
            curve = [c / peak if peak > 0 else 0.08 for c in series]
            start_label = (today - dt.timedelta(days=span_days - 1)).strftime("%b %d").replace(" 0", " ")
            chart_left = f"Commits/day, {start_label}–today"
            chart_right = f"{total_c} total · peak {peak}"
        else:
            repo_name = proj["display_name"]
            owner = proj.get("owner", username)
            desc = proj["description"]
            lang = proj["language"]
            url = proj["url"]
            curve = synthetic_wave(seed=idx, points=60, mode="card")
            chart_left = proj.get("chart_label", "Commit cadence")
            chart_right = proj.get("category", "featured")

        filename = f"project-{idx}.svg"
        (assets_dir / filename).write_text(
            build_project_card_svg(
                repo_name=repo_name,
                owner=owner,
                description=desc,
                language=lang,
                lang_color=proj.get("lang_color", "#38bdf8"),
                cta_label=proj.get("cta", "VIEW REPO"),
                chart_left=chart_left,
                chart_right=chart_right,
                curve=curve,
                theme_name=proj.get("theme", "cyan"),
                seed=idx,
            ),
            encoding="utf-8",
        )
        rendered_cards.append({"filename": filename, "url": url, "alt": repo_name})

    (assets_dir / "stack.svg").write_text(build_stack_svg(stack_rows), encoding="utf-8")

    rendered_links: list[dict[str, str]] = []
    for idx, link in enumerate(links_cfg, start=1):
        fname = f"link-{idx}.svg"
        pill_w = max(192, len(link["label"]) * 7 + 70)
        (assets_dir / fname).write_text(
            build_pill_svg(link["label"], icon=link.get("icon", "globe"), color=link.get("color", "#38bdf8"), width=pill_w),
            encoding="utf-8",
        )
        rendered_links.append({"filename": fname, "url": link["url"], "alt": link["label"]})

    c1, c2 = rendered_cards
    pills_html = "\n  ".join(
        f'<a href="{l["url"]}"><img src="./assets/{l["filename"]}" alt="{escape(l["alt"])}" /></a>'
        for l in rendered_links
    )
    readme_md = f'''<p align="center">
  <a href="{banner_cfg["url"]}">
    <img src="./assets/{banner_cfg["file"]}" width="100%" alt="{escape(banner_cfg["alt"])}" />
  </a>
</p>

<p align="center">
  <a href="{profile["portfolio_url"]}">
    <img src="./assets/hero.svg" width="100%" alt="{escape(profile["name"])} — GitHub Profile" />
  </a>
</p>

<p align="center">
  <a href="{c1["url"]}"><img src="./assets/{c1["filename"]}" width="49.3%" alt="{escape(c1["alt"])}" /></a>
  <a href="{c2["url"]}"><img src="./assets/{c2["filename"]}" width="49.3%" alt="{escape(c2["alt"])}" /></a>
</p>

<p align="center">
  <img src="./assets/stack.svg" width="100%" alt="Tech Stack" />
</p>

<p align="center">
  {pills_html}
</p>
'''
    (out_dir / "README.md").write_text(readme_md, encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate vibrant dithered GitHub README SVGs.")
    parser.add_argument("--config", type=Path, default=Path(__file__).resolve().parent.parent / "config.json")
    parser.add_argument("--out", type=Path, default=Path(__file__).resolve().parent.parent)
    parser.add_argument("--mode", choices=["live", "static"], default="live")
    args = parser.parse_args()
    generate_all(args.config, args.out, args.mode)
    print(f"Generated README and SVG assets in {args.out} (mode={args.mode})")


if __name__ == "__main__":
    main()
