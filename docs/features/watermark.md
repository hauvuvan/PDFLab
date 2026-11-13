# Watermark PDF hàng loạt

[← Tổng quan](../README.md)

## Mục đích và luồng

Công cụ watermark ảnh hoặc chữ trên PDF đơn/lô. Chọn PDF → chọn loại watermark → cấu hình hoặc áp dụng mẫu → chọn trang để xem trước → xử lý và tải ZIP. Preview và xuất dùng chung engine, không raster hóa nội dung PDF gốc.

## Nội dung watermark

- **Ảnh**: PNG, JPG, WebP. Giữ màu gốc hoặc bật đổi thành một màu; alpha giữ nguyên. Không tự xóa nền: JPG nền trắng vẫn có nền trắng nếu không dùng ảnh trong suốt.
- **Chữ**: tối đa 300 ký tự, 5 dòng, hỗ trợ tiếng Việt, xuống dòng và căn giữa. Chọn Arial, Times New Roman, Courier New và in đậm.
- Màu RGB qua bộ chọn màu. Độ trong suốt UI 0% = rõ hoàn toàn, 100% = ẩn hoàn toàn. API dùng `opacity` ngược lại: 100 = rõ, 0 = ẩn. Với ảnh, độ hiển thị nhân alpha gốc; ẩn hoàn toàn không chèn ảnh hoặc link vô hình.
- Chữ được tạo thành ảnh PNG trong suốt chất lượng cao (font cơ sở 160px, chiều rộng tối đa 2400px), nên watermark chữ không phải văn bản có thể chọn/tìm kiếm. Nội dung gốc vẫn là PDF, không chuyển cả trang thành ảnh. Ảnh xoay thu nhỏ tối đa 2400×2400 trước khi xoay để kiểm soát bộ nhớ. Đây là giới hạn thực tế nếu phóng rất lớn hoặc in khổ lớn.
- Font lấy từ macOS, không sao chép font vào repo; Linux fallback DejaVu Sans nếu đã cài. Chưa có bộ cài Windows; thiếu font sẽ báo lỗi thay vì thay chữ thành ô vuông. Trong fallback Linux, ba lựa chọn kiểu chữ cùng dùng DejaVu Sans.

## Vị trí, góc và kích thước

| Tùy chọn | Hành vi |
|---|---|
| Một watermark/trang | Chọn 9 điểm neo: trên/giữa/dưới × trái/giữa/phải |
| Lặp so le | Phủ toàn trang, hàng xen kẽ lệch nửa bước ngang; ảnh ở mép có thể bị cắt như tham khảo |
| Ngang/dọc tối đa | Rộng 5–95% trang, cao 1–80% trang; giữ tỷ lệ, khung bao **sau xoay** phải nằm trong cả hai giới hạn |
| Góc nghiêng | -180° đến 180°; góc dương nghiêng lên về bên phải, góc âm theo chiều ngược lại |
| Dịch ngang/dọc | -45% đến +45% kích thước trang; dấu âm sang trái/lên trên; watermark đơn được giữ trong trang, chế độ lặp dịch pha của lưới |
| Lề | 0–150 pt (1 pt = 1/72 inch), tự giới hạn còn 20% mỗi chiều trên trang nhỏ; dùng với watermark đơn và giới hạn kích thước |
| Khoảng trống lặp | 5–100% mỗi chiều trang, cộng thêm vào kích thước watermark để tạo bước lặp; tăng số này làm thưa hơn |
| Lớp hiển thị | Trên hoặc dưới nội dung; lớp dưới có thể bị trang scan/nền trắng che hoàn toàn |

Tọa độ tính theo hướng hiển thị thực tế, kể cả trang xoay và crop. Watermark đơn không bị xoay theo hướng trang một lần nữa. Chế độ lặp không dùng điểm neo; các nút vị trí bị khóa. Link HTTP/HTTPS là vùng chữ nhật bao watermark, giới hạn trong trang; có thể bỏ link. Với ảnh nghiêng vùng link bao gồm cả góc trong suốt của khung bao.

**Cấu hình nhanh giống ảnh tham khảo:** Chữ, nội dung `tailieuchuan.vn`, in đậm, màu `#808080`, trong suốt 65% (hiển thị 35%), góc +30°, rộng tối đa 38%, cao tối đa 35%, lặp so le, khoảng ngang 18%, dọc 12%, trên nội dung, không link. Nút “Chữ nghiêng lặp như ảnh mẫu” đặt các thông số này và giữ nội dung chữ mặc định; có thể sửa ngay sau đó. Mức độ giống còn phụ thuộc tỷ lệ trang và độ dài chữ.

**Logo chân trang:** ảnh, rộng 50%, cao 10%, giữa chân trang, lề 20pt, không nghiêng, hiển thị 100%, liên kết `https://tailieuonthi.org/`, tiền tố `[tailieuonthi.org]`, như script Colab ban đầu.

## Trang áp dụng và file đầu ra

Chọn tất cả, lẻ, chẵn hoặc khoảng tùy chọn `1-3, 5, 8-10`. Đánh số theo thứ tự PDF từ 1, không theo số trang in trên tài liệu. Khoảng vượt số trang làm lỗi riêng file đó, không âm thầm bỏ qua. Tài liệu 1 trang chọn chẵn bị báo không có trang phù hợp. Preview trang ngoài phạm vi vẫn hiển thị trang gốc để thấy hành vi thực tế.

Tiền tố tên file sửa được hoặc để trống; ký tự đường dẫn/điều khiển được thay thế, tên trùng thêm `(2)`, `(3)`… Không ghi đè nguồn, không xóa watermark cũ. Chạy lên file đã xử lý sẽ chèn thêm lần nữa. PDF hỏng, khóa mật khẩu hoặc có cờ chữ ký số bị báo lỗi riêng, các file khác vẫn xử lý. ZIP chỉ gồm file thành công, báo cáo/log theo phần dưới.

## Lưu mẫu, cập nhật và sao lưu

1. Chỉnh watermark, nhập tên mẫu rồi bấm **Lưu mẫu mới**. Mẫu ảnh lưu cả logo; mẫu chữ lưu nội dung, kiểu chữ và toàn bộ thiết lập xuất.
2. Chọn một mẫu và bấm **Áp dụng**; PDF nguồn không thay đổi và không nằm trong mẫu. Bấm **Xem** để kiểm tra lại.
3. Sửa tên/cấu hình rồi **Cập nhật mẫu** để ghi lại mẫu đang chọn. **Lưu mẫu mới** tạo id khác, kể cả khi trùng tên; nên đặt tên phân biệt.
4. **Xuất mẫu JSON** xuất bản đã lưu đang chọn (không phải cấu hình chưa lưu). **Nhập mẫu JSON** kiểm tra rồi lưu thành mẫu mới, tự áp dụng.
5. **Xóa mẫu** có xác nhận. Nên xuất JSON trước nếu muốn khôi phục; không có thùng rác mẫu.

Kho tại `data/presets.json`, tối đa 30 mẫu / 64 MB, không đưa vào Git. Ghi file nguyên tử với quyền 0600 và khóa khi cập nhật. JSON có chứa nội dung chữ/logo/link nên xem xét trước khi chia sẻ. Lỗi JSON/cấu trúc kho được báo và không tự ghi đè. Sao lưu file kho trước khi sửa tay. Dừng app rồi phục hồi bản sao đúng vị trí; hoặc nhập JSON từng mẫu trong giao diện. Xóa mẫu không ảnh hưởng PDF đã xuất. Mẫu chữ giữ lựa chọn font chứ không nhúng font gốc vào JSON, nên chuyển máy cần có font tương ứng.

## Giới hạn

100 PDF/lượt, request tối đa 200 MB, giao diện giới hạn PDF 195 MB, ảnh tối đa 15 MB / 25 triệu điểm ảnh; tổng request vẫn phải dưới 200 MB. Lô lớn/nhiều trang có thể cần chia nhỏ do bộ nhớ. Không hỗ trợ Word/Excel, HEIC, mở khóa PDF, nhiều lớp watermark khác nhau trong một lượt, chỉnh trực tiếp bằng kéo trên preview hoặc tài khoản nhiều người dùng. Mỗi lượt dùng một ảnh hoặc một nội dung chữ. Chưa kiểm thử trên tài liệu thật của người dùng hoặc khối lượng sát giới hạn.

PyMuPDF có giấy phép AGPL/thương mại; cần rà soát khi phân phối. [Tài liệu kỹ thuật PyMuPDF](https://pymupdf.readthedocs.io/en/latest/page.html) giải thích quy ước tọa độ và chèn ảnh; script gốc chỉ được đọc để tham khảo, không thực thi.

## API cục bộ

`GET /` dashboard; `GET /health` phiên bản; `POST /api/preview` multipart gồm `pdf`, `page` (1-based), `watermark` (chỉ bắt buộc khi kind=image) và cấu hình, trả PNG/`X-Page-Count`. `POST /api/process` đồng bộ trả ZIP, count header và báo cáo tóm tắt dưới 6000 ký tự; lô dài xem báo cáo trong ZIP. Giao diện hiện dùng API jobs ở phần dưới.

Cấu hình:

- `kind=image|text`, `text`, `font=sans|serif|mono`, `bold=true|false`, `color=#RRGGBB`, `tint=true|false`.
- `position=top-left|top|top-right|center-left|center|center-right|bottom-left|bottom|bottom-right`.
- `width=5..95`, `height=1..80`, `opacity=0..100`, `angle=-180..180`, `margin=0..150`, `offset_x/y=-45..45`, `spacing_x/y=5..100`.
- `layout=single|tile`, `layer=above|below`, `pages=all|odd|even|custom`, `page_range`, `link`, `prefix`.
- `GET /api/presets` → `{presets:[...]}`; `POST /api/presets` JSON `{name, options, image:base64, id?:...}` tạo/cập nhật; `DELETE /api/presets/<id>` xóa. `image` là base64 ảnh gốc không có data-URL prefix, không bắt buộc cho text. File trao đổi JSON UI thêm `format=paperdesk-watermark, version=1`.

Lỗi đầu vào JSON400, dung lượng413. Host localhost/127.0.0.1, Origin cùng nguồn nếu có. Không mở API ra Internet.

## Kiểm tra

Lệnh unittest ở [README](../../README.md). Test nâng cao xác minh render/pixel cho chữ, màu, alpha, góc, vị trí, tile/offset, phạm vi trang/lớp và vòng đời mẫu có logo; cộng regression PDF xoay/crop/batch/lỗi. Browser kiểm tra riêng chọn chữ tiếng Việt, xem trước, lưu mẫu qua reload, nhập/xuất JSON, cập nhật tên và tải ZIP. Chưa xác minh Windows/Linux, chữ ký số thật, kho64MB và lô200MB.

## Tiến trình và log cho xử lý đơn/lô

Chọn một PDF để xử lý riêng hoặc nhiều PDF để chạy lô, dùng cùng nút xuất. Giao diện hiển thị số file đã hoàn tất/tổng số, thành công/lỗi, tên file hiện tại và trang đã xử lý/tổng trang. Thanh tiến trình đo số file hoàn tất, không ước tính thời gian còn lại. Bước ghi/nén PDF có thể tiếp tục sau trang cuối. Các lỗi file không ngăn những file sau chạy; lỗi toàn lượt được báo riêng.

- `POST /api/jobs`: cùng multipart như `/api/process`, trả HTTP 202 và `id`.
- `GET /api/jobs/<id>`: trạng thái `queued|running|completed|error`, `total`, `completed`, `page`, `pages`, `current`, `success`, `failed`, `reports`, `error`.
- `GET /api/jobs/<id>/log`: tải JSONL ngay cả khi còn chạy hoặc toàn bộ PDF thất bại. Mỗi dòng có thời gian kèm múi giờ, sự kiện và dữ liệu tiến trình; lỗi có traceback giúp sửa lỗi.
- `GET /api/jobs/<id>/result`: ZIP khi hoàn tất và có ít nhất một file thành công; ngược lại HTTP 409. Giữ `/api/process` đồng bộ để tương thích khách cũ.

Xem [vận hành và lưu trữ](../README.md) cho nơi lưu, thời hạn, phục hồi khi khởi động lại và giới hạn bộ nhớ. Không hỗ trợ tiếp tục từ trang đang dở sau khi dừng máy chủ.
