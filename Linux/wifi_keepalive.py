import time
import subprocess
from playwright.sync_api import sync_playwright
import requests

SSID_NAME = "INET - Free WiFi"
GATEWAY_LOGIN = "http://192.168.200.1/login"
CHECK_INTERVAL = 0.5  # Kiểm tra kết nối mỗi 30 giây

def log(msg):
    ts = time.strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{ts}] {msg}")

def ensure_wifi_connected():
    try:
        # Kiểm tra xem Wi-Fi đã kết nối đúng SSID chưa
        res = subprocess.run(
            ["nmcli", "-t", "-f", "ACTIVE,SSID", "dev", "wifi"],
            capture_output=True, text=True, timeout=10
        )
        if f"yes:{SSID_NAME}" in res.stdout:
            return True
            
        log(f"WiFi chưa kết nối. Đang kết nối lại {SSID_NAME}...")
        subprocess.run(
            ["nmcli", "dev", "wifi", "connect", SSID_NAME],
            capture_output=True, text=True, timeout=15
        )
        time.sleep(5)
        
        res = subprocess.run(
            ["nmcli", "-t", "-f", "ACTIVE,SSID", "dev", "wifi"],
            capture_output=True, text=True, timeout=10
        )
        return f"yes:{SSID_NAME}" in res.stdout
    except Exception as e:
        log(f"Lỗi WiFi check: {e}")
        return False

def check_internet():
    try:
        r = requests.get("http://connectivitycheck.gstatic.com/generate_204", timeout=4, allow_redirects=False)
        return r.status_code == 204
    except:
        return False

def do_login_playwright():
    log("Đang mở trình duyệt (Playwright) để đăng nhập tự động vượt anti-bot...")
    success = False
    with sync_playwright() as p:
        browser = p.chromium.launch(
            headless=True,
            args=[
                "--no-sandbox",
                "--disable-setuid-sandbox",
                "--disable-dev-shm-usage",
                "--disable-blink-features=AutomationControlled",
            ]
        )
        context = browser.new_context(
            user_agent="Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
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
            page.goto(GATEWAY_LOGIN, wait_until="domcontentloaded", timeout=10000)
            
            # Simulate real user mouse activity
            page.mouse.move(100, 100)
            time.sleep(0.3)
            page.mouse.move(500, 300)
            time.sleep(0.3)
            page.mouse.click(600, 400)

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
            log(f"Lỗi trong quá trình Playwright action: {e}")
        finally:
            browser.close()

    time.sleep(2)
    return success or check_internet()

def main():
    print("=" * 60)
    print("   INET - Free WiFi Auto Keep-Alive (Linux Smart Monitor)")
    print("=" * 60)
    log("[*] Khởi động script thành công. Theo dõi trạng thái Internet liên tục...")

    while True:
        try:
            if not ensure_wifi_connected():
                log("Đang chờ kết nối WiFi...")
                time.sleep(10)
                continue

            # Chỉ kiểm tra xem có internet hay không
            if check_internet():
                # log("Internet OK. Kết nối ổn định.")
                continue
            else:
                log("[!] Phát hiện mất internet hoặc hết hạn session (15 phút). Đang đăng nhập lại...")
                if do_login_playwright():
                    log("[✓] Đăng nhập khôi phục kết nối thành công!")
                else:
                    log("[✗] Đăng nhập thất bại. Thử lại sau 10 giây...")
                    time.sleep(10)
                    continue

            time.sleep(CHECK_INTERVAL)

        except KeyboardInterrupt:
            log("Dừng script.")
            break
        except Exception as e:
            log(f"Lỗi không mong đợi: {e}")
            time.sleep(10)

if __name__ == "__main__":
    main()