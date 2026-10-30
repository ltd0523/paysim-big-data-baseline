# Track 9 — Phân tích đầy đủ 15 thay đổi đã định nghĩa

Phạm vi chỉ phân tích các marker có sẵn trong `view_operations.py`, `view_report.py`, `view_studio.py`, theo tài liệu 05/06. Không triển khai bố cục mới, không ghép ba AFTER, không sửa query/công thức/ground truth. Các lợi ích dưới đây là lập luận về thứ tự đọc từ code và ảnh; chưa phải kết quả đo usability.

## BEFORE 9 — Mốc Control Room

`render()` và `live_dashboard()` trong lõi hiển thị tiêu đề, sáu KPI lưới 3×2, tiến độ nguồn và sơ đồ pipeline trước điều hướng radio ngang. Trang Live có bốn chart và nhật ký batch; trang 10 tracks có các guardrail; trang Fraud có bảng model/rule, confusion matrix và scatter alerts; trang dữ liệu có bảng giao dịch và donut theo nghiệp vụ. Sidebar chứa liên kết System UIs. Bố cục phù hợp giới thiệu pipeline tổng quan; người cần bảng giao dịch phải đi qua phần mở đầu và chuyển trang.

## AFTER 9A — Operations

### 9A.1 — Khung tối, rộng và sidebar

Thay phần đầu Control Room bằng `PAGE_CONFIG` layout wide, `setup()` nền tối và radio dọc trong sidebar; vẫn có liên kết HDFS/Spark. Mục đích dành vùng chính cho tín hiệu vận hành. So BEFORE, điều hướng tách khỏi dải KPI/pipeline và tạo khu vực monitor riêng. Đánh đổi: sidebar lấy chiều rộng trên desktop, cần mở/đóng trên mobile; độ tương phản phải được đánh giá theo từng thành phần, không suy ra khả năng tiếp cận từ màu nền. Phù hợp người trực vận hành chuyển giữa bốn trang. Bằng chứng: các ảnh Operations và điều hướng browser đủ 4 trang trên cả hai viewport.

### 9A.2 — Ba KPI xử lý/tốc độ ở đầu

`summary()` đặt Spark đã xử lý (kèm lag), Ingest hiện tại và Processing throughput trên một hàng. Fraud alerts, latency và nguồn phát chuyển sang `watch()`. Mục đích ưu tiên quét tình trạng xử lý. So BEFORE, các tín hiệu xử lý/tốc độ cạnh nhau thay vì trộn với rủi ro trong lưới 3×2. Đánh đổi: sáu KPI nằm ở hai vùng, tác vụ muốn đọc hết phải dịch chuyển mắt hoặc cuộn trên mobile. Phù hợp kiểm tra ingest/processing. Audit và DOM xác nhận đủ sáu giá trị cùng delta, không bỏ KPI.

### 9A.3 — Throughput lớn và hai tín hiệu phụ

`signal()` vẽ throughput cao 300px; lag và latency cao 180px bên dưới, dùng các trường telemetry cũ và màu phù hợp nền tối. Mục đích đọc tốc độ làm trục chính rồi đối chiếu backlog/latency. So BEFORE, throughput được ưu tiên thị giác thay vì bốn chart ngang vai. Đánh đổi: chart phụ nhỏ hơn, màu và độ cao không chứng minh người dùng tìm bất thường nhanh hơn; trên mobile các chart xếp dọc. Phù hợp quan sát quan hệ giữa tốc độ, lag và độ trễ. Chỉ thay biểu diễn; không thay đơn vị events/s, ms hoặc 60 batch tải tối đa.

### 9A.4 — Cột giám sát và đối soát

`watch()` đặt alerts/alert rate, end-to-end p95, nguồn phát, vòng dữ liệu, progress và PASS/SYNCING ở cột cạnh chart trong bố cục 4:1. Mục đích đối chiếu trạng thái nguồn/rủi ro với tín hiệu xử lý. So BEFORE, các thông tin này không chiếm toàn bộ một dải pipeline ở đầu. Đánh đổi: cột 1 phần hẹp cho số dài; khi mobile xếp cột, thông tin không còn đồng thời trên một màn hình. Phù hợp trực giám sát cảnh báo và tính nhất quán. Snapshot này có display_correct=PASS; điều đó không đồng nghĩa lag=0 hoặc pipeline đang chạy.

### 9A.5 — Nhật ký và duration ở cuối

`render()` tổ chức main/aside; trang Live có expander “Micro-batch duration và nhật ký” mở sẵn, chart duration cao 100px và bảng cao 180px. Mục đích đặt chi tiết sau tín hiệu chính. So BEFORE, nhật ký ngắn gọn và liên kết với chart duration. Đánh đổi: bảng giới hạn chiều cao cần cuộn nội bộ; chart duration nhỏ; dữ liệu chi tiết ít nổi bật. Phù hợp truy batch sau khi thấy bất thường. Các trang chuyên sâu vẫn gọi `render_page()`; không mất ba trang còn lại.

## AFTER 9B — Report

### 9B.1 — Khổ đọc 1120px, nền kem, serif và mục lục

`setup()` dùng layout centered, giới hạn block 1120px, masthead báo cáo và selectbox mục lục thay radio dưới pipeline. Mục đích đọc tuần tự. So BEFORE, tiêu đề/điều hướng theo cấu trúc báo cáo và giảm độ trải ngang. Đánh đổi: không gian ngang ít hơn cho chart/bảng; selectbox cần mở danh sách để chuyển trang. Phù hợp trình bày kết quả cho hội đồng hoặc người đọc báo cáo. Browser kiểm tra chuyển đủ bốn mục trên desktop và mobile.

### 9B.2 — Hai kết quả xử lý và cảnh báo

`headline()` chia hai vùng quy mô xử lý và cảnh báo; nguồn phát ở caption, lag/alert rate vẫn là delta. Dòng giải thích alert không đồng nghĩa fraud thực tế làm rõ ý nghĩa số liệu. Mục đích trả lời đã xử lý bao nhiêu và tạo bao nhiêu cảnh báo trước khi đọc vận hành. So BEFORE, trọng tâm nghiệp vụ rõ hơn. Đánh đổi: cần đọc cuối trang để lấy ingest/processing/latency, không phù hợp xem nhanh mọi telemetry. Phù hợp báo cáo quy mô và khối lượng review cảnh báo. Sáu KPI vẫn có trên mỗi trang.

### 9B.3 — Thanh precision/recall/F1 model và rule

`comparison()` gọi lại `detector_metrics()` rồi vẽ thanh ngang theo detector trên trục 0..1 và tooltip phần trăm. Mục đích so đồng thời chất lượng hai detector ngay trang đầu. So BEFORE, người đọc không cần vào trang Fraud để thấy so sánh P/R/F1 bằng hình. Đánh đổi: thanh rất ngắn với precision/F1 thấp, số chính xác cần tooltip hoặc bảng ở trang Fraud; chart không trình bày mọi thành phần TP/FP/TN/FN. Phù hợp giải thích đánh đổi precision–recall. Audit kiểm tra bảng detector trên trang Fraud đúng snapshot; công thức và chart builder được giữ nguyên.

### 9B.4 — Confusion matrix và cơ cấu giao dịch

`business()` đặt confusion matrix cạnh so sánh detector, rồi biểu diễn cơ cấu giao dịch bằng thanh ngang sắp theo số lượng. Mục đích nối chất lượng phân loại với thành phần dữ liệu. So BEFORE, confusion matrix và cơ cấu có trên trang chính thay vì phân tán giữa trang Fraud và dữ liệu. Đánh đổi: hai cột chia diện tích trên desktop và kéo dài báo cáo trên mobile; tổng hợp loại giao dịch không thay cho tra cứu một giao dịch. Phù hợp phân tích false positives, false negatives và quy mô từng nghiệp vụ. Model matrix kiểm tra TP=52, FP=1186, TN=4962, FN=0.

### 9B.5 — Thông số vận hành và phụ lục cuối

`render()` đặt bốn KPI vận hành phía cuối và `render_page(Live)` trong expander telemetry đóng mặc định. Mục đích giữ đủ dữ liệu hỗ trợ mà ưu tiên kết quả nghiệp vụ ở đầu. So BEFORE, tuyến đọc báo cáo ít bị chart vận hành chen vào. Đánh đổi: giám sát batch cần mở phụ lục và cuộn; expander không phải cơ chế lazy-load hay cache mới, không được suy ra giảm query/response time. Phù hợp báo cáo định kỳ. Tất cả query và refresh 2 giây vẫn ở lõi chung.

## AFTER 9C — Transaction Studio

### 9C.1 — Thanh công cụ và giao dịch mặc định

`setup()` dùng segmented control với thứ tự Giao dịch, Fraud, Live, 10 tracks; mặc định chọn Giao dịch, sidebar đóng. Mục đích đi thẳng vào tác vụ đọc bản ghi. So BEFORE, không cần mở trang giao dịch sau phần tổng quan. Đánh đổi: thứ tự trang khác tài liệu PAGES; các nhãn dài chiếm diện tích khi mobile xếp dòng. Phù hợp điều tra giao dịch. Browser gốc mở lại trang mặc định ở ảnh studio-mobile; kiểm tra bổ sung mở đủ bốn trang mobile.

### 9C.2 — Bảng 60 giao dịch là vùng chính

`ledger()` đặt bảng cao 480px và các cột scored_at, event_id, type, amount, risk_score, prediction, cycle/row, latency ở workspace chính. Mục đích đối chiếu các bản ghi gần nhất. So BEFORE, bảng không bị dải sáu KPI/pipeline đẩy xuống. Đánh đổi: bảng nhiều cột cần cuộn ngang; chỉ 60 bản ghi đã tải, không có tìm kiếm toàn bộ lịch sử. Phù hợp rà soát giao dịch mới. Audit so toàn bộ giá trị 60 hàng với snapshot, sau chuẩn hóa UTC tương đương của BSON/Arrow; không nới bỏ đối chiếu dữ liệu.

### 9C.3 — Bộ chọn và inspector bên phải

`inspector()` chọn một index trong danh sách sẵn có, hiển thị amount, risk score, prediction, scored_at và end-to-end latency. Mục đích đọc một bản ghi mà vẫn giữ bảng làm ngữ cảnh. So BEFORE, không phải tìm mọi thuộc tính ở các cột xa nhau. Đánh đổi: người dùng phải chọn lại qua selectbox thay vì click trực tiếp hàng bảng; inspector nằm dưới bảng trên mobile. Phù hợp tra một giao dịch cụ thể trong 60 bản ghi. Đây là thao tác đọc; không cập nhật MongoDB hoặc chấm điểm lại. Progress chỉ biểu diễn score trong giới hạn 0..1.

### 9C.4 — Ngữ cảnh loại giao dịch và scatter alerts

`context()` đặt thanh số giao dịch theo nghiệp vụ và scatter amount/risk score của 300 alerts mới nhất dưới bảng. Mục đích đọc bản ghi trong bối cảnh chung. So BEFORE, hai biểu đồ không còn ở hai trang riêng khi đang điều tra giao dịch. Đánh đổi: scatter chỉ phản ánh alerts, không phải phân phối score toàn bộ giao dịch; amount là log scale, chart cao 150px có thể dày điểm. Phù hợp quan sát loại nghiệp vụ và cảnh báo gần đây. Audit xác nhận tải đúng 300/1238 alerts; không đánh tráo giới hạn hiển thị với tổng cảnh báo.

### 9C.5 — Sáu KPI cuối trang

`render()` đặt dải trạng thái nguồn và sáu KPI sau ledger/inspector/context hoặc nội dung chuyên sâu. Mục đích giữ trạng thái run mà không lấn vùng làm việc đầu trang. So BEFORE, ưu tiên tác vụ dữ liệu. Đánh đổi: người xem vận hành cần cuộn xuống để biết tổng quan; trên mobile sáu KPI xếp dọc làm trang dài. Phù hợp người phân tích bản ghi; không phải lựa chọn ưu tiên cho monitor toàn cảnh. Audit và browser kiểm tra sáu KPI cùng delta ở cả bốn trang bằng BEFORE.

## Tính đúng đắn và giới hạn

- Test repository: 7/7 đạt; gồm 3 phép kiểm tra AFTER trên 4 trang và 4 trường hợp DB rỗng. Fixture unit test không phải dữ liệu pipeline trong ảnh.
- AppTest snapshot thật: 16/16 trang không exception, 12/12 cặp AFTER giữ sáu KPI; bảng 60 giao dịch đúng từng giá trị ở cả bốn UI; bảng model/rule và confusion totals đúng trên trang Fraud của cả bốn UI.
- Browser: 16 desktop + 16 mobile, 24/24 cặp KPI/delta bằng BEFORE. PNG thực tế là viewport do vùng main của Streamlit cuộn bên trong, dù gọi full_page=True; không coi ảnh là bằng chứng nhìn thấy toàn bộ nội dung dài. AppTest và payload kiểm tra cả phần ngoài khung. Chỉ có Chromium, viewport desktop 1600×1600 và mobile 390×844; chưa kiểm thử thiết bị vật lý hoặc mọi trình duyệt.
- Payload chart: so đúng toàn bộ event_id/amount/risk_score/type của 300 alerts và cả bốn ô confusion matrix ở mỗi UI. Inspector Studio chọn bản ghi index 0 và 59, amount/scored_at đúng snapshot. Chi tiết: [visual-data-audit.json](visual-data-audit.json).
- Bảy collection nguồn có hash không đổi trong lúc snapshot; nội dung DB evidence khớp JSON. 1238 alert documents được giữ trong evidence, UI lấy 300; nguồn có 2000 recent documents, evidence chọn 60 theo script có sẵn. Đây là giới hạn hiển thị chủ đích, không phải mất dữ liệu do đổi view.
- Snapshot có 13 micro-batch, không đủ 60 batch để tạo bài stress ngưỡng tối đa. Không thay hạn mức và không tạo thêm giao dịch giả.
- Lag 200 chưa được xử lý; các metric không đại diện một run đã drain hoặc steady-state. Latency cao của backlog và freshness thay đổi theo thời gian không chứng minh tốc độ UI.
- Source `app.py` được đổi sang BEFORE từ bên ngoài trong phiên; giữ nguyên. Capture dùng entrypoint riêng, không phụ thuộc lựa chọn này. Hash lõi, ba view, scripts/test và pipeline khớp đầu phiên.
- Đã sửa hai vấn đề trong script audit riêng: UTC BSON và Arrow khác kiểu biểu diễn nhưng cùng thời điểm; kiểm tra hash cần tách lựa chọn app.py được đổi bên ngoài. Lưu cả log các lần đầu; không sửa metric để ép pass.

## Kết luận cho Capstone

Trên snapshot này, thay cách trình bày giữ nguyên kết quả nghiệp vụ của cả bốn UI trong phạm vi đã kiểm chứng. BEFORE phù hợp giới thiệu tổng quan; Operations ưu tiên trực pipeline; Report ưu tiên quy mô và chất lượng phát hiện; Studio ưu tiên đọc giao dịch. Mỗi AFTER có năm quyết định bố cục với chi phí cuộn/điều hướng riêng. Chọn giao diện theo tác vụ, dùng bản đối chiếu và ảnh làm bằng chứng về tính nhất quán, không tuyên bố tăng tốc hoặc nâng chất lượng model.

Số liệu đầy đủ và nguồn evidence: [bảng so sánh](dashboard-comparison.md), [snapshot](snapshot.json), [audit](snapshot-audit.json), [browser](browser-results.json), [test](test-results.txt), [biên bản](execution-summary.md).
