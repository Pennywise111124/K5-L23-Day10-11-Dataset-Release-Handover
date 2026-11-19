"""viewer.py — N5: Viewer ảnh delivery (detection box + panoptic segment).

Dùng Pillow (PIL). Không import urllib/socket/requests.
Không đọc _private/ hay data_source/.

CLI:
    python tools/viewer.py <tên_ảnh> --delivery <delivery_dir> [--crop <box_index>]

Ví dụ:
    python tools/viewer.py 000000000139 --delivery runs/r11007/delivery
    python tools/viewer.py img_0001     --delivery runs/r33/delivery
    python tools/viewer.py 000000000139 --delivery runs/r11007/delivery --crop 0

Kết quả lưu tại runs/viewer_out/<tên_ảnh>.png
"""

import sys
import json
import argparse
from pathlib import Path

try:
    from PIL import Image, ImageDraw, ImageFont
except ImportError:
    sys.exit("Lỗi: Pillow chưa cài. Chạy: py -m pip install pillow")

# ---------------------------------------------------------------------------
# Màu sắc
# ---------------------------------------------------------------------------
BOX_COLOR = (255, 80, 0)        # Cam — detection box YOLO
BOX_TEXT_BG = (255, 80, 0)
BOX_TEXT_FG = (255, 255, 255)
SEG_COLORS = [                  # Viền segment panoptic — xoay vòng
    (0, 200, 255),
    (50, 255, 100),
    (255, 220, 0),
    (200, 0, 255),
    (0, 255, 200),
    (255, 0, 150),
    (100, 180, 255),
]
SEG_WIDTH = 2                   # Độ dày viền segment


# ---------------------------------------------------------------------------
# Đọc dữ liệu delivery
# ---------------------------------------------------------------------------

def load_classes(delivery_dir: Path) -> list[str]:
    """Đọc classes.txt -> list tên lớp theo class_id."""
    path = delivery_dir / "classes.txt"
    classes = []
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if line:
            # Dạng "0 person" hoặc chỉ "person"
            parts = line.split(None, 1)
            if len(parts) == 2 and parts[0].isdigit():
                classes.append(parts[1])
            else:
                classes.append(parts[0])
    return classes


def load_panoptic_index(delivery_dir: Path) -> dict:
    """Đọc panoptic.json -> {image_stem: annotation_dict} và {cat_id: name}."""
    path = delivery_dir / "panoptic.json"
    data = json.loads(path.read_text(encoding="utf-8"))

    # Map image_id -> file_name stem
    id_to_stem = {}
    for img in data.get("images", []):
        stem = Path(img["file_name"]).stem
        id_to_stem[img["id"]] = stem

    # Map annotation by image stem
    ann_by_stem = {}
    for ann in data.get("annotations", []):
        stem = id_to_stem.get(ann["image_id"], ann.get("file_name", ""))
        if not stem:
            stem = Path(ann.get("file_name", "")).stem
        ann_by_stem[stem] = ann

    # Map category_id -> name
    cat_map = {c["id"]: c["name"] for c in data.get("categories", [])}

    return ann_by_stem, cat_map


def load_yolo_labels(label_path: Path) -> list[tuple]:
    """Đọc YOLO .txt -> list (class_id, cx, cy, w, h) normalized."""
    if not label_path.exists():
        return []
    boxes = []
    for line in label_path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line:
            continue
        parts = line.split()
        if len(parts) < 5:
            continue
        try:
            cls = int(parts[0])
            cx, cy, bw, bh = float(parts[1]), float(parts[2]), float(parts[3]), float(parts[4])
            boxes.append((cls, cx, cy, bw, bh))
        except ValueError:
            continue
    return boxes


# ---------------------------------------------------------------------------
# Vẽ mask viền segment từ PNG
# ---------------------------------------------------------------------------

def _read_mask_pixels(mask_path: Path):
    """Đọc mask PNG bằng Pillow (RGB) -> (width, height, pixels_bytes)."""
    img = Image.open(mask_path).convert("RGB")
    w, h = img.size
    pixels = img.tobytes()  # bytes: R G B R G B ...
    return w, h, pixels


def _seg_id_at(pixels, index):
    """Tính segment id từ vị trí byte."""
    r = pixels[index]
    g = pixels[index + 1]
    b = pixels[index + 2]
    return r + g * 256 + b * 65536


def draw_segment_outlines(draw: "ImageDraw.Draw", mask_path: Path,
                          segments_info: list, cat_map: dict,
                          scale_x: float, scale_y: float,
                          img_w: int, img_h: int):
    """Vẽ viền segment panoptic lên draw object (đã scale)."""
    if not mask_path.exists():
        return

    mw, mh, pixels = _read_mask_pixels(mask_path)

    # Nhóm pixel theo segment id
    # Dùng set biên: pixel khác id với láng giềng → là biên
    seg_color_map = {}
    for i, seg in enumerate(segments_info):
        seg_color_map[seg["id"]] = SEG_COLORS[i % len(SEG_COLORS)]

    # Tìm pixel biên: so sánh với pixel phải và pixel dưới
    border_pixels = {}  # (x, y) -> color
    stride = mw * 3
    for y in range(mh):
        for x in range(mw):
            idx = (y * mw + x) * 3
            sid = _seg_id_at(pixels, idx)
            if sid == 0:
                continue
            # So sánh với pixel bên phải
            if x + 1 < mw:
                idx_r = idx + 3
                sid_r = _seg_id_at(pixels, idx_r)
                if sid_r != sid:
                    color = seg_color_map.get(sid, (200, 200, 200))
                    border_pixels[(x, y)] = color
                    border_pixels[(x + 1, y)] = seg_color_map.get(sid_r, (200, 200, 200))
            # So sánh với pixel bên dưới
            if y + 1 < mh:
                idx_d = idx + stride
                sid_d = _seg_id_at(pixels, idx_d)
                if sid_d != sid:
                    color = seg_color_map.get(sid, (200, 200, 200))
                    border_pixels[(x, y)] = color
                    border_pixels[(x, y + 1)] = seg_color_map.get(sid_d, (200, 200, 200))

    # Vẽ lên ảnh đã scale
    for (x, y), color in border_pixels.items():
        sx = int(x * scale_x)
        sy = int(y * scale_y)
        draw.rectangle([sx, sy, sx + max(1, int(scale_x)), sy + max(1, int(scale_y))], fill=color)


# ---------------------------------------------------------------------------
# Hàm chính
# ---------------------------------------------------------------------------

def resolve_stem(image_arg: str, delivery_dir: Path) -> str | None:
    """Tìm stem tên ảnh (không đuôi) trong delivery/images/."""
    # Bỏ đuôi nếu có
    stem = Path(image_arg).stem

    # Kiểm tra trực tiếp
    for ext in (".jpg", ".jpeg", ".png"):
        if (delivery_dir / "images" / f"{stem}{ext}").exists():
            return stem

    # Nếu tên dạng img_0001 → tìm file đầu tiên trong images/
    # (đề ẩn không biết tên thật, cần mapping)
    # Thử tìm bằng cách đọc manifest
    manifest_path = delivery_dir / "manifest.json"
    if manifest_path.exists():
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        items = manifest.get("items", {})
        # items là dict: stem -> info
        if isinstance(items, dict):
            if stem in items:
                return stem
            # Thử theo thứ tự nếu dạng img_0001
            if stem.startswith("img_"):
                try:
                    idx = int(stem.split("_", 1)[1]) - 1  # img_0001 → index 0
                    keys = list(items.keys())
                    if 0 <= idx < len(keys):
                        return keys[idx]
                except (ValueError, IndexError):
                    pass

    return stem  # Trả về stem gốc, để downstream xử lý lỗi


def draw_image(image_arg: str, delivery_dir: Path, out_dir: Path,
               crop_box: int | None = None, min_size: int = 480):
    """Hàm vẽ chính: detection box + panoptic segment, lưu PNG."""
    stem = resolve_stem(image_arg, delivery_dir)

    # Tìm file ảnh
    img_path = None
    for ext in (".jpg", ".jpeg", ".png"):
        p = delivery_dir / "images" / f"{stem}{ext}"
        if p.exists():
            img_path = p
            break
    if img_path is None:
        print(f"[viewer] Không tìm thấy ảnh: {stem} trong {delivery_dir / 'images'}")
        return

    # Tải ảnh gốc
    orig = Image.open(img_path).convert("RGB")
    orig_w, orig_h = orig.size

    # Phóng to 2–3× nếu ảnh nhỏ (~240×320)
    scale = 1.0
    if orig_w < 400 or orig_h < 400:
        scale = min(3.0, min_size / max(orig_w, orig_h, 1))
    elif orig_w < 640 or orig_h < 640:
        scale = max(1.0, min(2.0, min_size / max(orig_w, orig_h, 1)))

    new_w = max(1, int(orig_w * scale))
    new_h = max(1, int(orig_h * scale))
    img = orig.resize((new_w, new_h), Image.LANCZOS)

    draw = ImageDraw.Draw(img)

    # Thử tải font; fallback về default
    try:
        font = ImageFont.truetype("arial.ttf", max(12, int(14 * scale)))
        font_small = ImageFont.truetype("arial.ttf", max(10, int(12 * scale)))
    except (OSError, IOError):
        font = ImageFont.load_default()
        font_small = font

    # --- Load classes ---
    classes = load_classes(delivery_dir)

    # --- Load panoptic ---
    ann_by_stem, cat_map = load_panoptic_index(delivery_dir)
    annotation = ann_by_stem.get(stem, {})
    segments_info = annotation.get("segments_info", [])

    # --- Vẽ viền segment panoptic ---
    mask_path = delivery_dir / "masks" / f"{stem}.png"
    draw_segment_outlines(draw, mask_path, segments_info, cat_map,
                          scale_x=scale, scale_y=scale,
                          img_w=new_w, img_h=new_h)

    # Vẽ legend segment ở góc trên phải
    legend_x = new_w - 160
    legend_y = 5
    for i, seg in enumerate(segments_info):
        cat_name = cat_map.get(seg["category_id"], f"cat{seg['category_id']}")
        color = SEG_COLORS[i % len(SEG_COLORS)]
        draw.rectangle([legend_x, legend_y, legend_x + 12, legend_y + 12], fill=color)
        draw.text((legend_x + 15, legend_y), cat_name, fill=color, font=font_small)
        legend_y += 16
        if legend_y > new_h - 20:
            break

    # --- Load YOLO labels ---
    label_path = delivery_dir / "labels" / f"{stem}.txt"
    boxes = load_yolo_labels(label_path)

    # --- Vẽ detection box ---
    for i, (cls_id, cx, cy, bw, bh) in enumerate(boxes):
        cls_name = classes[cls_id] if cls_id < len(classes) else f"cls{cls_id}"

        # Chuyển sang pixel (ảnh đã scale)
        x1 = int((cx - bw / 2) * new_w)
        y1 = int((cy - bh / 2) * new_h)
        x2 = int((cx + bw / 2) * new_w)
        y2 = int((cy + bh / 2) * new_h)
        x1, y1 = max(0, x1), max(0, y1)
        x2, y2 = min(new_w - 1, x2), min(new_h - 1, y2)

        # Vẽ hình chữ nhật
        for t in range(2):  # Dày 2px
            draw.rectangle([x1 - t, y1 - t, x2 + t, y2 + t], outline=BOX_COLOR)

        # Label box
        label = f"[{i}]{cls_name}"
        try:
            bbox = draw.textbbox((x1, y1 - 16), label, font=font)
            lw = bbox[2] - bbox[0]
            lh = bbox[3] - bbox[1]
        except AttributeError:
            lw, lh = len(label) * 7, 14
        ty = max(0, y1 - lh - 2)
        draw.rectangle([x1, ty, x1 + lw + 4, ty + lh + 2], fill=BOX_COLOR)
        draw.text((x1 + 2, ty + 1), label, fill=BOX_TEXT_FG, font=font)

    # --- Chế độ crop ---
    if crop_box is not None and 0 <= crop_box < len(boxes):
        cls_id, cx, cy, bw, bh = boxes[crop_box]
        pad = 0.15  # padding 15%
        x1 = max(0, int((cx - bw / 2 - pad * bw) * new_w))
        y1 = max(0, int((cy - bh / 2 - pad * bh) * new_h))
        x2 = min(new_w, int((cx + bw / 2 + pad * bw) * new_w))
        y2 = min(new_h, int((cy + bh / 2 + pad * bh) * new_h))
        img = img.crop((x1, y1, x2, y2))

    # --- Lưu kết quả ---
    out_dir.mkdir(parents=True, exist_ok=True)
    suffix = f"_crop{crop_box}" if crop_box is not None else ""
    out_path = out_dir / f"{stem}{suffix}.png"
    img.save(out_path)
    print(f"[viewer] Đã lưu: {out_path}  (scale={scale:.1f}×  {orig_w}×{orig_h} → {img.size[0]}×{img.size[1]})")
    print(f"         Detection boxes: {len(boxes)}  |  Panoptic segments: {len(segments_info)}")
    return out_path


# ---------------------------------------------------------------------------
# CLI entry-point
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(
        description="Viewer ảnh delivery: vẽ detection box + panoptic segment."
    )
    parser.add_argument("image", help="Tên ảnh (có hoặc không đuôi, hoặc img_0001)")
    parser.add_argument("--delivery", required=True, type=Path,
                        help="Đường dẫn tới thư mục delivery/")
    parser.add_argument("--crop", type=int, default=None,
                        help="Index box cần cắt phóng to (0-based)")
    parser.add_argument("--out", type=Path, default=Path("runs/viewer_out"),
                        help="Thư mục lưu ảnh kết quả (mặc định: runs/viewer_out)")
    args = parser.parse_args()

    if not args.delivery.exists():
        sys.exit(f"[viewer] Không tìm thấy delivery dir: {args.delivery}")

    draw_image(args.image, args.delivery, args.out, crop_box=args.crop)


if __name__ == "__main__":
    main()

