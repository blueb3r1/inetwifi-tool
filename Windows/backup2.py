import time
import subprocess
from playwright.sync_api import sync_playwright
import requests

SSID_NAME = "INET - Free WiFi"
GATEWAY_LOGIN = "http://192.168.200.1/login"
GATEWAY_LOGOUT = "http://192.168.200.1/logout"
REAUTH_INTERVAL = 13 * 60  # Gia hạn chủ động trước 2 phút (mốc 13 phút)
CHECK_INTERVAL = 15         # Kiểm tra mỗi 15 giây để phản ứng cực nhanh

def log(msg):
    ts = time.strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{ts}] {msg}")

def ensure_wifi_connected():
    try:
        res = subprocess.run(["netsh", "wlan", "show", "interfaces"], capture_output=True, text=True, timeout=10)
        if "connected" in res.stdout and SSID_NAME in res.stdout:
            return True
        log(f"WiFi chưa kết nối. Đang kết nối lại {SSID_NAME}...")
        subprocess.run(["netsh", "wlan", "connect", f"name={SSID_NAME}"], capture_output=True, text=True, timeout=10)
        time.sleep(5)
        res = subprocess.run(["netsh", "wlan", "show", "interfaces"], capture_output=True, text=True, timeout=10)
        return "connected" in res.stdout and SSID_NAME in res.stdout
    except Exception as e:
        log(f"Lỗi WiFi check: {e}")
        return False

def check_internet():
    try:
        r = requests.get("http://connectivitycheck.gstatic.com/generate_204", timeout=3, allow_redirects=False)
        return r.status_code == 204
    except:
        return False

def do_login_playwright():
    log("Đang mở trình duyệt ngầm (Playwright) để gia hạn/đăng nhập tự động...")
    success = False
    with sync_playwright() as p:
        browser = p.chromium.launch(
            channel="chrome",
            headless=True,
            args=[
                "--no-sandbox",
                "--disable-blink-features=AutomationControlled",
            ]
        )
        context = browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            viewport={"width": 1920, "height": 1080},
            locale="vi-VN",
            screen={"width": 1920, "height": 1080},
        )
        context.add_init_script("""
            Object.defineProperty(navigator, 'webdriver', { get: () => false });
            Object.defineProperty(navigator, 'languages', { get: () => ['vi-VN','vi','en-US','en'] });
            Object.defineProperty(navigator, 'plugins', { get: () => [1,2,3,4,5] });
            window.chrome = { runtime: {} };
        """)

        page = context.new_page()

        def on_req(req):
            nonlocal success
            if "192.168.200.1/login" in req.url and req.method == "POST":
                success = True
                log(f"[✓] Đã gửi request đăng nhập thành công: {req.post_data}")

        page.on("request", on_req)

        try:
            # Truy cập captive portal để kích hoạt đăng nhập
            page.goto(GATEWAY_LOGIN, wait_until="domcontentloaded", timeout=12000)
            
            # Giả lập thao tác chuột
            page.mouse.move(100, 100)
            time.sleep(0.3)
            page.mouse.move(500, 300)
            time.sleep(0.3)
            page.mouse.click(600, 400)

            # Chờ submit hoàn tất
            for _ in range(15):
                time.sleep(1)
                if success:
                    break
                try:
                    btn = page.query_selector("#connectToInternet, #btnContinue, .connect-button")
                    if btn and btn.is_visible():
                        btn.click()
                except:
                    pass
        except Exception as e:
            log(f"Thông báo Playwright: {e}")
        finally:
            browser.close()

    time.sleep(2)
    return success or check_internet()

def main():
    print("=" * 60)
    print("   INET - Free WiFi Auto Keep-Alive (Zero Disconnect)")
    print("=" * 60)

    # Đăng nhập ngay khi bật script để đồng bộ mốc thời gian 15 phút từ đầu
    log("[*] Khởi động script. Đang thực hiện đăng nhập để đồng bộ mốc 15 phút...")
    if do_login_playwright():
        last_login_time = time.time()
        log("[✓] Đã đồng bộ mốc thời gian thành công!")
    else:
        last_login_time = time.time()
        log("[!] Chưa đăng nhập được, tiếp tục theo dõi...")

    while True:
        try:
            if not ensure_wifi_connected():
                log("Đang chờ kết nối WiFi...")
                time.sleep(5)
                continue

            has_net = check_internet()
            elapsed = time.time() - last_login_time

            # 1. Nếu mất mạng đột ngột (do router reset hoặc rớt sóng): Đăng nhập ngay lập tức
            if not has_net:
                log("[!] Phát hiện mất kết nối. Đang phục hồi ngay lập tức...")
                if do_login_playwright():
                    last_login_time = time.time()
                    log("[✓] Khôi phục mạng thành công!")
                else:
                    log("[✗] Đăng nhập thất bại. Thử lại sau 5 giây...")
                    time.sleep(5)
                    continue

            # 2. Hoặc nếu đã đến mốc 13 phút: Chủ động gia hạn TRƯỚC KHI bị rớt mạng
            elif elapsed >= REAUTH_INTERVAL:
                log("[*] Đã qua 13 phút. Đang chủ động làm mới session để tránh ngắt quãng...")
                if do_login_playwright():
                    last_login_time = time.time()
                    log("[✓] Làm mới session thành công, mạng liên tục!")
                else:
                    log("[!] Thử gia hạn chưa thành công, sẽ tiếp tục theo dõi...")

            else:
                remaining = int(REAUTH_INTERVAL - elapsed)
                log(f"Internet OK. Lần gia hạn chủ động tiếp theo sau {remaining//60}m{remaining%60}s.")

            time.sleep(CHECK_INTERVAL)

        except KeyboardInterrupt:
            log("Dừng script.")
            break
        except Exception as e:
            log(f"Lỗi không mong đợi: {e}")
            time.sleep(5)

if __name__ == "__main__":
    main()