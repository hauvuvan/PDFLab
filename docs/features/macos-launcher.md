# Mở PDFLabs trên macOS

[Tổng quan](../README.md)

PDFLabs.app là bộ mở ứng dụng cục bộ: khởi động dịch vụ ở 127.0.0.1:8765 và mở trình duyệt mặc định. Không có cửa sổ Terminal. Đây chưa phải bản ứng dụng độc lập: cần giữ thư mục dự án và môi trường `.venv` tại vị trí hiện tại.

## Chuẩn bị và tạo app

Chạy `start.command` một lần để cài thư viện nếu chưa có. Tạo bundle bằng:

```sh
.venv/bin/python scripts/build_macos_app.py
```

Kết quả ở `output/macos/PDFLabs.app`. Có thể tạo trực tiếp ở thư mục mong muốn bằng đối số đường dẫn. Cần Command Line Tools (clang) để tạo executable macOS native. Trình tạo từ chối ghi đè bundle có sẵn. Launcher chứa đường dẫn tuyệt đối tới dự án; nếu chuyển dự án cần tạo lại app. Thư viện được quản lý bởi dự án, không đóng gói vào bundle.

## Hành vi và vận hành

- Mỗi lần mở, so sánh dấu phiên bản từ Python, template, CSS/JS và requirements trong thư mục dự án với phiên đang chạy. Nếu khớp thì dùng lại; nếu khác thì dừng đúng PID thuộc cùng dự án và khởi động bản mới. Không tải bản cập nhật từ Internet/GitHub. Giữ định dạng mẫu và khóa lượt chạy cũ để tương thích.
- Nếu job đang chờ/chạy hoặc engine đang xử lý, báo chờ hoàn tất rồi mở lại; không tự ngắt. Kiểm tra bận và dừng tiến trình chưa là một thao tác nguyên tử: tránh đồng thời gửi tác vụ mới từ tab khác trong lúc mở để cập nhật.
- Phiên cũ chưa có thông tin nhận diện không bị tự dừng; cần dừng đúng app.py cũ một lần để chuyển sang launcher mới.
- Nếu chưa chạy, khởi động bằng Python của `.venv`, chờ health/trang sẵn sàng rồi mở trình duyệt. Khóa khởi động tránh mở lặp tạo nhiều server.
- Nếu cổng đang thuộc dịch vụ khác, báo lỗi; không dừng tiến trình khác.
- Log khởi động: `output/launcher.log`. Mở app lại có thể dùng phiên đang chạy; đóng trình duyệt không dừng server. Bản này chưa có nút Quit để dừng server; dừng đúng tiến trình app.py của dự án khi cần cập nhật, tránh dừng hàng loạt Python.
- Nếu lỗi môi trường, chạy lại `start.command`; nếu di chuyển dự án, tạo bundle mới. Có thể xóa bundle/lối tắt để gỡ bộ mở mà không xóa tài liệu hay cấu hình dự án.

Bundle chỉ dùng cục bộ, chưa ký/notarize để phân phối. Không yêu cầu tắt bảo vệ macOS. Trạng thái cài Applications/Desktop và kiểm tra thực tế được ghi trong [log](../activity-log.md).
