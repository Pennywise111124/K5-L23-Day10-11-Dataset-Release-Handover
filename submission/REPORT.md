# Báo cáo nhóm 11

## 1. Số liệu luyện tập
- F1 theo seed (rule / cross_check / overall): <<seed: ... / ... / ...>>
- Số ứng viên trên lô sạch (`--no-faults`): <<...>>; hàng đợi trên seed luyện tập: <<... ảnh>>
- Ngưỡng đã chọn và cách chọn (không dùng `_private`): <<...>>

## 2. Vì sao báo hết ứng viên làm F1 giảm?
<<Trả lời bằng số của nhóm.>>

## 3. Quyết định và lineage
<<QC v1 a/b, kết luận, vì sao R-021 phải xem lại hoặc train lại.>>

## 4. Hash chứng minh gì, không chứng minh gì?
<<>>

## 5. Truy vết
Công cụ: `py -X utf8 tools/trace_query.py <delivery> --out trace.json` (chỉ đọc `delivery/`, không đọc `_private/`, không dùng `masks/`, không ghi cứng tên lớp/cảnh/ảnh).

Tiêu chí:
- **Lớp bị đổi quy tắc**: tên lớp trong `classes.txt` được nhắc ở mục phiên bản mới nhất của `guideline/changelog.md` (đối chiếu với lớp trong `incoming/ticket.md`). Seed 11007: `bottle`, đổi ở v1.3.
- **Guideline cũ lấy theo job** (`jobs.csv`): job có guideline nhỏ hơn phiên bản đổi quy tắc. Seed 11007: J01–J04 (v1.2). Không lấy `guideline_version` của từng ảnh vì chính trường đó có thể sai (lỗi `guideline_mismatch`); người gán làm việc theo guideline của job được giao.
- **"Có lớp"** = ảnh có ≥ 1 box detection của lớp đó trong `labels/` (không tính mask): ticket nói về box bị bỏ sót trong detection.
- **tier_a**: ảnh thuộc các cảnh team AI nêu trong ticket (seed 11007: scene_157, scene_511) + job guideline cũ + có lớp đó → 2 ảnh.
- **tier_b**: ảnh còn lại cùng điều kiện (job guideline cũ + có lớp đó) nhưng chưa ai báo → 4 ảnh. Không được bỏ tầng b vì nguyên nhân gốc nằm ở job còn guideline cũ, không ở riêng hai cảnh trong ticket.
- **notify**: người gán và người kiểm của mọi job chứa ảnh ở cả hai tầng. Seed 11007: A02, A03, A04, Q01, Q03.

Kiểm tính tổng quát: chạy không sửa code trên seed 11007, 11 (`wine glass`), 22 (`truck`), 33 `--opaque` (`cup`, tên `img_0001`, job cũ chỉ J01–J03), 3007 và lô sạch; `score_findings.py` cho F1 truy vết tier_a / tier_b / notify = 1,0 / 1,0 / 1,0 trên cả 6 lô.

## 6. Bug hoặc điểm chưa rõ trong lab (nếu có)
<<>>
