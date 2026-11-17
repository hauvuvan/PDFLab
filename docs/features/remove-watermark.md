# Xoá watermark PDF

[← Tổng quan](../README.md)

## Cách sử dụng

Từ dashboard chọn **Xoá watermark**. Bạn có thể kéo thả một hoặc nhiều file PDF vào khung **Kéo PDF vào đây hoặc Chọn file**. File đầu tiên (hoặc file bạn chọn bằng nút "Xem mẫu") sẽ được dùng làm tài liệu mẫu để mở trang xem trước.

Chọn chế độ ảnh rồi bấm khung xanh quanh logo/watermark có sẵn; khung đỏ là đã chọn. Có thể chọn nhiều ảnh, hoặc chuyển sang **Khoanh vùng xoá trắng** và kéo trực tiếp trên bản gốc để chọn header/footer. Danh sách bên trái cho bỏ từng lựa chọn hoặc bỏ tất cả. Mở trang khác giữ lựa chọn để áp dụng cùng một cấu hình; chuyển sang xem mẫu file khác trong danh sách giúp kiểm tra tính tương thích của toạ độ/ảnh.

Chọn tất cả/lẻ/chẵn/khoảng trang rồi **Xem sau khi xoá**. Nút **Về bản gốc để chọn** mở lại trang nguồn để chỉnh lựa chọn.
- **Khi có 1 file PDF:** Nút **Xoá & tải PDF** tạo file PDF mới tải về với tên `<tên_gốc>_da_xoa_watermark.pdf`, không ghi đè file nguồn.
- **Khi có nhiều file PDF (xử lý hàng loạt cùng mẫu):** Nút **Xoá hàng loạt (X file)** áp dụng cấu hình vùng khoanh/ảnh đã chọn cho toàn bộ danh sách file, tự động đóng gói kết quả thành file ZIP `da-xoa-watermark-hang-loat.zip` (gồm từng file PDF đã xoá watermark mang tên gốc kèm hậu tố `_da_xoa_watermark.pdf` và file `bao-cao.json`). Bạn cũng có thể nhấn **Chỉ xuất file mẫu này** nếu chỉ muốn tải trước file mẫu đang xem.
Xem trước dùng cùng xử lý với xuất; sau khi sửa lựa chọn cần xem lại. Phạm vi trang đánh số từ 1 theo thứ tự PDF, không theo số in trên giấy.

## Hành vi và giới hạn

- Nhận diện các đối tượng ảnh độc lập trên trang, không tự suy đoán ảnh nào là watermark. Người dùng chọn ảnh cần bỏ. Ảnh có cùng dữ liệu điểm ảnh được bỏ ở mọi lần xuất hiện trên các trang áp dụng. Chữ và hình vector chồng lên ảnh được giữ nguyên. Hỗ trợ ảnh trực tiếp và ảnh lồng trong Form XObject có tài nguyên riêng. Mỗi trang được sao chép nhóm/tài nguyên trước khi sửa để không ảnh hưởng trang khác. Chưa hỗ trợ ảnh inline (trang có ảnh inline không cung cấp chọn ảnh), watermark chữ/vector hoặc annotation. Nhóm tài nguyên kế thừa chưa hỗ trợ đầy đủ; nhóm có vòng lặp hoặc lồng quá sâu bị từ chối. Các trường hợp đó dùng khoanh vùng khi phù hợp.
- Khoanh vùng xoá thật chữ và làm trắng điểm ảnh nằm trong vùng; hình vector giao vùng có thể bị xoá cả đối tượng. Liên kết giao vùng cũng bị loại. Đây không phải chức năng khôi phục nội dung bị watermark che. Ảnh scan chứa watermark và chữ trong cùng ảnh không thể tách riêng bằng chế độ chọn ảnh; chọn ảnh cả trang sẽ bỏ cả trang scan. Không hứa phục hồi chữ nằm dưới watermark scan.
- Vùng được lưu theo tỷ lệ 0–1 của trang đang hiển thị, hỗ trợ crop và hướng xoay. Cùng tỷ lệ được áp dụng cho các trang khác, kể cả trang khác khổ; cần chọn khoảng trang phù hợp khi bố cục thay đổi. Tối đa 30 vùng, 100 ảnh được chọn. Hỗ trợ xử lý đơn hoặc nhiều PDF hàng loạt theo cùng cấu hình mẫu. Tổng request tối đa 200 MB.
- Xử lý đồng bộ và dùng khóa engine chung với công cụ thêm watermark. Tài liệu lớn có thể chờ lâu; chưa có tiến trình theo trang/khôi phục lượt chạy cho công cụ xoá. Không lưu nguồn hoặc kết quả của công cụ xoá trên máy chủ. Bản PNG hiển thị ở trình duyệt, tải lại trang mất lựa chọn.
- PDF lỗi, có mật khẩu hoặc cờ chữ ký số bị từ chối. Các liên kết/annotation vốn có bên ngoài vùng có thể vẫn còn; xoá ảnh không tự xoá liên kết của logo. Công cụ chỉnh nội dung hiển thị, không phải công cụ bảo đảm khử mọi dữ liệu nhạy cảm/metadata/attachment.

## Thành phần và API

`removal.py` kiểm tra cấu hình, liệt kê ảnh theo digest, bỏ lệnh vẽ ảnh khỏi stream nội dung riêng của trang và Form XObject lồng nhau (tokenizer tránh sửa nhầm chữ chứa tên ảnh), redact vùng và render. Hỗ trợ `batch_process` để xử lý danh sách file theo cùng cấu hình và xuất file ZIP. Không thay thế dữ liệu ảnh dùng chung nên trang ngoài phạm vi giữ nguyên. `/remove-watermark` phục vụ giao diện riêng trong `templates/removal.html`, `static/removal.js`, `static/removal.css`.

`POST /api/removal/inspect|preview|export|batch`: multipart `pdf` (hoặc `pdfs` cho batch), `page` 1-based. Inspect trả JSON `{pages, image:base64PNG, candidates:[{id,rect,width,height}]}` cho trang đang mở. Preview và export nhận thêm `images` JSON danh sách digest, `regions` JSON danh sách `[x0,y0,x1,y1]` chuẩn hoá, `pages=all|odd|even|custom`, `page_range`. Preview trả PNG, export trả PDF tải xuống (`<tên_gốc>_da_xoa_watermark.pdf`); batch trả ZIP (`da-xoa-watermark-hang-loat.zip`) kèm `bao-cao.json` và header `X-Success-Count`, `X-Total-Count`. `X-Removed-Images` đếm lệnh ảnh đã bỏ trên toàn phạm vi. Phải có ít nhất một ảnh hoặc vùng. Không tìm thấy ảnh khớp thì không bỏ ảnh và vẫn cho xuất. Lỗi đầu vào 400, request quá lớn 413, action không tồn tại 404. Cùng kiểm tra Host/Origin local với phần còn lại.

## Kiểm tra và vận hành

Chạy unittest toàn dự án theo [README](../../README.md). Kiểm thử độc lập dùng PDF tự tạo cho ảnh chồng chữ, ảnh lồng nhau chưa được chọn, phạm vi trang, crop/xoay, scan, vùng footer, preview/export, chuỗi giả lệnh trong chữ và đầu vào/API sai. Đã nghiệm thu PDF người dùng 15 trang: xoá 45 ảnh watermark (nền giữa trang kèm footer và hai logo header mỗi trang), giữ nguyên toàn bộ text trích xuất và 10 ảnh bài tập. Đã render cả15trang bằng Poppler, kiểm tra tổng quan và giữ SHA256 file gốc. Chưa nghiệm thu PDF rất lớn hoặc mọi biến thể Form XObject. Hai ảnh tham khảo chỉ minh hoạ, không thay cho PDF nguồn để xác nhận tách được watermark.

Không có cấu hình lưu trữ hay migration mới. Khởi động lại app để nạp route mới; chỉ phục vụ loopback. Khôi phục bằng phiên bản Git trước và xử lý lại từ nguồn, vì nguồn không bị ghi đè. Chưa có đích VPS.
