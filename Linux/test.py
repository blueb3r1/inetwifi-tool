import time
import subprocess
from playwright.sync_api import sync_playwright
import requests

SSID_NAME = "INET - Free WiFi"
GATEWAY_LOGIN = "http://192.168.200.1/login"
REAUTH_INTERVAL = 14 * 60  # 14 phút
CHECK_INTERVAL = 30         # 30 giây kiểm tra

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
        r = requests.get("http://connectivitycheck.gstatic.com/generate_204", timeout=5, allow_redirects=False)
        return r.status_code == 204
    except:
        return False

def do_login_playwright():
    log("Đang mở trình duyệt (Playwright) để đăng nhập tự động vượt anti-bot...")
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
        # Fake webdriver & languages to pass router's anti-bot check
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
            page.goto(GATEWAY_LOGIN, wait_until="domcontentloaded", timeout=15000)
            
            # Simulate real user mouse activity
            page.mouse.move(100, 100)
            time.sleep(0.3)
            page.mouse.move(500, 300)
            time.sleep(0.3)
            page.mouse.click(600, 400)

            # Wait for form submit / click connect button if needed
            for _ in range(40):
                time.sleep(1)
                if success:
                    break
                try:
                    btn = page.query_selector("#connectToInternet")
                    if btn and btn.is_visible():
                        btn.click()
                except:
                    pass
        except Exception as e:
            log(f"Lỗi trong quá trình Playwright login: {e}")
        finally:
            browser.close()

    time.sleep(3)
    return success and check_internet()

def main():
    print("=" * 60)
    print("   INET - Free WiFi Auto Keep-Alive (Playwright Anti-Bot)")
    print("=" * 60)

    last_login_time = 0

    while True:
        try:
            if not ensure_wifi_connected():
                log("Đang chờ kết nối WiFi...")
                time.sleep(10)
                continue

            now = time.time()
            elapsed = now - last_login_time
            has_net = check_internet()

            if not has_net or elapsed >= REAUTH_INTERVAL:
                if not has_net:
                    log("[!] Mất internet hoặc session hết hạn. Đang đăng nhập lại...")
                else:
                    log(f"[*] Đã qua {int(elapsed//60)} phút. Tiến hành gia hạn session...")

                if do_login_playwright():
                    last_login_time = time.time()
                    log("[✓] Gia hạn session thành công!")
                else:
                    log("[✗] Đăng nhập thất bại. Thử lại sau 15 giây...")
                    time.sleep(15)
                    continue
            else:
                remaining = int(REAUTH_INTERVAL - elapsed)
                log(f"Internet OK. Lần gia hạn tiếp theo sau {remaining//60}m{remaining%60}s.")

            time.sleep(CHECK_INTERVAL)

        except KeyboardInterrupt:
            log("Đã dừng script.")
            break
        except Exception as e:
            log(f"Lỗi không mong đợi: {e}")
            time.sleep(10)

if __name__ == "__main__":
    main()
