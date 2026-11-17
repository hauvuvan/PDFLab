# Trạng thái dự án

Cập nhật: 2026-11-13 16:54 Asia/Ho_Chi_Minh. Đọc cùng [nhật ký hoạt động](activity-log.md) và [tổng quan](README.md). Khi tiếp tục, kiểm tra Git vì có thể có task khác đang thay đổi mã.

## Đã làm và có kiểm tra ghi nhận

- PDF sang ảnh và ghép ảnh thành PDF: 58/58 kiểm thử đạt, browser local đã kiểm luồng chính; xem [hướng dẫn](features/pdf-images.md). Đã commit và push `61d9e97` lên origin/main; chưa triển khai VPS.

- Dashboard và watermark ảnh/chữ hàng loạt: xem trước, tùy chỉnh, lưu mẫu, tiến trình, ZIP và log.
- Word sang PDF hàng loạt qua LibreOffice; giao diện và trạng thái chuyển đổi đã được kiểm tra local.
- Xoá watermark bằng chọn ảnh hoặc khoanh vùng; hỗ trợ ảnh trong Form XObject. PDF thật 15 trang đã được kiểm tra, giữ nội dung văn bản và ảnh bài tập theo nhật ký.
- Có commit launcher macOS `298d3a1`; xem [hướng dẫn](features/macos-launcher.md). Không suy ra mọi thay đổi hiện tại đều thuộc commit này hoặc đã được nghiệm thu.
- Chi tiết bằng chứng và giới hạn của từng lần kiểm tra nằm trong nhật ký; đây không phải xác nhận chạy lại toàn bộ kiểm thử ở thời điểm cập nhật trang này.

## Đang làm / cần xác minh khi tiếp tục

- Hai công cụ PDF/ảnh đã kiểm tra trong task tương ứng; đã push commit `61d9e97` lên origin/main. Các thay đổi task khác cần đối chiếu Git riêng.
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

## Cập nhật 2026-11-13 17:21 Asia/Ho_Chi_Minh — Lô watermark lớn

- Hoàn tất bỏ giới hạn chọn100PDF/tổng195MB trên UI và API jobs/preview. PDF lưu tạm ổ đĩa, xử lý lần lượt từng file, dọn sau xử lý. Xem [chi tiết](features/watermark.md).
- QA độc lập7/7 mới; suite69tests,2skip LibreOffice; WSGI request hơn200MB (2PDF101MiB) xuất2/2, text giữ nguyên, staging xóa. 1005file API và5001file metadata UI đạt; chưa kiểm lô nhiềuGB/browser bản mới.
- Mã task chưa commit/chưa push trên main: môi trường chặn ghi .git/index.lock (Operation not permitted). Các thay đổi ở working tree; phần sắp xếp log có sẵn được giữ nguyên và chưa nghiệm thu. Chưa triển khai VPS; cần mở lại PDFLabs để launcher nạp mã mới.

## Cập nhật 2026-11-16 — Đưa bản watermark lô lớn lên GitHub

- Kiểm thử lại 69/69 đạt, gồm LibreOffice. Xem [nhật ký](activity-log.md) để biết kết quả xác minh GitHub. Chưa triển khai VPS vì chưa có đích hoặc cấu hình.
- Bản watermark lô lớn đã lên `origin/main` ở commit [`abcc8f9`](https://github.com/hauvuvan/PDFLab/commit/abcc8f9aca4d0d2848faee79262c58142bdb8206), đã đối chiếu SHA trên GitHub.

## Cập nhật 2026-11-17 16:26 Asia/Ho_Chi_Minh — Xoá watermark kéo thả, hàng loạt và tên file theo file gốc

- Hoàn thành nâng cấp công cụ Xoá watermark:
  + Khung kéo-thả Dropzone trong Bước 1 cho phép kéo thả hoặc chọn nhiều file PDF cùng lúc.
  + Danh sách file hiển thị file mẫu xem trước, cho phép chuyển đổi file mẫu xem trước linh hoạt.
  + Xử lý hàng loạt các file PDF cùng mẫu theo cấu hình ảnh/vùng khoanh đã chọn, đóng gói ZIP `da-xoa-watermark-hang-loat.zip` chứa từng file con và `bao-cao.json`.
  + Tự động đổi tên file xuất theo file gốc `<tên_gốc>_da_xoa_watermark.pdf` (cả khi xuất đơn và trong file ZIP).
  + Bổ sung nút "Chỉ xuất file mẫu này" khi có nhiều file trong danh sách.
- QA độc lập 72/72 tests pass (2 skip LibreOffice); đã kiểm tra logic thực tế qua Flask test_client; cú pháp JS đạt; HTML toàn vẹn.
- Trạng thái Git: Đã commit và push thành công lên `origin/main` ở commit [`9ee3d42`](https://github.com/hauvuvan/PDFLab/commit/9ee3d42). VPS: Không áp dụng.
