# Báo cáo nhóm 11

Seed luyện tập: **11007**, release v1 `lab250_d3cc716c084b` (máy N1, lô dùng để nộp). Ngoài ra nhóm đo trên seed thử 11 và 22, lô sạch seed 5 (`--no-faults`, 50 ảnh) và lô opaque seed 33. `score_findings.py` chỉ in F1 làm tròn một chữ số; nhóm chỉ dùng nó để chấm cả lô, không dò từng ảnh.

QA chạy trên máy thành viên N6, nơi lô seed 11007 có id `lab250_1948a084c5ce` (xem mục 6). Nhóm đã đối chiếu: `candidates.json` giống hệt file của N1, 10 lỗi luật trùng với phần lỗi luật trong `submission/r11007/errors.json`, `trace.json` giống hệt. Vì vậy số liệu dưới đây áp dụng cho bài nộp.

## 1. Số liệu luyện tập

**Lỗi luật** (`validator/validate.py`, chỉ thư viện chuẩn + `scripts/pngutil.py`):

| Lô | Lỗi luật báo | F1 lỗi luật | Thời gian chạy |
|---|---:|---:|---:|
| 11007 | 10 | 1,0 | 60 s |
| 11 | 13 | 1,0 | 57 s |
| 22 | 9 | 1,0 | 58 s |
| clean (50 ảnh, không lỗi) | 0 | — | 13 s |
| 33 `--opaque` (tên `img_0001`) | 11, không lỗi khi chạy | — | 58 s |

Loại lỗi luật trên seed 11007: `missing_image` 2, `invalid_category_id` 2, `wrong_hash` 1, `guideline_mismatch` 1, `scene_leak` 1, `bbox_out_of_bounds` 1, `duplicate_box` 1, `thing_overlap` 1.

**F1 theo nhóm lỗi** (rule / cross_check / overall):

| Seed | Chỉ lỗi luật (`rules.json`) | Sau review (`errors.json` từ `merge_review.py`) |
|---|---|---|
| 11007 | 1,0 / — / 0,7 | **1,0 / 0,8 / 0,9** (17 mục) |
| 11 | 1,0 / — / 0,8 | không review (chỉ dùng để thử validator) |
| 22 | 1,0 / — / 0,7 | không review (chỉ dùng để thử validator) |

Review seed 11007 (`submission/r11007/review_log.csv`, đủ 6 người): 10 ảnh trong hàng đợi, **7 `confirmed`** (2 `class_swap`, 2 `category_swap`, 2 `missing_box`, 1 `bbox_drift`) và **3 `rejected`**. Ba ca rejected đều là lệch tự nhiên do vật chứa nhau: bát chứa bông cải, người trong thùng xe tải, ly trên bàn ăn. Đây là bằng chứng phân biệt lỗi với lệch tự nhiên.

**Ứng viên đối chiếu** (`validator/crosscheck.py`):
- Lô sạch: **0 ứng viên** trên 50 ảnh.
- Hàng đợi trên seed luyện tập: **10 ảnh** (11007; 7 `class_swap`, 2 `missing_box`, 1 `bbox_drift`), 8 ảnh (seed 11), 11 ảnh (seed 22). Cả ba đều dưới mức ~80 ảnh mà 6 người xem kịp.
- Ngưỡng đang dùng (hằng số đầu `crosscheck.py`): segment nhỏ hơn `MIN_SEG = 800` px thì bỏ; `missing_box` chỉ báo khi segment thing không có box và ≥ `MIN_MISSING = 3500` px; tỉ lệ pixel segment nằm trong box ≥ `IN_MATCH = 0,55` thì coi là ghép; dưới `IN_DRIFT = 0,72` thì nghi `bbox_drift`; một segment có ≥ `IN_MERGE = 0,22` pixel nằm trong box cùng lớp thứ hai thì nghi `instance_merge`; bỏ segment `iscrowd`.
- Cách chọn ngưỡng: lô sạch chỉ có lệch tự nhiên của COCO (vật bị che, crowd), nên mọi ứng viên ở đó đều là báo thừa. Với ngưỡng trên, lô sạch ra 0 ứng viên và hàng đợi seed luyện tập ≤ 11 ảnh, đủ nhỏ để 6 người xem hết. Sau review, F1 lỗi gán nhãn seed 11007 ≈ 0,8, nên ngưỡng chặt chưa làm sót nhiều lỗi thật.
- `crosscheck` không tách được `class_swap` với `category_swap` (cả hai đều là "cùng chỗ, khác lớp"), nên mọi ca lệch lớp được đưa ra dưới dạng `guess = class_swap`. Người xem quyết bằng ảnh: 2 ca hoá ra panoptic sai, ghi `category_swap` (ví dụ `000000016598`: vật là cà vạt, detection ghi `tie` đúng, panoptic ghi `zebra`).

## 2. Vì sao báo hết ứng viên làm F1 giảm?

Nhóm đo trực tiếp: nộp `rules.json` cộng **toàn bộ** ứng viên (lấy `guess` làm loại lỗi, không xem ảnh):

| Seed | Số mục nộp | F1 lỗi gán nhãn | F1 tổng |
|---|---:|---:|---:|
| 11007 | 20 (10 luật + 10 ứng viên) | 0,4 | 0,7 |
| 11 | 21 | 0,3 | 0,8 |
| 22 | 20 | 0,2 | 0,6 |

Giải thích:
- Một ứng viên chỉ là dấu hiệu detection và panoptic không khớp. Nhiều chỗ không khớp là lệch tự nhiên của COCO (vật bị che, crowd, box vẽ rộng), không phải lỗi. Báo hết thì các ca đó thành **FP**, nên precision = TP / (TP + FP) tụt.
- Báo hết **không làm tăng recall**: ca thật nào ngưỡng không bắt được thì vẫn thiếu.
- Lỗi chỉ tính đúng khi **đúng loại**. Ví dụ cùng một chỗ lệch lớp, nếu detection sai là `class_swap`, nếu panoptic sai là `category_swap`. `guess` của máy chưa biết bên nào sai; chỉ người xem ảnh mới quyết được. Đoán sai loại vừa thành một FP vừa còn một FN.
- Vì F1 là trung bình điều hoà của precision và recall, precision tụt mà recall không tăng thì F1 giảm. Ví dụ seed 11007: F1 lỗi gán nhãn chỉ ≈ 0,4 khi báo hết. Vì thế nhóm chỉ đưa vào `errors.json` những dòng `confirmed` sau khi xem ảnh.

So sánh trên seed 11007:

| Cách nộp | Số mục | F1 lỗi gán nhãn | F1 tổng |
|---|---:|---:|---:|
| Báo hết 10 ứng viên theo `guess` | 20 | 0,4 | 0,7 |
| Chỉ dòng `confirmed` sau xem ảnh | 17 | **0,8** | **0,9** |

Xem ảnh vừa bỏ được 3 FP (ca `rejected`), vừa sửa được loại cho 2 ca `category_swap` mà `guess` ghi sai thành `class_swap`.

## 3. Quyết định và lineage

- QC v1 = số mục trong `errors.json` / 250 ảnh. Mỗi ảnh tối đa một lỗi; mỗi `scene_leak` tính một ảnh.
- **QC v1 = 17/250 = 6,8%**: 10 lỗi luật và 7 lỗi gán nhãn `confirmed`. Số này lớn hơn ngưỡng 2% (tức tối đa 5 lỗi), nên **v1: HOLD, không Release**.
- Dùng tỉ lệ chứ không dùng số lỗi tuyệt đối, vì lô to nhỏ khác nhau: 5 lỗi trên 250 ảnh (2%) khác hẳn 5 lỗi trên 25 000 ảnh.
- Lineage (`submission/lineage.jsonl`) có đủ 4 dòng theo thứ tự: `inject` v1, `train R-021`, `decision HOLD` cho `lab250_d3cc716c084b`, `release lab250_d3cc716c084b_v2` với `parent lab250_d3cc716c084b`.
- v2: 241 ảnh, 1682 nhãn. 9 ảnh lỗi nhãn detection hoặc thiếu file vào `rework_queue.csv`, giao lại đúng người gán/kiểm theo `jobs.csv`. 5 ảnh chỉ lỗi panoptic ở lại v2 và được báo cho team panoptic. Trong v2 không còn lỗi detection đã biết, nên kết luận v2 là Release.
- **Vì sao R-021 phải xem lại hoặc train lại:** R-021 đã train trên v1, nghĩa là trọng số đã học từ cả các nhãn sai (box thiếu, sai lớp, lệch). Sửa dataset ở v2 không đổi được trọng số đã học. Model chỉ hết bị ảnh hưởng khi được đánh giá lại trên dữ liệu đúng, hoặc train lại trên v2.

## 4. Hash chứng minh gì, không chứng minh gì?

- **Chứng minh:** byte của file hiện tại giống hệt byte lúc lập manifest. File không bị sửa, hỏng hay tráo sau khi chốt. Vì thế `wrong_hash` phải tính lại sha256 từ byte thật (mở `rb`) rồi so với manifest, không chỉ kiểm chuỗi dài 64 ký tự. `.sha256` của gói v2 cho phép người nhận kiểm lại đúng gói đã bàn giao.
- **Không chứng minh:** nhãn đúng. Một box sai lớp hay thiếu box vẫn có hash khớp nếu không ai đụng vào file sau khi lập manifest. Hash là kiểm toàn vẹn, không phải kiểm chất lượng. Chất lượng phải kiểm bằng validator và mắt người.
- **Không ghi đè v1:** `release_id` = hash của `manifest.json` + `metadata.json`. Sửa `delivery/` là đổi id, làm hỏng truy vết của R-021 và của mọi bên đã tham chiếu v1. Vì vậy mọi sửa đổi nằm trong `handover/<id>_v2/`, ảnh và nhãn copy nguyên byte (trừ ảnh rework), lineage ghi `release` v2 với `--parent` v1.

## 5. Truy vết

Công cụ: `py -X utf8 tools/trace_query.py <delivery> --out trace.json`. Chỉ đọc `delivery/`, không đọc `_private/`, không dùng `masks/`, không ghi cứng tên lớp, cảnh hay ảnh.

Tiêu chí:
- **Lớp bị đổi quy tắc:** tên lớp trong `classes.txt` được nhắc ở mục phiên bản mới nhất của `guideline/changelog.md`. Seed 11007: `bottle`, đổi ở v1.3.
- **Guideline cũ lấy theo job** (`jobs.csv`): job có guideline nhỏ hơn phiên bản đổi quy tắc. Seed 11007: J01–J04 (v1.2). Không lấy `guideline_version` của từng ảnh vì chính trường đó có thể sai (lỗi `guideline_mismatch`); người gán làm việc theo guideline của job được giao.
- **"Có lớp"** = ảnh có ≥ 1 box detection của lớp đó trong `labels/` (không tính mask), vì ticket nói về box bị bỏ sót trong detection.
- **tier_a:** ảnh thuộc các cảnh team AI nêu trong ticket (seed 11007: scene_157, scene_511), thuộc job guideline cũ và có lớp đó. Kết quả: 2 ảnh.
- **tier_b:** ảnh còn lại cùng điều kiện (job guideline cũ, có lớp đó) nhưng chưa ai báo. Kết quả: 4 ảnh. Không được bỏ tầng b vì nguyên nhân gốc nằm ở job còn guideline cũ, không chỉ ở hai cảnh trong ticket.
- **notify:** người gán và người kiểm của mọi job chứa ảnh ở cả hai tầng. Seed 11007: A02, A03, A04, Q01, Q03.

Kiểm tính tổng quát: chạy không sửa code trên seed 11007, 11 (`wine glass`), 22 (`truck`), 33 `--opaque` (`cup`, tên `img_0001`, job cũ chỉ J01–J03), 3007 và lô sạch. `score_findings.py` cho F1 truy vết tier_a / tier_b / notify = 1,0 / 1,0 / 1,0 trên cả 6 lô.

## 6. Bug hoặc điểm chưa rõ trong lab (nếu có)

- Không phát hiện bug trong `scripts/`; nhóm không sửa `scripts/` (`git diff --stat -- scripts/` rỗng).
- Điểm chưa rõ: cùng `--seed 11007`, kế hoạch ban đầu của nhóm ghi `release_id lab250_d3cc716c084b`, nhưng chạy lại trên máy thành viên ra `lab250_1948a084c5ce`. `release_id` là hash của `manifest.json` + `metadata.json`, nên khác id nghĩa là nội dung lô khác (khác phiên bản `scripts/` hoặc khác dữ liệu tải về). Tuy vậy, khi đối chiếu đầu ra (lỗi luật, ứng viên, truy vết) giữa hai máy, kết quả giống hệt nhau. Nhóm chưa xác định được nguyên nhân lệch id; số nộp đều lấy từ lô trên máy N1.
- Điểm của chính nhóm, phát hiện trong QA: `validate.py` import cứng `crosscheck`, `rules_label`, `rules_panoptic` ở đầu file nên dừng hẳn nếu thiếu một module (đã gặp khi N3/N4 chưa push). Ngoài ra thời gian chạy sát 60 s trên 250 ảnh.
