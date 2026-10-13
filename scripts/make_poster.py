"""Compose a shareable ChainPoker poster image (slogan + photo + QR)."""
from __future__ import annotations

from pathlib import Path

import segno
from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "app" / "static" / "img" / "chainpoker-hao-bao.png"
PHOTO = ROOT / "app" / "static" / "img" / "chainpoker-poster.png"
URL = "https://chainpoker.io?wsp=eyJjaWQiOiIxMDAwMSIsImFpZCI6IjUwMDA1In0="

W, H = 2160, 2880
GOLD = (232, 197, 71)
CREAM = (255, 248, 231)
DARK = (7, 12, 10)
INK = (42, 29, 4)


def font(path: str, size: int, index: int = 0) -> ImageFont.FreeTypeFont:
    return ImageFont.truetype(path, size=size, index=index)


def cover(im: Image.Image, tw: int, th: int, ax: float = 0.52, ay: float = 0.16) -> Image.Image:
    iw, ih = im.size
    scale = max(tw / iw, th / ih)
    nw, nh = int(iw * scale + 0.5), int(ih * scale + 0.5)
    im = im.resize((nw, nh), Image.Resampling.LANCZOS)
    left = max(0, min(int((nw - tw) * ax), nw - tw))
    top = max(0, min(int((nh - th) * ay), nh - th))
    return im.crop((left, top, left + tw, top + th))


def draw_spaced(draw: ImageDraw.ImageDraw, text: str, xy: tuple[int, int], fnt, fill, spacing: int) -> None:
    x, y = xy
    for ch in text:
        draw.text((x, y), ch, font=fnt, fill=fill)
        x += int(fnt.getlength(ch)) + spacing


def shadow_text(draw, xy, text, fnt, fill, offset=5):
    x, y = xy
    draw.text((x + offset, y + offset), text, font=fnt, fill=(0, 0, 0))
    draw.text((x, y), text, font=fnt, fill=fill)


def make_qr(size: int) -> Image.Image:
    path = ROOT / "app" / "static" / "img" / "_qr_tmp.png"
    qr = segno.make(URL, error="m")
    qr.save(path, scale=14, border=2, dark="#1a1408", light="#fffaf0")
    im = Image.open(path).convert("RGB").resize((size, size), Image.Resampling.NEAREST)
    path.unlink(missing_ok=True)
    return im


def main() -> None:
    canvas = cover(Image.open(PHOTO).convert("RGB"), W, H)

    # Bottom cinematic fade
    band = Image.new("L", (1, H))
    for y in range(H):
        t = (y - H * 0.46) / (H * 0.52)
        t = 0 if t < 0 else 1 if t > 1 else t
        band.putpixel((0, y), int(236 * (t ** 1.12)))
    canvas = Image.composite(Image.new("RGB", (W, H), DARK), canvas, band.resize((W, H), Image.Resampling.BILINEAR))

    draw = ImageDraw.Draw(canvas)

    # Gold inner frame
    m = 54
    draw.rounded_rectangle((m, m, W - m, H - m), radius=28, outline=GOLD, width=4)

    title = font(r"C:\Windows\Fonts\msyhbd.ttc", 176)
    sub = font(r"C:\Windows\Fonts\msyhbd.ttc", 118)
    kicker = font(r"C:\Windows\Fonts\timesbd.ttf", 36)
    latin = font(r"C:\Windows\Fonts\georgiab.ttf", 112)
    hint = font(r"C:\Windows\Fonts\msyh.ttc", 36)
    btn = font(r"C:\Windows\Fonts\msyhbd.ttc", 44)

    left = 160
    y = 1680
    draw_spaced(draw, "CHAINPOKER", (left, y), kicker, GOLD, 18)

    y = 1768
    shadow_text(draw, (left, y), "玩德州", title, CREAM, 6)
    y = 1988
    shadow_text(draw, (left, y), "就来", sub, CREAM, 5)
    y = 2140
    shadow_text(draw, (left, y), "ChainPoker", latin, GOLD, 5)

    y = 2290
    draw.text((left, y), "扫码开桌  ·  立即开玩", font=hint, fill=(215, 197, 138))

    # Gold CTA pill
    bx, by, bw, bh = 160, 2390, 520, 96
    draw.rounded_rectangle((bx, by, bx + bw, by + bh), radius=48, fill=GOLD)
    tw = btn.getlength("立即开桌")
    draw.text((bx + (bw - tw) / 2, by + 18), "立即开桌", font=btn, fill=INK)

    # QR card
    qr = make_qr(360)
    qx, qy = W - 160 - 400, 2288
    draw.rounded_rectangle((qx, qy, qx + 400, qy + 458), radius=28, fill=(255, 250, 240))
    canvas.paste(qr, (qx + 20, qy + 20))
    d2 = ImageDraw.Draw(canvas)
    label = "扫码进入"
    lw = hint.getlength(label)
    d2.text((qx + (400 - lw) / 2, qy + 396), label, font=hint, fill=INK)

    OUT.parent.mkdir(parents=True, exist_ok=True)
    canvas.save(OUT, "PNG", optimize=True)
    print("wrote", OUT, canvas.size)


if __name__ == "__main__":
    main()
