# Dashboard 9A — Điều chỉnh theo phản hồi

- Card giám sát chia hai cột bằng nhau: Fraud alerts bên trái, Alert rate bên phải; cùng nhãn 13px và giá trị 24px, giữ ngang trên desktop/mobile. Bỏ caption giải thích theo yêu cầu.
- Khôi phục thanh công cụ native của cả ba bảng bằng cách bỏ `overflow:hidden` đang cắt toolbar. Di chuột vào bảng để dùng **Download as CSV**. Không thay dữ liệu hoặc cột xuất.
- Ẩn riêng `.metric-code` và wrapper của chúng trong các trang chuyên sâu Operations, loại cả khoảng trống thừa. Giữ nguyên nhãn metric, giá trị, scope, Guardrail và các chú thích khác. Không sửa `dashboard_core.py`.

Kiểm thử `tests/test_dashboard.py`: **7 passed in 3.50s**. Cập nhật cách đối chiếu test để đọc Alert rate ở KPI riêng thay cho delta của Fraud alerts; số liệu kỳ vọng vẫn giữ nguyên.

Browser trên 1366×768 và 390×844: hai KPI cùng chiều rộng/cỡ chữ, không tràn số; tải thành công **6 CSV** (3 bảng × 2 viewport); xác nhận 13 micro-batches × 10 cột, 2 detector × 9 cột, 60 giao dịch × 9 cột. Kiểm tra TP/FP và latency mẫu đúng snapshot. Trang 10 Tracks ẩn các tên kỹ thuật, giữ đủ 10 Guardrail và mô tả. Không browser pageerror hoặc Streamlit exception. [Kết quả chi tiết](results.json).

CSV dùng database evidence cũ `paysim_ui_evidence_20261028_194420`. Kiểm thử headless buộc trình duyệt dùng nhánh Blob download được Streamlit hỗ trợ vì hộp thoại lưu tệp hệ điều hành của Chromium không phát sự kiện Playwright download. Không thay đường xuất CSV trong ứng dụng.

Ảnh: [card desktop](fraud-1366.png), [card mobile](fraud-390.png), [10 Tracks](tracks-1366.png), [toolbar history](history-1366.png), [toolbar detector](detectors-1366.png), [toolbar giao dịch](transactions-1366.png).

Đã build lại riêng image Streamlit và cập nhật bằng `docker compose up -d --no-deps streamlit`. Pipeline, MongoDB, Kafka, Spark và replayer đang chạy được giữ nguyên. Container kiểm thử riêng được dừng sau khi lưu bằng chứng. Không commit/push.
