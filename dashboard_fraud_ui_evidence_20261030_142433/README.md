# Evidence — 9A Fraud & Business

Ngày 30/10/2026. Dùng snapshot MongoDB cố định `paysim_ui_evidence_20261028_194420`, run `run-20261028-042515`; không ghi MongoDB.

- [Báo cáo, ảnh và giải thích](../fraud-business-ui-improvements.md).
- `before-source/`, `test_dashboard.before.py`, `git-status-before.txt`, `git-diff-before.txt`: trạng thái trước thay đổi. Git sạch lúc bắt đầu.
- `before/`: 16 tổ hợp 9A, gồm crop bốn vùng Fraud trước thay đổi.
- `after/`: 64 tổ hợp của bốn giao diện, crop performance/matrix/alerts/risk ở bốn viewport.
- `before-data.json`, `after-data.json`: toàn bộ KPI, bảng và chart spec/dataset trước/sau trên đủ 16 trang mỗi lượt.
- [KPI](kpi-comparison.json), [confusion counts](confusion-matrix-comparison.json), [chart data audit](chart-data-audit.json), [verification](verification.json).
- [Tests](test-results.txt), [syntax](syntax-results.txt), [edge browser](edges/results.json), [Docker browser](docker/results.json).
- `source-changes.diff`, `runtime-source-verification.json`, `deployment-verification.json`, `artifact-manifest.json`: phạm vi và provenance.

Các script `capture.py`, `audit.py`, `edge_browser.py`, `docker_smoke.py` chạy bằng virtualenv `/tmp/track9-venv/bin/python` trong container kiểm thử có repo read-only tại `/workspace`. Output ở `/tmp/paysim-fraud`, sau đó sao chép vào thư mục này. `finalize.py` chạy trên host, kiểm tra cú pháp/evidence, sinh bảng correctness từ audit và lập manifest.

Trình tự tái lập: lưu source vào `before-source/`, chạy `capture.py before` và `audit.py before`, sửa source, chạy `capture.py after` và `audit.py after`, sau đó `audit.py compare`. `capture.py after --views operations` chỉ làm mới phần 9A và giữ kết quả các view khác. Chạy `edge_browser.py` cho dữ liệu biên trong bộ nhớ. Sau khi rebuild riêng Streamlit, chạy `docker_smoke.py` cho service thật. Không chép dữ liệu edge vào database.
