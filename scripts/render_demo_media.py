"""Render a luxury Swiss-editorial 12s 1280x720@30fps MP4 showcase video and
palette-optimized GitHub README GIF for IdeaStress v0.8.1.
"""

from __future__ import annotations

import math
import shutil
import subprocess
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parents[1]
OUT_DIR = ROOT.parent
ASSETS_DIR = ROOT / "assets"
ASSETS_DIR.mkdir(parents=True, exist_ok=True)
FRAMES_DIR = Path("/tmp/ideastress_demo_frames")
if FRAMES_DIR.exists():
    shutil.rmtree(FRAMES_DIR)
FRAMES_DIR.mkdir(parents=True)

W, H = 1280, 720
FPS = 30
DURATION = 12.0
TOTAL_FRAMES = int(FPS * DURATION)

# Luxury Warm Obsidian & Brushed Champagne Gold Palette
BG = (10, 10, 11)
SURFACE = (18, 18, 22)
SURFACE_2 = (26, 26, 31)
BORDER = (52, 48, 41)
BORDER_HI = (95, 84, 66)
IVORY = (244, 241, 234)
MUTED = (154, 148, 138)
DIM = (99, 95, 88)
GOLD = (201, 169, 110)
GOLD_HI = (227, 201, 150)
EMERALD = (88, 181, 141)
CRIMSON = (212, 107, 107)

# Fonts
F_SERIF = "/usr/share/texmf/fonts/opentype/public/tex-gyre/texgyretermes-regular.otf"
F_SERIF_IT = "/usr/share/texmf/fonts/opentype/public/tex-gyre/texgyretermes-italic.otf"
F_SERIF_BD = "/usr/share/texmf/fonts/opentype/public/tex-gyre/texgyretermes-bold.otf"
F_SANS = "/usr/share/fonts/opentype/inter/InterDisplay-Regular.otf"
F_SANS_BD = "/usr/share/fonts/opentype/inter/Inter-Bold.otf"
F_MONO = "/usr/share/fonts/truetype/liberation2/LiberationMono-Regular.ttf"
F_MONO_BD = "/usr/share/fonts/truetype/liberation/LiberationMono-Bold.ttf"

def load_font(path: str, size: int) -> ImageFont.FreeTypeFont:
    try:
        return ImageFont.truetype(path, size)
    except Exception:
        return ImageFont.load_default()

FONT_H1 = load_font(F_SERIF, 74)
FONT_H1_IT = load_font(F_SERIF_IT, 74)
FONT_H2 = load_font(F_SERIF, 46)
FONT_BRAND = load_font(F_SERIF_BD, 26)
FONT_SUB = load_font(F_SANS, 21)
FONT_BODY = load_font(F_SANS, 16)
FONT_BODY_BD = load_font(F_SANS_BD, 16)
FONT_SMALL = load_font(F_SANS, 13)
FONT_MONO = load_font(F_MONO, 15)
FONT_MONO_SM = load_font(F_MONO, 12)
FONT_MONO_LG = load_font(F_MONO_BD, 32)
FONT_MONO_MD = load_font(F_MONO_BD, 20)


def ease_out(x: float) -> float:
    x = max(0.0, min(1.0, x))
    return 1.0 - (1.0 - x) ** 3


def ease_in_out(x: float) -> float:
    x = max(0.0, min(1.0, x))
    return 3 * x * x - 2 * x * x * x


def blend(c1: tuple[int, int, int], c2: tuple[int, int, int], a: float) -> tuple[int, int, int]:
    a = max(0.0, min(1.0, a))
    return (
        int(c1[0] + (c2[0] - c1[0]) * a),
        int(c1[1] + (c2[1] - c1[1]) * a),
        int(c1[2] + (c2[2] - c1[2]) * a),
    )


def draw_bg(draw: ImageDraw.ImageDraw, t: float) -> None:
    # Subtle architectural hairline grid
    grid_col = (22, 21, 19)
    for x in range(0, W, 80):
        draw.line([(x, 0), (x, H)], fill=grid_col, width=1)
    for y in range(0, H, 80):
        draw.line([(0, y), (W, y)], fill=grid_col, width=1)

    # Subtle ambient golden silk waves
    for idx, (amp, freq, yoff, col) in enumerate([
        (24, 0.0032, 0.78, (36, 31, 23)),
        (16, 0.0044, 0.68, (28, 25, 19)),
    ]):
        pts = []
        for x in range(0, W + 20, 20):
            y = H * yoff - 0.12 * (x / W) * H + math.sin(x * freq + t * (1.2 + idx * 0.4)) * amp
            pts.append((x, y))
        draw.line(pts, fill=col, width=2)

    # Outer fine champagne frame
    draw.rectangle([24, 24, W - 24, H - 24], outline=(42, 38, 32), width=1)


def draw_header_bar(draw: ImageDraw.ImageDraw, active_label: str) -> None:
    # Minimalist geometric monogram
    bx, by = 56, 48
    draw.rounded_rectangle([bx, by, bx + 28, by + 28], radius=4, outline=GOLD, width=2)
    draw.line([(bx + 6, by + 21), (bx + 15, by + 13), (bx + 22, by + 8)], fill=GOLD_HI, width=2)
    draw.ellipse([bx + 19, by + 5, bx + 25, by + 11], fill=GOLD_HI)
    draw.text((bx + 40, by + 1), "IDEASTRESS", font=FONT_BRAND, fill=IVORY)
    draw.rounded_rectangle([bx + 212, by + 4, bx + 276, by + 24], radius=10, outline=BORDER_HI, width=1)
    draw.text((bx + 223, by + 7), "v0.8.1", font=FONT_MONO_SM, fill=GOLD)
    # Right act indicator
    draw.text((W - 56, by + 7), active_label, font=FONT_MONO_SM, fill=GOLD_HI, anchor="ra")
    draw.line([(56, 92), (W - 56, 92)], fill=BORDER, width=1)


def render_act1(img: Image.Image, draw: ImageDraw.ImageDraw, p: float, t: float) -> None:
    """0.0s - 2.8s: Editorial Brand Reveal & Core Thesis."""
    draw_header_bar(draw, "01 / DETERMINISTIC FINANCE")
    a1 = ease_out(p * 2.2)
    a2 = ease_out((p - 0.14) * 2.2)
    a3 = ease_out((p - 0.30) * 2.2)

    # Kicker
    y_k = int(164 + (1 - a1) * 18)
    draw.line([(88, y_k + 8), (124, y_k + 8)], fill=blend(BG, GOLD, a1), width=2)
    draw.text((138, y_k), "EDITION 08.1  ·  MIT OPEN-SOURCE  ·  ZERO LLM MATH GUESSES", font=FONT_MONO_SM, fill=blend(BG, GOLD, a1))

    # Towering Serif H1
    y_h = int(210 + (1 - a1) * 24)
    draw.text((88, y_h), "Falsify the math", font=FONT_H1, fill=blend(BG, IVORY, a1))
    draw.text((88, y_h + 84), "before", font=FONT_H1_IT, fill=blend(BG, GOLD_HI, a1))
    bw = draw.textlength("before ", font=FONT_H1_IT)
    draw.text((88 + bw, y_h + 84), "you write the code.", font=FONT_H1, fill=blend(BG, IVORY, a1))

    # Subtitle
    y_s = int(406 + (1 - a2) * 18)
    draw.text(
        (88, y_s),
        "10 live deterministic financial calculators, 1,000-path Monte Carlo survival solver,",
        font=FONT_SUB,
        fill=blend(BG, MUTED, a2),
    )
    draw.text(
        (88, y_s + 32),
        "Auto-Fix rescue pricing, and 12 JSON-RPC MCP tools for your coding agent.",
        font=FONT_SUB,
        fill=blend(BG, MUTED, a2),
    )

    # Bottom 4-metric architectural strip
    y_m = int(524 + (1 - a3) * 16)
    draw.line([(88, y_m - 22), (W - 88, y_m - 22)], fill=blend(BG, BORDER, a3), width=1)
    metrics = [
        ("10", "LIVE CALCULATORS"),
        ("1,000×", "MONTE CARLO PATHS"),
        ("12", "MCP AGENT TOOLS"),
        ("0%", "UNVERIFIED CLAIMS"),
    ]
    col_w = (W - 176) // 4
    for i, (val, lbl) in enumerate(metrics):
        x = 88 + i * col_w
        draw.text((x, y_m), val, font=FONT_H2, fill=blend(BG, GOLD_HI if i == 1 else IVORY, a3))
        draw.text((x, y_m + 58), lbl, font=FONT_MONO_SM, fill=blend(BG, MUTED, a3))


def render_act2(img: Image.Image, draw: ImageDraw.ImageDraw, p: float, t: float) -> None:
    """2.8s - 6.6s: Live Interactive Falsification Desk + Slider & Crosshair Animation."""
    draw_header_bar(draw, "02 / LIVE FALSIFICATION DESK")

    # Smooth price sweep: $29 (danger) -> $49 (safe)
    sweep = ease_in_out(min(1.0, max(0.0, (p - 0.12) / 0.50)))
    price = 29 + 20 * sweep
    surv = 41.2 + (97.4 - 41.2) * sweep
    max_cac = 112 + (210 - 112) * sweep
    imp_cac = 260 - 70 * sweep  # CPC improves or price lifts ceiling
    viable = surv >= 85.0

    # Left panel: Controls & Auto-Fix Verdict
    lx, ly, lw, lh = 56, 118, 410, 548
    draw.rounded_rectangle([lx, ly, lx + lw, ly + lh], radius=16, fill=SURFACE, outline=BORDER_HI, width=1)
    draw.ellipse([lx + 24, ly + 26, lx + 32, ly + 34], fill=EMERALD if viable else CRIMSON)
    draw.text((lx + 42, ly + 23), "INTERACTIVE STRESS-TESTER", font=FONT_MONO_SM, fill=GOLD)
    draw.line([(lx + 24, ly + 52), (lx + lw - 24, ly + 52)], fill=BORDER, width=1)

    # Preset chips
    for i, (lbl, act) in enumerate([("B2B SaaS", True), ("AI Wrapper", False), ("DTC E-Com", False)]):
        px = lx + 24 + i * 122
        draw.rounded_rectangle(
            [px, ly + 68, px + 112, ly + 98],
            radius=8,
            fill=(36, 31, 22) if act else BG,
            outline=GOLD if act else BORDER,
            width=1,
        )
        draw.text((px + 56, ly + 83), lbl, font=FONT_MONO_SM, fill=GOLD_HI if act else MUTED, anchor="mm")

    # Animated Sliders
    sliders = [
        ("Unit Price / Monthly ARPA", f"${price:.0f}", (price - 15) / 100.0),
        ("Google Ads CPC (Paid Search)", f"${6.50 - 1.75 * sweep:.2f}", 0.55 - 0.18 * sweep),
        ("Starting Cash Runway", "$12,000", 0.38),
    ]
    for i, (lbl, val_str, frac) in enumerate(sliders):
        sy = ly + 130 + i * 76
        draw.text((lx + 24, sy), lbl, font=FONT_SMALL, fill=MUTED)
        draw.text((lx + lw - 24, sy), val_str, font=FONT_MONO, fill=IVORY, anchor="ra")
        track_y = sy + 32
        tx1, tx2 = lx + 24, lx + lw - 24
        draw.line([(tx1, track_y), (tx2, track_y)], fill=BORDER_HI, width=3)
        kx = int(tx1 + frac * (tx2 - tx1))
        draw.line([(tx1, track_y), (kx, track_y)], fill=GOLD, width=3)
        draw.ellipse([kx - 8, track_y - 8, kx + 8, track_y + 8], fill=GOLD_HI, outline=BG, width=2)

    # Auto-Fix Verdict Box
    vy = ly + 372
    v_col = EMERALD if viable else CRIMSON
    v_bg = (16, 30, 24) if viable else (34, 17, 18)
    draw.rounded_rectangle([lx + 24, vy, lx + lw - 24, vy + 148], radius=12, fill=v_bg, outline=v_col, width=1)
    if viable:
        draw.text((lx + 40, vy + 18), "FALSIFICATION PASSED", font=FONT_MONO_MD, fill=EMERALD)
        draw.text((lx + 40, vy + 54), "Raising price to $49 lifts 12-month", font=FONT_BODY, fill=IVORY)
        draw.text((lx + 40, vy + 78), "Monte Carlo survival to 97.4% and", font=FONT_BODY, fill=IVORY)
        draw.text((lx + 40, vy + 102), "clears your $210 Max Viable CAC.", font=FONT_BODY, fill=IVORY)
    else:
        draw.text((lx + 40, vy + 18), "AUTO-FIX PRESCRIPTION", font=FONT_MONO_MD, fill=CRIMSON)
        draw.text((lx + 40, vy + 54), f"Survival is only {surv:.1f}% at ${price:.0f}/mo.", font=FONT_BODY, fill=IVORY)
        draw.text((lx + 40, vy + 78), "Raise price to $49 or shift 35% to", font=FONT_BODY, fill=IVORY)
        draw.text((lx + 40, vy + 102), "20%-off Annual Prepay to survive.", font=FONT_BODY, fill=GOLD_HI)

    # Right panel: KPI Cards + Luxury Interactive Telemetry Chart
    rx, ry, rw, rh = 490, 118, 734, 548
    draw.rounded_rectangle([rx, ry, rx + rw, ry + rh], radius=16, fill=SURFACE, outline=BORDER_HI, width=1)

    kpis = [
        ("12M SURVIVAL (1,000 RUNS)", f"{surv:.1f}%", f"P10 Cash: ${int(-6200 + 13342 * sweep):,}", EMERALD if viable else CRIMSON),
        ("MAX VIABLE CAC CEILING", f"${max_cac:.0f}", f"Implied Ads CAC: ${imp_cac:.0f}", GOLD_HI),
        ("PAID CHANNEL VERDICT", "VIABLE" if viable else "BLOCKED", "2.5% CVR · Live Check", EMERALD if viable else CRIMSON),
    ]
    kw = (rw - 72) // 3
    for i, (kl, kv, ks, col) in enumerate(kpis):
        kx = rx + 24 + i * (kw + 12)
        draw.rounded_rectangle([kx, ry + 24, kx + kw, ry + 132], radius=12, fill=BG, outline=BORDER, width=1)
        draw.text((kx + 16, ry + 38), kl, font=FONT_MONO_SM, fill=MUTED)
        draw.text((kx + 16, ry + 62), kv, font=FONT_MONO_LG, fill=col)
        draw.text((kx + 16, ry + 104), ks, font=FONT_SMALL, fill=DIM)

    # Chart box
    cx, cy, cw, ch = rx + 24, ry + 152, rw - 48, 372
    draw.rounded_rectangle([cx, cy, cx + cw, cy + ch], radius=14, fill=BG, outline=BORDER, width=1)
    draw.text((cx + 20, cy + 16), "12M CASH TRAJECTORY (P10 · BASE · P90)", font=FONT_MONO_SM, fill=MUTED)
    draw.text((cx + cw - 20, cy + 16), "SEEDED DETERMINISTIC", font=FONT_MONO_SM, fill=GOLD, anchor="ra")

    # Plot coordinates
    px1, py1, px2, py2 = cx + 68, cy + 56, cx + cw - 72, cy + ch - 42
    pw, ph = px2 - px1, py2 - py1
    zero_y = int(py1 + ph * 0.72)

    # Horizontal gridlines + Y ticks
    for frac, lbl in [(0.0, "$36k"), (0.36, "$18k"), (0.72, "$0"), (1.0, "-$12k")]:
        gy = int(py1 + ph * frac)
        draw.line([(px1, gy), (px2, gy)], fill=(30, 28, 25), width=1)
        draw.text((px1 - 12, gy), lbl, font=FONT_MONO_SM, fill=CRIMSON if lbl == "$0" else DIM, anchor="rm")

    # Crimson diagonal hatch Insolvency Zone below $0
    for hx in range(px1, px2 + (py2 - zero_y), 14):
        x_start = max(px1, hx - (py2 - zero_y))
        y_start = zero_y + max(0, x_start - (hx - (py2 - zero_y)))
        x_end = min(px2, hx)
        y_end = zero_y + max(0, (hx - x_end))
        if x_end > x_start:
            draw.line([(x_start, py2 if hx - (py2 - zero_y) >= px1 else zero_y + (hx - px1)), (x_end, zero_y if hx <= px2 else zero_y + (hx - px2))], fill=(58, 24, 26), width=1)
    draw.line([(px1, zero_y), (px2, zero_y)], fill=CRIMSON, width=2)
    draw.text((px2 - 8, zero_y + 16), "INSOLVENCY ZONE", font=FONT_MONO_SM, fill=(140, 62, 64), anchor="ra")

    # Generate 13 smooth month points for P90 / Base / P10
    xs = [px1 + int((m / 12.0) * pw) for m in range(13)]
    opt_pts, base_pts, cons_pts = [], [], []
    for m in range(13):
        u = m / 12.0
        y_opt = zero_y - int((0.28 + (0.05 + 0.56 * sweep) * (u ** 1.45) - 0.08 * math.sin(u * math.pi)) * ph)
        y_base = zero_y - int((0.28 + (-0.34 + 0.62 * sweep) * (u ** 1.35) - 0.09 * math.sin(u * math.pi)) * ph)
        y_cons = zero_y - int((0.28 + (-0.52 + 0.44 * sweep) * u) * ph)
        opt_pts.append((xs[m], max(py1, min(py2, y_opt))))
        base_pts.append((xs[m], max(py1, min(py2, y_base))))
        cons_pts.append((xs[m], max(py1, min(py2, y_cons))))

    # Draw trajectories
    draw.line(opt_pts, fill=EMERALD, width=3)
    draw.line(cons_pts, fill=CRIMSON, width=2)
    draw.line(base_pts, fill=GOLD_HI, width=4)

    # Endpoint beacons & labels
    draw.ellipse([base_pts[-1][0] - 6, base_pts[-1][1] - 6, base_pts[-1][0] + 6, base_pts[-1][1] + 6], fill=GOLD_HI, outline=BG, width=2)
    draw.text((px2 + 10, opt_pts[-1][1]), f"${int(14 + 18 * sweep)}k", font=FONT_MONO_SM, fill=EMERALD, anchor="lm")
    draw.text((px2 + 10, base_pts[-1][1]), f"${int(-3 + 19 * sweep)}k", font=FONT_MONO_SM, fill=GOLD_HI, anchor="lm")
    draw.text((px2 + 10, cons_pts[-1][1]), f"${int(-11 + 14 * sweep)}k", font=FONT_MONO_SM, fill=CRIMSON, anchor="lm")

    # X axis ticks
    for m in (0, 3, 6, 9, 12):
        draw.text((xs[m], py2 + 18), f"M{m}", font=FONT_MONO_SM, fill=MUTED, anchor="mm")

    # Animated Crosshair Scrubbing HUD (activates cleanly after sweep finishes)
    if p > 0.62:
        scrub = ease_in_out((p - 0.62) / 0.34)
        idx = min(12, max(2, int(round(2 + scrub * 9))))
        ch_x = xs[idx]
        draw.line([(ch_x, py1), (ch_x, py2)], fill=GOLD, width=1)
        for pt, col in [(opt_pts[idx], EMERALD), (base_pts[idx], GOLD_HI), (cons_pts[idx], CRIMSON)]:
            draw.ellipse([pt[0] - 5, pt[1] - 5, pt[0] + 5, pt[1] + 5], fill=col, outline=BG, width=2)
        hx = ch_x - 196 if ch_x > cx + cw * 0.58 else ch_x + 14
        hy = py1 + 14
        draw.rounded_rectangle([hx, hy, hx + 182, hy + 102], radius=10, fill=(14, 14, 18), outline=GOLD, width=1)
        draw.text((hx + 12, hy + 10), f"MONTH {idx:02d}", font=FONT_MONO_SM, fill=GOLD_HI)
        draw.text((hx + 170, hy + 10), "+$1.4k/mo", font=FONT_MONO_SM, fill=EMERALD, anchor="ra")
        draw.line([(hx + 12, hy + 30), (hx + 170, hy + 30)], fill=BORDER, width=1)
        draw.text((hx + 12, hy + 38), "P90 Opt", font=FONT_MONO_SM, fill=MUTED)
        draw.text((hx + 170, hy + 38), f"${12000 + idx * 1650:,}", font=FONT_MONO_SM, fill=EMERALD, anchor="ra")
        draw.text((hx + 12, hy + 58), "Base", font=FONT_MONO_SM, fill=MUTED)
        draw.text((hx + 170, hy + 58), f"${12000 + idx * 620:,}", font=FONT_MONO_SM, fill=GOLD_HI, anchor="ra")
        draw.text((hx + 12, hy + 78), "P10 Cons", font=FONT_MONO_SM, fill=MUTED)
        draw.text((hx + 170, hy + 78), f"${12000 - idx * 380:,}", font=FONT_MONO_SM, fill=CRIMSON, anchor="ra")


def render_act3(img: Image.Image, draw: ImageDraw.ImageDraw, p: float, t: float) -> None:
    """6.6s - 9.6s: 5x2 Ten-Calculator Architectural Matrix Spotlight."""
    draw_header_bar(draw, "03 / 10-IN-1 INSTRUMENT MATRIX")
    a = ease_out(p * 2.5)
    draw.text((56, 118), "Ten deterministic calculators. All visible at a glance.", font=FONT_H2, fill=blend(BG, IVORY, a))
    draw.text((56, 178), "Zero black boxes · Per-tool 3-Step Guides, Exact Formulas, Worked Examples & 40 FAQs", font=FONT_BODY, fill=blend(BG, MUTED, a))

    tiles = [
        ("01", "Reverse Frontier", "1,000× Monte Carlo & CAC"),
        ("02", "Quit-Job MRR", "Stripe vs MoR & Tax"),
        ("03", "Freemium Drag", "Free-tier subsidy stress"),
        ("04", "Meta/TikTok CPM", "CPM → CTR → ROAS funnel"),
        ("05", "AI Token Margin", "LLM COGS & Whale limit"),
        ("06", "Geo-Arbitrage CPC", "US / UK / DE / SG / MY"),
        ("07", "Break-Even", "Unit floor & overhead"),
        ("08", "SaaS LTV / CAC", "Payback & 2026 medians"),
        ("09", "E-Com ROAS", "First-order margin floor"),
        ("10", "Startup Runway", "Shock-tested burn months"),
    ]
    active_idx = [0, 1, 4, 5][min(3, int(p * 4))]
    gw = (W - 112 - 4 * 16) // 5
    gh = 178
    for i, (num, title, sub) in enumerate(tiles):
        col = i % 5
        row = i // 5
        tx = 56 + col * (gw + 16)
        ty = 236 + row * (gh + 18)
        is_act = (i == active_idx)
        fill = (32, 28, 21) if is_act else SURFACE
        out = GOLD_HI if is_act else BORDER
        draw.rounded_rectangle([tx, ty, tx + gw, ty + gh], radius=14, fill=fill, outline=out, width=2 if is_act else 1)
        if is_act:
            draw.line([(tx + 12, ty + 2), (tx + gw - 12, ty + 2)], fill=GOLD_HI, width=3)
        draw.text((tx + 18, ty + 20), num, font=FONT_MONO_MD, fill=GOLD_HI if is_act else DIM)
        draw.ellipse([tx + gw - 28, ty + 24, tx + gw - 18, ty + 34], fill=GOLD_HI if is_act else SURFACE_2, outline=BORDER_HI)
        draw.text((tx + 18, ty + 74), title, font=FONT_BODY_BD, fill=IVORY)
        draw.text((tx + 18, ty + 106), sub, font=FONT_SMALL, fill=GOLD_HI if is_act else MUTED)
        draw.text((tx + 18, ty + 144), "LIVE + 4 FAQS", font=FONT_MONO_SM, fill=DIM)


def render_act4(img: Image.Image, draw: ImageDraw.ImageDraw, p: float, t: float) -> None:
    """9.6s - 12.0s: Business-as-Code CLI & 12-Tool MCP Closing Card."""
    draw_header_bar(draw, "04 / BUSINESS-AS-CODE MCP")
    a = ease_out(p * 2.8)
    draw.text((88, 134), "Run the exact same math", font=FONT_H2, fill=blend(BG, IVORY, a))
    draw.text((88, 188), "inside your IDE & AI agents.", font=FONT_H2, fill=blend(BG, GOLD_HI, a))

    # Matte-black Terminal Monograph
    tx, ty, tw, th = 88, 266, 1104, 290
    draw.rounded_rectangle([tx, ty, tx + tw, ty + th], radius=16, fill=(13, 13, 16), outline=BORDER_HI, width=1)
    draw.line([(tx, ty + 44), (tx + tw, ty + 44)], fill=BORDER, width=1)
    for idx in range(3):
        draw.ellipse([tx + 22 + idx * 18, ty + 17, tx + 32 + idx * 18, ty + 27], fill=(64, 58, 48))
    draw.text((tx + tw - 24, ty + 16), "STDIO JSON-RPC 2.0 MCP SERVER", font=FONT_MONO_SM, fill=GOLD, anchor="ra")

    lines = [
        ("$ pip install ideastress && ideastress mcp", GOLD_HI, 0.05),
        ("$ ideastress scan-repo ./my-saas --price 29", IVORY, 0.25),
        ("  ✓ Detected 3 LLM call sites · Whale bankruptcy limit: 108 req/day", EMERALD, 0.45),
        ("  ✓ 12 MCP tools ready · 47/47 unit tests · 10/10 benchmarks passed", EMERALD, 0.62),
    ]
    for i, (txt, col, start_p) in enumerate(lines):
        if p >= start_p:
            chars = int(len(txt) * min(1.0, (p - start_p) / 0.18))
            draw.text((tx + 28, ty + 68 + i * 48), txt[:chars], font=FONT_MONO_MD, fill=col)

    draw.text((W // 2, 616), "IDEASTRESS v0.8.1  ·  MIT OPEN-SOURCE  ·  ZERO-BACKEND WEB + MCP", font=FONT_MONO, fill=GOLD, anchor="mm")


print(f"Rendering {TOTAL_FRAMES} frames at {W}x{H}@{FPS}fps...")
for f in range(TOTAL_FRAMES):
    t = f / FPS
    img = Image.new("RGB", (W, H), BG)
    draw = ImageDraw.Draw(img)
    draw_bg(draw, t)

    if t < 2.8:
        render_act1(img, draw, t / 2.8, t)
    elif t < 6.6:
        render_act2(img, draw, (t - 2.8) / 3.8, t)
    elif t < 9.6:
        render_act3(img, draw, (t - 6.6) / 3.0, t)
    else:
        render_act4(img, draw, (t - 9.6) / 2.4, t)

    img.save(FRAMES_DIR / f"frame_{f:04d}.png", compress_level=1)

mp4_out = OUT_DIR / "ideastress_demo.mp4"
gif_out = OUT_DIR / "ideastress_demo.gif"
palette = Path("/tmp/ideastress_palette.png")

# 1. Encode crisp GitHub-compatible H.264 MP4
subprocess.run([
    "ffmpeg", "-y", "-framerate", str(FPS),
    "-i", str(FRAMES_DIR / "frame_%04d.png"),
    "-c:v", "libx264", "-pix_fmt", "yuv420p", "-crf", "18",
    "-movflags", "+faststart", str(mp4_out),
], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

# 2. Encode ultra-clean 2-pass palette-optimized GitHub README GIF (960x540 @ 15fps)
subprocess.run([
    "ffmpeg", "-y", "-i", str(mp4_out),
    "-vf", "fps=15,scale=960:-1:flags=lanczos,palettegen=max_colors=128:stats_mode=diff",
    str(palette),
], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

subprocess.run([
    "ffmpeg", "-y", "-i", str(mp4_out), "-i", str(palette),
    "-lavfi", "fps=15,scale=960:-1:flags=lanczos [x]; [x][1:v] paletteuse=dither=bayer:bayer_scale=3",
    str(gif_out),
], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

# Copy into ideastress/assets/ alongside social preview
shutil.copy2(mp4_out, ASSETS_DIR / "ideastress_demo.mp4")
shutil.copy2(gif_out, ASSETS_DIR / "ideastress_demo.gif")

social_src = Path("/working_dir/c_3dbd5e70ec1f8f59/user_uploaded_files/ttl=63d/tool_generated/watermarked_img_4883781542399704737.jpg")
if social_src.exists():
    shutil.copy2(social_src, ASSETS_DIR / "social-preview.jpg")

print(f"MP4 ready: {mp4_out.name} ({mp4_out.stat().st_size:,} bytes)")
print(f"GIF ready: {gif_out.name} ({gif_out.stat().st_size:,} bytes)")
print("Saved to ideastress/assets/:", [p.name for p in sorted(ASSETS_DIR.iterdir())])
