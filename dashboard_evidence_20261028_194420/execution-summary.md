# Track 9 — Biên bản thực thi 28/10/2026

## Môi trường và phạm vi

Workspace `D:\BigData_PJ\paysim-big-data-baseline`, branch `main`, commit `437462e4e2c149c427e23d36ff42002400a1ee52`. Git sạch khi bắt đầu. Host Windows PowerShell, Python 3.14.6; không dùng host Python để ép các dependency cũ. Kiểm thử trong container Linux/WSL2 độc lập `paysim-track9-20261028-194420`, Python 3.11.18, virtualenv `/tmp/track9-venv` dùng system-site-packages của image Streamlit. Source mount read-only, chỉ evidence mount được ghi.

Streamlit 1.50.0, PyMongo 4.10.1, pandas 2.2.3, Altair 5.5.0, pytest 9.1.1, mongomock 4.3.0, Playwright 1.64.1. MongoDB 8.0.29. Chi tiết: [environment.json](environment.json), [dependency freeze](test-environment-freeze.txt), [Docker](docker-version.json).

## Các phase thực hiện

1. Đọc đầy đủ hai hướng dẫn, app/core/ba view và ba script test/snapshot/capture bắt buộc. Kiểm tra git, Docker, Python, run/telemetry, health MongoDB và Streamlit. Ban đầu toàn bộ container đều dừng. Docker API cần quyền ngoài sandbox; đã sử dụng quyền được cấp.
2. Khởi động MongoDB/Streamlit để đọc dữ liệu lưu trong volumes. Lệnh `docker compose start mongodb streamlit` tự bật dependency Kafka/HDFS và Spark ngoài dự định; đã ngắt lệnh, dừng Spark/replayer và trả Kafka/HDFS về dừng. Spark hoàn thành batch 198: input/valid=500, alerts=94, duration khoảng 12,45s lúc 12:43:17 UTC; lần dừng tạo lỗi ở batch kế tiếp trước đoạn xử lý/ghi dữ liệu. Log `spark-observation.txt` được giữ nguyên; không gọi đây là lượt pipeline end-to-end thành công. Kiểm tra trạng thái và hash bảy collection ổn định trước/sau snapshot để xác nhận dữ liệu serving nhất quán sau lần dừng.
3. Chạy nguyên `tests/snapshot_dashboard.py` với URI nội bộ, database evidence mới `paysim_ui_evidence_20261028_194420`, output `snapshot.json`. Script từ chối DB có sẵn. Snapshot lúc `2026-10-28T12:45:54.977000+00:00`, run `run-20261028-042515`; aggregate tổng bằng evaluation processed và telemetry processed_total; alerts=TP+FP; evaluation revision không đổi. Wrapper còn đối chiếu toàn bộ hash của bảy collection nguồn trước/sau copy. Không ghi nguồn và không ghi đè evidence cũ.
4. Chạy nguyên `tests/capture_dashboard.py --output /evidence/captures` trên database evidence. Công cụ tuần tự mở BEFORE, Operations, Report, Studio qua entrypoint tạm, không sửa app.py; chụp 16 desktop và 4 mobile mặc định. Cài Chromium cùng thư viện cần thiết chỉ trong container kiểm thử, không cài vào Python hệ thống.
5. Chạy script bổ sung chỉ trong evidence để kiểm tra điều hướng đủ 4 trang mobile mỗi UI và chụp thêm 16 ảnh. Chạy pytest gốc và AppTest riêng trên snapshot thật. Hợp nhất kết quả browser vào file ở thư mục gốc evidence, giữ JSON thô của capture gốc trong captures.
6. Lập bảng đối chiếu, phân tích 15 marker và giới hạn. Không sửa logic/query/core/view/pipeline/MLlib/Kafka/HDFS/replayer; không commit/push, không reset volume hoặc xóa dữ liệu.

## Kết quả thực tế

| Kiểm tra | Kết quả |
|---|---|
| Pytest `python -m pytest -q tests/test_dashboard.py` (thêm `-p no:cacheprovider` vì source read-only) | 7 passed, exit 0 |
| AppTest trên Mongo snapshot thật | 16 trang, không exception; 12/12 cặp AFTER bằng BEFORE |
| Browser desktop | 16/16 trang, không exception/pageerror; 12/12 cặp KPI/delta |
| Browser mobile | 16/16 trang, không exception/pageerror; 12/12 cặp KPI/delta |
| Ảnh | 36 PNG: 16 desktop + 4 mobile mặc định + 16 mobile đủ trang |
| Bảng giao dịch | 60/60 bản ghi và toàn bộ giá trị bằng snapshot trên mỗi UI |
| Model/rule | Bảng P/R/F1 và TP/FP/TN/FN khớp evaluation trên trang Fraud của cả 4 UI |
| Payload biểu đồ và tương tác | 300 alerts và 4 ô confusion matrix đúng ở 4 UI; chọn bản ghi Studio index 0/59 đúng amount/scored_at |
| Snapshot/DB | Bảy collection documents khớp JSON; hash nguồn không đổi trong copy |
| Giới hạn tải | 60 giao dịch, 300 alerts, 13 batch hiện có; ngưỡng batch tối đa 60 giữ nguyên |
| Refresh / code logic | Refresh 2 giây giữ nguyên; hash core/ba view/pipeline/test/scripts không đổi |

Model P/R/F1: 4.20% / 100.00% / 8.06%. Rule P/R/F1: 11.11% / 15.38% / 12.90%. Nguồn phát 6,400, xử lý 6,200, lag 200, alerts 1,238, alert rate 19.97%; ingest 50.0 ev/s, processing 40.2 ev/s, end-to-end p95 29,763,813 ms. Precision thấp cùng recall cao của model là kết quả thật của snapshot; không sửa threshold hoặc ground truth.

## Sự cố kiểm thử và khả năng tái lập

Audit lần đầu thất bại vì timezone dtype `FixedOffset(0)` của BSON khác kiểu UTC của Arrow; đã chuẩn hóa thời điểm UTC trong expected table, vẫn so toàn bộ dữ liệu. Lần hai phát hiện app.py được đổi sang BEFORE từ bên ngoài; ghi riêng routing và bắt buộc các file còn lại giữ nguyên. Lần cuối audit đạt. Giữ các log `snapshot-audit-first-attempt.txt` và `snapshot-audit-second-attempt.txt`. Lệnh compileall thử ghi bytecode vào source read-only nên bị từ chối; thay bằng AST parse trong bộ nhớ, năm module hợp lệ. Các sự cố này không phải Streamlit exception trong UI.

Script audit payload có hai lỗi harness ban đầu: tên hàm giải mã Arrow phải là convert_arrow_bytes_to_pandas_df trong Streamlit 1.50, và AppTest cần đặt rõ giá trị segmented control trước khi thao tác selectbox Studio. Đã sửa script riêng trong evidence, lưu log hai lần đầu; không sửa view hoặc logic nghiệp vụ. Kiểm tra cuối xác nhận đủ 300 alert payloads, matrix bốn ô và thao tác chọn đầu/cuối.

Mobile capture bổ sung có hai lần lỗi công cụ: nút đóng sidebar vẫn được Playwright xem là visible khi đã nằm ngoài viewport, và vòng đọc từng locator KPI gặp fragment refresh xóa phần tử giữa hai lệnh. Đã kiểm tra bounding box thật của nút và đọc metric DOM nguyên tử trong một browser task; giữ refresh 2 giây. Lưu hai log mobile-capture-first-attempt.txt và mobile-capture-second-attempt.txt. Chạy tiếp các view còn thiếu, kết quả cuối đủ 16 trang mobile; không sửa ứng dụng để né lỗi công cụ.

Lựa chọn source app.py cuối phiên là BEFORE, do thay đổi bên ngoài được giữ lại; image Docker sẵn có vẫn là Operations và không tự nhận lựa chọn này khi chưa rebuild. Hash core và ba view trong image trùng source; xem runtime-dashboard-sha256.json. Capture dùng source và từng module view riêng, độc lập lựa chọn Docker live.

Trạng thái bàn giao: MongoDB/Streamlit/Spark/Kafka/NameNode healthy, replayer và DataNode đang chạy theo services-final.json. Stack đã khởi động lại sau khi lấy snapshot, khoảng 19:58 giờ Việt Nam, trong lúc cài browser/kiểm thử; replayer và Streamlit có container ID mới. Không truy nguyên tác nhân khởi động lại từ các quan sát này. Database nguồn paysim do đó tiếp tục thay đổi. Kiểm tra cuối ban đầu thất bại vì điều kiện phụ quá chặt “nguồn vẫn không đổi suốt capture”; điều kiện đúng cho so sánh là database evidence riêng phải giữ nguyên. Ghi nguyên fingerprint thay đổi của nguồn và bắt buộc cả bảy collection evidence vẫn khớp JSON; không nới điều kiện trên dữ liệu dùng so sánh.

Dashboard Docker ở http://127.0.0.1:8501 dùng image Operations hiện có và database live paysim, không phải DB evidence. Ảnh browser được chụp qua entrypoint tạm trên DB evidence ở cổng 8510 trong container kiểm thử, không lấy từ cổng demo live. Container kiểm thử riêng và database evidence mới được giữ để tái lập; xem services-final.json, post-capture-database-checks.json và final-verification.json. Không dừng lại stack live vừa được khởi động lại.

Snapshot không phải transaction MongoDB đa collection. Trong lần này writers đã dừng và fingerprint nguồn ổn định; không chỉ dựa vào một lần đọc evaluation. Database evidence và snapshot JSON được giữ lại để demo/tái lập. Muốn chạy lại capture, dùng môi trường đúng dependency, đặt `MONGO_DATABASE=paysim_ui_evidence_20261028_194420` và URI MongoDB truy cập được rồi chạy script có sẵn. URI từ host là `mongodb://127.0.0.1:27017`, từ mạng Docker là `mongodb://mongodb:27017`.

## Giới hạn và kết luận

Không train lại hoặc kiểm thử pipeline end-to-end mới; dữ liệu là run thật đã lưu và một batch phục hồi trước snapshot. Không bảo đảm run drain (còn lag 200). Latency ~8,27 giờ phản ánh backlog sau dừng lâu, không phải thời gian render dashboard. Không đo response time, FPS, tài nguyên UI hoặc thời gian người dùng hoàn thành tác vụ. Không kết luận AFTER nhanh hơn hoặc phát hiện fraud tốt hơn. Freshness và query latency phụ thuộc lúc mở UI, loại khỏi so sánh KPI tuyệt đối. Không đánh giá toàn bộ browser/device; mobile là viewport Chromium, không phải thiết bị vật lý. Ảnh 1600×1600 và 390×844 chỉ ghi viewport vì Streamlit cuộn trong vùng main; nội dung dài kiểm tra bằng AppTest/DOM/payload, không giả định full_page=True đã chụp hết.

Kết quả phù hợp đưa vào Capstone như bằng chứng đổi cách trình bày giữ nguyên dữ liệu và số liệu. Operations phục vụ giám sát, Report phục vụ báo cáo, Studio phục vụ tra cứu giao dịch; BEFORE giữ vai trò tổng quan. [Bảng so sánh](dashboard-comparison.md) và [phân tích đủ 15 thay đổi](dashboard-analysis.md) nêu mục đích, lợi ích và đánh đổi từng phương án.
