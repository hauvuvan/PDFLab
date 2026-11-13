# Paperdesk

Bộ công cụ tài liệu chạy trên máy cá nhân, với dashboard và công cụ watermark PDF hàng loạt đầu tiên.

## Mở công cụ trên macOS

Bấm đúp **start.command** trong Finder. Lần đầu cần mạng để cài thư viện; các lần sau không tải lại nếu thư viện đã đủ. Giữ cửa sổ Terminal mở trong lúc sử dụng. Trình duyệt mở tại http://127.0.0.1:8765. Dừng bằng Ctrl+C trong Terminal.

Cần Python 3.9+ và macOS có Python. Nếu Finder không cho chạy, mở Terminal trong thư mục dự án và chạy:

```sh
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
.venv/bin/python app.py
```

Mở trình duyệt tại địa chỉ trên. Nếu cổng đã được dùng, dừng bản cũ hoặc chạy `PORT=8766 .venv/bin/python app.py` và mở cổng tương ứng.

## Sử dụng

1. Chọn Watermark PDF trên dashboard.
2. Thêm một hoặc nhiều PDF, chọn ảnh PNG/JPG/WebP.
3. Chỉnh vị trí, kích thước tối đa, độ hiển thị và liên kết (để trống để không gắn link).
4. Chọn file và số trang rồi bấm **Xem**. Sau khi thay cấu hình cần bấm Xem lại.
5. Bấm **Thêm watermark & tải ZIP**. ZIP chứa PDF thành công và `bao-cao.json` ghi kết quả từng file. Có thể bấm tải lại nếu trình duyệt chặn tải tự động.

File gốc không bị ghi đè. Mặc định theo script Colab: rộng tối đa 50%, cao tối đa 10%, chân trang, cách mép dưới 20 pt, liên kết và tiền tố tailieuonthi.org. Ảnh luôn giữ tỷ lệ và căn giữa trong vùng đã chọn.

## Tài liệu và kiểm thử

- [Tổng quan, thiết lập và vận hành](docs/README.md)
- [Watermark PDF: hành vi, API và giới hạn](docs/features/watermark.md)
- [Nhật ký hoạt động](docs/activity-log.md)

```sh
.venv/bin/python -m unittest discover -s tests -v
```

Các ô ghép, tách, nén PDF mới là mục dự kiến, chưa triển khai. Bản này chỉ chạy trên loopback của máy cá nhân, chưa phải dịch vụ nhiều người dùng hay bản triển khai VPS.
