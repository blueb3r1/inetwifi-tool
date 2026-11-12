import time
from playwright.sync_api import sync_playwright

GATEWAY_LOGIN = "http://192.168.200.1/login"

def log(msg):
    ts = time.strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{ts}] {msg}")

def test_login():
    log("Starting Playwright Chrome (bypass anti-bot)...")
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

        login_posted = False
        login_payload = None

        def on_req(req):
            nonlocal login_posted, login_payload
            if "192.168.200.1/login" in req.url and req.method == "POST":
                login_payload = req.post_data
                login_posted = True
                log(f"[LOGIN POST] {req.post_data}")

        page.on("request", on_req)

        log(f"Navigating to {GATEWAY_LOGIN}...")
        page.goto(GATEWAY_LOGIN, wait_until="domcontentloaded", timeout=10000)

        # Simulate real user mouse interaction
        log("Simulating mouse activity...")
        page.mouse.move(100, 100)
        time.sleep(0.2)
        page.mouse.move(500, 300)
        time.sleep(0.2)
        page.mouse.click(600, 400)

        # Wait for anti-bot + Awing state machine + form submit
        for i in range(50):
            time.sleep(1)
            if login_posted:
                log("Login POST detected!")
                break
            try:
                btn = page.query_selector("#connectToInternet")
                if btn and btn.is_visible():
                    log("Clicking connectToInternet button...")
                    btn.click()
            except:
                pass

        log(f"Final URL: {page.url}")
        log(f"Login posted: {login_posted}")
        log(f"Payload: {login_payload}")
        browser.close()
        return login_posted

if __name__ == "__main__":
    result = test_login()
    log(f"Result: {'SUCCESS' if result else 'FAILED'}")
