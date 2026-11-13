# Trạng thái dự án

Cập nhật: 2026-11-13 16:54 Asia/Ho_Chi_Minh. Đọc cùng [nhật ký hoạt động](activity-log.md) và [tổng quan](README.md). Khi tiếp tục, kiểm tra Git vì có thể có task khác đang thay đổi mã.

## Đã làm và có kiểm tra ghi nhận

- Dashboard và watermark ảnh/chữ hàng loạt: xem trước, tùy chỉnh, lưu mẫu, tiến trình, ZIP và log.
- Word sang PDF hàng loạt qua LibreOffice; giao diện và trạng thái chuyển đổi đã được kiểm tra local.
- Xoá watermark bằng chọn ảnh hoặc khoanh vùng; hỗ trợ ảnh trong Form XObject. PDF thật 15 trang đã được kiểm tra, giữ nội dung văn bản và ảnh bài tập theo nhật ký.
- Có commit launcher macOS `298d3a1`; xem [hướng dẫn](features/macos-launcher.md). Không suy ra mọi thay đổi hiện tại đều thuộc commit này hoặc đã được nghiệm thu.
- Chi tiết bằng chứng và giới hạn của từng lần kiểm tra nằm trong nhật ký; đây không phải xác nhận chạy lại toàn bộ kiểm thử ở thời điểm cập nhật trang này.

## Đang làm / cần xác minh khi tiếp tục

- Working tree có thay đổi chưa commit trong mã/giao diện và các tệp chuyển đổi ảnh (`image_converter.py`, `static/images.*`, `templates/images.html`); chưa nghiệm thu trong task ghi quy tắc này.
- Đọc diff và xác nhận phạm vi của các task đang chạy trước khi commit; giữ nguyên thay đổi ngoài phạm vi.

## Chưa làm / giới hạn còn lại

- Ghép, tách, nén PDF chưa triển khai theo tài liệu hiện có.
- GitHub: remote `origin` là https://github.com/hauvuvan/PDFLab.git; đã push `main` tới `ab9c153`, xác minh SHA remote trùng local. Các thay đổi chưa commit không nằm trong lần push này; xem nhật ký cho cập nhật sau đó.
- Chưa có đích/cấu hình VPS: chưa triển khai VPS; ứng dụng hiện chạy local.
- Các giới hạn kiểm thử như lô lớn, tài liệu Word phức tạp, nền tảng khác và PDF ký số cần xem từng mục nhật ký; không coi là đã đạt.

## Bước tiếp theo

1. Xác minh và hoàn thiện các thay đổi đang làm theo task tương ứng; chạy kiểm thử phù hợp và ghi bằng chứng.
2. Sau mỗi task hoàn thiện, cập nhật trang này và thêm mục nhật ký: đã làm, kết quả, chưa làm, bước tiếp theo, GitHub/VPS.

## Cập nhật 2026-11-13 16:58 Asia/Ho_Chi_Minh

- Hoàn tất khoảng cách dashboard12px, mobile không tràn; builder cập nhật thay bản cũ có phục hồi khi lỗi.62/62 tests đạt. Đã thay bundle Applications, Desktop dùng chung symlink.
- Task này đã commit `dff51b9` và push thành công lên `origin/main`; các thay đổi công cụ ảnh đang ở working tree không thuộc nghiệm thu task này. VPS không áp dụng.
