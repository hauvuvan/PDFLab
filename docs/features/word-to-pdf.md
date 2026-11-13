# Word sang PDF hàng loạt

[← Tổng quan](../README.md)

## Mục đích và sử dụng

Mở **Word sang PDF** từ dashboard hoặc thanh bên. Kéo thả/chọn DOC và DOCX, bỏ file không cần rồi bấm **Chuyển sang PDF**. Tối đa 100 file, tổng dung lượng trên giao diện 195 MB; máy chủ giới hạn cả request 200 MB. Theo dõi tên file hiện tại và số file hoàn tất. Khi xong, bấm **Tải … PDF (.zip)**. Tên trùng được thêm số; lỗi từng file không dừng các file còn lại. ZIP chứa PDF thành công, `bao-cao.json`, `tien-trinh.jsonl`. Toàn bộ file lỗi vẫn tải được log riêng.

## Giao diện và trạng thái

Màn hình chia danh sách tài liệu và khối chuyển đổi/tải xuống. Các khối cách nhau 24px, nội dung panel đệm 24px, nhóm liên quan cách 8–16px và nhóm thao tác cách 20–24px. Bỏ tất cả chỉ hiện khi có file; từng dòng có tên, dung lượng và nút bỏ. File chọn trùng tên/dung lượng/thời gian sửa được bỏ qua. Lỗi đầu vào hiển thị cạnh vùng chọn.

Nút chính hiển thị số file, khóa khi đang gửi/chạy. Hoàn tất đổi sang tải ZIP nổi bật; nhật ký là liên kết phụ, chi tiết từng file nằm bên dưới. Khi mất kết nối theo dõi, giữ mã lượt và khóa gửi lô mới; dùng **Kết nối lại tiến trình** để đọc tiếp đúng lượt. Nếu lượt không còn (404), cho chọn/chạy lại. Mất phản hồi lúc tải lên ban đầu có thể chưa nhận được mã lượt; chưa bảo đảm chống lặp trong tình huống đó.

## Cấu hình và vận hành

Cài LibreOffice trên máy chạy ứng dụng. Bộ chuyển đổi tìm `soffice`/`libreoffice` trên PATH hoặc `/Applications/LibreOffice.app/Contents/MacOS/soffice`. Có thể đặt `LIBREOFFICE_PATH` là đường dẫn tuyệt đối tới chương trình thực thi rồi khởi động lại ứng dụng. Không cần Word, tài khoản hoặc API bên ngoài. Giao diện báo nếu chưa có bộ chuyển đổi.

Mỗi file có thư mục tạm và hồ sơ LibreOffice riêng, dọn khi kết thúc. Thời gian tối đa 120 giây/file. Xử lý nền tuần tự dùng chung hàng đợi với watermark; không có tiến trình chi tiết từng trang trong lúc LibreOffice đang chạy. Tải lại trang nối lại theo dõi nếu máy chủ chưa khởi động lại. Nguồn không bị ghi đè; PDF/log theo chính sách lưu 24 giờ tại `output/jobs/` trong [tổng quan vận hành](../README.md). Không khôi phục lượt dở dang sau khi tắt máy chủ; chạy lại nguồn. Khi cập nhật lỗi có thể khôi phục commit trước rồi khởi động lại; không có migration.

## API

- `GET /api/word/status`: `{available: boolean}`.
- `POST /api/word/jobs`: multipart `documents` lặp lại; trả 202 và `id`, 400 khi số file sai, 503 khi thiếu LibreOffice.
- `GET /api/jobs/<id>`: trạng thái và báo cáo từng file, `tool: word`.
- `GET /api/jobs/<id>/result`: ZIP khi hoàn tất và có ít nhất một thành công.
- `GET /api/jobs/<id>/log`: log JSONL; có thể tải trong lúc chạy.

## Giới hạn và kiểm thử

LibreOffice có thể phân trang khác Microsoft Word nếu thiếu font, có bảng/đối tượng phức tạp hoặc tính năng Word đặc thù. File hỏng/mật khẩu báo lỗi riêng, không có tính năng nhập mật khẩu. Chưa nghiệm thu tài liệu nhúng đối tượng/macro, lô sát giới hạn, hoặc đảm bảo giữ bố cục tuyệt đối; kiểm tra PDF trước khi phát hành. Chỉ dùng với tài liệu tin cậy trên máy cá nhân theo phạm vi ứng dụng hiện tại.

`tests/test_word.py` kiểm tra chuyển DOCX và DOC nhị phân thực có tiếng Việt, tên trùng/Unicode, lô hỗn hợp và toàn lỗi, ZIP/báo cáo/log, thiếu engine và timeout. Kiểm thử chuyển thực cần LibreOffice; nếu thiếu sẽ skip và phải ghi rõ chưa xác minh chuyển thực.
