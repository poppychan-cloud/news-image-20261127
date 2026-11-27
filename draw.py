#!/usr/bin/env python3
"""Render the 27 November 2026 one-page newspaper (1024x1024, PIL only).

Hybrid edition: the 3 lead illustrations are pre-generated flat-art images
in assets/ (no text in them); every word, badge, chart, card scene, map,
timeline and footer is drawn in code. Deterministic: no network, no clock,
no randomness. Two runs produce identical bytes.
"""
import json
import os
import sys
from PIL import Image, ImageDraw, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
W, H = 1024, 1024
PAPER = (247, 243, 232)
INK = (26, 26, 26)
GREY = (90, 90, 86)
RULE = (26, 26, 26)
RED = (179, 39, 30)
NAVY = (31, 58, 95)
GOLD = (201, 162, 39)
GREEN = (30, 107, 58)
BLUE = (31, 95, 179)
AMBER = (178, 106, 0)
SEA = (215, 229, 234)
LAND = (227, 220, 195)
CARD_BG = (255, 255, 255)

FONT_DIR = "/usr/share/fonts/truetype/dejavu"


def font(name, size):
    return ImageFont.truetype(os.path.join(FONT_DIR, name), size)


F_MAST = font("DejaVuSerif-Bold.ttf", 36)
F_DATE = font("DejaVuSans-Bold.ttf", 14)
F_STRAP = font("DejaVuSans.ttf", 11)
F_CHIP = font("DejaVuSans-Bold.ttf", 10)
F_LEAD_H = font("DejaVuSans-Bold.ttf", 16)
F_LEAD_D = font("DejaVuSans.ttf", 11)
F_SRC = font("DejaVuSans.ttf", 9)
F_STAT_V = font("DejaVuSans-Bold.ttf", 20)
F_STAT_L = font("DejaVuSans.ttf", 9)
F_CARD_H = font("DejaVuSans-Bold.ttf", 12)
F_CARD_D = font("DejaVuSans.ttf", 10)
F_TL_T = font("DejaVuSans-Bold.ttf", 10)
F_TL_X = font("DejaVuSans.ttf", 10)
F_BRIEF = font("DejaVuSans.ttf", 10)
F_BRIEF_B = font("DejaVuSans-Bold.ttf", 10)
F_BADGE = font("DejaVuSans-Bold.ttf", 8)
F_DC_T = font("DejaVuSans-Bold.ttf", 10)
F_DC = font("DejaVuSans.ttf", 9)
F_PIN = font("DejaVuSans-Bold.ttf", 10)

BADGE_FILL = {"OFFICIAL": GREEN, "REPORTED": BLUE, "CLAIM": AMBER}

TRIMS = 0
OVERFLOWS = 0


def wrap(text, fnt, width):
    """Greedy word wrap to pixel width; returns list of lines."""
    words = text.split()
    lines, cur = [], ""
    for w in words:
        trial = (cur + " " + w).strip()
        if fnt.getlength(trial) <= width:
            cur = trial
        else:
            if cur:
                lines.append(cur)
            cur = w
    if cur:
        lines.append(cur)
    return lines


def draw_wrapped(d, x, y, text, fnt, width, max_lines, fill=INK, leading=2):
    """Draw wrapped text; returns (lines_used, next_y). Counts a trim if cut."""
    global TRIMS
    lines = wrap(text, fnt, width)
    used = lines[:max_lines]
    if len(lines) > max_lines:
        TRIMS += 1
        used[-1] = used[-1][:-1] + "…"
    yy = y
    for ln in used:
        d.text((x, yy), ln, font=fnt, fill=fill)
        yy += fnt.size + leading
    return len(used), yy


def badge(d, x, y, label):
    """Draw a small badge chip; returns its width."""
    w = int(F_BADGE.getlength(label)) + 10
    h = 13
    d.rounded_rectangle([x, y, x + w, y + h], radius=3, fill=BADGE_FILL[label])
    d.text((x + 5, y + 2), label, font=F_BADGE, fill=(255, 255, 255))
    return w


def counts(items, key):
    out = {}
    for it in items:
        out[it[key]] = out.get(it[key], 0) + 1
    return out


# Simplified world coastline polygons (lon, lat), equirectangular.
CONTINENTS = [
    # North America
    [(-168, 66), (-140, 70), (-125, 72), (-110, 73), (-95, 80), (-85, 80),
     (-75, 73), (-65, 60), (-55, 47), (-70, 42), (-75, 35), (-80, 26),
     (-84, 30), (-90, 21), (-97, 26), (-105, 20), (-110, 23), (-117, 33),
     (-125, 40), (-125, 49), (-140, 60), (-155, 58), (-165, 60), (-168, 66)],
    # Greenland
    [(-58, 64), (-45, 60), (-32, 68), (-25, 70), (-30, 76), (-55, 76),
     (-58, 70)],
    # South America
    [(-80, 9), (-75, 11), (-62, 10), (-52, 5), (-50, 0), (-35, -8),
     (-40, -20), (-48, -28), (-58, -38), (-65, -45), (-70, -54),
     (-73, -40), (-73, -20), (-80, -5), (-81, 0), (-80, 9)],
    # Africa
    [(-17, 15), (-10, 31), (0, 36), (10, 37), (20, 32), (32, 31),
     (35, 28), (43, 12), (51, 11), (48, 2), (40, -10), (35, -18),
     (28, -33), (18, -35), (12, -18), (9, 4), (-8, 4), (-17, 15)],
    # Eurasia
    [(-10, 36), (-9, 43), (-2, 48), (-4, 50), (0, 51), (5, 53), (8, 57),
     (10, 59), (18, 56), (21, 55), (24, 59), (28, 60), (30, 62), (40, 68),
     (50, 69), (60, 69), (70, 72), (80, 73), (90, 75), (100, 77),
     (110, 74), (120, 73), (130, 72), (140, 72), (150, 70), (160, 69),
     (170, 66), (178, 65), (170, 60), (162, 56), (156, 51), (142, 45),
     (135, 43), (130, 42), (127, 40), (122, 38), (120, 32), (115, 23),
     (108, 18), (105, 10), (100, 8), (98, 12), (94, 16), (91, 22),
     (88, 22), (85, 19), (80, 13), (77, 8), (75, 12), (72, 20),
     (66, 25), (61, 25), (57, 26), (52, 26), (50, 29), (48, 30),
     (44, 29), (40, 31), (36, 36), (30, 36), (26, 38), (22, 37),
     (19, 40), (15, 44), (12, 44), (8, 44), (3, 43), (-2, 37),
     (-9, 37), (-10, 36)],
    # UK
    [(-5, 50), (-3, 53), (-5, 56), (-3, 58), (-1, 57), (0, 53), (1, 51),
     (-5, 50)],
    # Japan
    [(130, 31), (132, 33), (135, 34), (137, 35), (139, 35), (140, 36),
     (141, 38), (141, 40), (142, 42), (143, 44), (141, 45), (140, 44),
     (139, 40), (137, 37), (135, 34), (132, 33)],
    # Borneo
    [(109, 1), (113, 4), (117, 6), (119, 1), (117, -3), (112, -3),
     (109, 0)],
    # Sumatra
    [(95, 5), (100, 0), (104, -3), (106, -6), (103, -5), (99, -1),
     (95, 3)],
    # Java
    [(105, -6), (110, -7), (114, -8), (114, -9), (108, -8), (105, -7)],
    # New Guinea
    [(131, -1), (136, -2), (141, -3), (146, -6), (150, -9), (147, -9),
     (142, -8), (136, -6), (131, -2)],
    # Australia
    [(113, -22), (114, -30), (115, -35), (120, -34), (124, -33),
     (129, -32), (132, -32), (135, -35), (137, -35), (140, -38),
     (145, -38), (150, -37), (153, -32), (153, -27), (150, -22),
     (146, -19), (142, -15), (142, -11), (136, -12), (132, -11),
     (130, -13), (126, -14), (122, -17), (118, -20), (113, -22)],
    # New Zealand
    [(167, -45), (170, -42), (173, -41), (175, -38), (177, -38),
     (174, -41), (171, -43), (168, -46), (167, -45)],
    # Madagascar
    [(44, -16), (47, -15), (50, -16), (49, -20), (47, -24), (44, -25),
     (43, -21), (44, -16)],
    # Taiwan
    [(120, 22), (121, 23), (122, 25), (121, 25), (120, 23)],
]

# ---------------------------------------------------------------- card scenes
def scene_flags(d, x, y, w, h):
    d.rectangle([x, y, x + w, y + h], fill=(31, 58, 95))
    d.rectangle([x, y, x + w // 2 - 2, y + h], fill=(31, 95, 179))
    # union jack-ish cross on the left half
    d.rectangle([x + w // 4 - 3, y, x + w // 4 + 3, y + h], fill=(255, 255, 255))
    d.rectangle([x, y + h // 2 - 3, x + w // 2 - 2, y + h // 2 + 3],
                fill=(255, 255, 255))
    # eu stars circle on the right half
    cx, cy = x + w * 3 // 4, y + h // 2
    for k in range(8):
        import math
        a = math.pi * 2 * k / 8 - math.pi / 2
        d.ellipse([cx + int(13 * math.cos(a)) - 2, cy + int(13 * math.sin(a)) - 2,
                   cx + int(13 * math.cos(a)) + 2, cy + int(13 * math.sin(a)) + 2],
                  fill=GOLD)


def scene_candles(d, x, y, w, h):
    d.rectangle([x, y, x + w, y + h], fill=(232, 236, 240))
    base = y + h - 8
    d.line([x + 4, base, x + w - 4, base], fill=INK, width=2)
    bars = [(8, 26, 18, True), (30, 14, 30, False), (52, 34, 22, True),
            (74, 18, 26, False), (96, 10, 34, True), (118, 22, 18, False),
            (140, 12, 30, True), (162, 26, 16, False)]
    for bx, top, bh, up in bars:
        col = (30, 140, 70) if up else (200, 40, 30)
        d.rectangle([x + bx, y + top, x + bx + 12, y + top + bh], fill=col)
        d.line([x + bx + 6, y + top - 5, x + bx + 6, y + top + bh + 5],
               fill=col, width=2)
    d.line([x + 8, y + 18, x + w - 8, y + 44], fill=NAVY, width=2)


def scene_burst(d, x, y, w, h):
    d.rectangle([x, y, x + w, y + h], fill=(40, 40, 48))
    cx, cy = x + w // 2, y + h // 2
    import math
    for k in range(12):
        a = math.pi * 2 * k / 12
        r1, r2 = 8, 26
        d.polygon([(cx + int(r1 * math.cos(a - 0.12)), cy + int(r1 * math.sin(a - 0.12))),
                   (cx + int(r2 * math.cos(a)), cy + int(r2 * math.sin(a))),
                   (cx + int(r1 * math.cos(a + 0.12)), cy + int(r1 * math.sin(a + 0.12)))],
                  fill=(240, 160, 40))
    d.ellipse([cx - 9, cy - 9, cx + 9, cy + 9], fill=(250, 220, 90))
    d.ellipse([x + 12, y + h - 16, x + 26, y + h - 4], fill=(120, 120, 130))
    d.ellipse([x + w - 30, y + h - 12, x + w - 14, y + h - 2], fill=(120, 120, 130))


def scene_tv(d, x, y, w, h):
    d.rectangle([x, y, x + w, y + h], fill=(232, 236, 240))
    d.rectangle([x + 28, y + 12, x + w - 28, y + h - 14], fill=(31, 58, 95))
    d.rectangle([x + 34, y + 17, x + w - 34, y + h - 19], fill=(120, 190, 220))
    for i in range(3):
        d.arc([x + w - 30 + i * 6, y + 22 + i * 4, x + w - 8 + i * 6,
               y + 40 + i * 4], 300, 60, fill=RED, width=2)
    d.line([x + w // 2 - 8, y + h - 14, x + w // 2 - 14, y + h - 4],
           fill=INK, width=3)
    d.line([x + w // 2 + 8, y + h - 14, x + w // 2 + 14, y + h - 4],
           fill=INK, width=3)


def scene_jet(d, x, y, w, h):
    d.rectangle([x, y, x + w, y + h], fill=(200, 222, 235))
    d.polygon([(x + 30, y + h // 2 - 4), (x + 90, y + h // 2 - 8),
               (x + 150, y + h // 2), (x + 90, y + h // 2 + 8)],
              fill=(60, 60, 70))
    d.polygon([(x + 60, y + h // 2 - 4), (x + 75, y + h // 2 - 22),
               (x + 85, y + h // 2 - 4)], fill=(60, 60, 70))
    d.polygon([(x + 120, y + h // 2 - 2), (x + 135, y + h // 2 - 14),
               (x + 140, y + h // 2 - 2)], fill=(60, 60, 70))
    d.polygon([(x + 30, y + h // 2), (x + 45, y + h // 2 - 12),
               (x + 48, y + h // 2)], fill=(60, 60, 70))
    for i, cx in enumerate((x + 20, x + 55, x + 95)):
        d.ellipse([cx, y + 8 + (i % 2) * 8, cx + 14, y + 18 + (i % 2) * 8],
                  fill=(255, 255, 255))


def scene_rocket(d, x, y, w, h):
    d.rectangle([x, y, x + w, y + h], fill=(24, 28, 44))
    for sx, sy in ((x + 20, y + 10), (x + 150, y + 8), (x + 90, y + 18),
                   (x + 40, y + 30), (x + 130, y + 34)):
        d.ellipse([sx, sy, sx + 3, sy + 3], fill=(255, 255, 255))
    cx = x + w // 2
    d.polygon([(cx - 10, y + h - 12), (cx - 10, y + 16), (cx, y + 4),
               (cx + 10, y + 16), (cx + 10, y + h - 12)], fill=(230, 230, 235))
    d.polygon([(cx - 10, y + h - 22), (cx - 22, y + h - 8), (cx - 10, y + h - 12)],
              fill=RED)
    d.polygon([(cx + 10, y + h - 22), (cx + 22, y + h - 8), (cx + 10, y + h - 12)],
              fill=RED)
    d.polygon([(cx - 5, y + h - 12), (cx, y + h - 2), (cx + 5, y + h - 12)],
              fill=(240, 160, 40))
    d.ellipse([cx - 4, y + 20, cx + 4, y + 28], fill=NAVY)


def scene_skyline(d, x, y, w, h):
    d.rectangle([x, y, x + w, y + h], fill=(232, 226, 205))
    tops = [18, 8, 24, 12, 20, 6, 16]
    bw = w // 7
    for i, t in enumerate(tops):
        d.rectangle([x + i * bw + 2, y + t, x + (i + 1) * bw - 2, y + h - 8],
                    fill=(70, 80, 95))
    d.polygon([(x + w // 2 - 14, y + h - 8), (x + w // 2, y + 2),
               (x + w // 2 + 14, y + h - 8)], fill=(240, 120, 30))
    d.polygon([(x + w // 2 - 8, y + h - 8), (x + w // 2, y + 14),
               (x + w // 2 + 8, y + h - 8)], fill=(250, 200, 60))


def scene_factory(d, x, y, w, h):
    d.rectangle([x, y, x + w, y + h], fill=(232, 236, 240))
    d.rectangle([x + 14, y + 26, x + w - 14, y + h - 8], fill=(90, 95, 105))
    d.polygon([(x + 14, y + 26), (x + 40, y + 12), (x + 66, y + 26)],
              fill=(70, 75, 85))
    d.rectangle([x + 30, y + 6, x + 38, y + 26], fill=(70, 75, 85))
    d.rectangle([x + 60, y + 2, x + 68, y + 26], fill=(70, 75, 85))
    for sx, sy, r in ((x + 34, y + 2, 4), (x + 64, y - 2, 5), (x + 90, y + 10, 4)):
        d.ellipse([sx - r, sy - r, sx + r, sy + r], fill=(160, 160, 165))
    d.rectangle([x + 100, y + 34, x + 116, y + h - 8], fill=(200, 60, 50))
    d.rectangle([x + 122, y + 34, x + 138, y + h - 8], fill=(230, 190, 60))


def scene_ballot(d, x, y, w, h):
    d.rectangle([x, y, x + w, y + h], fill=(232, 236, 240))
    d.rectangle([x + 40, y + 26, x + w - 40, y + h - 8], fill=(120, 90, 60))
    d.rectangle([x + 34, y + 20, x + w - 34, y + 28], fill=(90, 65, 40))
    d.rectangle([x + w // 2 - 14, y + 22, x + w // 2 + 14, y + 26],
                fill=(30, 30, 30))
    d.polygon([(x + 52, y + 34), (x + 52, y + 16), (x + 88, y + 16),
               (x + 88, y + 22)], fill=(255, 255, 255))
    d.line([x + 58, y + 26, x + 66, y + 32, x + 80, y + 14], fill=GREEN, width=3)
    d.ellipse([x + w - 34, y + 8, x + w - 18, y + 24], fill=GOLD)
    d.text((x + w - 31, y + 10), "?", font=F_BADGE, fill=INK)


def scene_bank(d, x, y, w, h):
    d.rectangle([x, y, x + w, y + h], fill=(232, 226, 205))
    d.polygon([(x + 40, y + 14), (x + w // 2, y + 2), (x + w - 40, y + 14)],
              fill=NAVY)
    d.rectangle([x + 44, y + 14, x + w - 44, y + 18], fill=(230, 225, 200))
    for i in range(4):
        cx = x + 56 + i * 26
        d.rectangle([cx, y + 18, cx + 8, y + h - 10], fill=(240, 235, 210))
    d.rectangle([x + 40, y + h - 10, x + w - 40, y + h - 6], fill=NAVY)
    d.rectangle([x + w // 2 - 10, y + 30, x + w // 2 + 10, y + h - 10],
                fill=(40, 40, 50))


SCENES = {"flags": scene_flags, "candles": scene_candles,
          "burst": scene_burst, "tv": scene_tv, "jet": scene_jet,
          "rocket": scene_rocket, "skyline": scene_skyline,
          "factory": scene_factory, "ballot": scene_ballot,
          "bank": scene_bank}


def paste_lead_art(img, path, box):
    """Center-crop the 3:1 asset to the box aspect and paste it."""
    x, y, w, h = box
    src = Image.open(os.path.join(HERE, path)).convert("RGB")
    sw, sh = src.size
    target = w / h
    have = sw / sh
    if have > target:
        cw = int(sh * target)
        src = src.crop(((sw - cw) // 2, 0, (sw - cw) // 2 + cw, sh))
    else:
        ch = int(sw / target)
        src = src.crop((0, (sh - ch) // 2, sw, (sh - ch) // 2 + ch))
    src = src.resize((w, h), Image.LANCZOS)
    img.paste(src, (x, y))
    d = ImageDraw.Draw(img)
    d.rectangle([x, y, x + w - 1, y + h - 1], outline=(40, 40, 40), width=1)

# ---------------------------------------------------------------- map
def render_map(img, items, box):
    """Draw the world map with pins for the 13 illustrated items only."""
    x0, y0, w, h = box
    ss = 2
    m = Image.new("RGB", (w * ss, h * ss), SEA)
    md = ImageDraw.Draw(m)
    lat_top, lat_bot = 78.0, -58.0

    def proj(lon, lat):
        px = (lon + 180.0) / 360.0 * w * ss
        py = (lat_top - lat) / (lat_top - lat_bot) * h * ss
        return px, py

    for poly in CONTINENTS:
        md.polygon([proj(lon, lat) for lon, lat in poly], fill=LAND)
    m = m.resize((w, h), Image.LANCZOS)
    img.paste(m, (x0, y0))
    d = ImageDraw.Draw(img)
    d.rectangle([x0, y0, x0 + w - 1, y0 + h - 1], outline=(120, 120, 115), width=1)

    pts = []
    for it in items:
        px = x0 + (it["lon"] + 180.0) / 360.0 * w
        py = y0 + (lat_top - it["lat"]) / (lat_top - lat_bot) * h
        pts.append([it["n"], px, py, it["n"] <= 3])
    pts.sort(key=lambda p: p[1])
    placed = []
    for n, px, py, lead in pts:
        nx, ny = px, py
        for _ in range(6):
            clash = [q for q in placed
                     if abs(q[0] - nx) < 21 and abs(q[1] - ny) < 15]
            if not clash:
                break
            nx += 21 if nx < x0 + w - 24 else -21
        if (nx, ny) != (px, py):
            d.line([px, py, nx, ny], fill=(90, 90, 86), width=1)
        placed.append((nx, ny))
        r = 10
        if lead:
            d.ellipse([nx - r - 3, ny - r - 3, nx + r + 3, ny + r + 3],
                      fill=GOLD, outline=(255, 255, 255), width=1)
        d.ellipse([nx - r, ny - r, nx + r, ny + r], fill=RED,
                  outline=(255, 255, 255), width=2)
        tw = F_PIN.getlength(str(n))
        d.text((nx - tw / 2, ny - 6), str(n), font=F_PIN, fill=(255, 255, 255))


# ---------------------------------------------------------------- render
def render(data):
    global OVERFLOWS
    img = Image.new("RGB", (W, H), PAPER)
    d = ImageDraw.Draw(img)
    MX = 14
    CW = W - 2 * MX

    # masthead
    y = 6
    tw = F_MAST.getlength(data["masthead"])
    d.text(((W - tw) / 2, y), data["masthead"], font=F_MAST, fill=INK)
    y += 42
    tw = F_DATE.getlength(data["dateline"])
    d.text(((W - tw) / 2, y), data["dateline"], font=F_DATE, fill=INK)
    y += 18
    tw = F_STRAP.getlength(data["strapline"])
    d.text(((W - tw) / 2, y), data["strapline"], font=F_STRAP, fill=GREY)
    y += 15
    d.line([MX, y, W - MX, y], fill=RULE, width=2)
    y += 5

    # chips: region + field counts, computed from the stories
    all_items = data["leads"] + data["cards"] + data["briefs"]
    regions = counts(all_items, "region")
    fields = counts(all_items, "field")
    region_order = ["East Asia", "Europe", "Americas", "SE Asia",
                    "Middle East", "Africa", "South Asia", "Oceania"]
    field_order = ["Markets", "Politics", "Sport", "Rates", "Trade",
                   "Conflict", "Energy", "Weather"]
    for order, cmap in ((region_order, regions), (field_order, fields)):
        parts = [f"{k.upper()} {cmap[k]}" for k in order if k in cmap]
        line = " · ".join(parts)
        d.text((MX, y), line, font=F_CHIP, fill=INK)
        y += 11
    y += 2

    # leads
    col_w = 322
    gap = (CW - 3 * col_w) // 2
    lead_top = y
    for i, lead in enumerate(data["leads"]):
        x = MX + i * (col_w + gap)
        paste_lead_art(img, lead["asset"], (x, y, col_w, 112))
        yy = y + 116
        d.text((x, yy), f"{lead['n']}", font=F_LEAD_H, fill=RED)
        nw = F_LEAD_H.getlength(str(lead["n"]))
        d.text((x + nw + 6, yy + 2), f"{lead['city']} · {lead['field'].upper()}",
               font=F_CHIP, fill=GREY)
        bw = badge(d, x + col_w - 62, yy + 1, lead["badge"])
        yy += 20
        _, yy = draw_wrapped(d, x, yy, lead["headline"], F_LEAD_H, col_w, 2)
        _, yy = draw_wrapped(d, x, yy + 1, lead["deck"], F_LEAD_D, col_w, 3,
                             fill=(60, 60, 58))
        d.text((x, yy + 1), "SOURCE: " + lead["source"], font=F_SRC, fill=GREY)
    y = lead_top + 206

    # stat strip
    d.rectangle([MX, y, W - MX, y + 38], fill=NAVY)
    stats = data["stats"]
    sw = CW // len(stats)
    for i, s in enumerate(stats):
        cx = MX + i * sw + sw // 2
        vw = F_STAT_V.getlength(s["value"])
        d.text((cx - vw / 2, y + 5), s["value"], font=F_STAT_V,
               fill=(255, 255, 255))
        lw = F_STAT_L.getlength(s["label"])
        d.text((cx - lw / 2, y + 28), s["label"], font=F_STAT_L,
               fill=(190, 200, 215))
    y += 46

    # cards: 2 rows x 5
    card_w = 195
    card_gap = (CW - 5 * card_w) // 4
    for ri in range(2):
        for ci in range(5):
            card = data["cards"][ri * 5 + ci]
            x = MX + ci * (card_w + card_gap)
            cy = y + ri * 106
            SCENES[card["scene"]](d, x, cy, card_w, 44)
            d.rectangle([x, cy, x + card_w - 1, cy + 43], outline=(40, 40, 40),
                        width=1)
            bw = badge(d, x + card_w - 58, cy + 2, card["badge"])
            yy = cy + 47
            d.text((x, yy), f"{card['n']}", font=F_CARD_H, fill=RED)
            nw = F_CARD_H.getlength(str(card["n"]))
            d.text((x + nw + 4, yy + 1),
                   f"{card['city']} · {card['field'].upper()}",
                   font=F_CHIP, fill=GREY)
            yy += 15
            _, yy = draw_wrapped(d, x, yy, card["headline"], F_CARD_H,
                                 card_w, 2, leading=1)
            _, yy = draw_wrapped(d, x, yy, card["deck"], F_CARD_D,
                                 card_w, 2, leading=0, fill=(60, 60, 58))
    y += 212

    # timeline
    d.text((MX, y), "THE DAY IN UTC", font=F_TL_T, fill=RED)
    tl = data["timeline"]
    tw4 = CW // 4
    for i, m in enumerate(tl):
        col, row = i % 4, i // 4
        x = MX + col * tw4
        yy = y + 2 + row * 13
        d.text((x, yy), m["time"], font=F_TL_T, fill=RED)
        tw_ = F_TL_T.getlength(m["time"])
        d.text((x + tw_ + 5, yy), m["text"], font=F_TL_X, fill=INK)
    y += 28

    # map (pins 1-13 only) + caption
    d.text((MX, y), "WHERE IT HAPPENED — PINS 1–13",
           font=F_TL_T, fill=INK)
    d.text((MX + 260, y), "gold rings are the three leads",
           font=F_TL_X, fill=GREY)
    y += 14
    render_map(img, data["leads"] + data["cards"], (MX, y, CW, 120))
    y += 128

    # briefs: 2 columns x 16, one line each
    d.text((MX, y), "ALSO ON FRIDAY 27 NOVEMBER 2026 — STORIES 14–45",
           font=F_TL_T, fill=INK)
    y += 14
    col_w2 = CW // 2
    for i, b in enumerate(data["briefs"]):
        col, row = i // 16, i % 16
        x = MX + col * col_w2
        yy = y + row * 11
        d.text((x, yy), str(b["n"]), font=F_BRIEF_B, fill=RED)
        nw = F_BRIEF_B.getlength(str(b["n"]))
        head = f"{b['city']} — {b['text']}"
        bw = badge(d, x + col_w2 - 56, yy, b["badge"])
        _, _ = draw_wrapped(d, x + nw + 4, yy, head, F_BRIEF,
                            col_w2 - nw - 66, 1)
    y += 16 * 11 + 2

    # date check
    d.rectangle([MX, y, W - MX, y + 1], fill=RULE)
    y += 5
    d.text((MX, y), "DATE CHECK — THESE ARE NOT 27 NOVEMBER",
           font=F_DC_T, fill=RED)
    y += 13
    _, y = draw_wrapped(d, MX, y, data["date_check"]["included"], F_DC,
                        CW, 1)
    _, y = draw_wrapped(d, MX, y, data["date_check"]["excluded"], F_DC,
                        CW, 2)
    _, y = draw_wrapped(d, MX, y, data["date_check"]["not_yet"], F_DC,
                        CW, 1)
    y += 2
    _, y = draw_wrapped(d, MX, y, data["sources"] + " " + data["legend"],
                        F_DC, CW, 2, fill=GREY)
    if y > H:
        OVERFLOWS += 1
    return img, y


def main():
    with open(os.path.join(HERE, "stories.json"), encoding="utf-8") as f:
        data = json.load(f)
    n = len(data["leads"]) + len(data["cards"]) + len(data["briefs"])
    img, bottom = render(data)
    img.save(os.path.join(HERE, "entry.png"), optimize=True)
    size = os.path.getsize(os.path.join(HERE, "entry.png"))
    print(f"stories: {n} = {len(data['leads'])} leads + "
          f"{len(data['cards'])} cards + {len(data['briefs'])} briefs")
    print(f"bottom y: {bottom} (canvas {H})")
    print(f"trims: {TRIMS} overflows: {OVERFLOWS}")
    print(f"entry.png: {size} bytes")
    if size > 1048576:
        print("OVER 1 MiB LIMIT")
    if TRIMS or OVERFLOWS:
        print("LAYOUT NOT CLEAN")


if __name__ == "__main__":
    main()
