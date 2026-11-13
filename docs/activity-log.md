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

- Xác minh sau khởi động lại 2026-11-13 16:12 +0700: localhost:8765 GET /health HTTP200, version1.1.0; GET /api/presets HTTP200, 2 mẫu còn nguyên. Bản mã watermark commit9ed88d3. Đây là kiểm tra local, không có VPS.

## 2026-11-13 16:37 Asia/Ho_Chi_Minh — Word sang PDF hàng loạt

- Yêu cầu: thêm tool chuyển nhiều tài liệu Word thành PDF.
- Thay đổi: thẻ/sidebar Word sang PDF, chọn/kéo thả DOC/DOCX, bỏ file, giới hạn100 file/195MB, tiến trình nền/nối lại theo dõi, báo lỗi riêng, ZIP PDF/báo cáo/log, tên trùng thêm số. LibreOffice cục bộ, profile/thư mục tạm riêng, timeout120s/file; giữ nguồn. Dùng chung hàng đợi hiện có.
- Kiểm thử độc lập: agent `/root/word_qa`, 5/5 test Word đạt. Chuyển DOCX tiếng Việt và DOC nhị phân Word97 thực; xác minh nội dung PDF; lô2 tên trùng Unicode+1 lỗi; toàn lỗi chỉ log; thiếu engine/timeout/engine lỗi/file rỗng/sai đuôi. Agent chính chạy lại5/5 đạt, JS syntax đạt. Bản riêng xuất từ nội dung chuẩn bị commit Word đạt40/40 unittest; không chứa phần xóa watermark ngoài task. Regression lúc kiểm tra43/44 đạt, lỗi `test_removal.test_selected_image_keeps_other_contained_image` thuộc phần xóa watermark đang sửa song song, không đưa vào commit Word.
- Kiểm tra browser local `http://127.0.0.1:8772/#word`: bộ chuyển đổi sẵn sàng, chọn DOCX thử nghiệm → nút chuyển → hoàn tất1 thành công0lỗi, PDF1trang; có link ZIP và log. Đây là bản kiểm tra local, không phải triển khai VPS. Chưa nghiệm thu Word bố cục phức tạp, mật khẩu hoặc lô sát195MB.
- Tài liệu: [Word sang PDF](features/word-to-pdf.md), [tổng quan](README.md), [hướng dẫn mở](../README.md). Giữ nguyên thay đổi UI/xóa watermark ngoài task; chỉ stage phần Word.
- GitHub: commit local sau kiểm tra; chưa push vì không có remote. VPS: chưa triển khai do không có đích/cấu hình truy cập; công cụ chạy localhost.

## 2026-11-13 16:36 Asia/Ho_Chi_Minh — Tối ưu chữ, nút và điều khiển

- Yêu cầu: tối ưu thực chất UI UX về text/button/element sau lượt chỉnh bố cục.
- Thay đổi: rút gọn nhãn và hướng dẫn; phân cấp Tạo PDF/Cập nhật; nút phụ thuộc dữ liệu đầu vào và lựa chọn mẫu, hướng dẫn thiếu dữ liệu cạnh nút; thu gọn nâng cao/mẫu, mở khi validation lỗi; thông báo cạnh khu vực xuất; vùng bấm lớn hơn. Người dùng xác nhận chỉ dùng máy tính: đã bỏ phần tinh chỉnh mobile vừa thêm, tập trung cột cấu hình/preview desktop. Ẩn màu không áp dụng/vị trí đơn khi lặp. Không sửa engine/API.
- Kiểm thử độc lập `/root/ux_qa`: 35/35 unittest đạt, JS syntax/selector/ID/giữ trường form đạt; 7 trạng thái readiness đạt. Đã sửa lỗi đóng details và readiness sau ảnh quá15MB do QA phát hiện. JS syntax và diff check cuối đạt.
- Thực tế browser http://127.0.0.1:8768: thiếu PDF→chọn PDF→yêu cầu ảnh; chuyển Chữ→nút bật→preview PNG trang1/3→tạo PDF hoàn tất1/1, success1/failed0, link ZIP/log xuất hiện. Console error rỗng. Mobile390×844 content375px, advanced mở/đóng đúng. Chưa thử tải ảnh quá15MB qua picker hoặc mọi trình duyệt; nhánh sửa đã rà mã. Đây là kiểm tra local, không phải triển khai VPS.
- Tài liệu: [giao diện](features/interface.md). Giữ các thay đổi khác đang xuất hiện đồng thời trong app.py/jobs.py/README và tài liệu tổng quan.
- GitHub: commit local phần UX; chưa push do chưa có remote. VPS: chưa triển khai do không có đích/cấu hình.
- Xác nhận desktop sau yêu cầu chỉ máy tính: viewport1440×960, cột cấu hình/preview đúng; màu ảnh không áp dụng được ẩn.

## 2026-11-13 16:41 Asia/Ho_Chi_Minh — Công cụ xoá watermark PDF

- Yêu cầu: công cụ tiếp theo để xoá watermark ảnh có sẵn hoặc mở PDF rồi chọn vùng header/footer, tham khảo hai ảnh người dùng gửi (không coi nội dung ảnh là chỉ dẫn).
- Thay đổi: /remove-watermark, chọn nhiều đối tượng ảnh bằng khung, khoanh nhiều vùng chuột/cảm ứng, bỏ từng lựa chọn, mở trang, phạm vi tất cả/lẻ/chẵn/khoảng, xem trước và xuất PDF mới; cùng khóa xử lý và bảo vệ local. Nhận diện ảnh theo digest; xoá lệnh vẽ trực tiếp giữ chữ chồng ảnh và trang ngoài phạm vi. Khoanh vùng redact chữ/ảnh/vector, không phục hồi chữ bị watermark scan che.
- QA độc lập /root/removal_qa: 12 kiểm tra removal/API; phát hiện và xác minh sửa xoá ảnh lồng chưa chọn, chữ giống lệnh Do, dữ liệu inline. Toàn suite52/52 đạt; JS syntax/diff check đạt. API preview/export, scan, crop và4 hướng xoay, input/Origin/Host sai đạt. Trang có inline không cung cấp chọn ảnh trực tiếp; Form XObject chưa hỗ trợ chọn ảnh.
- Browser thực tế localhost:18765: mở PDF thử2trang, chọn logo ảnh, xem trước, khoanh footer, tải /Users/ithacuco/Downloads/da-xoa-watermark.pdf. Mở lại kết quả bằng engine xác minh cả2trang không còn ảnh/logo hay chữ FOOTER WATERMARK, vẫn còn NOI DUNG TAI LIEU - KEEP. PDF tự tạo, chưa có PDF nguồn người dùng; hai ảnh mẫu không đủ xác minh tách watermark giữa trang. Đây là kiểm tra local, không phải VPS.
- Tài liệu: [xoá watermark](features/remove-watermark.md), [tổng quan](README.md), [cách dùng](../README.md). Một PDF/lượt, đồng bộ chưa có progress cho xoá; ảnh scan dính chữ phải khoanh vùng và mất nội dung trong vùng.
- GitHub: commit local phạm vi công cụ xoá; chưa push do không có remote. Giữ thay đổi giao diện/Word song song ngoài phạm vi commit. VPS: chưa triển khai vì không có đích/cấu hình; không có kiểm thử sau triển khai VPS.

## 2026-11-13 16:49 Asia/Ho_Chi_Minh — Kiểm thử PDF thật và hỗ trợ nhóm ảnh

- Yêu cầu: thử file Thang nhiệt độ (HS).pdf trên Desktop; giữ nguyên nguồn. File15trang có nền watermark giữa trang và footer chung một ảnh, hai logo header riêng, cả3 đặt trong Form XObject.
- Sửa: chọn/xoá ảnh trong nhóm Form XObject, clone tài nguyên và stream riêng từng trang, xử lý Resources kế thừa từ Pages; từ chối nhóm thiếu tài nguyên riêng/vòng lặp/quá sâu. Cắt khung chọn theo trang hiển thị. Giữ mọi thay đổi task khác.
- Kết quả: output/pdf/Thang-nhiet-do-HS-da-xoa-watermark.pdf đủ15trang, bỏ45lệnh ảnh watermark. Text trích xuất15/15trang bằng nguồn tuyệt đối, ảnh bài tập giữ đúng digest/thứ tự trên mọi trang, SHA256 nguồn không đổi. Poppler render15trang và xem contact sheet; QA độc lập /root/removal_qa xem trang1/8 và kiểm thêm chỉ xoá trang1:14trang ngoài phạm vi giống nguồn từng pixel. Không đưa PDF nguồn/kết quả vào Git.
- Kiểm tra: toàn suite53/53 đạt,13 removal/API; JS syntax và diff check đạt. Test nhóm dùng chung giữ chữ và phạm vi, inherited resources đạt sau sửa. Hai ảnh mẫu trước không đủ phát hiện nhóm ảnh; PDF thật đã được nghiệm thu cho cấu trúc này.
- Tài liệu: cập nhật [hành vi/giới hạn xoá watermark](features/remove-watermark.md). GitHub: commit local, chưa push vì không có remote. VPS: không triển khai, chưa có đích/cấu hình; chỉ kiểm thử local.


## 2026-11-13 16:49 Asia/Ho_Chi_Minh — Tối ưu UI UX và khoảng cách Word sang PDF

- Yêu cầu: tối ưu UI UX; phản hồi ảnh giao diện cũ có các phần tử sát nhau, khoảng cách thiếu nhất quán.
- Thay đổi: giao diện Word hai cột chọn file/chuyển đổi, panel đệm24px, khối cách24px, tiêu đề cách vùng chọn20px, nhịp8/16/20/24px; Bỏ tất cả cùng hàng tiêu đề/chỉ hiện khi có file; danh sách tên/dung lượng/icon/nút bỏ. Tổng dung lượng, bỏ chọn trùng, lỗi sát vùng nhập. CTA theo trạng thái, tải ZIP nổi bật sau hoàn tất, nhật ký phụ, bảng kết quả riêng. Theo dõi mất kết nối giữ job/khóa tạo lô mới/nút kết nối lại; 404 cho chạy lại. Sửa điều hướng hash Word không bị router watermark đẩy về dashboard.
- QA độc lập `/root/word_ui_qa`:52/52 unittest đạt tại thời điểm kiểm; JS syntax, DOM selector/không ID trùng và diff check đạt. Harness tương tác Node VM kiểm rỗng/chọn/bỏ/trùng/sai đuôi, mất kết nối và retry GET cùng id không POST trùng, lô hỗn hợp/toàn lỗi/404. Bổ sung CSS spacing được agent rà scope và xem ảnh1280px đạt; không ảnh hưởng tool khác.
- Browser thực tế localhost8773: chọn DOCX→chuyển1/1 thành công→PDF1trang, nút tải ZIP và log; chuyển dashboard rồi vào Word giữ kết quả và hash đúng. Đo DOM khoảng cách khối24px, padding24px, heading→layout24px, title→drop20px. Ảnh kiểm tra /tmp/word-ui-spacing.png. Chưa thử mạng chậm cấp hệ điều hành/lô195MB. Đây là kiểm tra local, không phải VPS.
- Tài liệu: cập nhật [Word sang PDF](features/word-to-pdf.md). Giữ riêng thay đổi tên thương hiệu, launcher và tài liệu task khác đang làm song song.
- GitHub: commit local phần UI Word; chưa push vì không có remote. VPS: chưa triển khai, chưa có đích/cấu hình; bản kiểm tra local tại http://127.0.0.1:8773/#word.

## 2026-11-13 16:51 Asia/Ho_Chi_Minh — PDFLabs.app và mở phiên bản mới nhất

- Yêu cầu: đổi tên PDFLabs, tạo ứng dụng Applications/lối tắt Desktop; mỗi lần mở dùng bản mới nhất trên máy.
- Thay đổi: tên hiển thị PDFLabs, native macOS launcher, kiểm tra health/dấu mã nguồn/đúng dự án/PID, khởi động phiên mới nếu mã thay đổi và engine/job rảnh. Không tự tải GitHub; giữ khóa localStorage và định dạng preset cũ. Thiếu môi trường hoặc cổng bận báo lỗi. Chi tiết: [khởi động macOS](features/macos-launcher.md).
- QA độc lập `/root/launcher_qa`: 8/8 launcher mock đạt; sau sửa native bundle xác minh Mach-O arm64/plist/wrapper; thêm 6/6 freshness mock đạt (bản hiện tại/bản cũ/busy/legacy/hash/health). JS syntax, py_compile (cache /tmp), plutil, zsh syntax, diff check đạt. Lỗi ban đầu shell bundle bị LaunchServices từ chối đã sửa sang executable native qua clang.
- Cài local: /Applications/PDFLabs.app, /Users/ithacuco/Desktop/PDFLabs.app là symlink; đã thử mở qua ứng dụng, Safari hiện title/sidebar/footer PDFLabs, không có Terminal. Bộ mở phụ thuộc đường dẫn dự án/.venv, chưa ký để phân phối, chưa icon riêng.
- SAU cài/khởi động lại 2026-11-13 16:51 Asia/Ho_Chi_Minh: môi trường http://127.0.0.1:8765, health HTTP200/version1.2.0; QA kiểm tra route home/removal/presets200 và2 mẫu còn nguyên, launcher.log không traceback/error. Agent chính mở lại khi mã nguồn thay đổi: PID44801→45093, source_version khớp mã trên đĩa và project_id đúng; Safari thể hiện các tính năng mới nhất đang có trên máy. Các phiên cũ trước migration đã kiểm tra0 job active rồi mới dừng đúng PID.
- Giới hạn: check busy/TERM chưa nguyên tử, tránh gửi tác vụ từ tab khác đúng lúc cập nhật; chưa thử trên máy Mac khác. Không dùng chứng nhận VPS cho kiểm tra local.
- GitHub: commit local phạm vi launcher/tên/version; chưa push do chưa có remote. VPS: không áp dụng, ứng dụng local. Các tính năng khác đang sửa đồng thời được giữ nguyên.

## 2026-11-13 16:52 Asia/Ho_Chi_Minh — Quy tắc lưu tiến độ sau mỗi task

- Yêu cầu: mặc định ghi lại đã làm gì, tới đâu và còn gì chưa làm sau mỗi lần giao việc và hoàn thiện, để tiếp tục dự án về sau.
- Thay đổi: thêm [quy tắc dự án](../AGENTS.md) và [trạng thái đọc nhanh](status.md), tổng hợp từ nhật ký/tài liệu/Git hiện có; phân biệt rõ phần đã kiểm tra với thay đổi đang dở.
- Kiểm tra: đọc tài liệu và trạng thái Git; kiểm tra liên kết tương đối của hai tài liệu mới và diff. Chỉ thay đổi tài liệu, không chạy lại ứng dụng và không nghiệm thu mã đang sửa của task khác.
- Còn lại: hoàn thiện/kiểm thử các thay đổi đang dở theo task tương ứng; cập nhật trạng thái và nhật ký sau mỗi task.
- GitHub: commit local phần quy tắc/trạng thái và mục log này; chưa push vì không có remote. VPS: không áp dụng cho thay đổi tài liệu; không triển khai.

## 2026-11-13 16:54 Asia/Ho_Chi_Minh — Kết nối và push GitHub

- Yêu cầu: đẩy repo lên https://github.com/hauvuvan/PDFLab.git và mặc định báo cáo trạng thái push sau mỗi task/lần thử.
- Thực hiện: xác minh repo rỗng, thêm remote origin, push main và thiết lập upstream. Đã push ab9c153; git ls-remote xác nhận SHA ab9c15368eefcf1a086c411cff02fa02573eb46c khớp HEAD.
- Tài liệu: cập nhật [quy tắc](../AGENTS.md) và [trạng thái](status.md). Phần log/quy tắc này được lưu và push trong commit tiếp theo của cùng task; xác minh remote sau push.
- Kiểm tra: diff và liên kết tài liệu; không sửa mã/chạy lại ứng dụng. Giữ nguyên thay đổi chuyển đổi ảnh chưa commit của task khác, không đưa vào push. Lần truy cập mạng ban đầu không phân giải được GitHub; thử lại với quyền mạng đã thành công.
- GitHub: push mã đã commit thành công lên main; các thay đổi chưa commit vẫn chỉ ở local. VPS: không áp dụng, không triển khai.

## 2026-11-13 16:58 Asia/Ho_Chi_Minh — Khoảng cách dashboard và thay bản cập nhật

- Yêu cầu: tối ưu khoảng cách thẻ công cụ và bỏ bản cũ khi thêm bản cập nhật.
- Sửa: grid gap12px chung, bỏ margin riêng thẻ; mobile menu xuống dòng. Builder tạo bundle hoàn chỉnh rồi thay đúng PDFLabs cũ, dọn cũ sau thành công, giữ/khôi phục bản cũ nếu compile/cài lỗi; từ chối bundle khác/symlink.
- QA độc lập /root/spacing_update_qa:62/62 unittest đạt,4 regression cập nhật bundle. Browser desktop đo4 khoảng đều12px; mobile390 content375 không tràn,4 khoảng12px. Diff check đạt.
- SAU cập nhật local: đã thay /Applications/PDFLabs.app; Desktop symlink vẫn trỏ đúng. Nạp lại localhost8765; agent QA health200/version1.2.0, home/removal/hai công cụ ảnh200,2preset còn nguyên; browser bản cuối khoảng cách đạt. Không có VPS.
- Tài liệu: [giao diện](features/interface.md), [launcher](features/macos-launcher.md), [trạng thái](status.md). Giữ thay đổi công cụ ảnh ngoài task. GitHub: chuẩn bị push commit task lên main/origin, ghi kết quả trong báo cáo cuối; không coi commit local là đã push. VPS không áp dụng, ứng dụng local.

- Kết quả GitHub: push `main` lên `origin/main` thành công, commit `dff51b9` (Normalize dashboard spacing and replace old launcher on update). Log/trạng thái bổ sung trong commit tài liệu tiếp theo; không triển khai lại cho thay đổi log.

## 2026-11-13 17:00 Asia/Ho_Chi_Minh — PDF sang ảnh và ghép ảnh thành PDF

- Yêu cầu: thêm hai công cụ chuyển PDF thành ảnh và ghép ảnh thành PDF.
- Thay đổi: dashboard 5 công cụ; PNG/JPG và 4 mức DPI, ZIP từng trang; ảnh PNG/JPG/WebP ghép theo thứ tự tùy chỉnh, A4 hoặc tỷ lệ ảnh, EXIF/nền trắng; API kiểm tra dữ liệu và giới hạn pixel. Xử lý đồng bộ, không ghi đè nguồn.
- QA độc lập `/root/test_images`: 58/58 unittest đạt, gồm 5 test mới kiểm nội dung/màu/thứ tự/DPI/EXIF/alpha, PDF mã hóa/hỏng, giới hạn và HTTP; JS syntax, Python compile (cache /tmp), diff check đạt. Browser local8774: chọn2ảnh→đổi thứ tự→ghép→tải PDF; PDF2trang→chuyển PNG→link ZIP hiện. Trang công cụ HTTP200. Chưa thử drag/drop trực tiếp, lô sát195MB hoặc máy khác; không có tiến trình từng trang/khôi phục sau reload.
- Tài liệu: [PDF và ảnh](features/pdf-images.md), cập nhật README/tổng quan và trạng thái. Giữ thay đổi sắp xếp nhật ký có sẵn ngoài phạm vi trong working tree.
- GitHub: chuẩn bị commit phần task trên main và push origin; kết quả push ghi bổ sung sau xác minh. VPS: chưa triển khai, không có đích/cấu hình; đây là kiểm tra local.

- Xác minh GitHub 2026-11-13 17:01 Asia/Ho_Chi_Minh: đã push origin/main thành công commit `61d9e97` (hai công cụ và kiểm thử). VPS chưa triển khai vì chưa có cấu hình.
