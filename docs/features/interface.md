# Giao diện Paperdesk

[Tổng quan](../README.md)

Giao diện ưu tiên thao tác tài liệu: dashboard chỉ hiển thị công cụ đã có, không có slogan, minh họa trang trí hoặc thẻ tính năng dự kiến. Dùng nền xám nhẹ, panel trắng, một màu nhấn xanh và chữ hệ thống; không tải font/CDN.

## Cách dùng và bố cục

- Chọn Watermark PDF từ danh sách hoặc thanh điều hướng.
- Cột trái dành cho tài liệu, nội dung và cấu hình; cột phải xem trước và xuất ZIP, giữ trong tầm nhìn khi cuộn trên màn hình rộng.
- Dưới 850 px chuyển một cột, dưới 600 px điều hướng nằm ngang. Các trường có nhãn, nút có trạng thái focus bàn phím; vùng chọn file có focus rõ ràng.
- Giữ nguyên ID và luồng xử lý hiện có. CSS dùng chung cho phần chữ, màu, vị trí neo và mẫu lưu nếu các tính năng tương ứng được bật; tài liệu này không xác nhận chúng đã nghiệm thu.

## Kiểm tra và giới hạn

Kiểm tra desktop, điện thoại 390 px, điều hướng, trường nhập, trạng thái rỗng; xác minh preview và xuất ZIP. Không có thay đổi API, dữ liệu hay cấu hình triển khai. Sửa tại `templates/index.html`, `static/style.css`; khởi động lại ứng dụng sau cập nhật để tránh cache template. Khôi phục bằng phiên bản Git trước nếu cần.

Tham khảo cách tổ chức công cụ: [Adobe Acrobat](https://helpx.adobe.com/acrobat/desktop/edit-documents/add-backgrounds-and-watermarks/add-watermarks.html), [iLovePDF](https://www.ilovepdf.com/pdf_add_watermark).
