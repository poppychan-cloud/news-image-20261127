#!/usr/bin/env python3
"""Render news-image-20261127 V3: photorealistic-lead newspaper, 1024x1024.

Reads stories.json + 3 ChatGPT lead photos from assets/. Deterministic:
no clock, no randomness, no network. Prints TRIM/OVERFLOW report.
"""
import json
import os
import sys
from PIL import Image, ImageDraw, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
W, H = 1024, 1024

SERIF_B = "/usr/share/fonts/truetype/dejavu/DejaVuSerif-Bold.ttf"
SANS = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"
SANS_B = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"

PAPER = (246, 241, 231)
INK = (26, 26, 26)
NAVY = (20, 33, 61)
NAVY_LT = (31, 52, 92)
GOLD = (176, 141, 55)
GOLD_LT = (201, 162, 74)
GREY = (110, 108, 100)
LINE = (180, 172, 150)
CARD_BG = (255, 255, 255)
OCEAN = (216, 230, 240)
LAND = (231, 220, 195)
LAND_EDGE = (150, 134, 102)

BADGE = {
    "OFFICIAL": (31, 78, 121),
    "REPORTED": (14, 124, 123),
    "CONFIRMED": (46, 125, 50),
    "CLAIM": (178, 106, 0),
    "ONGOING": (163, 22, 33),
}

TRIMS = 0
OVERFLOWS = 0


def font(path, size):
    return ImageFont.truetype(path, size)


def text_w(draw, s, f):
    return draw.textlength(s, font=f)


def wrap(draw, text, f, max_w, max_lines):
    """Greedy wrap. Returns (lines, trimmed_bool)."""
    global TRIMS
    words = text.split()
    lines, cur = [], ""
    for w_ in words:
        trial = (cur + " " + w_).strip()
        if text_w(draw, trial, f) <= max_w or not cur:
            cur = trial
        else:
            lines.append(cur)
            cur = w_
    if cur:
        lines.append(cur)
    trimmed = False
    if len(lines) > max_lines:
        lines = lines[:max_lines]
        trimmed = True
        while lines and text_w(draw, lines[-1] + "…", f) > max_w:
            lines[-1] = lines[-1][:-1]
        lines[-1] = lines[-1].rstrip() + "…"
    if trimmed:
        TRIMS += 1
        print(f"TRIM: {text!r} -> {lines[-1]!r}", file=sys.stderr)
    return lines, trimmed


def fit_text(draw, text, f, max_w, max_lines):
    lines, _ = wrap(draw, text, f, max_w, max_lines)
    return lines


def draw_lines(draw, lines, x, y, f, fill, lh):
    for ln in lines:
        draw.text((x, y), ln, font=f, fill=fill)
        y += lh
    return y


def check_y(y, what):
    global OVERFLOWS
    if y > H:
        OVERFLOWS += 1
        print(f"OVERFLOW: {what} ends at y={y}", file=sys.stderr)


# ---------------------------------------------------------------- continents
# Hand-authored coarse outlines (lon, lat). Stylised newspaper map.
N_AMERICA = [(-168, 66), (-158, 58), (-152, 60), (-140, 60), (-135, 57),
             (-130, 54), (-125, 49), (-124, 42), (-120, 34), (-114, 29),
             (-110, 24), (-105, 20), (-97, 16), (-92, 15), (-86, 13),
             (-83, 9), (-79, 9), (-81, 13), (-83, 16), (-87, 21), (-90, 21),
             (-91, 19), (-96, 19), (-97, 26), (-93, 30), (-89, 30),
             (-84, 30), (-81, 26), (-80, 32), (-75, 36), (-73, 41),
             (-70, 42), (-68, 45), (-65, 44), (-60, 47), (-55, 52),
             (-60, 55), (-65, 58), (-68, 55), (-72, 58), (-78, 62),
             (-85, 66), (-90, 68), (-95, 69), (-110, 68), (-125, 70),
             (-140, 70), (-155, 71), (-165, 68), (-168, 66)]
GREENLAND = [(-58, 64), (-52, 60), (-45, 60), (-40, 65), (-32, 68),
             (-22, 70), (-20, 74), (-25, 78), (-35, 80), (-50, 80),
             (-58, 76), (-60, 70), (-58, 64)]
S_AMERICA = [(-79, 9), (-77, 4), (-80, -3), (-81, -6), (-77, -12),
             (-72, -18), (-70, -23), (-70, -30), (-72, -37), (-73, -44),
             (-74, -50), (-70, -54), (-66, -55), (-65, -48), (-62, -41),
             (-58, -34), (-52, -32), (-48, -27), (-41, -23), (-39, -17),
             (-35, -9), (-35, -6), (-40, -3), (-44, -2), (-50, 0),
             (-53, 4), (-58, 6), (-62, 9), (-68, 11), (-72, 12),
             (-76, 10), (-79, 9)]
AFRICA = [(-17, 15), (-17, 21), (-15, 27), (-10, 31), (-5, 35), (0, 36),
          (10, 37), (11, 34), (15, 32), (19, 31), (25, 32), (30, 31),
          (32, 31), (34, 28), (35, 24), (37, 20), (39, 18), (43, 12),
          (48, 11), (51, 10), (51, 2), (46, -2), (41, -4), (40, -10),
          (37, -16), (35, -20), (32, -26), (28, -33), (20, -35),
          (17, -32), (15, -27), (13, -18), (12, -10), (13, -4), (9, 0),
          (9, 4), (4, 6), (-2, 5), (-8, 5), (-13, 8), (-17, 12), (-17, 15)]
EURASIA = [(-10, 36), (-9, 43), (-2, 44), (-1, 46), (-4, 48), (-2, 50),
           (0, 51), (3, 53), (8, 57), (10, 59), (5, 60), (5, 62),
           (10, 64), (12, 66), (18, 69), (25, 71), (30, 70), (40, 68),
           (50, 69), (60, 69), (70, 72), (80, 73), (90, 74), (100, 76),
           (110, 74), (120, 73), (130, 72), (140, 72), (150, 70),
           (158, 69), (162, 66), (170, 66), (178, 65), (178, 62),
           (170, 60), (162, 60), (158, 56), (155, 52), (150, 59),
           (142, 55), (140, 50), (135, 45), (130, 42), (128, 39),
           (129, 36), (126, 35), (122, 34), (120, 31), (121, 28),
           (120, 25), (115, 22), (110, 20), (108, 15), (105, 10),
           (104, 6), (104, 2), (104, 1), (102, 2), (101, 5), (100, 8),
           (98, 12), (95, 16), (92, 21), (90, 22), (88, 22), (85, 19),
           (80, 16), (78, 10), (76, 8), (73, 15), (70, 20), (66, 25),
           (60, 26), (58, 28), (54, 29), (50, 30), (46, 31), (42, 31),
           (38, 32), (36, 36), (33, 36), (30, 36), (27, 37), (23, 36),
           (22, 38), (19, 40), (18, 42), (14, 45), (12, 44), (8, 44),
           (3, 43), (0, 40), (-2, 37), (-6, 36), (-9, 37), (-10, 36)]
ARABIA = [(58, 26), (56, 27), (52, 28), (50, 29), (48, 30), (46, 30),
          (42, 31), (39, 31), (36, 32), (35, 30), (37, 27), (38, 24),
          (39, 21), (41, 17), (43, 13), (45, 13), (48, 14), (51, 16),
          (54, 19), (56, 22), (58, 26)]
MED = [(-6, 36), (3, 37), (10, 38), (15, 38), (20, 38), (25, 36),
       (30, 36), (34, 36), (36, 35), (34, 33), (30, 33), (25, 34),
       (20, 36), (15, 38), (10, 38), (5, 37), (0, 37), (-6, 36)]
UK = [(-5, 50), (-3, 53), (-5, 56), (-3, 58), (-1, 57), (0, 53),
      (1, 51), (-5, 50)]
JAPAN = [(130, 31), (132, 33), (134, 34), (136, 35), (138, 35),
         (141, 36), (141, 38), (141, 41), (142, 44), (144, 44),
         (143, 42), (141, 40), (140, 38), (139, 36), (137, 34),
         (135, 33), (132, 32), (130, 31)]
BORNEO = [(109, 1), (111, -1), (114, -3), (117, -2), (119, 1), (118, 4),
          (116, 6), (112, 4), (109, 1)]
SUMATRA = [(95, 5), (98, 3), (101, 0), (104, -3), (106, -5), (104, -6),
           (101, -3), (98, 0), (95, 5)]
NEW_GUINEA = [(131, -1), (134, -3), (137, -5), (141, -6), (145, -7),
              (148, -9), (150, -10), (146, -8), (142, -8), (138, -7),
              (135, -4), (131, -1)]
MADAGASCAR = [(44, -16), (47, -15), (50, -17), (49, -21), (46, -25),
              (44, -23), (43, -19), (44, -16)]
AUSTRALIA = [(114, -22), (114, -30), (115, -34), (118, -35), (124, -33),
             (129, -32), (132, -32), (135, -35), (138, -35), (140, -38),
             (145, -38), (150, -37), (153, -32), (153, -27), (150, -23),
             (146, -19), (142, -15), (142, -11), (137, -12), (135, -15),
             (132, -12), (130, -13), (126, -14), (122, -17), (118, -20),
             (114, -22)]
NEW_ZEALAND = [(167, -45), (170, -42), (173, -40), (175, -38), (177, -38),
               (174, -41), (171, -43), (168, -46), (167, -45)]
ICELAND = [(-22, 64), (-18, 63), (-15, 64), (-14, 66), (-18, 66),
           (-22, 65)]
CONTINENTS = [N_AMERICA, GREENLAND, S_AMERICA, AFRICA, EURASIA, ARABIA,
              UK, JAPAN, BORNEO, SUMATRA, NEW_GUINEA, MADAGASCAR,
              AUSTRALIA, NEW_ZEALAND, ICELAND]


def lonlat_to_xy(lon, lat, x0, y0, w, h):
    """Equirectangular, lat 84..-65.5, vertical exaggeration 1.35."""
    x = x0 + (lon + 180.0) / 360.0 * w
    y = y0 + (84.0 - lat) / 149.5 * h
    return x, y


# ---------------------------------------------------------------- card art
def art_canvas(bg):
    img = Image.new("RGB", (384, 112), bg)
    return img, ImageDraw.Draw(img)


def art_nvidia():
    img, d = art_canvas((10, 40, 24))
    d.rounded_rectangle([150, 18, 234, 94], 10, fill=(118, 185, 0),
                        outline=(220, 240, 200), width=3)
    d.rounded_rectangle([168, 36, 216, 76], 6, fill=(10, 40, 24))
    for i in range(5):
        d.line([150, 30 + i * 12, 168, 30 + i * 12], fill=(220, 240, 200), width=3)
        d.line([216, 30 + i * 12, 234, 30 + i * 12], fill=(220, 240, 200), width=3)
    d.rectangle([262, 30, 276, 82], fill=(200, 40, 40))
    d.rectangle([288, 30, 302, 82], fill=(200, 40, 40))
    d.rectangle([64, 78, 120, 88], fill=(118, 185, 0))
    d.polygon([(64, 78), (120, 78), (92, 62)], fill=(118, 185, 0))
    return img


def art_kyiv():
    img, d = art_canvas((16, 22, 48))
    for bx, bw, bh in [(20, 34, 60), (62, 26, 78), (96, 40, 52), (144, 30, 70)]:
        d.rectangle([bx, 112 - bh, bx + bw, 112], fill=(38, 48, 74))
    for wx in range(26, 170, 14):
        d.rectangle([wx, 78, wx + 5, 84], fill=(240, 200, 90))
    d.line([300, 10, 210, 70], fill=(255, 120, 60), width=5)
    d.line([340, 30, 260, 78], fill=(255, 120, 60), width=4)
    d.line([200, 96, 330, 30], fill=(90, 230, 120), width=4)
    d.ellipse([326, 24, 340, 38], fill=(90, 230, 120))
    d.ellipse([204, 64, 214, 74], fill=(255, 220, 90))
    return img


def art_kuwait():
    img, d = art_canvas((196, 122, 62))
    d.polygon([(30, 112), (70, 30), (110, 112)], fill=(90, 60, 40))
    d.rectangle([64, 44, 76, 112], fill=(60, 40, 28))
    d.ellipse([96, 22, 128, 54], fill=(255, 150, 40))
    d.ellipse([104, 30, 120, 46], fill=(255, 220, 90))
    for i in range(3):
        d.ellipse([150 + i * 52, 84 - i * 8, 170 + i * 52, 104 - i * 8],
                  fill=(120, 110, 105))
    d.polygon([(300, 60), (330, 52), (360, 60), (345, 68), (315, 68)],
              fill=(40, 40, 44))
    d.line([330, 52, 330, 40], fill=(40, 40, 44), width=3)
    return img


def art_markets():
    img, d = art_canvas((16, 74, 74))
    bars = [(40, 76, 30), (90, 62, 38), (140, 52, 48), (190, 40, 58),
            (240, 30, 68), (290, 20, 78)]
    for x, y, h in bars:
        d.rectangle([x, 112 - h, x + 30, 112], fill=(64, 200, 130))
    d.line([36, 84, 96, 66, 156, 52, 216, 38, 276, 24, 336, 12],
           fill=(255, 220, 90), width=5)
    d.polygon([(336, 12), (316, 10), (334, 26)], fill=(255, 220, 90))
    return img


def art_hera():
    img, d = art_canvas((8, 8, 18))
    for sx, sy in [(30, 20), (90, 34), (150, 14), (220, 26), (300, 16),
                   (350, 40), (60, 90), (250, 92), (330, 84)]:
        d.ellipse([sx, sy, sx + 3, sy + 3], fill=(255, 255, 255))
    d.ellipse([140, 22, 240, 104], fill=(150, 148, 142))
    d.ellipse([168, 38, 196, 66], fill=(110, 108, 102))
    d.ellipse([206, 62, 226, 82], fill=(120, 118, 112))
    for bx, by, r in [(262, 50, 7), (282, 74, 5), (110, 60, 6),
                      (96, 88, 4), (300, 44, 4)]:
        d.ellipse([bx - r, by - r, bx + r, by + r], fill=(170, 168, 160))
    d.rectangle([286, 18, 330, 34], fill=(200, 200, 205))
    d.polygon([(330, 20), (352, 26), (330, 32)], fill=(160, 160, 168))
    return img


def art_migration():
    img, d = art_canvas((24, 44, 96))
    d.polygon([(60, 30), (120, 30), (120, 52), (140, 52), (90, 82),
               (40, 52), (60, 52)], fill=(90, 180, 255))
    d.polygon([(324, 82), (264, 82), (264, 60), (244, 60), (294, 30),
               (344, 60), (324, 60)], fill=(255, 180, 90))
    d.rounded_rectangle([164, 34, 220, 82], 6, fill=(150, 110, 70),
                        outline=(230, 200, 160), width=3)
    d.line([192, 34, 192, 82], fill=(230, 200, 160), width=3)
    d.rectangle([182, 26, 202, 34], fill=(230, 200, 160))
    return img


def art_storm():
    img, d = art_canvas((52, 60, 78))
    d.polygon([(150, 12), (120, 58), (142, 58), (118, 100), (168, 52),
               (144, 52), (170, 12)], fill=(255, 220, 60))
    for i in range(6):
        x = 40 + i * 22
        d.line([x, 20 + (i % 2) * 14, x - 12, 60 + (i % 2) * 14],
               fill=(180, 210, 240), width=4)
    for i in range(6):
        x = 250 + i * 20
        d.line([x, 30 + (i % 2) * 12, x - 12, 70 + (i % 2) * 12],
               fill=(180, 210, 240), width=4)
    d.line([300, 112, 300, 70], fill=(40, 44, 52), width=6)
    d.line([280, 78, 320, 78], fill=(40, 44, 52), width=5)
    d.line([282, 88, 318, 88], fill=(40, 44, 52), width=5)
    return img


def art_nfl():
    img, d = art_canvas((24, 60, 40))
    d.rectangle([0, 96, 384, 112], fill=(40, 110, 60))
    for gx in range(0, 385, 48):
        d.line([gx, 96, gx, 112], fill=(255, 255, 255), width=2)
    d.rectangle([150, 20, 234, 78], fill=(120, 40, 40),
                outline=(255, 255, 255), width=3)
    d.ellipse([176, 38, 208, 60], fill=(150, 90, 50),
              outline=(255, 255, 255), width=2)
    d.line([176, 49, 208, 49], fill=(255, 255, 255), width=2)
    for sx, sy in [(30, 16), (80, 40), (300, 24), (340, 52), (60, 70),
                   (320, 78), (20, 44), (260, 60)]:
        d.ellipse([sx, sy, sx + 5, sy + 5], fill=(255, 255, 255))
    return img


def art_iss():
    img, d = art_canvas((10, 16, 44))
    for sx, sy in [(24, 18), (80, 30), (140, 14), (220, 22), (300, 16),
                   (356, 34), (60, 88), (200, 92), (330, 88)]:
        d.ellipse([sx, sy, sx + 3, sy + 3], fill=(255, 255, 255))
    d.rectangle([120, 48, 260, 62], fill=(180, 184, 190))
    d.rectangle([150, 40, 230, 70], fill=(140, 144, 152))
    d.rectangle([40, 52, 120, 60], fill=(40, 90, 200))
    d.rectangle([260, 52, 340, 60], fill=(40, 90, 200))
    d.ellipse([290, 76, 322, 104], fill=(220, 224, 230),
              outline=(150, 150, 158), width=2)
    d.rectangle([296, 70, 316, 78], fill=(180, 184, 190))
    return img


def art_bok():
    img, d = art_canvas((44, 32, 84))
    for cx in (96, 140, 184, 228):
        d.rectangle([cx - 12, 62, cx + 12, 96], fill=(210, 200, 170))
    d.polygon([(76, 62), (264, 62), (170, 26)], fill=(230, 220, 190))
    d.rectangle([76, 96, 264, 104], fill=(210, 200, 170))
    d.line([290, 88, 310, 64, 330, 74, 356, 34], fill=(90, 220, 130),
           width=6)
    d.polygon([(356, 34), (336, 32), (352, 50)], fill=(90, 220, 130))
    for cx, cy in [(60, 34), (52, 52), (70, 52)]:
        d.ellipse([cx - 9, cy - 9, cx + 9, cy + 9], fill=(255, 215, 90),
                  outline=(180, 140, 40), width=2)
    return img


ART = {"nvidia": art_nvidia, "kyiv": art_kyiv, "kuwait": art_kuwait,
       "markets": art_markets, "hera": art_hera,
       "migration": art_migration, "storm": art_storm, "nfl": art_nfl,
       "iss": art_iss, "bok": art_bok}


# ---------------------------------------------------------------- leads
def lead_image(path, slot_w, slot_h, precrop=None):
    im = Image.open(path).convert("RGB")
    if precrop:
        im = im.crop(precrop)
    target = slot_w / slot_h
    w, h = im.size
    if w / h > target:  # too wide -> crop sides
        nw = int(h * target)
        x0 = (w - nw) // 2
        im = im.crop((x0, 0, x0 + nw, h))
    else:  # too tall -> crop top/bottom
        nh = int(w / target)
        y0 = (h - nh) // 2
        im = im.crop((0, y0, w, y0 + nh))
    return im.resize((slot_w, slot_h), Image.LANCZOS)


def badge_chip(draw, x, y, text, f):
    tw = draw.textlength(text, font=f)
    w = int(tw) + 12
    h = 15
    draw.rounded_rectangle([x, y, x + w, y + h], 3,
                           fill=BADGE[text])
    draw.text((x + 6, y + 2), text, font=f, fill=(255, 255, 255))
    return w


# ---------------------------------------------------------------- main
def main():
    with open(os.path.join(HERE, "stories.json")) as fh:
        data = json.load(fh)

    img = Image.new("RGB", (W, H), PAPER)
    d = ImageDraw.Draw(img)

    # ---- masthead
    d.rectangle([0, 0, W, 78], fill=NAVY)
    title_f = font(SERIF_B, 40)
    d.text((16, 16), data["edition"].upper(), font=title_f, fill=(255, 255, 255))
    meta_f = font(SANS_B, 13)
    date_f = font(SANS_B, 15)
    d.text((W - 16 - text_w(d, data["date"], date_f), 14), data["date"],
           font=date_f, fill=(255, 255, 255))
    d.text((W - 16 - text_w(d, data["meta"], meta_f), 38), data["meta"],
           font=meta_f, fill=GOLD_LT)
    d.rectangle([0, 78, W, 81], fill=GOLD)

    # ---- stat strip
    stats = data["stats"]
    cell_w = (W - 32) / 6
    big_f = font(SANS_B, 18)
    lab_f = font(SANS, 9)
    for i, st in enumerate(stats):
        x = 16 + i * cell_w
        if i:
            d.line([x - 4, 86, x - 4, 110], fill=LINE, width=1)
        lines, _ = wrap(d, st["label"], lab_f, cell_w - 12, 2)
        d.text((x, 84), st["big"], font=big_f, fill=NAVY)
        draw_lines(d, lines, x, 104, lab_f, GREY, 10)
    d.line([0, 126, W, 126], fill=LINE, width=1)

    # ---- leads
    lead_y, lead_img_h = 130, 146
    lead_w = 322
    lead_xs = [16, 351, 686]
    badge_f = font(SANS_B, 9)
    h_f = font(SANS_B, 16)
    deck_f = font(SANS, 11)
    tag_f = font(SANS_B, 9)
    for lead, lx in zip(data["leads"], lead_xs):
        precrop = (0, 0, 1590, 830) if "blackfriday" in lead["img"] else None
        li = lead_image(os.path.join(HERE, lead["img"]), lead_w, lead_img_h,
                        precrop)
        img.paste(li, (lx, lead_y))
        d.rectangle([lx, lead_y, lx + lead_w, lead_y + lead_img_h],
                    outline=LINE, width=1)
        badge_chip(d, lx + 6, lead_y + 6, lead["badge"], badge_f)
        num_f = font(SANS_B, 11)
        d.ellipse([lx + lead_w - 28, lead_y + 6, lx + lead_w - 6,
                   lead_y + 28], fill=GOLD)
        num = str(lead["id"])
        d.text((lx + lead_w - 17 - text_w(d, num, num_f) / 2, lead_y + 9),
               num, font=num_f, fill=(255, 255, 255))
        y = lead_y + lead_img_h + 8
        lines, _ = wrap(d, lead["headline"], h_f, lead_w, 2)
        y = draw_lines(d, lines, lx, y, h_f, INK, 19)
        y += 2
        lines, _ = wrap(d, lead["deck"], deck_f, lead_w, 2)
        y = draw_lines(d, lines, lx, y, deck_f, (60, 58, 52), 14)
        tag = f"{lead['place'].upper()} · {lead['region']} · {lead['field']}"
        d.text((lx, 352), tag, font=tag_f, fill=GOLD)
    d.line([0, 368, W, 368], fill=LINE, width=1)

    # ---- region / field chips
    chip_f = font(SANS, 10)
    reg = "REGIONS — " + " · ".join(f"{n} {c}" for n, c in data["region_counts"])
    fld = "FIELDS — " + " · ".join(f"{n} {c}" for n, c in data["field_counts"])
    d.text((16, 372), reg, font=chip_f, fill=NAVY)
    d.text((16, 386), fld, font=chip_f, fill=NAVY)
    d.line([0, 402, W, 402], fill=LINE, width=1)

    # ---- illustrated cards (5 x 2)
    card_w, card_h = 192, 108
    card_xs = [16 + i * 200 for i in range(5)]
    card_ys = [410, 522]
    ch_f = font(SANS_B, 11)
    cd_f = font(SANS, 9)
    for i, card in enumerate(data["cards"]):
        cx = card_xs[i % 5]
        cy = card_ys[i // 5]
        art = ART[card["art"]]().resize((card_w, 56), Image.LANCZOS)
        img.paste(art, (cx, cy))
        d.rectangle([cx, cy, cx + card_w, cy + 56], outline=LINE, width=1)
        badge_chip(d, cx + 4, cy + 4, card["badge"], badge_f)
        d.ellipse([cx + card_w - 24, cy + 4, cx + card_w - 4, cy + 24],
                  fill=NAVY)
        num = str(card["id"])
        nf = font(SANS_B, 10)
        d.text((cx + card_w - 14 - text_w(d, num, nf) / 2, cy + 7),
               num, font=nf, fill=(255, 255, 255))
        y = cy + 62
        lines, _ = wrap(d, card["headline"], ch_f, card_w, 2)
        y = draw_lines(d, lines, cx, y, ch_f, INK, 13)
        lines, _ = wrap(d, card["deck"], cd_f, card_w, 1)
        draw_lines(d, lines, cx, y, cd_f, (60, 58, 52), 11)
    d.line([0, 636, W, 636], fill=LINE, width=1)

    # ---- map panel
    map_x, map_y, map_w, map_h = 16, 670, 330, 185
    mt_f = font(SANS_B, 12)
    ms_f = font(SANS, 9)
    d.text((map_x, 642), "WHERE IT HAPPENED", font=mt_f, fill=NAVY)
    d.text((map_x, 656), "13 illustrated stories — gold rings are the 3 leads",
           font=ms_f, fill=GREY)
    ss = 3
    mimg = Image.new("RGB", (map_w * ss, map_h * ss), OCEAN)
    md = ImageDraw.Draw(mimg)

    def mxy(lon, lat):
        return lonlat_to_xy(lon, lat, 0, 0, map_w * ss, map_h * ss)

    for poly in CONTINENTS:
        pts = [mxy(lon, lat) for lon, lat in poly]
        md.polygon(pts, fill=LAND, outline=LAND_EDGE)
    mpts = [mxy(lon, lat) for lon, lat in MED]
    md.polygon(mpts, fill=OCEAN)
    # graticule
    for lon in range(-150, 181, 30):
        x, _ = mxy(lon, 84)
        md.line([x, 0, x, map_h * ss], fill=(200, 214, 226), width=1)
    for lat in (-40, 0, 40):
        _, y = mxy(0, lat)
        md.line([0, y, map_w * ss, y], fill=(200, 214, 226), width=1)
    # pins on the supersampled map
    illustrated = list(data["leads"]) + list(data["cards"])
    pin_xy = {}
    for it in illustrated:
        px, py = mxy(it["lon"], it["lat"])
        pin_xy[it["id"]] = (px / ss, py / ss)
        lead = it["id"] <= 3
        r = 15 if lead else 11
        if lead:
            md.ellipse([px - r, py - r, px + r, py + r], fill=GOLD,
                       outline=(255, 255, 255), width=3)
            md.ellipse([px - 7, py - 7, px + 7, py + 7], fill=NAVY)
        else:
            md.ellipse([px - r, py - r, px + r, py + r], fill=NAVY,
                       outline=(255, 255, 255), width=3)
    mimg = mimg.resize((map_w, map_h), Image.LANCZOS)
    img.paste(mimg, (map_x, map_y))
    d.rectangle([map_x, map_y, map_x + map_w, map_y + map_h],
                outline=LINE, width=1)
    # numbered label chips with leader lines (hand-tuned de-collision)
    offsets = {1: (8, -8), 2: (8, 4), 3: (8, -8), 4: (8, -8), 5: (8, -8),
               6: (-36, -16), 7: (-8, 12), 8: (6, -20), 9: (-32, -8),
               10: (-32, -8), 11: (-8, -20), 12: (8, -8), 13: (-32, -8)}
    lf = font(SANS_B, 9)
    for it in illustrated:
        pid = it["id"]
        px, py = pin_xy[pid]
        ax, ay = map_x + px, map_y + py
        dx, dy = offsets[pid]
        label = str(pid)
        tw = d.textlength(label, font=lf)
        cw, chh = int(tw) + 8, 13
        lx = ax + dx - (cw if dx < 0 else 0)
        ly = ay + dy - (chh if dy < 0 else 0)
        ex = lx + (cw if dx < 0 else 0)
        ey = ly + (chh if dy < 0 else 0)
        d.line([ax, ay, ex, ey], fill=GREY, width=1)
        d.rounded_rectangle([lx, ly, lx + cw, ly + chh], 3, fill=NAVY)
        d.text((lx + 4, ly + 1), label, font=lf, fill=(255, 255, 255))
    d.text((map_x, 860), "Gold rings mark the 3 lead stories; numbers match the story list.",
           font=ms_f, fill=GREY)

    # ---- briefs (3 cols x 11 rows)
    bx0, by0 = 358, 642
    bh_f = font(SANS_B, 12)
    d.text((bx0, 642), "THE DAY IN BRIEF — 32 STORIES", font=bh_f, fill=NAVY)
    d.line([bx0, 658, 1008, 658], fill=LINE, width=1)
    col_w, row_h = 212, 20
    col_xs = [bx0, bx0 + 219, bx0 + 438]
    bh2_f = font(SANS_B, 10)
    bd_f = font(SANS, 9)
    for i, b in enumerate(data["briefs"]):
        col, row = divmod(i, 11)
        x = col_xs[col]
        y = 664 + row * row_h
        num = f"{b['id']}"
        nw = d.textlength(num + "  ", font=bh2_f)
        d.text((x, y), num, font=bh2_f, fill=BADGE[b["badge"]])
        lines, _ = wrap(d, b["headline"], bh2_f, col_w - nw, 1)
        draw_lines(d, lines, x + nw, y, bh2_f, INK, 12)
        lines, _ = wrap(d, b["deck"], bd_f, col_w, 1)
        draw_lines(d, lines, x, y + 10, bd_f, (60, 58, 52), 11)
    d.line([346, 642, 346, 884], fill=LINE, width=1)

    # ---- timeline
    d.line([0, 884, W, 884], fill=LINE, width=1)
    d.text((16, 887), "THE DAY IN UTC — ALL TIMES UTC",
           font=font(SANS_B, 10), fill=NAVY)
    line_y = 928
    x0, x1, span = 40, 984, 1110
    d.line([x0, line_y, x1, line_y], fill=NAVY, width=2)
    tt_f = font(SANS_B, 9)
    tl_f = font(SANS, 8)
    anchor_shift = {2: 8, 5: -20}
    for idx, ev in enumerate(data["timeline"]):
        cx = x0 + ev["min"] / span * (x1 - x0)
        d.ellipse([cx - 4, line_y - 4, cx + 4, line_y + 4], fill=GOLD,
                  outline=NAVY, width=1)
        above = idx % 2 == 0
        tag = f"{ev['t']} UTC" + (" (26 NOV)" if ev["day"] == "26 NOV" else "")
        tx = cx + anchor_shift.get(idx, -54)
        tx = min(max(tx, 16), W - 140)
        if idx == 7:
            tx = 938
        if above:
            d.line([cx, line_y - 5, cx, 920], fill=GREY, width=1)
            d.text((tx, 898), tag, font=tt_f, fill=NAVY)
            lines, _ = wrap(d, ev["label"], tl_f, 130, 1)
            draw_lines(d, lines, tx, 909, tl_f, INK, 10)
        else:
            d.line([cx, line_y + 5, cx, 934], fill=GREY, width=1)
            d.text((tx, 936), tag, font=tt_f, fill=NAVY)
            lines, _ = wrap(d, ev["label"], tl_f, 130, 1)
            draw_lines(d, lines, tx, 947, tl_f, INK, 10)

    # ---- footer
    d.rectangle([0, 963, W, 966], fill=GOLD)
    leg_f = font(SANS, 9)
    y = 968
    lines, _ = wrap(d, "LEGEND — " + data["legend"], leg_f, W - 32, 2)
    y = draw_lines(d, lines, 16, y, leg_f, INK, 11)
    lines, _ = wrap(d, data["datecheck"], leg_f, W - 32, 2)
    y = draw_lines(d, lines, 16, y + 1, leg_f, INK, 11)
    lines, _ = wrap(d, data["sources"], leg_f, W - 32, 2)
    y = draw_lines(d, lines, 16, y + 1, leg_f, (60, 58, 52), 11)
    check_y(y, "footer")
    d.text((W - 16 - text_w(d, "V3 · PHOTO LEADS", font(SANS_B, 8)), 1012),
           "V3 · PHOTO LEADS", font=font(SANS_B, 8), fill=GREY)

    out = os.path.join(HERE, "entry.png")
    img.save(out, "PNG")
    print(f"TRIMS {TRIMS} OVERFLOWS {OVERFLOWS}")
    print(f"WROTE {out} {os.path.getsize(out)} bytes")
    return 0 if (TRIMS == 0 and OVERFLOWS == 0) else 1


if __name__ == "__main__":
    sys.exit(main())
