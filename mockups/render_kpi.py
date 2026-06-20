#!/usr/bin/env python3
"""Render the redesigned 'Current Month Overview' KPI strip to a PNG."""
from PIL import Image, ImageDraw, ImageFont

S = 2  # supersample for crispness
W, H = 1320 * S, 230 * S
BG = (244, 245, 247)
INK = (31, 36, 48)
MUTED = (107, 114, 128)
BRAND = (232, 115, 26)
WHITE = (255, 255, 255)
BORDER = (238, 240, 243)

img = Image.new("RGB", (W, H), BG)
d = ImageDraw.Draw(img)

def font(sz, bold=False):
    paths = [
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf" if bold
        else "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
    ]
    for p in paths:
        try:
            return ImageFont.truetype(p, sz * S)
        except Exception:
            pass
    return ImageFont.load_default()

f_title = font(19, True)
f_sub = font(11)
f_val = font(23, True)
f_lbl = font(10, True)
f_pill = font(9)
f_btn = font(11, True)

def rrect(xy, r, fill, outline=None, width=1):
    d.rounded_rectangle(xy, radius=r * S, fill=fill, outline=outline, width=width * S)

def shadow(xy, r):
    # cheap soft shadow
    x0, y0, x1, y1 = xy
    for i in range(6, 0, -1):
        a = 6 + i
        d.rounded_rectangle(
            (x0 - i, y0 - i + 3, x1 + i, y1 + i + 4),
            radius=(r + i) * S,
            fill=(225 - a, 228 - a, 233 - a),
        )

# ---- section header ----
mx = 40 * S
d.rounded_rectangle((mx, 24 * S, mx + 5 * S, 50 * S), radius=2 * S, fill=BRAND)
d.text((mx + 16 * S, 20 * S), "Current Month Overview", font=f_title, fill=INK)
d.text((mx + 16 * S, 46 * S), "June 2026  ·  Field + Indirect", font=f_sub, fill=MUTED)

# reset button (right)
btn_w, btn_h = 130 * S, 32 * S
bx1 = W - 40 * S
bx0 = bx1 - btn_w
rrect((bx0, 24 * S, bx1, 24 * S + btn_h), 8, BRAND)
d.text((bx0 + 18 * S, 32 * S), "Reset Filters", font=f_btn, fill=WHITE)
# filter chip
fcw = 190 * S
fx1 = bx0 - 12 * S
fx0 = fx1 - fcw
rrect((fx0, 24 * S, fx1, 24 * S + btn_h), 8, WHITE, outline=BORDER, width=1)
d.text((fx0 + 14 * S, 32 * S), "Month / Week Ending  v", font=f_sub, fill=INK)

# ---- KPI cards ----
cards = [
    ("LABOUR HOURS", "4.61K", "Field + indirect", (253, 238, 226), (182, 90, 18)),
    ("BILLABLE FTE", "27", "Indirect", (231, 240, 254), (34, 87, 191)),
    ("LABOUR SPEND", "$4.8K", "Field + indirect", (234, 247, 239), (22, 128, 90)),
    ("APPRENTICE RATIO", "0.19", "Indirect vs field", (241, 236, 251), (111, 55, 189)),
    ("WORKFORCE AVG", "34", "Field + indirect", (253, 242, 220), (154, 110, 21)),
    ("DT : RT RATIO", "0.17", "Lab DT / RT hrs", (253, 234, 234), (178, 47, 39)),
    ("TRUCK HRS BILLED", "979.25", "8 trucks / day", (228, 244, 244), (10, 118, 118)),
]

n = len(cards)
left = 40 * S
right = W - 40 * S
gap = 14 * S
cw = (right - left - gap * (n - 1)) / n
cy0 = 78 * S
ch = 116 * S

for i, (lbl, val, pill, tint, tcol) in enumerate(cards):
    cx0 = int(left + i * (cw + gap))
    cx1 = int(cx0 + cw)
    shadow((cx0, cy0, cx1, cy0 + ch), 12)
    rrect((cx0, cy0, cx1, cy0 + ch), 12, WHITE, outline=BORDER, width=1)
    # icon tile top-right
    it = 30 * S
    rrect((cx1 - it - 12 * S, cy0 + 12 * S, cx1 - 12 * S, cy0 + 12 * S + it), 8, tint)
    d.ellipse((cx1 - it - 12 * S + 9 * S, cy0 + 12 * S + 9 * S,
               cx1 - 12 * S - 9 * S, cy0 + 12 * S + it - 9 * S), fill=tcol)
    # label (wrap to 2 lines if long)
    d.text((cx0 + 14 * S, cy0 + 16 * S), lbl, font=f_lbl, fill=MUTED)
    # value
    d.text((cx0 + 14 * S, cy0 + 44 * S), val, font=f_val, fill=INK)
    # divider
    d.line((cx0 + 14 * S, cy0 + 84 * S, cx1 - 14 * S, cy0 + 84 * S), fill=(242, 243, 246), width=1 * S)
    # pill
    pill_pad = 8 * S
    pw = d.textlength(pill, font=f_pill) + pill_pad * 2
    rrect((cx0 + 14 * S, cy0 + 92 * S, cx0 + 14 * S + pw, cy0 + 92 * S + 16 * S), 10, tint)
    d.text((cx0 + 14 * S + pill_pad, cy0 + 95 * S), pill, font=f_pill, fill=tcol)

img = img.resize((W // S, H // S), Image.LANCZOS)
img.save("/home/user/Power-Bi-Dashboard/mockups/kpi-strip-redesign.png")
print("saved")
