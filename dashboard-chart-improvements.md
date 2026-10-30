# PaySim Dashboard 9A — Chart Visualization Improvements

Ngày thực hiện: 30/10/2026. Mục tiêu: giúp đọc duration, đối chiếu hai loại latency và so sánh số giao dịch theo nghiệp vụ. Chỉ thay lớp trình bày của Operations; giữ banner, menu, KPI, màu Fraud alerts/Alert rate và các tùy chỉnh UI có sẵn.

## Ba thay đổi

| Biểu đồ | Trước | Sau | Lý do |
|---|---|---|---|
| Micro-batch Duration | Line | Cột đứng, 180px, `#2563EB`, Y bắt đầu từ 0 | Mỗi batch là một lần xử lý rời rạc; cột thể hiện trực tiếp số giây của từng batch, Batch ID tăng dần |
| Latency p95 | Hai series chung một chart | Hai line chart 220px: Ingest `#0284C7`, End-to-End `#E11D48` | Hai metric có độ lớn khác nhau; dùng cùng miền timestamp và hai thang Y độc lập để đọc được cả hai |
| Transaction Distribution của 9A | Donut | Thanh ngang 300px, `#2563EB`, số lượng in cạnh thanh | Dễ xếp hạng theo `transactions`, đọc tên loại giao dịch và so sánh độ dài |

Latency không chuẩn hóa, lấy log, giới hạn giá trị lớn hoặc đổi đơn vị. Trục Y dùng hậu tố SI để nhãn gọn (`30M` trên trục `ms` là 30 triệu milliseconds); tooltip hiển thị timestamp, giá trị và đơn vị ms. Hai chart có tiêu đề và chú thích thang đo riêng, nằm cạnh nhau trên desktop và xếp dọc trên mobile. Duration có tooltip Batch ID, timestamp và giây với tối đa sáu chữ số thập phân. History phía dưới giữ nguyên dữ liệu, cột và thứ tự.

Thanh giao dịch dùng nguyên aggregate hiện có, xếp giảm dần theo `transactions`; `total_amount` chỉ nằm trong tooltip. Một khoảng 85px được dành ở cuối vùng vẽ để hiển thị nhãn số, gồm cả nhóm có 0 giao dịch. Nền trắng, chữ tối và gridline `#E2E8F0` theo Light Enterprise.

## Phạm vi mã nguồn

| File | Hàm | Thay đổi của lần này |
|---|---|---|
| `dashboard/view_operations.py` | `chart_style()` | Gom cấu hình hiển thị chart riêng của 9A |
| | `signal()` | Nhận miền thời gian tùy chọn; ghi rõ ms/thang Y riêng; giữ gán màu theo tên metric |
| | `batch_duration()` | Renderer cột đứng cho telemetry đã tải |
| | `transaction_distribution()` | Renderer thanh ngang và nhãn số cho aggregate đã tải |
| | `render()` | Bố trí lag và hai chart latency; gọi duration mới; truyền renderer giao dịch của 9A |
| `dashboard/dashboard_core.py` | `render_page()` | Thêm keyword tùy chọn `transaction_renderer=None`; mặc định vẫn dùng Donut cũ |
| `tests/test_dashboard.py` | Hai test có tham số và `chart_payloads()` | Kiểm tra chart, tooltip, dữ liệu, thứ tự, trường hợp rỗng/ít batch/backlog và phạm vi renderer |

Các script và bản mã nguồn trước thay đổi nằm trong [thư mục evidence](dashboard_evidence_20261030_charts/README.md). `app.py`, Dockerfile, view 9B/9C và requirements không bị sửa trong lần này. Các thay đổi chưa commit có trước phiên làm việc đã được lưu ở [pre-existing-changes.diff](dashboard_evidence_20261030_charts/pre-existing-changes.diff); không reset, stage, commit hoặc push.

**Khác biệt so với mô tả đầu bài:** 9C hiện có trang giao dịch riêng dùng cột đứng và scatter, không gọi Donut của lõi. Giữ nguyên các biểu đồ đó. BEFORE và trang giao dịch 9B tiếp tục có Donut; default renderer của lõi vẫn là Donut. Đối chiếu trước/sau xác nhận toàn bộ chart spec và dữ liệu của BEFORE/9B/9C không đổi.

## Ảnh trước/sau trên cùng snapshot

| Biểu đồ | Trước 1440×900 | Sau 1440×900 |
|---|---|---|
| Duration | [Line](dashboard_evidence_20261030_charts/before/duration-1440x900.png) | [Column](dashboard_evidence_20261030_charts/after/duration-1440x900.png) |
| Latency | [Hai series chung](dashboard_evidence_20261030_charts/before/latency-1440x900.png) | [Ingest](dashboard_evidence_20261030_charts/after/latency-1440x900.png), [End-to-End](dashboard_evidence_20261030_charts/after/e2e-latency-1440x900.png) |
| Transaction Distribution | [Donut](dashboard_evidence_20261030_charts/before/distribution-1440x900.png) | [Horizontal Bar](dashboard_evidence_20261030_charts/after/distribution-1440x900.png) |

Có các bộ ảnh tương ứng hậu tố `1600x900` và `390x844` trong `before/`, `after/`; ảnh crop chart giữ nguyên pixels trình duyệt. Ảnh toàn viewport có tên `{view}-{page}-{width}x{height}.png`. `before-source/` là mã đang có trong workspace trước khi sửa, không phải bản Git HEAD cũ.

## Metric correctness

Dùng database evidence có sẵn `paysim_ui_evidence_20261028_194420`, run `run-20261028-042515`. Tất cả collection khớp snapshot gốc [snapshot.json](dashboard_evidence_20261028_194420/snapshot.json), fingerprint không đổi trong cả hai lần chụp. Không thêm hoặc sửa bản ghi MongoDB.

| Metric | Trước | Sau | Kết quả |
|---|---:|---:|---|
| Nguồn đã phát | 6,400 | 6,400 | PASS |
| Spark đã xử lý | 6,200 | 6,200 | PASS |
| Consumer lag | 200 | 200 | PASS |
| Fraud alerts | 1,238 | 1,238 | PASS |
| Alert rate | 19.97% | 19.97% | PASS |
| Ingest hiện tại | 50.0 ev/s | 50.0 ev/s | PASS |
| Processing throughput | 40.2 ev/s | 40.2 ev/s | PASS |
| End-to-end p95 | 29,763,813 ms | 29,763,813 ms | PASS |
| Model TP / FP / TN / FN | 52 / 1186 / 4962 / 0 | 52 / 1186 / 4962 / 0 | PASS |
| Model Precision / Recall / F1 | 0.0420032310 / 1.0 / 0.0806201550 | 0.0420032310 / 1.0 / 0.0806201550 | PASS |
| Rule TP / FP / TN / FN | 8 / 64 / 6084 / 44 | 8 / 64 / 6084 / 44 | PASS |
| Rule Precision / Recall / F1 | 0.1111111111 / 0.1538461538 / 0.1290322581 | 0.1111111111 / 0.1538461538 / 0.1290322581 | PASS |
| Batch / giao dịch / alerts đã tải | 13 / 60 / 300 | 13 / 60 / 300 | PASS |

Sáu KPI canonical và Alert rate khớp trước/sau trên bốn trang 9A ở cả ba viewport. Các metric nghiệp vụ, toàn bộ bảng, dữ liệu chart và confusion matrix đã được đối chiếu qua AppTest trên cả 16 cặp giao diện–trang. Số trong ảnh Docker live có thể khác vì nguồn live tiếp tục ghi; chỉ dùng snapshot cố định để kết luận bằng nhau. Query latency và freshness phụ thuộc thời điểm nên được loại khỏi phép đối chiếu tuyệt đối.

## Kết quả kiểm thử thực tế

| Kiểm tra | Kết quả | Bằng chứng |
|---|---|---|
| Cú pháp tất cả module dashboard và test dashboard | PASS | [syntax-results.txt](dashboard_evidence_20261030_charts/syntax-results.txt) |
| `tests/test_dashboard.py` | 14 passed | [test-results.txt](dashboard_evidence_20261030_charts/test-results.txt) |
| AppTest trước/sau, dữ liệu Mongo thật | 16 cặp giao diện–trang; metric/bảng/chart data giữ nguyên | [verification.json](dashboard_evidence_20261030_charts/verification.json) |
| Chromium trước sửa 9A | 4 trang × 3 viewport = 12 | [before/browser-results.json](dashboard_evidence_20261030_charts/before/browser-results.json) |
| Chromium sau sửa cả bốn giao diện | 4 giao diện × 4 trang × 3 viewport = 48; không pageerror/Streamlit exception | [after/browser-results.json](dashboard_evidence_20261030_charts/after/browser-results.json) |
| 9A responsive | 1440×900, 1600×900, 390×844; không tràn ngang trang/chart | Cùng browser-results và ảnh trong `after/` |
| Dữ liệu rỗng / 1 batch với latency 10^12 ms | 4 trường hợp desktop/mobile, không console error/exception/tràn trang | [edges/results.json](dashboard_evidence_20261030_charts/edges/results.json) |
| 60 batch, timestamp thưa và missing latency, nhóm 0 giao dịch | PASS qua AppTest; dữ liệu đầu vào giữ nguyên | `test-results.txt` và mã test |
| Biểu đồ các giao diện khác | BEFORE/9B giữ Donut; 9C giữ cột/scatter sẵn có; chart spec/data trước/sau giống nhau | `verification.json`, test tham số theo view |
| Công thức/truy vấn | AST lõi giống bản trước sau khi loại đúng điểm mở rộng renderer | `business_logic_ast_unchanged` trong `verification.json` |
| Docker thực tế | Streamlit healthy; mở đủ bốn trang 9A, 5 chart live và 1 chart giao dịch | [docker/results.json](dashboard_evidence_20261030_charts/docker/results.json) |
| Image khớp source | Hash 5 module dashboard và Banner khớp workspace | [runtime-source-verification.json](dashboard_evidence_20261030_charts/runtime-source-verification.json) |
| Pipeline containers | ID/thời gian start không đổi cho MongoDB, Spark, Kafka, Replayer, NameNode, DataNode | [deployment-verification.json](dashboard_evidence_20261030_charts/deployment-verification.json) |

Môi trường kiểm thử: virtualenv có sẵn trong container, Python 3.11, Streamlit 1.50.0, Altair 5.5.0, Playwright/Chromium. Các lỗi selector/sidebar trong quá trình hoàn thiện harness đã được xử lý trước bộ kết quả cuối. Dữ liệu synthetic chỉ dùng trong bộ nhớ cho edge tests, không xuất hiện trong dashboard production.

## Ràng buộc bảo toàn và Docker

Giữ nguyên Spark Structured Streaming, Kafka/HDFS, MongoDB query/schema, model/threshold/ground truth, công thức Precision/Recall/F1 và metric khác. Không thêm truy vấn MongoDB. Giữ refresh 2 giây, giới hạn 60 giao dịch / 300 alerts / 60 batch, bốn trang điều hướng và toàn bộ marker BEFORE/AFTER.

Chỉ cập nhật service dashboard bằng lệnh sau, trên cấu hình Compose tiêu chuẩn đang chạy (đã kiểm tra không dùng overlay low-memory):

```powershell
docker compose -f docker-compose.yml up -d --build --no-deps streamlit
```

Dashboard demo: <http://127.0.0.1:8501>. Không reset volumes, xóa database hay restart dịch vụ dữ liệu. Container kiểm thử riêng được dừng sau khi thu thập evidence.

## Đánh đổi và giới hạn

Tách latency giúp đọc mỗi metric ở độ lớn thực tế, nhưng độ dốc/chiều cao giữa hai chart không thể so sánh trực tiếp vì thang Y riêng. Cùng miền thời gian giúp đối chiếu thời điểm; không suy diễn quan hệ nhân quả từ hai đường. Một batch duy nhất hiển thị điểm thay vì đường nối.

Trang Live dài hơn vì lag dùng một hàng, hai latency dùng hàng riêng; mobile vẫn cần cuộn. Thanh ngang dành 85px cho nhãn, nên phần thanh ngắn hơn ở mobile; nhãn số hiện tại vẫn đọc được. Với rất nhiều batch, Altair có thể bỏ bớt nhãn X để tránh chồng chữ, nhưng vẫn giữ mọi cột và tooltip.

Đây là cải thiện trình bày, chưa đo tốc độ thao tác của người dùng hoặc hiệu năng pipeline. Không xác nhận lại chất lượng model hay chạy benchmark toàn hệ thống. CSS và screenshot được kiểm tra với theme light và các phiên bản thư viện đã khóa; cần kiểm tra lại khi nâng phiên bản.
