"""Cong cu xem anh de review (dung Pillow, KHONG dung trong validator).

  py tools/viewer.py <delivery> <anh> [<anh> ...] [--out DIR] [--zoom 2] [--crop]

Moi anh ra mot file PNG co hai khung canh nhau:
  trai : anh + box DETECTION (do) kem ten lop
  phai : anh + mask PANOPTIC to mau, ten lop cua segment thing (xanh) kem ten lop
Neu --crop: chi giu vung quanh cac box/segment bi nghi (khong ap dung khi khong biet vung).
Ten anh co the la ten that (000000000139) hoac dang img_0001.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "validator"))
from common import Delivery  # noqa: E402


def font(size: int):
    for name in ("arial.ttf", "DejaVuSans.ttf"):
        try:
            return ImageFont.truetype(name, size)
        except OSError:
            pass
    return ImageFont.load_default()


def render(d: Delivery, stem: str, zoom: int, region=None) -> Image.Image:
    img = Image.open(d.image_path(stem)).convert("RGB")
    W, H = img.size
    mask = Image.open(d.mask_path(stem)).convert("RGB")
    if mask.size != img.size:
        mask = mask.resize(img.size, Image.NEAREST)
    left = img.copy()
    right = Image.blend(img, mask, 0.45)
    f = font(max(11, 5 * zoom))
    big = lambda im: im.resize((W * zoom, H * zoom), Image.LANCZOS)
    left, right = big(left), big(right)
    dl, dr = ImageDraw.Draw(left), ImageDraw.Draw(right)
    for cid, x0, y0, x1, y1 in d.box_pixels(stem):
        pts = [x0 * zoom, y0 * zoom, x1 * zoom, y1 * zoom]
        dl.rectangle(pts, outline=(255, 40, 40), width=2)
        dl.text((pts[0] + 2, pts[1] + 1), d.classes.get(cid, str(cid)), fill=(255, 255, 0), font=f, stroke_width=1, stroke_fill=(0, 0, 0))
    ann = d.pan_ann.get(stem, {"segments_info": []})
    for s in ann["segments_info"]:
        cat = d.categories.get(s["category_id"])
        if not cat or not cat.get("isthing"):
            continue
        x, y, w, h = s["bbox"]
        dr.rectangle([x * zoom, y * zoom, (x + w) * zoom, (y + h) * zoom], outline=(0, 255, 255), width=1)
        dr.text((x * zoom + 2, y * zoom + 1), cat["name"] + (" (crowd)" if s.get("iscrowd") else ""), fill=(255, 255, 255), font=f, stroke_width=1, stroke_fill=(0, 0, 0))
    if region:
        rx0, ry0, rx1, ry1 = [int(v * zoom) for v in region]
        left, right = left.crop((rx0, ry0, rx1, ry1)), right.crop((rx0, ry0, rx1, ry1))
    out = Image.new("RGB", (left.width + right.width + 6, left.height), (30, 30, 30))
    out.paste(left, (0, 0))
    out.paste(right, (left.width + 6, 0))
    ImageDraw.Draw(out).text((4, out.height - 14), f"{stem}  trai=DETECTION  phai=PANOPTIC", fill=(255, 255, 255), font=font(11))
    return out


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("delivery")
    ap.add_argument("images", nargs="*")
    ap.add_argument("--candidates", help="candidates.json: moi ung vien ra mot anh cat quanh vung nghi")
    ap.add_argument("--pad", type=int, default=40)
    ap.add_argument("--out", default="runs/viewer_out")
    ap.add_argument("--zoom", type=int, default=2)
    args = ap.parse_args()
    d = Delivery(Path(args.delivery))
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    if args.candidates:
        cands = json.loads(Path(args.candidates).read_text(encoding="utf-8"))["candidates"]
        for i, c in enumerate(cands):
            stem = c["image"]
            if not d.image_path(stem).is_file():
                continue
            W, H = d.size(stem)
            reg = c.get("region")
            if reg:
                x0, y0, x1, y1 = reg
                reg = (max(0, x0 - args.pad), max(0, y0 - args.pad), min(W, x1 + args.pad), min(H, y1 + args.pad))
            p = out / f"{i:02d}_{stem}_{c['guess']}.png"
            render(d, stem, args.zoom, reg).save(p)
            print(p, "|", c["reason"])
    for stem in args.images:
        if not d.image_path(stem).is_file():
            print(f"{stem}: khong co file anh")
            continue
        p = out / f"{stem}.png"
        render(d, stem, args.zoom).save(p)
        print(p)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
