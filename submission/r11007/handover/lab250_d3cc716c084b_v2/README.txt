Release: lab250_d3cc716c084b_v2
Parent: lab250_d3cc716c084b
Số ảnh: 241
Số nhãn: 1682
Guideline: v1.2 (J01–J04), v1.3 (J05–J10)
QC v1: 17/250 = 6,8%
Kết luận v1: Hold — 17/250 ảnh/cảnh lỗi (6,8%), vượt ngưỡng 2% nên không Release; run R-021 đã train trên v1 phải xem lại hoặc train lại
Kết luận v2: Release — sản phẩm detection: đã tách 9 ảnh lỗi nhãn detection/thiếu file vào rework, sửa hash, guideline, split theo mục Ghi chú; 241 ảnh còn lại không có lỗi detection đã biết; 5 ảnh lỗi panoptic ở lại v2 và báo team panoptic
Ghi chú: guideline_mismatch 000000025424: truyvet.csv ghi guideline v1.3 của job J10, không theo guideline ghi ở ảnh; scene_leak scene_193: đưa cả cảnh về một split (val trong truyvet.csv); wrong_hash 000000022969: đã kiểm file ảnh (đúng chữ ký JPEG, đọc được), ảnh còn nguyên nên chỉ manifest cũ sai, manifest.csv ghi hash mới; 9 ảnh vào rework_queue.csv, giao lại cho người gán/kiểm theo jobs.csv (A01/Q02, A02/Q01, A02/Q03, A03/Q03, A04/Q01, A04/Q03); lỗi chỉ ở panoptic, ảnh ở lại v2, báo team panoptic: 000000003845 (invalid_category_id), 000000016598 (category_swap), 000000019432 (invalid_category_id), 000000020247 (thing_overlap), 000000025386 (category_swap)
