#!/usr/bin/env python3
"""Render entry.png (1024x1024) for news-image-20261127 from stories.json.

Fresh build for the 27 November 2026 edition. Deterministic: no network,
no randomness, fixed fonts. Run: python3 draw.py  -> writes entry.png
and prints a layout report (trims / overflows must be 0).
"""
import json
import math
import os
import sys

from PIL import Image, ImageDraw, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
DATA = json.load(open(os.path.join(HERE, "stories.json"), encoding="utf-8"))

W, H = 1024, 1024
PAPER = (246, 241, 231)
INK = (32, 36, 46)
NAVY = (30, 58, 95)
RED = (179, 64, 47)
GOLD = (197, 146, 44)
TAN = (221, 210, 184)
TAN_DK = (201, 185, 143)
CARD = (255, 253, 246)
CARD_BD = (216, 205, 180)
MUTED = (96, 92, 82)

FDIR = "/usr/share/fonts/truetype/dejavu"


def font(name, size):
    return ImageFont.truetype(os.path.join(FDIR, name), size)


F_SERIF = lambda s: font("DejaVuSerif-Bold.ttf", s)
F_SANS = lambda s: font("DejaVuSans.ttf", s)
F_SANSB = lambda s: font("DejaVuSans-Bold.ttf", s)

report = {"trims": [], "overflows": []}


def wrap(draw, text, fnt, max_w):
    """Greedy wrap; returns list of lines."""
    words = text.split()
    lines, cur = [], ""
    for w in words:
        trial = (cur + " " + w).strip()
        if draw.textlength(trial, font=fnt) <= max_w:
            cur = trial
        else:
            if cur:
                lines.append(cur)
            cur = w
    if cur:
        lines.append(cur)
    return lines


def fit_lines(draw, text, fnt, max_w, max_lines, tag):
    """Wrap to max_lines; if it still does not fit, trim words and record."""
    lines = wrap(draw, text, fnt, max_w)
    if len(lines) > max_lines:
        report["trims"].append(tag)
        flat = text.split()
        while len(wrap(draw, " ".join(flat) + " …", fnt, max_w)) > max_lines and len(flat) > 4:
            flat = flat[:-1]
        lines = wrap(draw, " ".join(flat) + " …", fnt, max_w)[:max_lines]
    return lines


def draw_text(draw, xy, lines, fnt, fill, leading):
    x, y = xy
    for ln in lines:
        draw.text((x, y), ln, font=fnt, fill=fill)
        y += leading
    return y


# ---------------------------------------------------------------- continents
# Coarse lon/lat outlines, good enough at map scale.
CONTINENTS = [
    # North America
    [(-168, 66), (-158, 58), (-140, 60), (-130, 54), (-125, 49), (-124, 42),
     (-120, 34), (-114, 29), (-110, 24), (-105, 20), (-97, 16), (-92, 15),
     (-86, 12), (-83, 9), (-79, 9), (-81, 13), (-84, 16), (-87, 21),
     (-90, 21), (-97, 26), (-93, 30), (-89, 30), (-84, 30), (-81, 25),
     (-80, 32), (-76, 35), (-74, 40), (-70, 42), (-68, 45), (-65, 44),
     (-60, 47), (-55, 52), (-60, 55), (-65, 60), (-68, 58), (-78, 62),
     (-85, 66), (-95, 69), (-110, 68), (-125, 70), (-140, 70), (-155, 71),
     (-165, 68)],
    # Greenland
    [(-58, 64), (-52, 60), (-43, 60), (-40, 64), (-32, 68), (-22, 70),
     (-20, 74), (-25, 76), (-35, 77), (-50, 76), (-58, 74), (-60, 70)],
    # South America
    [(-79, 9), (-77, 4), (-80, -3), (-81, -6), (-77, -12), (-72, -18),
     (-70, -23), (-70, -30), (-72, -37), (-73, -44), (-74, -50), (-70, -54),
     (-66, -55), (-68, -50), (-65, -45), (-62, -41), (-58, -35), (-52, -32),
     (-48, -28), (-41, -23), (-35, -9), (-35, -6), (-40, -3), (-44, -2),
     (-50, 0), (-53, 4), (-58, 6), (-62, 9), (-68, 11), (-72, 12), (-75, 10)],
    # Africa
    [(-6, 35), (-10, 31), (-15, 27), (-17, 21), (-17, 15), (-15, 11),
     (-12, 8), (-8, 5), (-4, 5), (0, 6), (6, 4), (9, 4), (9, 0), (12, -5),
     (13, -10), (12, -17), (14, -22), (16, -28), (19, -34), (26, -34),
     (32, -29), (35, -24), (40, -16), (40, -10), (42, -4), (46, 0),
     (51, 11), (48, 11), (44, 11), (40, 15), (38, 18), (35, 22), (32, 27),
     (30, 31), (25, 32), (19, 33), (11, 34), (10, 37), (5, 37), (-1, 35)],
    # Eurasia (Europe + Asia, one mass)
    [(-10, 36), (-9, 43), (-2, 44), (-1, 46), (-4, 48), (-2, 50), (0, 51),
     (3, 53), (5, 53), (8, 55), (8, 57), (10, 59), (5, 60), (5, 62),
     (10, 64), (12, 66), (18, 69), (25, 71), (30, 70), (40, 68), (50, 69),
     (60, 69), (68, 72), (75, 73), (85, 75), (95, 76), (105, 77),
     (115, 74), (125, 73), (135, 72), (145, 72), (155, 70), (162, 69),
     (170, 66), (178, 65), (178, 62), (170, 60), (162, 60), (158, 56),
     (156, 51), (150, 59), (142, 59), (142, 54), (140, 48), (138, 44),
     (135, 43), (132, 43), (130, 42), (127, 40), (126, 38), (122, 37),
     (120, 32), (121, 28), (118, 25), (113, 22), (109, 20), (108, 18),
     (106, 10), (104, 9), (101, 7), (99, 6), (98, 10), (97, 16), (94, 17),
     (92, 21), (89, 22), (86, 20), (83, 18), (80, 15), (78, 8), (76, 10),
     (73, 16), (72, 20), (70, 21), (67, 25), (62, 25), (58, 24), (56, 26),
     (54, 27), (52, 27), (50, 29), (48, 30), (48, 27), (50, 26), (52, 25),
     (55, 25), (57, 26), (59, 23), (58, 21), (55, 18), (52, 16), (49, 14),
     (45, 13), (43, 12), (41, 15), (39, 20), (39, 22), (36, 26), (35, 29),
     (35, 31), (34, 31), (36, 36), (33, 36), (30, 36), (28, 37), (27, 37),
     (26, 38), (23, 36), (23, 40), (20, 40), (19, 42), (16, 41), (14, 42),
     (12, 44), (10, 44), (8, 44), (6, 43), (3, 43), (0, 40), (-2, 37),
     (-6, 36)],
    # United Kingdom
    [(-5, 50), (-3, 53), (-5, 56), (-3, 58), (-1, 57), (0, 53), (1, 51)],
    # Japan
    [(130, 31), (131, 33), (133, 34), (135, 34), (137, 35), (139, 35),
     (140, 37), (141, 39), (141, 41), (143, 42), (145, 44), (142, 44),
     (140, 42), (139, 39), (137, 37), (134, 35), (132, 33)],
    # Australia
    [(114, -22), (114, -30), (115, -33), (118, -35), (124, -33), (129, -32),
     (132, -32), (135, -35), (138, -35), (140, -38), (144, -38), (147, -39),
     (150, -37), (153, -32), (153, -27), (150, -23), (146, -19), (142, -11),
     (137, -12), (135, -15), (132, -12), (129, -15), (126, -14), (122, -17),
     (118, -20)],
    # New Zealand
    [(167, -45), (168, -44), (170, -42), (173, -41), (175, -38), (177, -38),
     (178, -37), (175, -40), (172, -43), (169, -46)],
    # Borneo / Sumatra / Java / New Guinea (rough blobs)
    [(109, 1), (111, 2), (114, 4), (117, 6), (119, 1), (117, -3), (114, -3),
     (110, -2)],
    [(95, 5), (98, 3), (100, 0), (102, -3), (104, -5), (106, -6),
     (104, -4), (101, 0), (98, 4)],
    [(105, -6), (108, -7), (112, -7), (114, -8), (111, -8), (107, -7)],
    [(131, -1), (136, -2), (138, -4), (141, -5), (141, -8), (137, -8),
     (134, -5), (132, -2)],
]


def project(lon, lat, box):
    x0, y0, x1, y1 = box
    x = x0 + (lon + 168.0) / 360.0 * (x1 - x0)
    y = y0 + (85.0 - lat) / 145.0 * (y1 - y0)
    return x, y


# ---------------------------------------------------------------- art panels
def art_cpi(d, box):
    x0, y0, x1, y1 = box
    d.rectangle(box, fill=(232, 222, 198))
    base = y1 - 18
    top = y0 + 14
    # target line 2.0% (scale 0..3.2%)
    def val_y(v):
        return base - (v / 3.2) * (base - top)
    d.line([(x0 + 8, base), (x1 - 8, base)], fill=INK, width=2)
    bw = 52
    for i, (lab, v, col) in enumerate([("OCT", 2.6, NAVY), ("NOV", 2.9, RED)]):
        bx = x0 + 48 + i * 108
        d.rectangle([bx, val_y(v), bx + bw, base], fill=col)
        d.text((bx + 4, val_y(v) - 15), f"{v}%", font=F_SANSB(13), fill=INK)
        d.text((bx + 8, base + 3), lab, font=F_SANSB(10), fill=INK)
    d.line([(x0 + 8, val_y(2.0)), (x1 - 8, val_y(2.0))], fill=RED, width=2)
    lab = "BOJ TARGET 2%"
    d.text((x1 - 8 - d.textlength(lab, font=F_SANSB(9)), val_y(2.0) - 13),
           lab, font=F_SANSB(9), fill=RED)


def art_f1(d, box):
    x0, y0, x1, y1 = box
    d.rectangle(box, fill=(214, 228, 238))
    # floodlights
    for fx in (x0 + 40, x0 + 150, x0 + 260):
        d.line([(fx, y0 + 12), (fx, y0 + 58)], fill=(90, 100, 112), width=3)
        d.ellipse([fx - 9, y0 + 6, fx + 9, y0 + 20], fill=(250, 244, 200))
    # track
    d.rectangle([x0, y1 - 34, x1, y1], fill=(70, 76, 88))
    d.line([(x0, y1 - 34), (x1, y1 - 34)], fill=(255, 255, 255), width=2)
    for cx in range(x0 + 20, x1 - 10, 46):
        d.rectangle([cx, y1 - 19, cx + 22, y1 - 15], fill=(255, 255, 255))
    # car body (side profile, pointing right)
    cy = y1 - 52
    d.polygon([(x0 + 55, cy), (x0 + 205, cy - 4), (x0 + 250, cy + 10),
               (x0 + 245, cy + 16), (x0 + 60, cy + 16)], fill=(178, 34, 34))
    d.polygon([(x0 + 120, cy - 2), (x0 + 165, cy - 2), (x0 + 175, cy - 12),
               (x0 + 135, cy - 12)], fill=(40, 44, 54))  # cockpit
    d.rectangle([x0 + 228, cy - 14, x0 + 254, cy - 8], fill=(40, 44, 54))  # wing
    d.rectangle([x0 + 240, cy - 8, x0 + 244, cy + 2], fill=(40, 44, 54))  # strut
    d.rectangle([x0 + 52, cy + 2, x0 + 60, cy + 16], fill=(40, 44, 54))  # nose
    for wx in (x0 + 88, x0 + 205):
        d.ellipse([wx - 15, cy + 4, wx + 15, cy + 34], fill=(20, 20, 24))
        d.ellipse([wx - 7, cy + 12, wx + 7, cy + 26], fill=(180, 180, 190))


def art_shop(d, box):
    x0, y0, x1, y1 = box
    d.rectangle(box, fill=(238, 226, 205))
    # storefront
    d.rectangle([x0 + 30, y0 + 34, x1 - 30, y1 - 12], fill=(250, 247, 238))
    d.rectangle([x0 + 30, y0 + 34, x1 - 30, y0 + 52], fill=RED)
    d.text((x0 + 42, y0 + 37), "SALE", font=F_SANSB(13), fill=(255, 255, 255))
    for i in range(7):
        ax = x0 + 30 + i * 38
        d.polygon([(ax, y0 + 52), (ax + 19, y0 + 52), (ax + 19, y0 + 64),
                   (ax, y0 + 64)], fill=(255, 255, 255) if i % 2 == 0 else RED)
    d.rectangle([x0 + 130, y0 + 74, x1 - 130, y1 - 12], fill=(60, 70, 90))
    # price tags
    for i, (tx, lab) in enumerate([(x0 + 48, "-50%"), (x0 + 240, "$1,000")]):
        d.polygon([(tx, y0 + 74), (tx + 46, y0 + 74), (tx + 46, y0 + 92),
                   (tx, y0 + 92)], fill=GOLD)
        d.text((tx + 4, y0 + 77), lab, font=F_SANSB(10), fill=(255, 255, 255))
    # queue of shoppers (dots + bodies)
    for i in range(5):
        qx = x0 + 60 + i * 44
        qy = y1 - 22
        d.ellipse([qx - 6, qy - 26, qx + 6, qy - 14], fill=(60, 60, 70))
        d.rectangle([qx - 7, qy - 14, qx + 7, qy], fill=[NAVY, RED, GOLD, (46, 120, 80), (120, 60, 110)][i])


ART = {"cpi": art_cpi, "f1": art_f1, "shop": art_shop}

# ---------------------------------------------------------------- main render
def render():
    img = Image.new("RGB", (W, H), PAPER)
    d = ImageDraw.Draw(img)
    MX = 14  # outer margin
    CW = W - 2 * MX  # 996

    # ---- masthead
    y = 12
    d.text((MX, y), DATA["dateline"], font=F_SANSB(13), fill=NAVY)
    r = DATA["dateline_right"]
    d.text((W - MX - d.textlength(r, font=F_SANSB(13)), y), r,
           font=F_SANSB(13), fill=RED)
    y += 22
    d.text((MX, y), DATA["date"], font=F_SERIF(40), fill=INK)
    pn = DATA["paper"]
    d.text((W - MX - d.textlength(pn, font=F_SANSB(13)), y + 16), pn,
           font=F_SANSB(13), fill=MUTED)
    y += 52
    d.line([(MX, y), (W - MX, y)], fill=INK, width=2)
    y += 8

    # ---- chips: regions then fields
    regions = {}
    fields = {}
    for b in DATA["briefs"]:
        regions[b["region"]] = regions.get(b["region"], 0) + 1
        fields[b["field"]] = fields.get(b["field"], 0) + 1
    for lead in DATA["leads"]:
        regions[lead["region"]] = regions.get(lead["region"], 0) + 1
        fields[lead["field"]] = fields.get(lead["field"], 0) + 1
    reg_order = ["EAST ASIA", "EUROPE", "AMERICAS", "SE ASIA",
                 "MIDDLE EAST", "AFRICA", "SOUTH ASIA", "OCEANIA"]
    fld_order = ["MARKETS", "SPORT", "POLITICS", "TECH", "TRADE",
                 "CONFLICT", "WEATHER", "RATES", "ENERGY"]
    reg_line = "  ·  ".join(f"{r} {regions.get(r, 0)}" for r in reg_order)
    fld_line = "  ·  ".join(f"{f} {fields.get(f, 0)}" for f in fld_order)
    d.text((MX, y), reg_line, font=F_SANSB(11), fill=NAVY)
    y += 16
    d.text((MX, y), fld_line, font=F_SANSB(11), fill=NAVY)
    y += 20

    # ---- three leads
    lead_y = y
    lead_h = 224
    lead_w = (CW - 2 * 14) // 3
    for i, lead in enumerate(DATA["leads"]):
        x0 = MX + i * (lead_w + 14)
        x1 = x0 + lead_w
        d.rectangle([x0, lead_y, x1, lead_y + lead_h], fill=CARD,
                    outline=CARD_BD, width=1)
        art_box = (x0 + 6, lead_y + 6, x1 - 6, lead_y + 104)
        ART[lead["art"]](d, art_box)
        ty = lead_y + 110
        # badge chip
        badge = lead["badge"]
        bcol = {"OFFICIAL": (34, 110, 60), "REPORTED": NAVY,
                "CLAIM": (150, 90, 20)}[badge]
        bw = d.textlength(badge, font=F_SANSB(9)) + 10
        d.rectangle([x0 + 8, ty, x0 + 8 + bw, ty + 14], fill=bcol)
        d.text((x0 + 13, ty + 2), badge, font=F_SANSB(9), fill=(255, 255, 255))
        kick = f"{lead['city']} · {lead['field']}"
        d.text((x0 + 8 + bw + 6, ty + 2), kick, font=F_SANSB(10), fill=RED)
        ty += 19
        hl = fit_lines(d, lead["headline"], F_SANSB(16), lead_w - 16, 3,
                       "lead-" + lead["id"])
        ty = draw_text(d, (x0 + 8, ty), hl, F_SANSB(16), INK, 19)
        ty += 3
        dk = fit_lines(d, lead["deck"], F_SANS(11), lead_w - 16, 3,
                       "lead-" + lead["id"] + "-deck")
        draw_text(d, (x0 + 8, ty), dk, F_SANS(11), (60, 58, 52), 14)
    y = lead_y + lead_h + 10

    # ---- stat strip
    stat_y = y
    stat_h = 50
    d.rectangle([MX, stat_y, W - MX, stat_y + stat_h], fill=NAVY)
    d.text((MX + 10, stat_y + 6), "BY THE", font=F_SANSB(10), fill=(180, 195, 220))
    d.text((MX + 10, stat_y + 20), "NUMBERS", font=F_SANSB(10), fill=(180, 195, 220))
    stats = DATA["stats"]
    col_w = (CW - 120) // len(stats)
    for i, st in enumerate(stats):
        cx = MX + 120 + i * col_w
        d.text((cx, stat_y + 5), st["big"], font=F_SANSB(19), fill=(255, 255, 255))
        lab = fit_lines(d, st["label"], F_SANS(9), col_w - 8, 2, "stat-" + str(i))
        draw_text(d, (cx, stat_y + 28), lab, F_SANS(9), (180, 195, 220), 11)
    y = stat_y + stat_h + 8

    # ---- map
    map_label_y = y
    d.text((MX, map_label_y), "WHERE IT HAPPENED", font=F_SANSB(12), fill=NAVY)
    d.text((MX + 190, map_label_y + 1),
           "numbered dots match the list below · gold stars are the three leads",
           font=F_SANS(10), fill=MUTED)
    map_box = (MX, map_label_y + 18, W - MX, map_label_y + 150)
    d.rectangle(map_box, fill=(238, 231, 214), outline=CARD_BD, width=1)
    for poly in CONTINENTS:
        pts = [project(lon, lat, map_box) for lon, lat in poly]
        d.polygon(pts, fill=TAN, outline=TAN_DK)
    # dots: jitter duplicates on a deterministic ring
    seen = {}
    items = [(b["n"], b["lat"], b["lon"]) for b in DATA["briefs"]]
    for n, lat, lon in items:
        key = (round(lat, 1), round(lon, 1))
        k = seen.get(key, 0)
        seen[key] = k + 1
        cx, cy = project(lon, lat, map_box)
        if k:
            ang = k * 2.399963  # golden angle
            rad = 8 + 3.5 * k
            cx += rad * math.cos(ang)
            cy += rad * math.sin(ang) * 0.8
        r = 7
        d.ellipse([cx - r, cy - r, cx + r, cy + r], fill=RED,
                  outline=(255, 255, 255), width=1)
        t = str(n)
        tw = d.textlength(t, font=F_SANSB(8))
        d.text((cx - tw / 2, cy - 5), t, font=F_SANSB(8), fill=(255, 255, 255))
    for lead in DATA["leads"]:
        cx, cy = project(lead["lon"], lead["lat"], map_box)
        s = 9
        star = [(cx, cy - s), (cx + 2.6, cy - 2.6), (cx + s, cy), (cx + 2.6, cy + 2.6),
                (cx, cy + s), (cx - 2.6, cy + 2.6), (cx - s, cy), (cx - 2.6, cy - 2.6)]
        d.polygon(star, fill=GOLD, outline=(255, 255, 255))
    y = map_box[3] + 8

    # ---- brief list: 3 columns x 14 rows, one line each
    list_y = y
    cols = 3
    rows = 14
    col_w = (CW - 2 * 14) // 3
    row_h = 23
    for idx, b in enumerate(DATA["briefs"]):
        col = idx // rows
        row = idx % rows
        x0 = MX + col * (col_w + 14)
        yy = list_y + row * row_h
        # number badge
        r = 7
        cx, cy = x0 + r, yy + r + 1
        d.ellipse([cx - r, cy - r, cx + r, cy + r], fill=RED)
        t = str(b["n"])
        tw = d.textlength(t, font=F_SANSB(8))
        d.text((cx - tw / 2, cy - 5), t, font=F_SANSB(8), fill=(255, 255, 255))
        line = f"{b['city']} — {b['text']}"
        max_w = col_w - 20
        if d.textlength(line, font=F_SANS(11)) > max_w:
            report["overflows"].append(f"brief-{b['n']}")
            while d.textlength(line + "…", font=F_SANS(11)) > max_w and len(line) > 12:
                line = line[:-1]
            line = line.rstrip() + "…"
        d.text((x0 + 18, yy + 2), line, font=F_SANS(11), fill=INK)
    y = list_y + rows * row_h + 6

    # ---- timeline
    tl_y = y
    d.line([(MX, tl_y), (W - MX, tl_y)], fill=INK, width=1)
    tl_y += 5
    d.text((MX, tl_y), "THE DAY IN UTC", font=F_SANSB(11), fill=NAVY)
    tl = DATA["timeline"]
    per_row = 5
    tw_col = (CW - 150) // per_row
    for i, ev in enumerate(tl):
        row = i // per_row
        col = i % per_row
        ex = MX + 150 + col * tw_col
        ey = tl_y + row * 14
        d.text((ex, ey), ev["time"], font=F_SANSB(10), fill=RED)
        txt = ev["text"]
        if d.textlength(txt, font=F_SANS(10)) > tw_col - 42:
            report["overflows"].append("timeline-" + ev["time"])
            while d.textlength(txt + "…", font=F_SANS(10)) > tw_col - 42 and len(txt) > 8:
                txt = txt[:-1]
            txt = txt.rstrip() + "…"
        d.text((ex + 40, ey), txt, font=F_SANS(10), fill=INK)
    y = tl_y + 2 * 14 + 6

    # ---- footer: date check + sources
    d.line([(MX, y), (W - MX, y)], fill=INK, width=1)
    y += 5
    dc = fit_lines(d, DATA["datecheck"], F_SANS(9), CW, 2, "datecheck")
    y = draw_text(d, (MX, y), dc, F_SANS(9), (60, 58, 52), 12)
    lg = fit_lines(d, DATA["legend"], F_SANS(9), CW, 1, "legend")
    y = draw_text(d, (MX, y), lg, F_SANS(9), MUTED, 12)
    src = fit_lines(d, DATA["sources"], F_SANS(9), CW, 1, "sources")
    y = draw_text(d, (MX, y), src, F_SANS(9), MUTED, 12)
    if y > H - 4:
        report["overflows"].append(f"footer-bottom y={y}")

    out = os.path.join(HERE, "entry.png")
    img.save(out, format="PNG")
    return out


if __name__ == "__main__":
    path = render()
    import hashlib
    raw = open(path, "rb").read()
    im = Image.open(path)
    print(f"wrote {path}: {len(raw)} bytes, {im.size}, sha256 "
          f"{hashlib.sha256(raw).hexdigest()}")
    print(f"stories: {len(DATA['briefs'])} briefs + {len(DATA['leads'])} leads "
          f"= {len(DATA['briefs']) + len(DATA['leads'])}")
    print(f"trims: {len(report['trims'])} {report['trims']}")
    print(f"overflows: {len(report['overflows'])} {report['overflows']}")
    sys.exit(1 if report["overflows"] else 0)
