# PaySim Dashboard 9A — Modern Fintech / Spacious

Ngày thực hiện: 29/10/2026. Thay đổi mã ứng dụng chỉ trong `dashboard/view_operations.py`. `dashboard/app.py` đã chọn AFTER 9A khi bắt đầu nên giữ nguyên. Giữ đầy đủ marker BEFORE Start/END và AFTER Start/END.

## Ảnh trước và sau

| Bằng chứng | Trước | Sau |
|---|---|---|
| Laptop 1366×768 | [9A ban đầu](before/1-1366x768.png) | [9A mới](after/1-1366x768.png) |
| Desktop 1440×900 | [9A ban đầu](before/1-1440x900.png) | [9A mới](after/1-1440x900.png) |
| Desktop 1600×900 | [9A ban đầu](before/1-1600x900.png) | [9A mới](after/1-1600x900.png) |
| Mobile 390×844 | [9A ban đầu](before/1-390x844.png) | [9A mới](after/1-390x844.png) |
| Lịch sử micro-batch | [Ban đầu](before/history-1440x900.png) | [Mới](after/history-1440x900.png) |

Ảnh bổ sung: [Consumer lag và latency](after/signals-1366x768.png), [giám sát mobile](after/monitor-390x844.png), [10 Tracks](after/2-1440x900.png), [Fraud & Business](after/3-1440x900.png), [giao dịch](after/4-1440x900.png). Thư mục `after/` có ảnh phần cuối của ba trang chuyên sâu và ảnh biểu đồ/monitoring/lịch sử ở từng viewport.

Streamlit cuộn trong vùng main; ảnh chụp là viewport tại các vị trí cuộn, không gọi một ảnh `full_page` là bằng chứng toàn bộ trang.

## Bảng thay đổi visual

| Khu vực | Trước | Sau | Lợi ích và đánh đổi |
|---|---|---|---|
| 9A.1 Theme | Nền tối nhưng sidebar theo theme sáng; typography thiếu đồng bộ | Background `#0B1220`, sidebar `#142237`, surface `#1B2B40`, border `#304258`; font Inter nếu có, fallback system; không tải font ngoài | Phân biệt surface rõ hơn, màu nhất quán |
| 9A.1 Sidebar | Radio tiêu chuẩn, nhấn bằng dấu tròn | Rộng 252px, mục đang chọn có nền riêng và viền cyan; giữ đúng `PAGES` và `dashboard_page`; đủ HDFS/Spark Web UI | Nhận biết vị trí hiện tại; vẫn dùng radio thật để điều khiển bằng bàn phím |
| 9A.2 Header | “Trung tâm vận hành”, metadata một dòng | “Operations Center”; mô tả theo đặc tả; nhãn RUN/STOPPED, Run ID và chu kỳ 2 giây; HTML metadata được escape | Trạng thái run dễ đọc; không suy diễn snapshot lịch sử thành dữ liệu đang chảy |
| 9A.2 KPI | Card nhỏ, giá trị lag dương và alert rate có sắc xanh/mũi tên tăng | Ba KPI trên cùng, cao tối thiểu 136px, số 34px và tabular numerals; lag giữ nguyên nội dung với màu amber, bỏ mũi tên; ba KPI còn lại trong monitoring | Phân cấp giá trị/nhãn rõ; giữ nguyên chuỗi giá trị và delta để đối chiếu |
| 9A.3 Chart | Processing dùng amber; màu series không cố định giữa biểu đồ | Ingest cyan, processing emerald, lag amber, ingest p95 violet, end-to-end p95 orange, batch trung tính; nét 2.5px, điểm nhỏ, grid nhẹ | Series có ý nghĩa nhất quán; giữ nguyên thời điểm và toàn bộ giá trị, kể cả latency rất lớn |
| 9A.3 Tooltip | Timestamp/metric/value thiếu đơn vị rõ ràng | Timestamp có ngày/giờ/giây, metric, value và unit; miền màu tường minh theo tên series | Đọc giá trị chính xác khi latency quá lớn làm chuỗi nhỏ khó nhìn trên cùng trục |
| 9A.4 Workspace | Tỉ lệ 4:1; khoảng cách và panel hẹp | Tỉ lệ 3:1, gap 24px; plot cao 340px và hai plot phụ 220px; monitoring riêng với alerts, p95, emitted, vòng dữ liệu và đối soát | Không gian đọc dễ hơn; phần giám sát dài có thể khiến vùng history xuống thấp hơn |
| 9A.4 Ngữ nghĩa | PASS ít ngữ cảnh, alerts dùng delta xanh | Ghi rõ alerts chưa là fraud đã xác nhận; PASS/SYNCING chỉ kiểm tra aggregate/alerts với evaluation | Không gán màu cảnh báo thành lỗi hệ thống hoặc tuyên bố pipeline khỏe mạnh |
| 9A.5 History | Nằm trong main hẹp, plot 100px, bảng 180px | Đặt dưới toàn bộ workspace; plot 150px, bảng cuộn 240px; đủ 10 cột cũ khi dữ liệu có các cột đó | Bảng có thêm chiều rộng; tăng chiều dài trang |
| Responsive và accessibility | Thừa padding laptop; một số icon/chú thích kém tương phản | Padding 28px desktop/20px mobile, stack ở màn nhỏ, số dài được wrap đầy đủ, focus viền cyan, caption không bị opacity mặc định làm mờ | Không cắt số, không tràn ngang toàn trang trong viewport kiểm thử; mobile cần cuộn nhiều hơn |

## Bảo toàn dữ liệu và phạm vi

Dùng lại nguyên database `paysim_ui_evidence_20261028_194420`, đối chiếu bảy collection với [snapshot JSON gốc](../dashboard_evidence_20261028_194420/snapshot.json). Không tạo snapshot mới, không seed lại database, không sửa collection. Fingerprint database trước/sau browser capture giống nhau ở cả hai lượt: [trước](before/database-fingerprints.json), [sau](after/database-fingerprints.json).

Run `run-20261028-042515`, trạng thái `stopped`: đã phát **6,400**, Spark xử lý **6,200**, lag **200**, alerts **1,238**, alert rate **19.97%**, ingest **50.0 ev/s**, processing **40.2 ev/s**, end-to-end p95 **29,763,813 ms**. Đây là telemetry lịch sử; latency lớn được hiển thị nguyên vẹn và không phải thời gian phản hồi UI.

Giữ nguyên `dashboard_core.py`, Mongo queries, refresh `@st.fragment(run_every=2.0)`, Spark/Kafka/HDFS/MLlib, scoring threshold và ground truth. Ba trang chuyên sâu vẫn gọi `render_page(s, page)` từ core. Không commit/push. Xem [hash trước](source-before.json), [hash sau](source-after.json) và [data audit](data-audit.json).

## Kết quả kiểm thử

| Kiểm tra | Kết quả |
|---|---|
| `tests/test_dashboard.py` gốc | **7 passed**; [log](test-results.txt) |
| AppTest trên snapshot thật | 4 trang 9A trước/sau: sáu KPI và delta bằng nhau, tất cả bảng và dữ liệu biểu đồ bằng nhau |
| Chart chuyên sâu | JSON specification không đổi; 300 điểm alert và bốn ô confusion matrix khớp snapshot |
| Bảng giao dịch | Đủ 60 giao dịch và mọi giá trị khớp snapshot |
| History | Đủ 13 micro-batches hiện có; bảng giữ toàn bộ cột cũ; giới hạn query vẫn 60 |
| Browser trước | 4 trang × 4 viewport = 16 tổ hợp; không pageerror/Streamlit exception |
| Browser sau | 4 trang × 4 viewport = 16 tổ hợp; không pageerror/Streamlit exception; không KPI bị cắt/tràn; không tràn ngang tài liệu; sidebar 252px |
| Bàn phím | Focus hiển thị rõ; ArrowDown/ArrowUp chuyển trang thật |
| Tooltip | Hover điểm dữ liệu SVG thật, có Timestamp/Metric/Value/Unit |
| Biên hiển thị | Telemetry trống hiển thị chờ, không dựng chart giả; latency `9,876,543,210,123 ms` trên desktop và mobile không mất số; SYNCING và metadata chứa ký tự HTML hiển thị đúng |
| Refresh | Giữ nguyên 2 giây trong cả AppTest và browser; tình huống biên chờ thêm một chu kỳ, không exception |

Log và dữ liệu chi tiết: [browser trước](before/browser-results.json), [browser sau](after/browser-results.json), [data audit](data-audit.json), [browser edge cases](edge-cases/results.json), [kết luận tự động](verification.json). Các tình huống biên chỉ sửa bản snapshot **trong bộ nhớ của entrypoint kiểm thử**, không ghi MongoDB, không dùng làm số liệu vận hành thực tế.

Môi trường kiểm thử: container có sẵn `paysim-track9-20261028-194420`, Python 3.11.18, Streamlit 1.50.0, Altair 5.5.0, pandas 2.2.3, PyMongo 4.10.1, pytest 9.1.1, mongomock 4.3.0, Playwright 1.64.1/Chromium. Host Windows; không cài package vào Python hệ thống. Chỉ mở lại MongoDB và container kiểm thử để đọc snapshot, không khởi động Spark/replayer.

Sau khi lưu bằng chứng, đã dừng lại đúng hai container mở cho kiểm thử để khôi phục trạng thái ban đầu. Các container pipeline khác giữ nguyên trạng thái dừng.

## Giới hạn và kết luận UX

Spacious giúp tách nhóm thông tin, đọc số và nhận biết series dễ hơn qua ảnh kiểm tra. Đây là nhận xét thiết kế, chưa phải kết quả nghiên cứu người dùng. Đánh đổi là cuộn dài hơn, đặc biệt trên mobile và khi monitoring cao hơn cụm biểu đồ.

**Giới hạn theme:** capture cố ý chạy với native Streamlit theme `light` để kiểm tra trường hợp bất lợi. Shell, sidebar, KPI, expander và chart Operations dùng dark tokens. Canvas của bảng native và một số chart do `dashboard_core.py` tạo vẫn kế thừa theme Streamlit, nên còn nền sáng với chữ tối. CSS bên ngoài không đổi palette/canvas một cách đáng tin cậy. Giữ nguyên payload core theo phạm vi yêu cầu; không tuyên bố toàn bộ canvas đã đồng bộ dark. Việc đặt native Streamlit theme sang Dark có thể đổi nền các thành phần kế thừa, nhưng không được âm thầm áp vào bộ ảnh trước/sau này.

CSS sử dụng `data-testid`, `:has()` và container keys, đã kiểm chứng trên Streamlit 1.50.0/Chromium; cần kiểm tra lại nếu nâng Streamlit hoặc đổi browser. Mobile là viewport mô phỏng, không phải thiết bị vật lý. Chưa đo response time, FPS, tải CPU/RAM hay thời gian hoàn thành tác vụ; không kết luận UI nhanh hơn hoặc model phát hiện fraud tốt hơn.

Trong quá trình kiểm thử có lỗi ở công cụ chụp (selector mở sidebar, chọn ký hiệu legend thay vì điểm dữ liệu) và một lần thử tham số `width` chưa có trong API Altair chart của Streamlit 1.50.0. Đã sửa công cụ và giữ `use_container_width=True` cho chart; bảng dùng `width="stretch"` được 1.50.0 hỗ trợ. Kết quả cuối được chạy lại sau sửa, không dùng lượt lỗi làm bằng chứng đạt.

Thay đổi nằm ở source, chưa rebuild image/deploy dashboard Docker đang dùng. File app vẫn chọn Operations. Toàn bộ ảnh và dữ liệu ở đây được tạo từ source mới qua entrypoint kiểm thử riêng.
