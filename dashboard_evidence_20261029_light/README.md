# PaySim 9A — Light Enterprise

Ngày thực hiện: 29/10/2026. Giữ bố cục, nội dung và các chỉnh sửa trước đó; đổi bảng màu theo đặc tả mới, thay điều hướng bằng option menu dọc và Material Icons.

## Thay đổi giao diện

| Thành phần | Trước | Sau |
|---|---|---|
| Shell và sidebar | Nền tối | Page `#F5F7FB`, sidebar `#EDF2F8`, card trắng, chữ `#0F172A`, viền `#DCE5EF` |
| Điều hướng | Radio được tạo kiểu menu, chữ 13px, emoji | Option menu bằng `st.pills` native, chữ 16px, Material Icons; sidebar 260px |
| Mục đang chọn | Nền tối, chữ cyan | Nền xanh nhạt, chữ xanh `#2563EB`; giữ việc bỏ vạch nhấn bên trái theo yêu cầu trước đó |
| Biểu đồ Live | Canvas tối, series màu sáng | Canvas trắng; Ingest xanh, Processing teal, lag amber, ingest p95 tím, end-to-end p95 cam |
| Biểu tượng `?` | Nét trắng trên card tối | Giữ nét trắng, thêm nền tròn xanh để đọc được trên card trắng; tooltip vẫn hoạt động |
| Liên kết hệ thống | Ký tự mũi tên | Material Icons `storage` và `open_in_new`; đích HDFS/Spark giữ nguyên |

Menu dùng widget Streamlit có sẵn, không thêm package hoặc tải font ngoài. Các icon menu là `sensors`, `analytics`, `shield`, `receipt_long`. `PAGES` và key `dashboard_page` giữ nguyên; `format_func` chỉ đổi phần hiển thị. Click lại mục đang chọn vẫn giữ trang hiện tại. Test điều hướng được cập nhật theo widget mới, các phép đối chiếu KPI giữ nguyên.

Giữ nguyên: ba KPI phía trên; hai KPI Fraud alerts/Alert rate ngang hàng và cùng cỡ chữ; caption đã bỏ; tên metric kỹ thuật đã ẩn; CSV native; góc bo 15px của các biểu đồ Fraud/Business và tổng hợp transaction type; tên/nhãn nội dung; khoảng cách và bố cục workspace/history. Các yêu cầu này được ưu tiên khi khác với đề xuất bố cục/vạch nhấn trong bản đặc tả.

## Ảnh trước và sau

| Viewport | Trước | Sau |
|---|---|---|
| 1366×768 | [Live](before/1-1366x768.png) | [Live](after/1-1366x768.png) |
| 1440×900 | [Live](before/1-1440x900.png) | [Live](after/1-1440x900.png) |
| 1600×900 | [Live](before/1-1600x900.png) | [Live](after/1-1600x900.png) |
| 390×844 | [Live](before/1-390x844.png) | [Live](after/1-390x844.png) |

Trong `before/` và `after/`, tiền tố `1` là Live, `2` là 10 Tracks, `3` là Fraud & Business, `4` là Dòng dữ liệu mới. `details-*` chụp vùng cuối trang; `sidebar-390x844.png` chụp menu mở trên mobile. Streamlit cuộn trong vùng main, nên mỗi ảnh là một viewport tại vị trí cuộn cụ thể.

## Kiểm chứng

- [Unit/AppTest: 7 passed](test-results.txt), đối chiếu sáu KPI canonical trên bốn trang và trạng thái database rỗng.
- [Data audit](data-audit.json): so trước/sau bảy KPI (sáu KPI canonical và Alert rate), mọi giá trị bảng, mọi dataset biểu đồ. Chỉ palette/config hình thức của chart Live thay đổi; cấu trúc và dữ liệu chart chuyên sâu giữ nguyên. Kiểm tra menu không mất lựa chọn khi deselect.
- [Browser trước](before/results.json), [browser sau](after/results.json): 4 trang × 4 viewport ở mỗi lượt, không pageerror/Streamlit exception, không KPI tràn và không tràn ngang toàn trang. Xác nhận Material Icons, chữ menu 16px, đúng mục đang chọn, màu nền sáng, `?` trắng và tooltip, biểu đồ bo góc.
- Sáu CSV tải qua thao tác chuột trên toolbar native ở desktop/mobile: 13 micro-batch, 2 detector, 60 giao dịch; giữ đầy đủ cột. Các CSV nằm trong `after/`. Headless Chromium dùng Blob fallback được Streamlit hỗ trợ để thay hộp thoại lưu của hệ điều hành.
- [Fingerprint trước](before/database-fingerprints.json), [fingerprint sau](after/database-fingerprints.json): database evidence không thay đổi. Các collection khớp hoàn toàn snapshot gốc `dashboard_evidence_20261028_194420/snapshot.json`.

Dùng lại database `paysim_ui_evidence_20261028_194420`, run `run-20261028-042515`, trạng thái `stopped`: nguồn phát 6,400; Spark xử lý 6,200; lag 200; alerts 1,238; alert rate 19.97%; Ingest 50.0 ev/s; Processing 40.2 ev/s; end-to-end p95 29,763,813 ms. Audit xác nhận 300 alerts mới nhất, 60 giao dịch và 13 batch hiện có. Đây là snapshot lịch sử, không phải số liệu live hiện tại.

Đối chiếu phạm vi theo `docs/05_Huong_Dan_Cai_Tien_Dashboard.md`: không sửa core, query, scoring, formatters, model, Spark/Kafka/HDFS, schema, các giới hạn bản ghi hoặc refresh 2 giây. Mã ứng dụng chỉ sửa `dashboard/view_operations.py`; `tests/test_dashboard.py` đổi cách chọn menu khi kiểm thử. Giữ đủ năm nhóm marker BEFORE/AFTER 9A. Không commit, stage hoặc push.

## Giới hạn

Phân cấp màu sáng giúp tách nền, nội dung và series theo cùng palette; đây là nhận xét thiết kế, chưa đo thời gian thao tác, hiệu năng hoặc chứng nhận accessibility. Bố cục Spacious giữ nguyên nên cần cuộn để xem history, đặc biệt trên mobile.

Canvas native của bảng và các biểu đồ core vẫn kế thừa theme Streamlit. Bộ ảnh và browser checks dùng native theme `light`; không sửa core/config ngoài phạm vi để ép theme khi người dùng chủ động chọn Dark. CSS phụ thuộc `data-testid` và DOM của Streamlit 1.50.0; cần kiểm tra lại khi nâng phiên bản.

Môi trường: container kiểm thử độc lập có sẵn, Python 3.11, Streamlit 1.50.0, Altair 5.5.0, Chromium/Playwright. Chỉ đọc snapshot. Build/cập nhật riêng service `streamlit`; không khởi động lại pipeline. Container kiểm thử được dừng sau khi bàn giao.
