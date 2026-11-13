# Nhật ký hoạt động

## 2026-11-13 16:01 Asia/Ho_Chi_Minh — Dashboard và watermark PDF v1.0

- Yêu cầu: đọc script Colab `/Users/ithacuco/Desktop/them_watermark_tu_dong.py`, xây bộ công cụ tài liệu có dashboard và công cụ đầu tiên thêm watermark PDF hàng loạt. Script chỉ được đọc để tham khảo, không thực thi/chỉnh sửa.
- Thay đổi: dashboard tiếng Việt, công cụ watermark nhiều PDF, ảnh PNG/JPG/WebP, cấu hình vị trí/kích thước/alpha/link/tên, preview chọn trang, tải ZIP có báo cáo từng file, xử lý tên trùng và lỗi riêng. Chạy loopback trên máy, file gốc giữ nguyên. Thẻ ghép/tách/nén là chức năng dự kiến, chưa triển khai.
- Kiểm thử độc lập: agent `/root/qa`, 12 unittest đạt; kiểm tra nhiều trang, nội dung gốc, link, alpha, xoay/crop, preview, password/PDF hỏng, validation, batch hỗn hợp/Unicode/trùng tên, header gọn và giới hạn request. Phát hiện lệch vị trí ở rotated crop và đã sửa/kiểm tra hồi quy. Preview và bản render xuất cho phép sai khác antialias tối đa 1/255.
- Kiểm tra thực tế: agent chính thử browser tại `http://127.0.0.1:8765`, mở dashboard → chọn PDF/ảnh → preview → tải `/Users/ithacuco/Downloads/pdf-watermark.zip`. ZIP có 1 PDF 3 trang và bao-cao.json, cả 3 trang có 1 ảnh và link `https://tailieuonthi.org/`; đã render/mở xem trang đầu, watermark đúng chân trang. Browser không ghi nhận console error. Đây là kiểm tra bản local, không phải triển khai VPS.
- Kiểm tra bổ sung: `node --check static/app.js` đạt; `zsh -n start.command` trả 0 (môi trường có cảnh báo nice cho background job). Lệnh khởi động thực tế bằng Python đạt, health/API đã kiểm tra. Chưa thử bấm đúp launcher qua Finder, PDF ký số thật, lô sát 200 MB hoặc hàng nghìn trang, chưa có PDF/logo thật của người dùng.
- Tài liệu: [Tổng quan](README.md), [chi tiết watermark](features/watermark.md), [hướng dẫn mở công cụ](../README.md).
- GitHub: khởi tạo Git local, lưu commit bản đầu sau kiểm tra; chưa push vì chưa có remote GitHub/đích repo được cung cấp. Không tạo repo bên ngoài tự suy đoán.
- VPS: không áp dụng cho bản chạy cục bộ; chưa triển khai vì không có đích/cấu hình truy cập. Dịch vụ localhost đã chạy và thử luồng thực tế như trên; không tuyên bố nghiệm thu môi trường production.

## 2026-11-13 16:08 Asia/Ho_Chi_Minh — Tiến trình và log xử lý đơn/lô

- Yêu cầu: xử lý từng file hoặc hàng loạt, lưu tiến trình/lỗi để kiểm tra và cho người dùng xem đang chạy tới đâu.
- Thay đổi: lượt chạy nền tuần tự, API theo dõi file/trang, thanh tiến trình, đếm thành công/lỗi, tiếp tục sau PDF lỗi; tải log JSONL kể cả toàn bộ thất bại, ZIP có báo cáo và log. Lưu `output/jobs/<id>/`, dọn lượt kết thúc quá 24 giờ khi tạo lượt mới; nối lại theo dõi khi tải lại trang nếu máy chủ còn chạy. Engine dùng khóa chung với preview/API cũ.
- Kiểm thử: agent `/root/qa` xác minh độc lập 5 test mới và 12 regression đạt. Đã kiểm tra riêng đúng nội dung chuẩn bị commit tại `/tmp/pdf-progress-check`: 17/17 đạt, bao gồm tiến trình khi đang chạy, chặn tải ZIP sớm, lô hỗn hợp, tên trùng, tất cả lỗi, log traceback/múi giờ và dọn hết hạn. `node --check static/app.js`, `git diff --check` đạt.
- Giới hạn: chưa kiểm thử browser cho thay đổi này, lô sát 200 MB hoặc hết dung lượng đĩa. Thư mục có task khác đang sửa watermark nâng cao/presets; lần chạy toàn bộ 32 test ghi nhận 2 fail + 1 error của phần text đang sửa đồng thời, không thuộc nội dung commit này. Giữ nguyên các thay đổi ngoài task, chỉ lưu phần tiến trình/log vào commit.
- Tài liệu: [tổng quan/vận hành](README.md), [API và hành vi](features/watermark.md), [cách dùng](../README.md).
- GitHub: lưu commit local sau kiểm tra; chưa push vì không có remote cấu hình.
- VPS: chưa triển khai, không có đích/cấu hình VPS; công cụ dành cho localhost. Không tuyên bố đã kiểm thử sau triển khai.
