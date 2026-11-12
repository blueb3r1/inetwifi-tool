# inetwifi-tool

Script Python thử tự động kết nối lại mạng INET - Free WiFi tại Ký túc xá khu A, ĐHQG-HCM. Repo cũng có các file HTML/JavaScript đã lưu để phân tích trang captive portal.

Khi chưa có Internet hoặc phiên đăng nhập hết hạn, script mở trang đăng nhập của gateway bằng Playwright, mô phỏng một số thao tác chuột và thử bấm nút kết nối. Cổng có JavaScript kiểm tra một số dấu hiệu automation; cách này chỉ là thử tự động hóa luồng đăng nhập, không đảm bảo luôn vượt qua được kiểm tra hoặc đăng nhập thành công.

Script dùng `requests` để kiểm tra Internet qua endpoint trả mã HTTP 204. `requests` không được dùng để lấy password hay tự gửi thông tin đăng nhập. Playwright theo dõi xem có request POST tới gateway hay không, nhưng việc phát hiện POST không đảm bảo gateway đã chấp nhận đăng nhập; cần kiểm tra Internet thực tế.

Thời hạn phiên khoảng 15 phút là quan sát được ghi nhận khi sử dụng, không phải giá trị được xác minh bởi script. Việc mất kết nối trong bao lâu còn tùy trạng thái mạng và captive portal.

## Yêu cầu

- Python 3
- Các thư viện Python `requests` và `playwright`
- Linux: Chromium do Playwright quản lý
- Windows: Google Chrome đã cài đặt (script dùng Playwright với `channel="chrome"`)

Cài thư viện Python:

```bash
python -m pip install requests playwright
```

Trên Linux, cài Chromium cho Playwright:

```bash
python3 -m playwright install chromium
```

## Chạy

Chạy các lệnh từ thư mục gốc của repo.

### Linux

```bash
python3 Linux/wifi_keepalive.py
```

Script kiểm tra SSID bằng `nmcli`; máy cần có NetworkManager và quyền kết nối Wi-Fi phù hợp.

### Windows

```powershell
python Windows/wifi_keepalive.py
```

Script kiểm tra và kết nối Wi-Fi bằng `netsh wlan`; Windows cần có cấu hình Wi-Fi cho SSID này.

## Lưu ý về hành vi hiện tại

- Windows chờ 30 giây sau mỗi lần kiểm tra/khôi phục.
- Linux khai báo khoảng chờ 0,5 giây, nhưng khi Internet đang hoạt động, vòng lặp tiếp tục ngay mà không chờ. Vì vậy script hiện kiểm tra liên tục trong trạng thái mạng ổn định.
- Ý tưởng dùng đồng thời hai card Wi-Fi để chuyển đổi kết nối mới chỉ là thử nghiệm/dự định. Script hiện tại không quản lý hai card hoặc điều chỉnh độ ưu tiên kết nối.
