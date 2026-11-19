# Bảo mật khi làm việc

> Trả lời gắn với lô lab250_d3cc716c084b (seed 11007) nhóm vừa bàn giao. Ảnh trong lô là ảnh COCO công khai, nhưng ngoài đời lô dữ liệu thật của dự án phải được đối xử như dữ liệu mật.

## 1. Ca USB: hết giờ, muốn chép lô về nhà làm tiếp
Không chép. Dữ liệu dự án chỉ được lưu và xử lý trên máy và kho do công ty cấp. Chép ra USB cá nhân làm mất kiểm soát: không ai biết bản sao nằm ở đâu, không xoá được, không truy được ai đã mở. Gửi qua email cá nhân hay nhờ người khác làm hộ cũng sai vì vẫn đưa dữ liệu ra ngoài vùng quản lý và qua tay người không được giao job. Cách đúng là báo người phụ trách, xin gia hạn hoặc xin quyền làm việc từ xa bằng kênh được duyệt (VPN, máy ảo công ty), để lại phần chưa xong trong hàng đợi của job (ví dụ `rework_queue.csv`) và tiếp tục vào hôm sau.

## 2. Năm việc: được hay không
- Mở job được giao trên máy công ty: **được**, đây là đúng việc, đúng thiết bị, đúng quyền được cấp.
- Chụp màn hình gửi người quen: **không**, ảnh chụp là bản sao dữ liệu ra ngoài, có thể lộ mặt người, biển số, tên file.
- Chép lô ra USB: **không**, vì lý do ở mục 1, USB không có kiểm soát truy cập.
- Dán nhãn thật lên chatbot: **không** với dữ liệu thật của dự án, vì nội dung bị gửi tới dịch vụ bên ngoài và có thể bị lưu hay đánh chỉ mục. Riêng ảnh COCO công khai dùng ở lab thì được, nhưng vẫn phải ghi lại trong `prompts.md`.
- Đưa tài khoản CVAT cho đồng nghiệp: **không**, tài khoản gắn với người gán/kiểm trong `jobs.csv` và lineage; dùng chung làm sai truy vết (không biết ai sửa nhãn) và vi phạm phân quyền. Đồng nghiệp cần quyền thì xin tài khoản riêng.

## 3. Ca khuôn mặt: thấy mặt người rõ trong lô, guideline yêu cầu làm mờ
Kết luận: **Hold + báo người phụ trách**. Trong lô có ảnh người nhìn rõ mặt, ví dụ `000000025386` (hai người cười nhìn thẳng vào máy ảnh trên tàu) và `000000016598` (chân dung tự chụp, mặt nhìn rõ). Khi guideline yêu cầu làm mờ mà lô đang có mặt rõ, em dừng việc dùng và chuyển lô sang trạng thái Hold, ghi tên các ảnh đó vào ticket và báo người phụ trách dữ liệu (data owner/DPO) để họ quyết định cách xử lý và ai được phép làm. Không tự làm mờ hay tự xoá ảnh vì: làm mờ là sửa dữ liệu đã giao, phá hash và lineage, có thể làm hỏng nhãn detection (box người, mặt), và làm sai quy trình duyệt; xoá ảnh làm mất dấu vết kiểm toán và lệch số liệu bàn giao. Sau khi có quyết định, bản xử lý được đóng gói thành lô mới có lô cha, không ghi đè lô cũ.
