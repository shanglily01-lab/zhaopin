"""把 D4 / D6 裁成两侧广告，底部贴上用户提供的二维码原图，不再缩放。"""
from __future__ import annotations

import shutil
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parent.parent
SRC = Path(r"C:\Users\Win10\Desktop\发推资料\chainpoker_blonde_tg_en")
QR_SRC = Path(
    r"C:\Users\Win10\.cursor\projects\d-zhaopin\assets"
    r"\c__Users_Win10_AppData_Roaming_Cursor_User_workspaceStorage_abb20c22ae0492156ff341a9a53cc341_images_image-5ac13b0e-a816-4d94-a6b9-bb26e1d1a9f0.png"
)
OUT = ROOT / "app" / "static" / "img" / "ads"

W, H = 680, 2800


def cover_top(im: Image.Image, tw: int, th: int) -> Image.Image:
    iw, ih = im.size
    scale = max(tw / iw, th / ih)
    nw, nh = int(iw * scale + 0.5), int(ih * scale + 0.5)
    im = im.resize((nw, nh), Image.Resampling.LANCZOS)
    left = max(0, (nw - tw) // 2)
    top = 0 if nh >= th else 0
    if top + th > nh:
        top = max(0, nh - th)
    return im.crop((left, top, left + tw, top + th))


def compose(src_name: str, dest_name: str, qr: Image.Image) -> None:
    photo = Image.open(SRC / src_name).convert("RGB")
    pw, ph = photo.size
    photo = photo.crop((0, 0, pw, int(ph * 0.76)))

    qw, qh = qr.size
    card_pad_x, card_pad_top, card_pad_bot = 28, 24, 64
    card_w = qw + card_pad_x * 2
    card_h = qh + card_pad_top + card_pad_bot
    art_h = H - card_h - 20
    full = Image.new("RGB", (W, H), (8, 12, 10))
    full.paste(cover_top(photo, W, art_h), (0, 0))

    fade = Image.new("L", (1, 180))
    for i in range(180):
        fade.putpixel((0, i), int(255 * (i / 179) ** 1.3))
    shade = Image.new("RGB", (W, 180), (8, 12, 10))
    full.paste(shade, (0, art_h - 140), fade.resize((W, 180)))

    draw = ImageDraw.Draw(full)
    x0 = (W - card_w) // 2
    y0 = H - card_h - 8
    draw.rounded_rectangle(
        (x0, y0, x0 + card_w, y0 + card_h), radius=28, fill=(255, 255, 255)
    )
    full.paste(qr, (x0 + card_pad_x, y0 + card_pad_top))

    font = ImageFont.truetype(r"C:\Windows\Fonts\msyhbd.ttc", 30)
    label = "扫码进入"
    tw = font.getlength(label)
    draw.text(((W - tw) / 2, y0 + card_pad_top + qh + 8), label, font=font, fill=(26, 20, 8))

    dest = OUT / dest_name
    full.save(dest, "PNG")
    print("wrote", dest.name, full.size, dest.stat().st_size)


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(QR_SRC, OUT / "qr.png")
    qr = Image.open(OUT / "qr.png").convert("RGB")
    print("qr", qr.size)
    compose("D4.png", "side-left.png", qr)
    compose("D6.png", "side-right.png", qr)


if __name__ == "__main__":
    main()
