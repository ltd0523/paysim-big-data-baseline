# Evidence — PaySim 9A Chart Improvements

Thực hiện ngày 30/10/2026 trên cùng MongoDB evidence snapshot `paysim_ui_evidence_20261028_194420`, run `run-20261028-042515`. Không ghi dữ liệu vào database.

- [Báo cáo thay đổi, ảnh và bảng correctness](../dashboard-chart-improvements.md).
- `before-source/`: mã và banner hiện có trước khi sửa; `pre-existing-changes.diff`/`git-status-before.txt`: trạng thái ban đầu.
- `before/`: 12 tổ hợp 9A trước sửa; `after/`: 48 tổ hợp của bốn giao diện sau sửa, kèm crop duration/latency/distribution.
- `before-data.json`, `after-data.json`: KPI, toàn bộ bảng và dataset/spec biểu đồ trên đủ 16 trang mỗi lượt.
- [verification.json](verification.json): đối chiếu số liệu, AST lõi, chart các view khác và database fingerprints.
- [Test results](test-results.txt), [syntax](syntax-results.txt), [edge browser](edges/results.json), [Docker browser](docker/results.json).
- [Runtime hashes](runtime-source-verification.json), [container preservation](deployment-verification.json).

`capture.py`, `audit.py`, `edge_browser.py`, `docker_smoke.py`, `checks.py` là công cụ tái lập. Chạy bằng virtualenv `/tmp/track9-venv/bin/python` trong container kiểm thử có mount repo read-only tại `/workspace`, cùng network MongoDB. Output trung gian ở `/tmp/paysim-charts/`, sau đó sao chép vào thư mục này. Thứ tự: `capture.py before`, `audit.py before`, sửa source, `capture.py after`, `audit.py after`, `audit.py compare`; `checks.py` chạy syntax/pytest/audit cuối. Bản trước được import từ `before-source/`, bản sau từ `dashboard/`.

9C trước phiên đã dùng cột đứng/scatter ở trang giao dịch, không có Donut tại trang này. Các chart đó được giữ nguyên. Donut mặc định của lõi, BEFORE và trang giao dịch 9B vẫn giữ nguyên.
