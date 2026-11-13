# Nhật ký hoạt động

## 2026-11-13 16:01 Asia/Ho_Chi_Minh — Dashboard và watermark PDF v1.0

- Yêu cầu: đọc script Colab `/Users/ithacuco/Desktop/them_watermark_tu_dong.py`, xây bộ công cụ tài liệu có dashboard và công cụ đầu tiên thêm watermark PDF hàng loạt. Script chỉ được đọc để tham khảo, không thực thi/chỉnh sửa.
- Thay đổi: dashboard tiếng Việt, công cụ watermark nhiều PDF, ảnh PNG/JPG/WebP, cấu hình vị trí/kích thước/alpha/link/tên, preview chọn trang, tải ZIP có báo cáo từng file, xử lý tên trùng và lỗi riêng. Chạy loopback trên máy, file gốc giữ nguyên. Thẻ ghép/tách/nén là chức năng dự kiến, chưa triển khai.
- Kiểm thử độc lập: agent `/root/qa`, 12 unittest đạt; kiểm tra nhiều trang, nội dung gốc, link, alpha, xoay/crop, preview, password/PDF hỏng, validation, batch hỗn hợp/Unicode/trùng tên, header gọn và giới hạn request. Phát hiện lệch vị trí ở rotated crop và đã sửa/kiểm tra hồi quy. Preview và bản render xuất cho phép sai khác antialias tối đa 1/255.
- Kiểm tra thực tế: agent chính thử browser tại `http://127.0.0.1:8765`, mở dashboard → chọn PDF/ảnh → preview → tải `/Users/ithacuco/Downloads/pdf-watermark.zip`. ZIP có 1 PDF 3 trang và bao-cao.json, cả 3 trang có 1 ảnh và link `https://tailieuonthi.org/`; đã render/mở xem trang đầu, watermark đúng chân trang. Browser không ghi nhận console error. Đây là kiểm tra bản local, không phải triển khai VPS.
- Kiểm tra bổ sung: `node --check static/app.js` đạt; `zsh -n start.command` trả 0 (môi trường có cảnh báo nice cho background job). Lệnh khởi động thực tế bằng Python đạt, health/API đã kiểm tra. Chưa thử bấm đúp launcher qua Finder, PDF ký số thật, lô sát 200 MB hoặc hàng nghìn trang, chưa có PDF/logo thật của người dùng.
- Tài liệu: [Tổng quan](README.md), [chi tiết watermark](features/watermark.md), [hướng dẫn mở công cụ](../README.md).
- GitHub: khởi tạo Git local, lưu commit bản đầu sau kiểm tra; chưa push vì chưa có remote GitHub/đích repo được cung cấp. Không tạo repo bên ngoài tự suy đoán.
- VPS: không áp dụng cho bản chạy cục bộ; chưa triển khai vì không có đích/cấu hình truy cập. Dịch vụ localhost đã chạy và thử luồng thực tế như trên; không tuyên bố nghiệm thu môi trường production.

## 2026-11-13 16:08 Asia/Ho_Chi_Minh — Tiến trình và log xử lý đơn/lô

- Yêu cầu: xử lý từng file hoặc hàng loạt, lưu tiến trình/lỗi để kiểm tra và cho người dùng xem đang chạy tới đâu.
- Thay đổi: lượt chạy nền tuần tự, API theo dõi file/trang, thanh tiến trình, đếm thành công/lỗi, tiếp tục sau PDF lỗi; tải log JSONL kể cả toàn bộ thất bại, ZIP có báo cáo và log. Lưu `output/jobs/<id>/`, dọn lượt kết thúc quá 24 giờ khi tạo lượt mới; nối lại theo dõi khi tải lại trang nếu máy chủ còn chạy. Engine dùng khóa chung với preview/API cũ.
- Kiểm thử: agent `/root/qa` xác minh độc lập 5 test mới và 12 regression đạt. Đã kiểm tra riêng đúng nội dung chuẩn bị commit tại `/tmp/pdf-progress-check`: 17/17 đạt, bao gồm tiến trình khi đang chạy, chặn tải ZIP sớm, lô hỗn hợp, tên trùng, tất cả lỗi, log traceback/múi giờ và dọn hết hạn. `node --check static/app.js`, `git diff --check` đạt.
- Giới hạn: chưa kiểm thử browser cho thay đổi này, lô sát 200 MB hoặc hết dung lượng đĩa. Thư mục có task khác đang sửa watermark nâng cao/presets; lần chạy toàn bộ 32 test ghi nhận 2 fail + 1 error của phần text đang sửa đồng thời, không thuộc nội dung commit này. Giữ nguyên các thay đổi ngoài task, chỉ lưu phần tiến trình/log vào commit.
- Tài liệu: [tổng quan/vận hành](README.md), [API và hành vi](features/watermark.md), [cách dùng](../README.md).
- GitHub: lưu commit local sau kiểm tra; chưa push vì không có remote cấu hình.
- VPS: chưa triển khai, không có đích/cấu hình VPS; công cụ dành cho localhost. Không tuyên bố đã kiểm thử sau triển khai.

## 2026-11-13 16:12 Asia/Ho_Chi_Minh — Làm gọn giao diện

- Yêu cầu: giao diện phần mềm hiện đại, thân thiện, bỏ minh họa/chữ thừa; tham khảo mẫu trên mạng.
- Thay đổi: bỏ hero/slogan và công cụ chưa triển khai; danh sách công cụ gọn, hệ màu trung tính/xanh, form và preview hai cột, responsive, focus bàn phím; bổ sung kiểu hiển thị cho điều khiển nâng cao đang được sửa trong task khác, giữ nguyên chức năng/ID.
- Kiểm tra độc lập: `/root/ui_qa`: JS syntax đạt, ID không trùng/khớp selector; Flask GET200, preview PNG200/2 trang, job202→success1/failed0→ZIP200. Toàn bộ working tree tại thời điểm QA 32/33 test đạt; một lỗi alpha chữ thực tế165 so với ≤128 ở test_advanced.py:80 thuộc engine đang sửa ngoài task, chưa xác nhận hết lỗi.
- Kiểm tra giao diện thực tế: trình duyệt tại http://127.0.0.1:8767, dashboard→editor hiển thị đúng; điện thoại viewport390×844, content375px không tràn ngang; desktop hai cột. Không ghi nhận lỗi console tại8767; có một lỗi từ8765 cũ do JS/template khác phiên bản khi sửa đồng thời. Không nghiệm thu đầy đủ tính năng nâng cao của task khác.
- Tài liệu: [giao diện](features/interface.md), [mục lục](README.md). Chỉ commit phần UI/tài liệu; giữ thay đổi khác trong working tree.
- GitHub: commit local; chưa push do chưa có remote. VPS: chưa triển khai, không có đích/cấu hình; đây là kiểm tra local, không phải sau triển khai VPS.

## 2026-11-13 16:11 Asia/Ho_Chi_Minh — Watermark ảnh/chữ, tùy chỉnh và lưu mẫu

- Yêu cầu: mở rộng watermark ảnh hoặc text, màu/độ trong suốt/vị trí/góc nghiêng/tỷ lệ %, lưu mẫu; nghiên cứu ảnh tham khảo chữ xám nghiêng lặp so le.
- Thay đổi: chữ Việt 3 kiểu font/in đậm/nhiều dòng; màu chữ hoặc tint ảnh; alpha0–100, góc ±180, 9 điểm neo, offset %, tỷ lệ rộng/cao, tile so le/khoảng trống, lớp trước/sau, phạm vi tất cả/lẻ/chẵn/khoảng. Có cấu hình nhanh theo ảnh và logo chân trang. Preview và xuất chung engine; giữ nguyên dạng nội dung PDF gốc.
- Mẫu: CRUD local tại data/presets.json (30 mẫu/64MB), lưu cả logo, đổi tên bằng cập nhật, xuất/nhập JSON, ghi nguyên tử/quyền0600/khóa cập nhật, kho sai cấu trúc không tự ghi đè. Data không vào Git. Hai mẫu chữ tham khảo được lưu khi thử browser.
- QA độc lập: agent /root/qa thêm tests/test_advanced.py (18 tests). Tổng 35 tests đạt (18 advanced +12 regression +5 jobs từ thay đổi song song), xác minh ảnh/text/tiếng Việt/màu/alpha/xoay/9 neo/offset/tile/phạm vi/lớp/preset logo roundtrip/cập nhật/xóa/kho hỏng/giới hạn30. Đã sửa kích thước float khi render chữ, alpha overshoot sau resample, tile offset phủ trang và kiểm tra shape kho. Node kiểm cú pháp JS đạt.
- Browser thực tế localhost:8765: chữ Việt nghiêng preview; lưu mẫu, reload rồi áp dụng; xuất JSON tới Downloads/paperdesk-watermark.json, nhập lại và cập nhật tên; xuất 1 PDF3trang thành công0lỗi. Mở ZIP tải về Downloads/pdf-watermark (1).zip: PDF3trang,10 watermark/trang, nội dung chữ gốc còn; render trang đầu tmp/pdfs/advanced-export.png nhìn đúng chữ xám nghiêng so le. Console không có error. Ảnh giao diện thử tại tmp/pdfs/watermark-studio.png. Dữ liệu mẫu tự tạo, không tài liệu thật.
- Giới hạn: watermark text là PNG trong suốt chất lượng cao, không phải selectable text; ảnh xoay giới hạn2400px, font macOS (Linux fallback chưa nghiệm thu); chưa thử Windows, lô200MB/kho64MB hoặc PDF ký số thật. Chưa có nhiều lớp watermark riêng trong một lượt.
- Tài liệu: [Watermark chi tiết](features/watermark.md) là nguồn chính cho tùy chọn/API/mẫu/sao lưu/khôi phục; cập nhật [Tổng quan](README.md), [hướng dẫn](../README.md). Giữ các thay đổi tiến trình và giao diện được cập nhật song song trong dự án.
- GitHub: lưu commit local của phạm vi watermark sau kiểm tra; chưa push vì chưa có remote. VPS: chưa triển khai, không có đích/cấu hình; chỉ kiểm thử bản chạy cục bộ.
