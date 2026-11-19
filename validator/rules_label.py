"""Luat nhan detection: invalid_class, bbox_out_of_bounds, duplicate_box."""

from __future__ import annotations

from common import Delivery

NUM_CLASSES = 80
EDGE_TOL_PX = 1.0        # sai so lam tron duoi 1 pixel
DUP_SIZE_TOL_PX = 1.5    # cung kich thuoc
DUP_CENTER_TOL_PX = 3.5  # tam lech toi da


def check(d: Delivery) -> list[dict]:
    errors = []
    for stem in d.stems():
        if not d.label_path(stem).is_file():
            continue
        boxes = d.read_label(stem)
        size = d.size(stem)
        found = None
        if any(not (0 <= cid < NUM_CLASSES) for cid, *_ in boxes):
            found = "invalid_class"
        elif size:
            W, H = size
            for _, xc, yc, w, h in boxes:
                if ((xc - w / 2) * W < -EDGE_TOL_PX or (yc - h / 2) * H < -EDGE_TOL_PX
                        or (xc + w / 2) * W > W + EDGE_TOL_PX or (yc + h / 2) * H > H + EDGE_TOL_PX):
                    found = "bbox_out_of_bounds"
                    break
        if not found and size:
            W, H = size
            for i in range(len(boxes)):
                for j in range(i + 1, len(boxes)):
                    a, b = boxes[i], boxes[j]
                    if a[0] != b[0]:
                        continue
                    if (abs(a[3] - b[3]) * W <= DUP_SIZE_TOL_PX and abs(a[4] - b[4]) * H <= DUP_SIZE_TOL_PX
                            and abs(a[1] - b[1]) * W <= DUP_CENTER_TOL_PX and abs(a[2] - b[2]) * H <= DUP_CENTER_TOL_PX):
                        found = "duplicate_box"
                        break
                if found:
                    break
        if found:
            errors.append({"type": found, "target": stem})
    return errors
