# Quy tắc ghi nhận công việc

- Mặc định sau mỗi task đã hoàn thiện có thay đổi dự án, phải cập nhật `docs/activity-log.md` và `docs/status.md`, không cần người dùng nhắc lại. Task chỉ đọc/trả lời không cần tạo commit chỉ để ghi log.
- Khi mở lại dự án, đọc `docs/status.md`, các mục mới nhất trong `docs/activity-log.md` và kiểm tra Git trước khi sửa.
- Nhật ký ghi giờ Asia/Ho_Chi_Minh, yêu cầu, thay đổi thực tế, kiểm tra và kết quả, giới hạn/chưa kiểm tra, việc còn lại, liên kết tài liệu, trạng thái commit/push GitHub và triển khai VPS. Không ghi bí mật; không tuyên bố hoàn tất khi thiếu bằng chứng.
- Trang trạng thái tóm tắt đã làm, đang làm, chưa làm và bước tiếp theo. Phân biệt rõ mã đã commit với thay đổi chưa commit; không coi thay đổi của task khác là đã nghiệm thu.
- Giữ nguyên thay đổi không liên quan; chỉ commit phần thuộc task. Có remote GitHub và quyền thì push theo quy trình, không force-push hoặc tự merge. Chỉ triển khai khi có đích và cấu hình rõ; sau triển khai phải kiểm thử thực tế và bổ sung log.
- Với thay đổi mã/tính năng/triển khai, tạo agent kiểm thử độc lập, không tự deploy/push hoặc tạo thêm agent. Tài liệu/quy tắc thuần túy kiểm tra tính nhất quán và liên kết phù hợp.
- Tính năng lớn cần tài liệu chi tiết, liên kết từ `docs/README.md`; nhật ký chỉ tóm tắt và dẫn tới nguồn chính.
