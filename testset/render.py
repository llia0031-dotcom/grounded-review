"""Render the image ads of the test set.

Each image is drawn from its spec in items_*.yaml: a background, a simple product drawing, the ad
text (image.lines) and, for some items, a visual element (national flag, lanterns, before/after
panels). The "frames" layout (harder set) shows three frames of a short video with subtitles. A few items use a photo made with an image model as the background (testset/photos/).
The words in every image are known exactly, so OCR and quotes can be checked against them.

Run: python testset/render.py            (renders every image item, and revised versions)
"""
from __future__ import annotations

import math
import random
import sys
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont, ImageFilter

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from load import load_items  # noqa: E402

OUT = HERE / "images"
PHOTOS = HERE / "photos"
FONTS = Path("C:/Windows/Fonts")
FONT_ZH = {"bold": "msyhbd.ttc", "regular": "msyh.ttc", "alt": "simhei.ttf"}
FONT_EN = {"bold": "arialbd.ttf", "regular": "segoeui.ttf", "alt": "georgiab.ttf", "impact": "impact.ttf"}

PALETTES = {
    "blue": ("#dce9f7", "#8fb6e3", "#173b6c", "#2f6fb5"),
    "navy": ("#d9dee9", "#2b3a5c", "#ffffff", "#f2c14e"),
    "purple": ("#ece3f6", "#a58bcf", "#3b2160", "#7b4fb3"),
    "gray": ("#eeeeee", "#b9b9b9", "#222222", "#555555"),
    "green": ("#e3f2df", "#8cc084", "#1f4d1a", "#3c8a34"),
    "red": ("#fbe1dc", "#d9534f", "#7a1010", "#c0392b"),
    "orange": ("#fdebd6", "#f0a35e", "#6b3305", "#d9731a"),
    "pink": ("#fbe4ec", "#e79bb6", "#6b1f3a", "#c2456f"),
    "teal": ("#dff3f1", "#6cbfb5", "#0f4842", "#1f8a7f"),
    "gold": ("#fbf2d5", "#d9b44a", "#4a3505", "#a8801a"),
    "beige": ("#f5efe3", "#d8c7a6", "#4a3b22", "#8a6d3b"),
    "amber": ("#fdf0d5", "#e0a030", "#4d2c00", "#b36b00"),
}


def font(lang: str, weight: str, size: int) -> ImageFont.FreeTypeFont:
    name = (FONT_ZH if lang == "zh" else FONT_EN)[weight]
    return ImageFont.truetype(str(FONTS / name), size)


def fit(draw, text, lang, weight, size, max_w):
    while size > 14:
        f = font(lang, weight, size)
        if draw.textlength(text, font=f) <= max_w:
            return f
        size -= 2
    return font(lang, weight, size)


def gradient(w, h, c1, c2, vertical=True):
    a, b = Image.new("RGB", (w, h), c1), Image.new("RGB", (w, h), c2)
    mask = Image.linear_gradient("L").resize((w, h))
    if not vertical:
        mask = mask.rotate(90, expand=True).resize((w, h))
    return Image.composite(b, a, mask)


# ---------------------------------------------------------------- product drawings
def draw_product(d: ImageDraw.ImageDraw, shape: str, box, colors, brand: str, lang: str, rnd: random.Random):
    x0, y0, x1, y1 = box
    w, h = x1 - x0, y1 - y0
    cx = (x0 + x1) // 2
    body, accent, dark = colors[1], colors[3], colors[2]
    label_font = font(lang, "bold", max(16, int(w * 0.11)))

    def label(y):
        tw = d.textlength(brand, font=label_font)
        d.text((cx - tw / 2, y), brand, font=label_font, fill="#ffffff")

    bottles = {"bottle", "liquor", "wine", "oil", "beer", "pills"}
    if shape in bottles:
        neck_w = w * (0.16 if shape in {"wine", "beer", "liquor", "oil"} else 0.3)
        body_top = y0 + h * (0.35 if shape in {"wine", "beer"} else 0.22)
        d.rounded_rectangle([cx - neck_w / 2, y0, cx + neck_w / 2, body_top + 20], 8, fill=dark)
        d.rounded_rectangle([x0 + w * 0.18, body_top, x1 - w * 0.18, y1], 28, fill=accent)
        d.rectangle([x0 + w * 0.18, body_top + h * 0.25, x1 - w * 0.18, body_top + h * 0.42], fill=body)
        label(body_top + h * 0.27)
    elif shape in {"tube"}:
        d.polygon([(x0 + w * 0.3, y0), (x1 - w * 0.3, y0), (x1 - w * 0.18, y1 - 40), (x0 + w * 0.18, y1 - 40)], fill=accent)
        d.rounded_rectangle([cx - w * 0.14, y1 - 50, cx + w * 0.14, y1], 10, fill=dark)
        label(y0 + h * 0.35)
    elif shape in {"jar", "candle"}:
        d.rounded_rectangle([x0 + w * 0.12, y0 + h * 0.18, x1 - w * 0.12, y0 + h * 0.32], 12, fill=dark)
        d.rounded_rectangle([x0 + w * 0.08, y0 + h * 0.3, x1 - w * 0.08, y1], 30, fill=accent)
        if shape == "candle":
            d.ellipse([cx - 10, y0 + h * 0.02, cx + 10, y0 + h * 0.16], fill="#f6b73c")
        label(y0 + h * 0.55)
    elif shape in {"tumbler", "teaware"}:
        d.rounded_rectangle([x0 + w * 0.28, y0, x1 - w * 0.28, y0 + h * 0.12], 10, fill=dark)
        d.polygon([(x0 + w * 0.25, y0 + h * 0.12), (x1 - w * 0.25, y0 + h * 0.12), (x1 - w * 0.3, y1), (x0 + w * 0.3, y1)], fill=accent)
        label(y0 + h * 0.45)
    elif shape in {"phone", "laptop", "card", "powerbank", "book"}:
        if shape == "laptop":
            d.rounded_rectangle([x0, y0 + h * 0.2, x1, y1 - h * 0.2], 14, fill=dark)
            d.rectangle([x0 + 14, y0 + h * 0.2 + 14, x1 - 14, y1 - h * 0.2 - 14], fill=body)
            d.rectangle([x0 - 20, y1 - h * 0.2, x1 + 20, y1 - h * 0.14], fill=accent)
        else:
            ratio = {"phone": 0.52, "card": 1.55, "powerbank": 0.62, "book": 0.75}[shape]
            bw = min(w * 0.9, h * ratio)
            bh = bw / ratio
            top = y0 + (h - bh) / 2
            d.rounded_rectangle([cx - bw / 2, top, cx + bw / 2, top + bh], 26 if shape != "book" else 6, fill=accent)
            if shape == "phone":
                d.rounded_rectangle([cx - bw / 2 + 12, top + 30, cx + bw / 2 - 12, top + bh - 30], 16, fill=body)
            if shape == "card":
                d.rectangle([cx - bw / 2, top + bh * 0.25, cx + bw / 2, top + bh * 0.4], fill=dark)
            label(top + bh * 0.55)
    elif shape in {"box", "tea", "dryer", "blender", "vacuum"}:
        if shape == "vacuum":
            d.ellipse([x0, y0 + h * 0.25, x1, y1], fill=accent)
            d.ellipse([x0 + w * 0.3, y0 + h * 0.45, x1 - w * 0.3, y1 - h * 0.2], fill=dark)
        elif shape == "dryer":
            d.ellipse([x0, y0, x0 + w * 0.7, y0 + h * 0.5], fill=accent)
            d.rounded_rectangle([x0 + w * 0.25, y0 + h * 0.35, x0 + w * 0.45, y1], 18, fill=dark)
        elif shape == "blender":
            d.polygon([(x0 + w * 0.2, y0), (x1 - w * 0.2, y0), (x1 - w * 0.28, y0 + h * 0.65), (x0 + w * 0.28, y0 + h * 0.65)], fill=body, outline=dark, width=6)
            d.rounded_rectangle([x0 + w * 0.2, y0 + h * 0.65, x1 - w * 0.2, y1], 16, fill=accent)
            label(y0 + h * 0.75)
        else:
            d.polygon([(x0 + w * 0.15, y0 + h * 0.15), (x1 - w * 0.05, y0 + h * 0.15), (x1 - w * 0.05, y1), (x0 + w * 0.15, y1)], fill=accent)
            d.polygon([(x0 + w * 0.15, y0 + h * 0.15), (x0 + w * 0.3, y0), (x1 + w * 0.05, y0), (x1 - w * 0.05, y0 + h * 0.15)], fill=body)
            label(y0 + h * 0.5)
    elif shape in {"shoe", "slipper"}:
        d.ellipse([x0, y0 + h * 0.45, x1, y1], fill=accent)
        d.rounded_rectangle([x0 + w * 0.05, y0 + h * 0.2, x0 + w * 0.55, y0 + h * 0.75], 40, fill=accent)
        d.rectangle([x0, y1 - h * 0.12, x1, y1 - h * 0.04], fill=dark)
    elif shape in {"bag", "jacket", "sofa", "bedding"}:
        d.rounded_rectangle([x0 + w * 0.1, y0 + h * 0.25, x1 - w * 0.1, y1], 30, fill=accent)
        if shape == "bag":
            d.arc([cx - w * 0.22, y0, cx + w * 0.22, y0 + h * 0.5], 180, 360, fill=dark, width=14)
        if shape == "jacket":
            d.line([cx, y0 + h * 0.25, cx, y1], fill=dark, width=8)
        label(y0 + h * 0.55)
    elif shape in {"earbuds"}:
        for dx in (-0.22, 0.22):
            ex = cx + w * dx
            d.ellipse([ex - w * 0.15, y0 + h * 0.2, ex + w * 0.15, y0 + h * 0.5], fill=accent)
            d.rounded_rectangle([ex - w * 0.05, y0 + h * 0.45, ex + w * 0.05, y1], 14, fill=accent)
    elif shape in {"ball", "tape"}:
        d.ellipse([x0 + w * 0.1, y0 + h * 0.1, x1 - w * 0.1, y1 - h * 0.1], fill=accent)
        if shape == "tape":
            d.ellipse([cx - w * 0.15, (y0 + y1) / 2 - h * 0.15, cx + w * 0.15, (y0 + y1) / 2 + h * 0.15], fill=body)
        else:
            d.polygon([(cx, y0 + h * 0.35), (cx + w * 0.12, y0 + h * 0.45), (cx + w * 0.08, y0 + h * 0.6), (cx - w * 0.08, y0 + h * 0.6), (cx - w * 0.12, y0 + h * 0.45)], fill=dark)
    elif shape in {"car", "school"}:
        if shape == "car":
            d.rounded_rectangle([x0, y0 + h * 0.45, x1, y1 - h * 0.15], 30, fill=accent)
            d.rounded_rectangle([x0 + w * 0.2, y0 + h * 0.2, x1 - w * 0.2, y0 + h * 0.5], 30, fill=accent)
            for wx in (x0 + w * 0.25, x1 - w * 0.25):
                d.ellipse([wx - 40, y1 - h * 0.3, wx + 40, y1 - h * 0.3 + 80], fill=dark)
        else:
            d.rectangle([x0 + w * 0.1, y0 + h * 0.3, x1 - w * 0.1, y1], fill=accent)
            d.polygon([(x0, y0 + h * 0.32), (cx, y0), (x1, y0 + h * 0.32)], fill=dark)
            for i in range(3):
                d.rectangle([x0 + w * (0.2 + i * 0.22), y0 + h * 0.5, x0 + w * (0.32 + i * 0.22), y0 + h * 0.65], fill=body)
    else:
        raise ValueError(shape)


def draw_flag(img: Image.Image, x: int, y: int, w: int):
    """National flag of the PRC, drawn from its published geometry (30 x 20 grid)."""
    h = w * 2 // 3
    flag = Image.new("RGB", (w, h), "#de2910")
    d = ImageDraw.Draw(flag)
    u = w / 30

    def star(cx, cy, r, angle):
        pts = []
        for i in range(10):
            a = angle + i * math.pi / 5
            rr = r if i % 2 == 0 else r * 0.382
            pts.append((cx + rr * math.sin(a), cy - rr * math.cos(a)))
        d.polygon(pts, fill="#ffde00")

    star(5 * u, 5 * u, 3 * u, 0)
    for sx, sy in [(10, 2), (12, 4), (12, 7), (10, 9)]:
        ang = math.atan2(5 - sx, -(5 - sy))
        star(sx * u, sy * u, 1 * u, ang)
    img.paste(flag, (x, y))


def draw_lanterns(d: ImageDraw.ImageDraw, x: int, y: int, size: int):
    for i in range(2):
        cx = x + i * int(size * 1.3)
        d.line([cx + size / 2, y, cx + size / 2, y + size * 0.3], fill="#7a1010", width=4)
        d.ellipse([cx, y + size * 0.3, cx + size, y + size * 1.2], fill="#e0301e")
        d.rectangle([cx + size * 0.3, y + size * 0.25, cx + size * 0.7, y + size * 0.35], fill="#f2c14e")
        d.rectangle([cx + size * 0.3, y + size * 1.15, cx + size * 0.7, y + size * 1.25], fill="#f2c14e")
        for k in range(5):
            tx = cx + size * 0.35 + k * size * 0.07
            d.line([tx, y + size * 1.25, tx, y + size * 1.55], fill="#f2c14e", width=2)


SKIN, SHIRTS = "#e8b99a", ["#3c6e9e", "#a8443c", "#4f7d3a", "#6b4f9e"]


def person(d, cx, base, shirt, lean=0.0, drinking=False, cup="#f4d27a", lying=False):
    """A flat figure: head, body, legs, arms. drinking=True raises a glass to the mouth."""
    if lying:
        d.rounded_rectangle([cx - 150, base - 70, cx + 60, base - 20], 22, fill=shirt)
        d.ellipse([cx + 55, base - 95, cx + 125, base - 25], fill=SKIN)
        d.rectangle([cx - 230, base - 60, cx - 150, base - 32], fill="#333333")
        d.ellipse([cx - 40, base - 12, cx + 20, base + 4], fill="#c9a24a")  # spilled drink
        return
    hx = cx + lean * 60
    d.ellipse([hx - 42, base - 430, hx + 42, base - 346], fill=SKIN)
    body = [(cx - 70, base - 335), (cx + 70, base - 335), (cx + 60 + lean * 40, base - 150), (cx - 60 + lean * 40, base - 150)]
    d.polygon([(x + lean * 40, y) for x, y in body[:2]] + body[2:], fill=shirt)
    d.rectangle([cx - 50 + lean * 40, base - 150, cx - 10 + lean * 40, base], fill="#333333")
    d.rectangle([cx + 10 + lean * 40, base - 150, cx + 50 + lean * 40, base], fill="#333333")
    sx = cx + 62 + lean * 40
    if drinking:
        # upper arm up, forearm to the mouth, glass tipped against the lips
        d.line([sx, base - 320, sx + 55, base - 300], fill=SKIN, width=26)
        d.line([sx + 55, base - 300, hx + 30, base - 375], fill=SKIN, width=24)
        glass = [(hx + 18, base - 405), (hx + 62, base - 425), (hx + 80, base - 368), (hx + 44, base - 352)]
        d.polygon(glass, fill=cup, outline="#7a5a10")
    else:
        d.line([sx, base - 320, sx + 30, base - 190], fill=SKIN, width=26)
    d.line([cx - 62 + lean * 40, base - 320, cx - 95 + lean * 40, base - 190], fill=SKIN, width=26)


def draw_scene(d, scene: str, colors, rnd: random.Random):
    """Illustrated scenes for the alcohol items (people drinking; a drunken party)."""
    floor = 500 if scene == "drunk-party" else 600  # keep the floor clear of the caption band
    d.rectangle([0, floor, 800, 800], fill="#d8c7a6")
    if scene == "toast-baijiu":
        d.rectangle([250, floor - 120, 550, floor - 100], fill="#8a6d3b")  # table
        d.rectangle([380, floor - 210, 420, floor - 120], fill="#b0302a")  # bottle
        d.rectangle([390, floor - 240, 410, floor - 210], fill="#7a1010")
        person(d, 200, floor, SHIRTS[0], drinking=True, cup="#f1e6c8")
        person(d, 600, floor, SHIRTS[1], drinking=True, cup="#f1e6c8")
    elif scene == "drink-beer":
        person(d, 400, floor, SHIRTS[2], drinking=True, cup="#e8a317")
        d.rectangle([560, floor - 90, 610, floor], fill="#8a5a10")  # bottle on the floor beside
    elif scene == "drunk-party":
        person(d, 170, floor, SHIRTS[0], lean=1.3, drinking=True, cup="#e8a317")
        person(d, 420, floor, SHIRTS[3], lean=-1.4)
        person(d, 640, floor + 85, SHIRTS[1], lying=True)
        for _ in range(9):  # empty cans and bottles on the floor
            x = rnd.randint(40, 760)
            if rnd.random() < 0.5:
                d.rectangle([x, floor + 20, x + 26, floor + 64], fill="#c9a24a", outline="#7a5a10")
            else:
                d.polygon([(x, floor + 60), (x + 60, floor + 40), (x + 66, floor + 56), (x + 6, floor + 76)], fill="#7a5a10")
        for k in range(3):  # dizzy spirals over the heads
            cx, cy = (300, 470, 700)[k], (40, 40, 470)[k]
            for r in range(6, 34, 7):
                d.arc([cx - r, cy - r, cx + r, cy + r], 0, 300, fill="#555555", width=3)
    else:
        raise ValueError(scene)


def text_block(d, lines, lang, colors, area, align="center"):
    x0, y0, x1, y1 = area
    sizes = [64, 38, 30] if lang == "zh" else [58, 36, 28]
    weights = ["bold", "regular", "bold"]
    fills = [colors[2], colors[2], colors[3]]
    y = y0
    for i, line in enumerate(lines):
        f = fit(d, line, lang, weights[min(i, 2)], sizes[min(i, 2)], x1 - x0)
        tw = d.textlength(line, font=f)
        tx = x0 + (x1 - x0 - tw) / 2 if align == "center" else x0
        d.text((tx, y), line, font=f, fill=fills[min(i, 2)])
        y += f.size * 1.45


def body_shape(d, cx, top, wide: bool):
    """A plain body silhouette, wide or slim (the before-and-after figures of the split layout)."""
    skin, bw = "#e8b99a", 150 if wide else 80
    d.ellipse([cx - 40, top, cx + 40, top + 80], fill=skin)
    d.rounded_rectangle([cx - bw, top + 85, cx + bw, top + 280], 60, fill=skin)
    d.rectangle([cx - bw * 0.7, top + 270, cx - 8, top + 380], fill=skin)
    d.rectangle([cx + 8, top + 270, cx + bw * 0.7, top + 380], fill=skin)


def render_frames(spec: dict, lines: list[str], lang: str, colors, rnd: random.Random) -> Image.Image:
    """Three frames of a short vertical video side by side, each with its subtitle (lines[i]) in a dark band,
    as a screenshot sequence of the clip would show. Frame art: a product drawing (no brand label), an
    illustrated scene, a body silhouette, or a plain background. The frames carry no other words."""
    fw, fh, gap, pad = 400, 600, 18, 20
    W, H = pad * 2 + 3 * fw + 2 * gap, pad * 2 + fh
    img = Image.new("RGB", (W, H), "#111111")
    for i, art in enumerate(spec["frames"]):
        cell = gradient(800, 800, colors[0], "#ffffff")
        cd = ImageDraw.Draw(cell)
        if "shape" in art:
            draw_product(cd, art["shape"], (230, 170, 570, 640), colors, "", lang, rnd)
        elif "scene" in art:
            draw_scene(cd, art["scene"], colors, rnd)
        elif "body" in art:
            body_shape(cd, 400, 170, art["body"] == "wide")
        cell = cell.resize((fw, fw))
        frame = gradient(fw, fh, colors[0], "#ffffff")
        frame.paste(cell, (0, 40))
        fd = ImageDraw.Draw(frame, "RGBA")
        fd.polygon([(fw - 46, 22), (fw - 46, 50), (fw - 22, 36)], fill=(255, 255, 255, 210))  # play mark, no text
        fd.rectangle([0, fh - 130, fw, fh - 40], fill=(0, 0, 0, 165))
        f = fit(fd, lines[i], lang, "bold", 34 if lang == "zh" else 30, fw - 36)
        tw = fd.textlength(lines[i], font=f)
        fd.text(((fw - tw) / 2, fh - 85 - f.size / 2 - 4), lines[i], font=f, fill="#ffffff")
        img.paste(frame, (pad + i * (fw + gap), pad))
    return img


def render_item(item: dict, lines: list[str], out: Path):
    spec = item["image"]
    lang = item["lang"]
    colors = PALETTES[spec["palette"]]
    rnd = random.Random(item["id"])
    layout = spec["layout"]
    brand = spec.get("brand", "")

    if layout == "poster":
        W, H = 800, 800
        img = gradient(W, H, colors[0], "#ffffff")
        d = ImageDraw.Draw(img)
        top = 150 if spec.get("extra") in {"flag", "lanterns"} else 70  # keep words clear of the corner element
        text_block(d, lines, lang, colors, (60, top, W - 60, 330))
        draw_product(d, spec["shape"], (W // 2 - 170, 380, W // 2 + 170, 770), colors, brand, lang, rnd)
    elif layout == "banner":
        W, H = 1000, 560
        img = gradient(W, H, colors[0], "#ffffff", vertical=False)
        d = ImageDraw.Draw(img)
        draw_product(d, spec["shape"], (60, 110, 400, 500), colors, brand, lang, rnd)
        text_block(d, lines, lang, colors, (440, 150, W - 40, H - 40), align="left")
    elif layout == "split":
        W, H = 1000, 560
        img = Image.new("RGB", (W, H), "#ffffff")
        d = ImageDraw.Draw(img)
        skin = "#e8b99a"
        for i, panel_x in enumerate((20, 510)):
            d.rectangle([panel_x, 20, panel_x + 470, 440], fill=colors[0])
            if spec["panel"] == "skin":
                d.ellipse([panel_x + 60, 60, panel_x + 410, 420], fill=skin)
                if i == 0:
                    for _ in range(45):
                        px, py = rnd.randint(panel_x + 110, panel_x + 360), rnd.randint(110, 370)
                        r = rnd.randint(4, 11)
                        d.ellipse([px - r, py - r, px + r, py + r], fill=rnd.choice(["#b5523b", "#8c4a2f", "#c9614a"]))
            else:  # body silhouette, wide then slim
                bw = 150 if i == 0 else 80
                cx = panel_x + 235
                d.ellipse([cx - 40, 50, cx + 40, 130], fill=skin)
                d.rounded_rectangle([cx - bw, 135, cx + bw, 330], 60, fill=skin)
                d.rectangle([cx - bw * 0.7, 320, cx - 8, 430], fill=skin)
                d.rectangle([cx + 8, 320, cx + bw * 0.7, 430], fill=skin)
            f = font(lang, "bold", 40)
            lab = lines[i]
            tw = d.textlength(lab, font=f)
            d.rounded_rectangle([panel_x + 235 - tw / 2 - 16, 380, panel_x + 235 + tw / 2 + 16, 432], 10, fill=colors[3])
            d.text((panel_x + 235 - tw / 2, 382), lab, font=f, fill="#ffffff")
        f = fit(d, lines[2], lang, "bold", 48, W - 80)
        tw = d.textlength(lines[2], font=f)
        d.text(((W - tw) / 2, 470), lines[2], font=f, fill=colors[2])
    elif layout in {"photo", "scene"}:
        W, H = 800, 800
        if layout == "photo":
            img = Image.open(PHOTOS / f"{spec['photo']}.png").convert("RGB").resize((W, H))
        else:
            img = gradient(W, H, colors[0], "#ffffff")
            draw_scene(ImageDraw.Draw(img), spec["scene"], colors, rnd)
        d = ImageDraw.Draw(img, "RGBA")
        d.rectangle([0, H - 190, W, H], fill=(0, 0, 0, 150))
        y = H - 170
        for i, line in enumerate(lines):
            f = fit(d, line, lang, "bold" if i == 0 else "regular", 56 if i == 0 else 36, W - 80)
            tw = d.textlength(line, font=f)
            d.text(((W - tw) / 2, y), line, font=f, fill="#ffffff")
            y += f.size * 1.45
    elif layout == "frames":
        img = render_frames(spec, lines, lang, colors, rnd)
    else:
        raise ValueError(layout)

    if spec.get("small"):
        d = ImageDraw.Draw(img)
        f = font(lang, "regular", 17)
        y = img.height - 30 * len(spec["small"])
        for line in spec["small"]:
            d.text((20, y), line, font=f, fill="#8a8a8a")
            y += 26
    extra = spec.get("extra")
    if extra == "flag":
        draw_flag(img, 24, 24, 150)
    elif extra == "flag_small":
        draw_flag(img, img.width - 84, img.height - 66, 60)
    elif extra == "lanterns":
        draw_lanterns(ImageDraw.Draw(img), 24, 10, 60)
    img.save(out, optimize=True)


def main():
    OUT.mkdir(exist_ok=True)
    n = 0
    for item in load_items():
        if item["kind"] != "image":
            continue
        photo = item["image"].get("photo")
        if photo and not (PHOTOS / f"{photo}.png").exists():
            print(f"skip {item['id']}: photo {photo}.png not made yet")
            continue
        render_item(item, item["image"]["lines"], OUT / f"{item['id']}.png")
        n += 1
        rev = item.get("revision")
        if rev and "image_lines" in rev:
            render_item(item, rev["image_lines"], OUT / f"{item['id']}-rev.png")
            n += 1
    print(f"rendered {n} images into {OUT}")


if __name__ == "__main__":
    main()
