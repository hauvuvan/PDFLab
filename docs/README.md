# Tổng quan Paperdesk

Paperdesk gom các tác vụ tài liệu lặp lại vào một dashboard. Phiên bản 1.0 có công cụ watermark PDF; các thẻ còn lại là kế hoạch, không có API xử lý.

## Thành phần

- `app.py`: Flask phục vụ trang và API trên 127.0.0.1.
- `watermark.py`: kiểm tra đầu vào, xử lý ảnh, chèn watermark/link và render preview bằng PyMuPDF.
- `templates/`, `static/`: giao diện tiếng Việt, không phụ thuộc CDN hoặc dịch vụ bên ngoài.
- `tests/`: kiểm thử độc lập cho engine và HTTP.
- `start.command`: khởi động trên macOS, tạo môi trường riêng và mở trình duyệt.

## Thiết lập, kiểm thử và vận hành

Xem [README](../README.md) cho lệnh cài đặt, khởi động và kiểm thử. Cấu hình duy nhất hiện tại là biến `PORT` (mặc định 8765). Không cần tài khoản hoặc khóa API.

Ứng dụng xử lý mỗi lượt đồng bộ; không có hàng đợi nền. Giữ tab và tiến trình hoạt động đến khi nhận ZIP. Dữ liệu tải lên do Flask/Werkzeug quản lý trong bộ nhớ hoặc file tạm của hệ điều hành trong vòng đời request; ứng dụng không tạo kho lưu tài liệu. ZIP được giữ trong bộ nhớ của request và trình duyệt để tải lại. Đóng tab để giải phóng URL tải kết quả, dừng tiến trình để giải phóng bộ nhớ máy chủ. Không tuyên bố xóa an toàn dữ liệu khỏi thiết bị.

Chỉ mở trên localhost; có kiểm tra Host và Origin, không hỗ trợ truy cập qua LAN hoặc reverse proxy. Chạy một worker không song song để hạn chế tăng bộ nhớ vì nhiều lượt xử lý. Không dùng Flask development server làm VPS production. Chưa có đích VPS hay remote GitHub được cấu hình cho dự án.

Nếu lỗi: kiểm tra thông báo trên trang và báo cáo trong ZIP, chia lô nhỏ hơn nếu thiếu bộ nhớ, mở khóa PDF trước, hoặc khởi động lại. Không ghi đè nguồn nên có thể xử lý lại từ file gốc. Khi cập nhật, dừng tiến trình, lưu phiên bản mã cũ hoặc dùng Git để khôi phục, cài requirements tương ứng và chạy lại. Không có migration dữ liệu.

## Mục lục

- [Công cụ watermark PDF](features/watermark.md)
- [Nhật ký hoạt động](activity-log.md)
