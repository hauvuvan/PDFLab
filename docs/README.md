# Tổng quan PDFLabs

PDFLabs gom các tác vụ tài liệu lặp lại vào một dashboard. Phiên bản 1.2 có watermark PDF và chuyển Word sang PDF hàng loạt.

Công cụ [xoá watermark](features/remove-watermark.md) cho chọn ảnh có sẵn hoặc khoanh vùng header/footer trên PDF.

## Thành phần

- `app.py`: Flask phục vụ trang và API trên 127.0.0.1.
- `watermark.py`: kiểm tra đầu vào, xử lý ảnh, chèn watermark/link và render preview bằng PyMuPDF.
- `word_converter.py`: chuyển DOC/DOCX cục bộ qua LibreOffice, hồ sơ tạm riêng và giới hạn thời gian.
- `presets.py`: kiểm tra và lưu mẫu watermark tại `data/presets.json`, gồm logo/cấu hình, không lưu PDF.
- `templates/`, `static/`: giao diện tiếng Việt, không phụ thuộc CDN hoặc dịch vụ bên ngoài.
- `tests/`: kiểm thử độc lập cho engine và HTTP.
- `start.command`: khởi động trên macOS, tạo môi trường riêng và mở trình duyệt.

## Thiết lập, kiểm thử và vận hành

Xem [README](../README.md) cho lệnh cài đặt, khởi động và kiểm thử. Cấu hình gồm `PORT` (mặc định 8765) và `LIBREOFFICE_PATH` tùy chọn cho công cụ Word. Không cần tài khoản hoặc khóa API.

Giao diện tạo lượt chạy nền, đọc tiến trình mỗi 600 ms và giữ mã lượt chạy trong trình duyệt để nối lại khi tải lại trang. Một worker xử lý tuần tự; preview và xuất PDF dùng chung khóa để tránh truy cập engine đồng thời. Trong lúc tải lên, giao diện báo đang tải; tiến trình file/trang bắt đầu sau khi máy chủ nhận đủ dữ liệu.

Kết quả và log lưu tại `output/jobs/<mã-lượt>/` và được dọn khi tạo lượt mới nếu đã quá 24 giờ. Log JSONL ghi thời gian Asia/Ho_Chi_Minh, sự kiện, tên file, số trang và traceback khi lỗi; có thể chứa tên tài liệu/đường dẫn máy, cần kiểm tra trước khi chia sẻ. Không lưu PDF nguồn vào kho lâu dài. ZIP kết quả có báo cáo và bản log hoàn tất. Dừng máy chủ làm mất trạng thái/hàng đợi trong bộ nhớ, không tự tiếp tục lượt dở dang; file log trên đĩa vẫn còn, có thể đọc trực tiếp. Xóa thư mục lượt đã kết thúc để dọn sớm khi cần. Không xóa thư mục đang chạy. Không tuyên bố xóa an toàn dữ liệu khỏi thiết bị.

Chỉ mở trên localhost; có kiểm tra Host và Origin, không hỗ trợ truy cập qua LAN hoặc reverse proxy. HTTP phục vụ đồng thời để đọc tiến trình; engine xử lý từng file tuần tự. Tránh gửi nhiều lô cùng lúc vì dữ liệu chờ nằm trong bộ nhớ. Không dùng Flask development server làm VPS production. Chưa có đích VPS hay remote GitHub được cấu hình cho dự án.

Nếu lỗi: kiểm tra thông báo trên trang và báo cáo trong ZIP, chia lô nhỏ hơn nếu thiếu bộ nhớ, mở khóa PDF trước, hoặc khởi động lại. Không ghi đè nguồn nên có thể xử lý lại từ file gốc. Khi cập nhật, dừng tiến trình, lưu phiên bản mã cũ hoặc dùng Git để khôi phục, cài requirements tương ứng và chạy lại. Không có migration dữ liệu.

Kho mẫu tồn tại qua khởi động lại tại `data/presets.json`, tách khỏi log/kết quả của từng lượt. [Hướng dẫn watermark](features/watermark.md) mô tả sao lưu/khôi phục mẫu, font chữ và giới hạn render.

## Mục lục

- [Xoá watermark PDF](features/remove-watermark.md)

- [Word sang PDF hàng loạt](features/word-to-pdf.md)
- [Công cụ watermark PDF](features/watermark.md)
- [Giao diện và bố cục](features/interface.md)
- [Nhật ký hoạt động](activity-log.md)

- [Mở PDFLabs trên macOS](features/macos-launcher.md)
