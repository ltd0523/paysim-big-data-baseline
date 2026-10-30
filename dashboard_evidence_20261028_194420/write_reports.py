"""Build Vietnamese reports from measured evidence; fail if validation is missing."""
import hashlib
import json
from pathlib import Path
import re
from datetime import timezone

from bson import json_util

OUT = Path('/evidence')
audit = json.loads((OUT/'snapshot-audit.json').read_text())
snap = json_util.loads((OUT/'snapshot.json').read_text())
desktop = json.loads((OUT/'captures/browser-results.json').read_text())
mobile = json.loads((OUT/'mobile-results.json').read_text())
assert len(desktop) == len(mobile) == 16
assert all(not r['browser_errors'] for r in desktop + mobile)
assert all(r['streamlit_exceptions'] == 0 for r in mobile)
c = audit['canonical']
labels = ['Nguồn đã phát', 'Spark đã xử lý', 'Fraud alerts', 'Ingest hiện tại',
          'Processing throughput', 'End-to-end latency p95']


def clean(value):
    return ' '.join(value.replace('arrow_upward', '').replace('arrow_downward', '').split())


def desktop_metrics(row):
    return sorted(clean(text) for text in row['metrics'] if any(text.strip().startswith(label) for label in labels))


equivalence = []
combined = []
for r in desktop:
    baseline = next(b for b in desktop if b['view'] == 'baseline' and b['page'] == r['page'])
    assert desktop_metrics(r) == desktop_metrics(baseline), (r['view'], r['page'])
    combined.append({**r, 'device': 'desktop', 'viewport': {'width':1600, 'height':1600},
                     'screenshot': 'captures/'+r['screenshot'], 'six_kpis_equal_before': True,
                     'streamlit_exceptions': 0,
                     'exception_check': 'asserted by unmodified tests/capture_dashboard.py'})
    if r['view'] != 'baseline':
        equivalence.append({'view': r['view'], 'page': r['page'], 'device': 'desktop',
                            'six_kpis_and_deltas_equal_before': True})
for r in mobile:
    expected = next(p for p in audit['pages'] if p['view'] == r['view'] and p['page'] == r['page'])['metrics']
    observed = sorted((m['label'], m['value'], clean(m['delta'])) for m in r['metrics'])
    assert observed == sorted((label, value, clean(delta)) for label, value, delta in expected), (r['view'], r['page'], observed, expected)
    combined.append({**r, 'device': 'mobile', 'six_kpis_equal_before': True})
    if r['view'] != 'baseline':
        equivalence.append({'view': r['view'], 'page': r['page'], 'device': 'mobile',
                            'six_kpis_and_deltas_equal_before': True})
(OUT/'browser-results.json').write_text(json.dumps(combined, ensure_ascii=False, indent=2), encoding='utf-8')
(OUT/'browser-equivalence.json').write_text(json.dumps(equivalence, ensure_ascii=False, indent=2), encoding='utf-8')

rid = snap['run_id']
db = snap['database']
timestamp = snap['captured_at'].replace(tzinfo=timezone.utc).isoformat()
pct = lambda value: f'{value*100:.2f}%'
fraud = f"Model P/R/F1: {pct(c['model']['Precision'])} / {pct(c['model']['Recall'])} / {pct(c['model']['F1'])}"
rule = f"Rule P/R/F1: {pct(c['rule']['Precision'])} / {pct(c['rule']['Recall'])} / {pct(c['rule']['F1'])}"
common = [
    ('Run ID', [rid]*4),
    ('Nguồn đã phát', [f"{c['emitted']:,}"]*4),
    ('Spark đã xử lý / lag', [f"{c['processed']:,} / {c['lag']:,}"]*4),
    ('Fraud alerts / alert rate', [f"{c['alerts']:,} / {pct(c['model']['Alert rate'])}"]*4),
    ('Ingest hiện tại', [f"{c['ingest_events_per_second']:,.1f} ev/s"]*4),
    ('Processing throughput', [f"{c['processing_events_per_second']:,.1f} ev/s"]*4),
    ('End-to-end latency p95', [f"{c['latency_p95_ms']:,.0f} ms"]*4),
    ('Fraud metrics — model', [fraud]*4),
    ('Fraud metrics — rule', [rule]*4),
    ('Confusion matrix — model TP/FP/TN/FN', ['52 / 1,186 / 4,962 / 0']*4),
    ('Confusion matrix — rule TP/FP/TN/FN', ['8 / 64 / 6,084 / 44']*4),
    ('Dữ liệu UI', ['60 giao dịch; 300/1,238 alerts; 13/60 batch']*4),
    ('Navigation', ['Radio ngang sau KPI/pipeline; sidebar System UIs',
                    'Radio trong sidebar; trang đầu Live',
                    'Selectbox mục lục; trang đầu báo cáo',
                    'Segmented control; mặc định giao dịch']),
    ('Readability', ['Tổng quan sáu KPI và pipeline trước chi tiết',
                     'Throughput lớn; lag/latency và cột giám sát',
                     'Kết quả nghiệp vụ, thanh P/R/F1 và cơ cấu',
                     'Bảng giao dịch, inspector và ngữ cảnh']),
    ('Desktop UX', ['4/4 trang render; KPI nằm phía trên',
                    '4/4 trang render; main/aside tỷ lệ 4:1',
                    '4/4 trang render; khổ đọc tối đa 1120px',
                    '4/4 trang render; bảng + inspector 4:1']),
    ('Mobile UX', ['4/4 trang render tại 390×844; cần cuộn qua phần đầu',
                   '4/4 trang; mở sidebar để chuyển; các cột xếp dọc',
                   '4/4 trang; mục lục selectbox; nhiều phần đọc dọc',
                   '4/4 trang; bảng có cuộn ngang, inspector/KPI phía dưới']),
    ('Tests passed', ['7/7 test gốc dùng chung; AppTest snapshot 4/4; browser 8/8']*4),
    ('Trade-offs', ['Thông tin tổng quan chiếm vùng đầu, bảng ở trang riêng',
                    'Ưu tiên vận hành; nhiều vùng cuộn trên điện thoại',
                    'Telemetry trong phụ lục, thêm thao tác khi giám sát',
                    'KPI ở cuối và bảng nhiều cột trên màn hình nhỏ']),
]
table = '| Tiêu chí | BEFORE 9 | AFTER 9A | AFTER 9B | AFTER 9C |\n|---|---|---|---|---|\n'
table += '\n'.join('| '+title+' | '+' | '.join(values)+' |' for title, values in common)
comparison = f'''# Track 9 — So sánh dashboard trên cùng snapshot

Ngày thực nghiệm: 28/10/2026, múi giờ Asia/Saigon. Snapshot lúc `{timestamp}` (19:45:54 giờ Việt Nam).
Database duy nhất: `{db}`. Commit: `437462e4e2c149c427e23d36ff42002400a1ee52`, nhánh `main`.

{table}

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
'''
(OUT/'dashboard-comparison.md').write_text(comparison, encoding='utf-8')

analysis = '''# Track 9 — Phân tích đầy đủ 15 thay đổi đã định nghĩa

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
'''
(OUT/'dashboard-analysis.md').write_text(analysis, encoding='utf-8')

summary = f'''# Track 9 — Biên bản thực thi 28/10/2026

## Môi trường và phạm vi

Workspace `D:\\BigData_PJ\\paysim-big-data-baseline`, branch `main`, commit `437462e4e2c149c427e23d36ff42002400a1ee52`. Git sạch khi bắt đầu. Host Windows PowerShell, Python 3.14.6; không dùng host Python để ép các dependency cũ. Kiểm thử trong container Linux/WSL2 độc lập `paysim-track9-20261028-194420`, Python 3.11.18, virtualenv `/tmp/track9-venv` dùng system-site-packages của image Streamlit. Source mount read-only, chỉ evidence mount được ghi.

Streamlit 1.50.0, PyMongo 4.10.1, pandas 2.2.3, Altair 5.5.0, pytest 9.1.1, mongomock 4.3.0, Playwright 1.64.1. MongoDB 8.0.29. Chi tiết: [environment.json](environment.json), [dependency freeze](test-environment-freeze.txt), [Docker](docker-version.json).

## Các phase thực hiện

1. Đọc đầy đủ hai hướng dẫn, app/core/ba view và ba script test/snapshot/capture bắt buộc. Kiểm tra git, Docker, Python, run/telemetry, health MongoDB và Streamlit. Ban đầu toàn bộ container đều dừng. Docker API cần quyền ngoài sandbox; đã sử dụng quyền được cấp.
2. Khởi động MongoDB/Streamlit để đọc dữ liệu lưu trong volumes. Lệnh `docker compose start mongodb streamlit` tự bật dependency Kafka/HDFS và Spark ngoài dự định; đã ngắt lệnh, dừng Spark/replayer và trả Kafka/HDFS về dừng. Spark hoàn thành batch 198: input/valid=500, alerts=94, duration khoảng 12,45s lúc 12:43:17 UTC; lần dừng tạo lỗi ở batch kế tiếp trước đoạn xử lý/ghi dữ liệu. Log `spark-observation.txt` được giữ nguyên; không gọi đây là lượt pipeline end-to-end thành công. Kiểm tra trạng thái và hash bảy collection ổn định trước/sau snapshot để xác nhận dữ liệu serving nhất quán sau lần dừng.
3. Chạy nguyên `tests/snapshot_dashboard.py` với URI nội bộ, database evidence mới `{db}`, output `snapshot.json`. Script từ chối DB có sẵn. Snapshot lúc `{timestamp}`, run `{rid}`; aggregate tổng bằng evaluation processed và telemetry processed_total; alerts=TP+FP; evaluation revision không đổi. Wrapper còn đối chiếu toàn bộ hash của bảy collection nguồn trước/sau copy. Không ghi nguồn và không ghi đè evidence cũ.
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

{fraud}. {rule}. Nguồn phát {c['emitted']:,}, xử lý {c['processed']:,}, lag {c['lag']:,}, alerts {c['alerts']:,}, alert rate {pct(c['model']['Alert rate'])}; ingest {c['ingest_events_per_second']:.1f} ev/s, processing {c['processing_events_per_second']:.1f} ev/s, end-to-end p95 {c['latency_p95_ms']:,.0f} ms. Precision thấp cùng recall cao của model là kết quả thật của snapshot; không sửa threshold hoặc ground truth.

## Sự cố kiểm thử và khả năng tái lập

Audit lần đầu thất bại vì timezone dtype `FixedOffset(0)` của BSON khác kiểu UTC của Arrow; đã chuẩn hóa thời điểm UTC trong expected table, vẫn so toàn bộ dữ liệu. Lần hai phát hiện app.py được đổi sang BEFORE từ bên ngoài; ghi riêng routing và bắt buộc các file còn lại giữ nguyên. Lần cuối audit đạt. Giữ các log `snapshot-audit-first-attempt.txt` và `snapshot-audit-second-attempt.txt`. Lệnh compileall thử ghi bytecode vào source read-only nên bị từ chối; thay bằng AST parse trong bộ nhớ, năm module hợp lệ. Các sự cố này không phải Streamlit exception trong UI.

Script audit payload có hai lỗi harness ban đầu: tên hàm giải mã Arrow phải là convert_arrow_bytes_to_pandas_df trong Streamlit 1.50, và AppTest cần đặt rõ giá trị segmented control trước khi thao tác selectbox Studio. Đã sửa script riêng trong evidence, lưu log hai lần đầu; không sửa view hoặc logic nghiệp vụ. Kiểm tra cuối xác nhận đủ 300 alert payloads, matrix bốn ô và thao tác chọn đầu/cuối.

Mobile capture bổ sung có hai lần lỗi công cụ: nút đóng sidebar vẫn được Playwright xem là visible khi đã nằm ngoài viewport, và vòng đọc từng locator KPI gặp fragment refresh xóa phần tử giữa hai lệnh. Đã kiểm tra bounding box thật của nút và đọc metric DOM nguyên tử trong một browser task; giữ refresh 2 giây. Lưu hai log mobile-capture-first-attempt.txt và mobile-capture-second-attempt.txt. Chạy tiếp các view còn thiếu, kết quả cuối đủ 16 trang mobile; không sửa ứng dụng để né lỗi công cụ.

Lựa chọn source app.py cuối phiên là BEFORE, do thay đổi bên ngoài được giữ lại; image Docker sẵn có vẫn là Operations và không tự nhận lựa chọn này khi chưa rebuild. Hash core và ba view trong image trùng source; xem runtime-dashboard-sha256.json. Capture dùng source và từng module view riêng, độc lập lựa chọn Docker live.

Trạng thái bàn giao: MongoDB/Streamlit/Spark/Kafka/NameNode healthy, replayer và DataNode đang chạy theo services-final.json. Stack đã khởi động lại sau khi lấy snapshot, khoảng 19:58 giờ Việt Nam, trong lúc cài browser/kiểm thử; replayer và Streamlit có container ID mới. Không truy nguyên tác nhân khởi động lại từ các quan sát này. Database nguồn paysim do đó tiếp tục thay đổi. Kiểm tra cuối ban đầu thất bại vì điều kiện phụ quá chặt “nguồn vẫn không đổi suốt capture”; điều kiện đúng cho so sánh là database evidence riêng phải giữ nguyên. Ghi nguyên fingerprint thay đổi của nguồn và bắt buộc cả bảy collection evidence vẫn khớp JSON; không nới điều kiện trên dữ liệu dùng so sánh.

Dashboard Docker ở http://127.0.0.1:8501 dùng image Operations hiện có và database live paysim, không phải DB evidence. Ảnh browser được chụp qua entrypoint tạm trên DB evidence ở cổng 8510 trong container kiểm thử, không lấy từ cổng demo live. Container kiểm thử riêng và database evidence mới được giữ để tái lập; xem services-final.json, post-capture-database-checks.json và final-verification.json. Không dừng lại stack live vừa được khởi động lại.

Snapshot không phải transaction MongoDB đa collection. Trong lần này writers đã dừng và fingerprint nguồn ổn định; không chỉ dựa vào một lần đọc evaluation. Database evidence và snapshot JSON được giữ lại để demo/tái lập. Muốn chạy lại capture, dùng môi trường đúng dependency, đặt `MONGO_DATABASE={db}` và URI MongoDB truy cập được rồi chạy script có sẵn. URI từ host là `mongodb://127.0.0.1:27017`, từ mạng Docker là `mongodb://mongodb:27017`.

## Giới hạn và kết luận

Không train lại hoặc kiểm thử pipeline end-to-end mới; dữ liệu là run thật đã lưu và một batch phục hồi trước snapshot. Không bảo đảm run drain (còn lag 200). Latency ~8,27 giờ phản ánh backlog sau dừng lâu, không phải thời gian render dashboard. Không đo response time, FPS, tài nguyên UI hoặc thời gian người dùng hoàn thành tác vụ. Không kết luận AFTER nhanh hơn hoặc phát hiện fraud tốt hơn. Freshness và query latency phụ thuộc lúc mở UI, loại khỏi so sánh KPI tuyệt đối. Không đánh giá toàn bộ browser/device; mobile là viewport Chromium, không phải thiết bị vật lý. Ảnh 1600×1600 và 390×844 chỉ ghi viewport vì Streamlit cuộn trong vùng main; nội dung dài kiểm tra bằng AppTest/DOM/payload, không giả định full_page=True đã chụp hết.

Kết quả phù hợp đưa vào Capstone như bằng chứng đổi cách trình bày giữ nguyên dữ liệu và số liệu. Operations phục vụ giám sát, Report phục vụ báo cáo, Studio phục vụ tra cứu giao dịch; BEFORE giữ vai trò tổng quan. [Bảng so sánh](dashboard-comparison.md) và [phân tích đủ 15 thay đổi](dashboard-analysis.md) nêu mục đích, lợi ích và đánh đổi từng phương án.
'''
(OUT/'execution-summary.md').write_text(summary, encoding='utf-8')
print('PASS: 24/24 browser KPI comparisons; wrote all three Vietnamese reports and combined browser results')
