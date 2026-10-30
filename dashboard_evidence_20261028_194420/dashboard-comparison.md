# Track 9 — So sánh dashboard trên cùng snapshot

Ngày thực nghiệm: 28/10/2026, múi giờ Asia/Saigon. Snapshot lúc `2026-10-28T12:45:54.977000+00:00` (19:45:54 giờ Việt Nam).
Database duy nhất: `paysim_ui_evidence_20261028_194420`. Commit: `437462e4e2c149c427e23d36ff42002400a1ee52`, nhánh `main`.

| Tiêu chí | BEFORE 9 | AFTER 9A | AFTER 9B | AFTER 9C |
|---|---|---|---|---|
| Run ID | run-20261028-042515 | run-20261028-042515 | run-20261028-042515 | run-20261028-042515 |
| Nguồn đã phát | 6,400 | 6,400 | 6,400 | 6,400 |
| Spark đã xử lý / lag | 6,200 / 200 | 6,200 / 200 | 6,200 / 200 | 6,200 / 200 |
| Fraud alerts / alert rate | 1,238 / 19.97% | 1,238 / 19.97% | 1,238 / 19.97% | 1,238 / 19.97% |
| Ingest hiện tại | 50.0 ev/s | 50.0 ev/s | 50.0 ev/s | 50.0 ev/s |
| Processing throughput | 40.2 ev/s | 40.2 ev/s | 40.2 ev/s | 40.2 ev/s |
| End-to-end latency p95 | 29,763,813 ms | 29,763,813 ms | 29,763,813 ms | 29,763,813 ms |
| Fraud metrics — model | Model P/R/F1: 4.20% / 100.00% / 8.06% | Model P/R/F1: 4.20% / 100.00% / 8.06% | Model P/R/F1: 4.20% / 100.00% / 8.06% | Model P/R/F1: 4.20% / 100.00% / 8.06% |
| Fraud metrics — rule | Rule P/R/F1: 11.11% / 15.38% / 12.90% | Rule P/R/F1: 11.11% / 15.38% / 12.90% | Rule P/R/F1: 11.11% / 15.38% / 12.90% | Rule P/R/F1: 11.11% / 15.38% / 12.90% |
| Confusion matrix — model TP/FP/TN/FN | 52 / 1,186 / 4,962 / 0 | 52 / 1,186 / 4,962 / 0 | 52 / 1,186 / 4,962 / 0 | 52 / 1,186 / 4,962 / 0 |
| Confusion matrix — rule TP/FP/TN/FN | 8 / 64 / 6,084 / 44 | 8 / 64 / 6,084 / 44 | 8 / 64 / 6,084 / 44 | 8 / 64 / 6,084 / 44 |
| Dữ liệu UI | 60 giao dịch; 300/1,238 alerts; 13/60 batch | 60 giao dịch; 300/1,238 alerts; 13/60 batch | 60 giao dịch; 300/1,238 alerts; 13/60 batch | 60 giao dịch; 300/1,238 alerts; 13/60 batch |
| Navigation | Radio ngang sau KPI/pipeline; sidebar System UIs | Radio trong sidebar; trang đầu Live | Selectbox mục lục; trang đầu báo cáo | Segmented control; mặc định giao dịch |
| Readability | Tổng quan sáu KPI và pipeline trước chi tiết | Throughput lớn; lag/latency và cột giám sát | Kết quả nghiệp vụ, thanh P/R/F1 và cơ cấu | Bảng giao dịch, inspector và ngữ cảnh |
| Desktop UX | 4/4 trang render; KPI nằm phía trên | 4/4 trang render; main/aside tỷ lệ 4:1 | 4/4 trang render; khổ đọc tối đa 1120px | 4/4 trang render; bảng + inspector 4:1 |
| Mobile UX | 4/4 trang render tại 390×844; cần cuộn qua phần đầu | 4/4 trang; mở sidebar để chuyển; các cột xếp dọc | 4/4 trang; mục lục selectbox; nhiều phần đọc dọc | 4/4 trang; bảng có cuộn ngang, inspector/KPI phía dưới |
| Tests passed | 7/7 test gốc dùng chung; AppTest snapshot 4/4; browser 8/8 | 7/7 test gốc dùng chung; AppTest snapshot 4/4; browser 8/8 | 7/7 test gốc dùng chung; AppTest snapshot 4/4; browser 8/8 | 7/7 test gốc dùng chung; AppTest snapshot 4/4; browser 8/8 |
| Trade-offs | Thông tin tổng quan chiếm vùng đầu, bảng ở trang riêng | Ưu tiên vận hành; nhiều vùng cuộn trên điện thoại | Telemetry trong phụ lục, thêm thao tác khi giám sát | KPI ở cuối và bảng nhiều cột trên màn hình nhỏ |

Sáu KPI là sáu thẻ Nguồn đã phát, Spark đã xử lý, Fraud alerts, Ingest hiện tại, Processing throughput và End-to-end latency p95. Lag và alert rate là delta đi kèm. Các số dùng dấu phân cách như giao diện để tiện đối chiếu.

Kết quả browser: **16 trang desktop + 16 trang mobile**, không Streamlit exception hoặc JavaScript pageerror trong các lần kiểm tra. Sáu KPI và delta bằng BEFORE ở **12/12 cặp desktop + 12/12 cặp mobile**. Ảnh `*-mobile.png` do script gốc tạo thêm là bốn trang mặc định; 16 ảnh `*-1-mobile.png` đến `*-4-mobile.png` ghi điều hướng mobile đầy đủ.

## Ảnh tham chiếu trong thực nghiệm này

| UI | Trang đầu desktop theo tác vụ | Mobile tương ứng |
|---|---|---|
| BEFORE | [Control Room](captures/baseline-1-desktop.png) | [Control Room](captures/baseline-1-mobile.png) |
| 9A | [Vận hành](captures/operations-1-desktop.png) | [Vận hành](captures/operations-1-mobile.png) |
| 9B | [Báo cáo](captures/report-1-desktop.png) | [Báo cáo](captures/report-1-mobile.png) |
| 9C | [Giao dịch](captures/studio-4-desktop.png) | [Giao dịch](captures/studio-4-mobile.png) |

Toàn bộ 36 ảnh do script sinh nằm trong [captures/](captures/). Kích thước PNG thực tế là 1600×1600 hoặc 390×844: dù công cụ gọi `full_page=True`, Streamlit cuộn bên trong vùng main nên ảnh vẫn là viewport, không bao trùm nội dung ngoài khung. Nội dung ngoài khung được đối chiếu bằng AppTest/payload và DOM. Studio mặc định mở trang giao dịch; số trang trong tên file theo thứ tự PAGES dùng chung, không theo thứ tự hiển thị của Studio.

## Cách diễn giải

Các giá trị tốc độ/latency là telemetry đã lưu của pipeline, không phải thời gian render UI. End-to-end p95 khoảng 8,27 giờ xuất hiện ở batch sau khi xử lý dữ liệu tồn đọng; đây không phải benchmark steady-state. Snapshot còn lag 200 nên không tuyên bố đã xử lý hết nguồn.

Ưu thế bố cục là phân tích từ code và ảnh, chưa có đo thời gian hoàn thành tác vụ với người dùng. Không kết luận dashboard nhanh hơn, pipeline nhanh hơn hoặc model tốt hơn khi đổi view. [Phân tích 15 marker](dashboard-analysis.md), [audit dữ liệu thật](snapshot-audit.json), [browser](browser-results.json), [đối chiếu KPI](browser-equivalence.json).
