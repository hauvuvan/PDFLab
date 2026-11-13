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
