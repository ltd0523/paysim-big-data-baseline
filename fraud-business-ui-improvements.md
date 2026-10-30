# PaySim 9A — Fraud & Business UI/UX Improvements

Ngày thực hiện: 30/10/2026. Giao diện áp dụng: AFTER 9A — Operations.

## Hiện trạng và mục đích

Trang trước thay đổi có bảng detector, heatmap với một màu chữ cố định, grouped bar dọc và scatter trên trục Amount log. Cải tiến giúp đọc chất lượng hai detector, hiểu bốn ô confusion matrix và so sánh số alerts theo nghiệp vụ. Giữ nguyên bảng chi tiết, KPI, Monitoring Panel, menu và các cải tiến Duration/Latency/Transaction Distribution từ lần trước.

Git sạch khi bắt đầu. Đã lưu mã nguồn, Git status/diff và ảnh BEFORE mới của phiên này trong [thư mục evidence](dashboard_fraud_ui_evidence_20261030_142433/README.md). BEFORE ở đây là phiên bản Light Enterprise đã có các cải tiến trước, không phải giao diện Control Room gốc.

## Bốn thay đổi

| Thành phần | Trước | Sau và lý do |
|---|---|---|
| Model Performance Comparison | Chỉ có bảng | Thêm horizontal grouped bar cho Precision → Recall → F1; miền X cố định 0–100%, nhãn và tooltip hai chữ số thập phân. Giữ nguyên bảng bên dưới, gồm Alert rate và TP/FP/TN/FN |
| Confusion Matrix | Heatmap 2×2, một màu chữ | Giữ hàng Actual/cột Predicted và đúng vị trí bốn count; bổ sung nhãn TP/FN/FP/TN, số ở giữa ô, navy trên ô sáng và trắng trên ô tối; chú thích các ô cùng diện tích |
| Alerts by Transaction Type | Vertical grouped bar | Horizontal grouped bar 330px; mỗi loại giao dịch có hai thanh, xếp giảm dần theo `model_alerts`, bắt đầu từ 0; hiển thị cả nhóm có 0 alerts |
| Risk Score Analysis | Scatter log Amount, Risk Score 0–1 | Giữ scatter và toàn bộ bản ghi đầu vào; marker tròn 65px², opacity 0.65, viền trắng 0.6px, màu type cố định, legend/tooltip rõ, cao 380px |

Model chart và alerts chart cùng dùng **Spark MLlib `#2563EB`**, **Rule Baseline `#0F766E`**. Tên trong bảng chi tiết vẫn là `Spark SQL rule` như trước. Không sửa công thức `detector_metrics()` hoặc dựng lại bảng theo công thức riêng.

Scatter giữ `amount` nguyên giá trị, trục X log và Risk Score 0–1. Palette cố định: CASH_OUT blue, PAYMENT teal, CASH_IN ocean blue, TRANSFER rose, DEBIT slate. Không dùng tím/nâu. Tooltip giữ event_id, transaction type, amount và risk_score. Zoom chỉ tác động trục X để giữ miền Risk Score.

Nếu Amount ≤ 0, thiếu, không hữu hạn hoặc không chuyển được sang số, UI cảnh báo rõ số bản ghi không thể hiển thị trên trục log. Dataset vẫn giữ tất cả các bản ghi đó; không có bước lọc hoặc thay giá trị. Snapshot thật dùng trong lần kiểm tra này không có Amount không hợp lệ; edge tests kiểm tra riêng tình huống này trong bộ nhớ.

## Bố cục và màu sắc

Giữ nền `#F5F7FB`, card trắng bo 15px, border `#DCE5EF`, chữ navy `#0F172A`/secondary `#475569`, gridline `#E2E8F0`. Khoảng cách section 28px.

Trên desktop rộng 1600px, performance và confusion matrix dùng tỷ lệ cột 3:2. Ở 1366/1440px và mobile, hai card xếp dọc để đủ chỗ cho nhãn và bảng. Alerts và scatter chiếm toàn chiều rộng khu vực nội dung chính. Monitoring Panel vẫn nằm trong workspace hiện có; sidebar và dải KPI không đổi.

## Ảnh BEFORE / AFTER

| Vùng | Trước, 1600×900 | Sau, 1600×900 | Sau, mobile 390×844 |
|---|---|---|---|
| Performance | [Bảng](dashboard_fraud_ui_evidence_20261030_142433/before/performance-1600x900.png) | [Grouped bar và bảng](dashboard_fraud_ui_evidence_20261030_142433/after/performance-1600x900.png) | [Mobile](dashboard_fraud_ui_evidence_20261030_142433/after/performance-390x844.png) |
| Confusion Matrix | [Heatmap cũ](dashboard_fraud_ui_evidence_20261030_142433/before/matrix-1600x900.png) | [Heatmap mới](dashboard_fraud_ui_evidence_20261030_142433/after/matrix-1600x900.png) | [Mobile](dashboard_fraud_ui_evidence_20261030_142433/after/matrix-390x844.png) |
| Alerts theo type | [Thanh dọc](dashboard_fraud_ui_evidence_20261030_142433/before/alerts-1600x900.png) | [Thanh ngang](dashboard_fraud_ui_evidence_20261030_142433/after/alerts-1600x900.png) | [Mobile](dashboard_fraud_ui_evidence_20261030_142433/after/alerts-390x844.png) |
| Risk Score | [Scatter cũ](dashboard_fraud_ui_evidence_20261030_142433/before/risk-1600x900.png) | [Scatter mới](dashboard_fraud_ui_evidence_20261030_142433/after/risk-1600x900.png) | [Mobile](dashboard_fraud_ui_evidence_20261030_142433/after/risk-390x844.png) |

Có bộ ảnh tương ứng cho 1366×768 và 1440×900. Tên ảnh toàn viewport theo `{view}-{page}-{width}x{height}.png`; ảnh card là crop trực tiếp từ Chromium, không chỉnh sửa nội dung.

## Bằng chứng dữ liệu giữ nguyên

Nguồn: database evidence có sẵn `paysim_ui_evidence_20261028_194420`, run `run-20261028-042515`. Các collection khớp [snapshot pipeline gốc](dashboard_evidence_20261028_194420/snapshot.json) và fingerprint không đổi trong cả hai lượt chụp. Không tạo dữ liệu demo trong database.

<!-- METRICS_START -->
| Metric | Trước | Sau | Kết quả |
|---|---:|---:|---|
| Nguồn đã phát | 6,400 | 6,400 | PASS |
| Spark đã xử lý | 6,200 | 6,200 | PASS |
| Fraud alerts | 1,238 | 1,238 | PASS |
| Alert rate | 19.97% | 19.97% | PASS |
| Ingest hiện tại | 50.0 ev/s | 50.0 ev/s | PASS |
| Processing throughput | 40.2 ev/s | 40.2 ev/s | PASS |
| End-to-end latency p95 | 29,763,813 ms | 29,763,813 ms | PASS |
| Spark MLlib — Precision | 4.20% | 4.20% | PASS |
| Spark MLlib — Recall | 100.00% | 100.00% | PASS |
| Spark MLlib — F1 | 8.06% | 8.06% | PASS |
| Spark MLlib — Alert rate | 19.97% | 19.97% | PASS |
| Spark MLlib — TP | 52 | 52 | PASS |
| Spark MLlib — FP | 1,186 | 1,186 | PASS |
| Spark MLlib — TN | 4,962 | 4,962 | PASS |
| Spark MLlib — FN | 0 | 0 | PASS |
| Rule Baseline — Precision | 11.11% | 11.11% | PASS |
| Rule Baseline — Recall | 15.38% | 15.38% | PASS |
| Rule Baseline — F1 | 12.90% | 12.90% | PASS |
| Rule Baseline — Alert rate | 1.16% | 1.16% | PASS |
| Rule Baseline — TP | 8 | 8 | PASS |
| Rule Baseline — FP | 64 | 64 | PASS |
| Rule Baseline — TN | 6,084 | 6,084 | PASS |
| Rule Baseline — FN | 44 | 44 | PASS |
| Alerts CASH_IN — Rule Baseline | 0 | 0 | PASS |
| Alerts CASH_IN — Spark MLlib | 0 | 0 | PASS |
| Alerts CASH_OUT — Rule Baseline | 4 | 4 | PASS |
| Alerts CASH_OUT — Spark MLlib | 708 | 708 | PASS |
| Alerts DEBIT — Rule Baseline | 0 | 0 | PASS |
| Alerts DEBIT — Spark MLlib | 0 | 0 | PASS |
| Alerts PAYMENT — Rule Baseline | 0 | 0 | PASS |
| Alerts PAYMENT — Spark MLlib | 0 | 0 | PASS |
| Alerts TRANSFER — Rule Baseline | 68 | 68 | PASS |
| Alerts TRANSFER — Spark MLlib | 530 | 530 | PASS |
| Bản ghi scatter | 300 | 300 | PASS |
<!-- METRICS_END -->

Bảng trên được script `finalize.py` sinh từ kết quả audit đã chạy, không hardcode dữ liệu chart. Đối chiếu cả 16 cặp giao diện–trang xác nhận toàn bộ bảng và KPI nghiệp vụ không đổi. Loại Query latency, Snapshot response và Dashboard freshness khỏi phép so bằng tuyệt đối vì chúng phụ thuộc thời điểm.

Chi tiết máy đọc:

- [KPI comparison](dashboard_fraud_ui_evidence_20261030_142433/kpi-comparison.json).
- [Confusion Matrix comparison](dashboard_fraud_ui_evidence_20261030_142433/confusion-matrix-comparison.json).
- [Chart data audit](dashboard_fraud_ui_evidence_20261030_142433/chart-data-audit.json): sáu giá trị performance lấy từ detector_metrics, từng cặp type/detector, scatter đủ 300 bản ghi và không có Amount lỗi trong snapshot.
- [Verification](dashboard_fraud_ui_evidence_20261030_142433/verification.json): chart spec/data của các trang 9A khác và toàn bộ BEFORE/9B/9C giống bản trước.

Audit JSON lưu số thực ở độ chính xác 15 chữ số; phép so performance có dung sai tuyệt đối `1e-14` do tuần tự hóa JSON. Test AppTest trực tiếp so giá trị chart với `detector_metrics()` trước khi tuần tự hóa. Không làm tròn dữ liệu tính toán; `.2%` chỉ áp dụng cho nhãn/tooltip/bảng hiển thị.

## Kiểm thử thực tế

| Kiểm tra | Kết quả | Evidence |
|---|---|---|
| Python syntax | PASS tất cả module dashboard, test và script evidence | [syntax-results.txt](dashboard_fraud_ui_evidence_20261030_142433/syntax-results.txt) |
| `tests/test_dashboard.py` | **17 passed** | [test-results.txt](dashboard_fraud_ui_evidence_20261030_142433/test-results.txt) |
| AppTest dữ liệu thật trước/sau | 4 giao diện × 4 trang; KPI/bảng/dữ liệu giữ nguyên | `verification.json`, `before-data.json`, `after-data.json` |
| Chromium BEFORE | 4 trang 9A × 4 viewport = 16 | [before/browser-results.json](dashboard_fraud_ui_evidence_20261030_142433/before/browser-results.json) |
| Chromium AFTER | 4 giao diện × 4 trang × 4 viewport = **64**; không pageerror, console error hoặc Streamlit exception | [after/browser-results.json](dashboard_fraud_ui_evidence_20261030_142433/after/browser-results.json) |
| Responsive 9A | 1366×768, 1440×900, 1600×900, 390×844; không tràn ngang trang/chart | Cùng browser-results và bộ ảnh AFTER |
| Zero metrics, dữ liệu rỗng, zero alerts, Amount lỗi | 4 tổ hợp desktop/mobile đạt; cảnh báo rõ 4/5 Amount lỗi, không lọc dataset | [edges/results.json](dashboard_fraud_ui_evidence_20261030_142433/edges/results.json), test AppTest |
| Bảo toàn snapshot object | PASS qua AppTest; render không sửa đầu vào | `test_fraud_renderer_preserves_snapshot_and_all_chart_values` |
| Biểu đồ cải tiến trước | Duration column, hai latency line và transaction horizontal bar giữ nguyên spec/data | `prior_operations_charts_identical` trong `verification.json` |
| Docker đã rebuild | Bốn trang 9A chạy đúng, không exception; 5 chart Live, 4 Fraud, 1 Distribution | [docker/results.json](dashboard_fraud_ui_evidence_20261030_142433/docker/results.json) |
| Runtime source | Năm module dashboard và Banner khớp hash workspace | [runtime-source-verification.json](dashboard_fraud_ui_evidence_20261030_142433/runtime-source-verification.json) |
| Pipeline containers | MongoDB, Spark, Kafka, Replayer, NameNode, DataNode giữ ID và thời gian start | [deployment-verification.json](dashboard_fraud_ui_evidence_20261030_142433/deployment-verification.json) |

Môi trường: Python 3.11 trong virtualenv kiểm thử có sẵn, Streamlit 1.50.0, Altair 5.5.0, Chromium/Playwright. Các lỗi trong quá trình phát triển (fontWeight không thuộc enum Altair, timezone UTC tương đương trong Arrow và độ chính xác JSON audit) đã được xử lý; kết quả trên là các lượt xác nhận cuối. Dữ liệu edge chỉ tồn tại trong bộ nhớ.

## Kiến trúc và file đã sửa

| File | Hàm/phạm vi | Nội dung |
|---|---|---|
| `dashboard/dashboard_core.py` | `render_page()` | Thêm keyword `fraud_renderer=None` và nhánh gọi callback ở trang Fraud; default cũ và `transaction_renderer` giữ nguyên |
| `dashboard/view_operations.py` | `performance_comparison()`, `confusion_matrix()`, `alerts_by_type()`, `risk_score_analysis()`, `fraud_business()`, `detector_color()` | Presentation riêng 9A cho bốn cải tiến |
| | `setup()`, `render()` | CSS card/responsive/spacing; truyền callback mới vào hook lõi |
| `tests/test_dashboard.py` | Hai test mới, tổng ba trường hợp có tham số | Kiểm tra giá trị, màu/domain/tooltip, bảng, count/type/detector, đầu vào không bị sửa và Amount không hợp lệ |
| Báo cáo và thư mục evidence | Scripts, ảnh, JSON, log, source backup | Tái lập và kiểm chứng |

Lõi chỉ thay điểm mở rộng presentation; AST của toàn bộ core khớp bản trước khi loại đúng hook mới. Không sao chép render_page hoặc công thức metric. Các hàm cũ khác của 9A có AST giữ nguyên. `app.py`, view 9B/9C, requirements, Dockerfile và Banner không sửa. [Diff đầy đủ](dashboard_fraud_ui_evidence_20261030_142433/source-changes.diff).

Không thay Kafka/Spark/HDFS, query/schema MongoDB, model/threshold/rule/ground truth, metric hoặc dữ liệu bảng. Giữ refresh 2 giây, tối đa 300 alerts / 60 giao dịch / 60 batch, bốn trang điều hướng và mọi marker BEFORE/AFTER. Không commit, stage, push, reset volumes hoặc xóa database.

Chỉ rebuild service `streamlit` với cấu hình Compose tiêu chuẩn đang dùng:

```powershell
docker compose -f docker-compose.yml up -d --build --no-deps streamlit
```

Dashboard demo: <http://127.0.0.1:8501>. Số live có thể tiếp tục đổi; không dùng ảnh live để chứng minh bằng nhau với snapshot. Container kiểm thử riêng được dừng sau khi thu thập evidence.

## Đánh đổi và giới hạn

Thêm performance chart làm trang dài hơn. Khi không đủ chiều rộng, performance và matrix xếp dọc; bảng chi tiết giữ đầy đủ cột nhưng cần cuộn ngang trong bảng. Miền 0–100% giúp so sánh trung thực; các thanh rất thấp vẫn ngắn và phải đọc nhãn hoặc tooltip.

Heatmap dùng thang màu theo số count lớn nhất trong snapshot; không nên so độ đậm giữa hai thời điểm mà bỏ qua legend/count. Việc đổi màu chữ dùng ngưỡng 75% của miền màu, không thay count. Các ô có cùng diện tích, không biểu thị tỷ lệ bằng kích thước.

Scatter có thể chồng điểm khi nhiều giao dịch cùng amount/risk_score; giữ opacity và toàn bộ bản ghi. Với Amount không hợp lệ, log-scale không thể vẽ điểm đó và UI báo rõ. Không tự chuyển sang linear hoặc đổi dữ liệu.

Kiểm tra này xác nhận UI và tính bảo toàn dữ liệu trên snapshot, không đánh giá lại chất lượng model, thời gian thao tác người dùng hoặc hiệu năng pipeline. CSS/DOM và ảnh đã kiểm tra với theme light và phiên bản thư viện khóa; cần kiểm tra lại khi nâng Streamlit/Altair.
