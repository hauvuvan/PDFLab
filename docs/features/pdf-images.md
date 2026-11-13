# PDF và ảnh

[← Tổng quan](../README.md)

## Cách dùng

Dashboard có hai công cụ độc lập:

- **PDF sang ảnh** (`/pdf-to-images`): chọn một PDF, PNG hoặc JPG, chọn 72/150/200/300 DPI, chuyển đổi rồi tải ZIP. Tên ảnh `trang-0001` trở đi theo thứ tự trang. Mặc định PNG, 150 DPI. Ảnh render có nền trắng; không giữ lớp chữ có thể chọn, liên kết hoặc biểu mẫu tương tác.
- **Ghép ảnh thành PDF** (`/images-to-pdf`): thêm PNG/JPG/WebP, dùng nút lên/xuống để đổi thứ tự, bỏ ảnh nếu cần, chọn khổ trang rồi ghép và tải PDF. Một ảnh tương ứng một trang. A4 tự chọn ngang/dọc theo ảnh, lề 20 pt; chế độ theo ảnh quy đổi kích thước ở 150 DPI. Cả hai giữ tỷ lệ, tự xoay theo EXIF, chuyển nền trong suốt thành trắng. Ảnh được mã hóa JPEG chất lượng 95, có thể mất chi tiết so với nguồn; ảnh động lấy khung đầu tiên.

File nguồn không bị ghi đè. Công cụ chạy đồng bộ trên máy, hiển thị trạng thái đang xử lý; giữ trang mở đến khi có nút tải. Không có tiến trình từng trang hoặc khôi phục lượt chạy khi tải lại trang. Kết quả nằm trong bộ nhớ và trình duyệt, không lưu vào thư mục jobs. Thay đổi file/thứ tự/cấu hình sẽ bỏ liên kết kết quả cũ.

## API và giới hạn

- `POST /api/pdf-to-images`: multipart `pdf`, `format=png|jpg`, `dpi=72|150|200|300`; trả ZIP.
- `POST /api/images-to-pdf`: multipart lặp `images` theo thứ tự, `paper=a4|image`; trả PDF.
- Lỗi đầu vào trả JSON `error` và HTTP 400; quá 200 MB toàn bộ request trả 413. Giao diện giới hạn file 195 MB để chừa dung lượng multipart.
- PDF từ 1–200 trang, không có mật khẩu; ảnh từ 1–100 file. Giới hạn 25 triệu điểm ảnh mỗi trang/ảnh và 200 triệu điểm ảnh mỗi lượt. PDF vượt giới hạn cần giảm DPI hoặc chia nhỏ; ảnh cần giảm kích thước hoặc chia lô.
- Dùng PyMuPDF và Pillow sẵn có; không cần LibreOffice, mạng hay cấu hình mới. Dùng chung khóa engine để tránh xử lý đồng thời với các công cụ khác. Lượt lớn vẫn có thể tốn bộ nhớ và thời gian; không dành cho máy chủ nhiều người dùng.

## Kiểm tra và vận hành

Chạy `.venv/bin/python -m unittest discover -s tests -v`. Kiểm thử chuyển đổi nằm trong `tests/test_image_converter.py`, gồm kiểm tra nội dung kết quả và lỗi đầu vào.

Nếu lỗi, giảm DPI/chia nhỏ đầu vào, mở khóa PDF hoặc thay ảnh hỏng rồi chạy lại. Dừng và khởi động ứng dụng để cập nhật mã. Có thể khôi phục phiên bản mã trước; không có migration dữ liệu hay thay đổi file nguồn. Chưa có cấu hình triển khai VPS.
