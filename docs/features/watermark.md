# Watermark PDF hàng loạt

[← Tổng quan](../README.md)

## Mục đích và luồng

Chuyển script Colab do người dùng cung cấp thành công cụ chạy cục bộ. Chọn PDF → chọn ảnh → cấu hình → xem trước một trang → xuất ZIP chứa các PDF thành công và báo cáo. Preview và xuất dùng chung hàm chèn watermark để tránh lệch kết quả.

## Hành vi

- Tất cả các trang nhận cùng ảnh, giữ tỷ lệ. Mặc định rộng tối đa 50% trang, cao tối đa 10%, chân trang, cách mép 20 pt.
- Chọn đầu trang, giữa trang hoặc chân trang; căn giữa theo chiều ngang. Kích thước thực tế bị giới hạn bởi cả hai tỷ lệ và khoảng lề.
- Độ hiển thị 1–100% nhân với alpha sẵn có của ảnh. Đây không phải công cụ xóa nền; JPG vẫn có nền ảnh.
- Chèn ảnh phía trên nội dung, link HTTP/HTTPS nằm đúng vùng ảnh. Có thể bỏ link. Trang xoay dùng biến đổi tọa độ để vị trí theo trang nhìn thấy.
- Tiền tố mặc định `[tailieuonthi.org]`, có thể sửa hoặc để trống; ký tự đường dẫn và điều khiển bị thay thế. File trùng tên thêm số `(2)`, `(3)`… không ghi đè nhau.
- PDF hỏng, có mật khẩu hoặc có cờ chữ ký số bị từ chối từng file. Các file khác vẫn tiếp tục. Không có file thành công thì trả lỗi, không tải ZIP rỗng.
- Không chỉnh sửa nguồn, không xóa watermark cũ. Chạy lại lên kết quả sẽ thêm watermark lần nữa.

## Giới hạn

100 PDF/lượt; HTTP request tối đa 200 MB; giao diện giới hạn tổng PDF 195 MB và ảnh 15 MB, tổng request vẫn phải nằm trong 200 MB. Ảnh tối đa 25 triệu pixel. Xử lý trong bộ nhớ, nên lô PDF có nhiều trang/ảnh lớn có thể cần chia nhỏ hơn. Preview chỉ render trang được chọn, không phải toàn bộ tài liệu.

Không hỗ trợ Word, Excel, ảnh HEIC, mật khẩu mở PDF, watermark chữ, chọn khoảng trang, hàng đợi, lưu hồ sơ cấu hình hoặc nhiều người dùng. PDF số hóa và PDF scan đều có thể thêm ảnh. Lưu PDF có thể thay đổi cấu trúc nội bộ; cần tự đối chiếu với tài liệu quan trọng hoặc có cấu trúc đặc biệt. PyMuPDF dùng AGPL hoặc giấy phép thương mại; cần rà soát giấy phép nếu đóng gói/phân phối sản phẩm thương mại.

## API cục bộ

- `GET /`: dashboard.
- `GET /health`: trạng thái và phiên bản.
- `POST /api/preview`: multipart `pdf`, `watermark`, `page` (1-based) và cấu hình; trả PNG, header `X-Page-Count`.
- `POST /api/process`: multipart `pdfs` (lặp), `watermark` và cấu hình; trả ZIP kèm `bao-cao.json`. Header tổng số thành công/thất bại; chi tiết ngắn qua `X-Reports`, lô dài xem báo cáo trong ZIP.

Cấu hình: `position=top|center|bottom`, `width=5..95`, `height=1..80`, `opacity=1..100`, `margin=0..150` (pt), `link`, `prefix`. Các giá trị mặc định như trên. Lỗi đầu vào trả JSON 400; quá dung lượng trả JSON 413. Chỉ nhận Host localhost/127.0.0.1 và Origin cùng nguồn nếu có.

## Kiểm tra

Chạy lệnh unittest ở [README](../../README.md). Phạm vi: batch/ZIP/báo cáo, bảo toàn văn bản và số trang, link, file trùng tên, trang xoay/crop, alpha, preview và lỗi đầu vào. Kiểm tra thủ công thêm bằng file thực tế của người dùng trước khi dùng số lượng lớn; chưa có file PDF/logo thật được cung cấp trong task ban đầu.

Nguồn kỹ thuật: [PyMuPDF Page](https://pymupdf.readthedocs.io/en/latest/page.html), đặc biệt quy ước tọa độ chèn ảnh trên trang xoay. Script mẫu được đọc tại `/Users/ithacuco/Desktop/them_watermark_tu_dong.py`; không chỉnh sửa script nguồn.

## Tiến trình và log cho xử lý đơn/lô

Chọn một PDF để xử lý riêng hoặc nhiều PDF để chạy lô, dùng cùng nút xuất. Giao diện hiển thị số file đã hoàn tất/tổng số, thành công/lỗi, tên file hiện tại và trang đã xử lý/tổng trang. Thanh tiến trình đo số file hoàn tất, không ước tính thời gian còn lại. Bước ghi/nén PDF có thể tiếp tục sau trang cuối. Các lỗi file không ngăn những file sau chạy; lỗi toàn lượt được báo riêng.

- `POST /api/jobs`: cùng multipart như `/api/process`, trả HTTP 202 và `id`.
- `GET /api/jobs/<id>`: trạng thái `queued|running|completed|error`, `total`, `completed`, `page`, `pages`, `current`, `success`, `failed`, `reports`, `error`.
- `GET /api/jobs/<id>/log`: tải JSONL ngay cả khi còn chạy hoặc toàn bộ PDF thất bại. Mỗi dòng có thời gian kèm múi giờ, sự kiện và dữ liệu tiến trình; lỗi có traceback giúp sửa lỗi.
- `GET /api/jobs/<id>/result`: ZIP khi hoàn tất và có ít nhất một file thành công; ngược lại HTTP 409. Giữ `/api/process` đồng bộ để tương thích khách cũ.

Xem [vận hành và lưu trữ](../README.md) cho nơi lưu, thời hạn, phục hồi khi khởi động lại và giới hạn bộ nhớ. Không hỗ trợ tiếp tục từ trang đang dở sau khi dừng máy chủ.
