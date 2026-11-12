"""
Deobfuscated INET WiFi anti-bot script analysis.
This file annotates what the router's JavaScript actually does.
"""

# The script appended to jquery-3.6.1.min.js does this:
#
# (function() {
#     if (window._vr) return;          // already ran
#     window._vr = 1;
#     var startTime = Date.now();
#     var hadMouseEvent = 0;           // tracks if user moved mouse / clicked
#     var ua = navigator.userAgent;
#     var isMobile = /iPhone|iPad|iPod|Android/i.test(ua);
#
#     // Desktop only: listen for real user interaction
#     if (!isMobile) {
#         ['mousemove', 'pointerdown', 'mousedown'].forEach(function(e) {
#             window.addEventListener(e, function() { hadMouseEvent = 1; }, { once: true });
#         });
#     }
#
#     // _0x5(id): get value of hidden input by id
#     function getVal(id) {
#         var el = document.getElementById(id);
#         return (el && el.value && el.value.indexOf('$(') !== 0) ? el.value : '';
#     }
#
#     // _0x6(): ANTI-BOT CHECK
#     // Returns 1 (is bot) if:
#     //   - User-Agent contains: curl, python, wget, httpclient, headless, selenium
#     //   - navigator.webdriver is true
#     //   - navigator.languages is empty/missing
#     //   - screen.width === 0
#     function isBot() {
#         var uaLower = ua.toLowerCase();
#         var botStrings = ["curl", "python", "wget", "httpclient", "headless", "selenium"];
#         for (var i = 0; i < botStrings.length; i++) {
#             if (uaLower.indexOf(botStrings[i]) !== -1) return 1;
#         }
#         if (navigator.webdriver || !navigator.languages || navigator.languages.length === 0 || screen.width === 0)
#             return 1;
#         return 0;
#     }
#
#     // _0x7(c): redirect to Awing Connect with chap_challenge = c
#     function redirectToAwing(chapChallenge) {
#         var domain = "v1.awingconnect.vn";
#         var url = "http://" + domain + "/login?"
#             + "serial="        + getVal('serial')
#             + "&client_mac="   + getVal('client_mac')
#             + "&client_ip="    + getVal('client_ip')
#             + "&userurl="      + getVal('userurl')
#             + "&login_url="    + getVal('login_url')
#             + "&chap_id="      + getVal('chap-id')
#             + "&chap_challenge=" + chapChallenge;
#         window.location.replace(url);
#     }
#
#     // _0x8(): main state machine
#     function checkAndRedirect() {
#         var elapsed = Date.now() - startTime;
#         var chapCh = getVal('chap-challenge');
#         if (!chapCh) { setTimeout(checkAndRedirect, 500); return; }
#
#         // REVERSED challenge string for bots
#         var reversed = chapCh.split('').reverse().join('');
#
#         // ===== BOT DETECTED =====
#         if (isBot()) {
#             if (elapsed > 2000) {     // 0x7d0 = 2000ms
#                 redirectToAwing(reversed);   // <<< SENDS REVERSED/WRONG CHALLENGE
#                 return;
#             }
#             setTimeout(checkAndRedirect, 500);
#             return;
#         }
#
#         // ===== MOBILE =====
#         if (isMobile) {
#             var isOld = (Android < 9 or iOS < 11);
#             var wait = isOld ? 1000 : 3000;     // 0x3e8=1000, 0xbb8=3000
#             if (elapsed > wait) {
#                 redirectToAwing(chapCh);   // <<< SENDS CORRECT CHALLENGE
#                 return;
#             }
#             setTimeout(checkAndRedirect, 500);
#             return;
#         }
#
#         // ===== DESKTOP (real user) =====
#         if (!isMobile) {
#             if (elapsed > 13000) {    // 0x32c8 = 13000ms - force after 13s
#                 redirectToAwing(chapCh);   // <<< SENDS CORRECT CHALLENGE
#                 return;
#             }
#             if (elapsed > 3000 && hadMouseEvent) {  // 0xbb8=3000ms + mouse moved
#                 redirectToAwing(chapCh);   // <<< SENDS CORRECT CHALLENGE
#                 return;
#             }
#             setTimeout(checkAndRedirect, 500);
#             return;
#         }
#     }
#
#     setTimeout(checkAndRedirect, 1000);  // 0x3e8 = 1000ms initial delay
# })();

# ===================== CONCLUSION =====================
# 
# The anti-bot system works as follows:
# 
# 1. If User-Agent contains "python", "headless", "curl", "wget", "selenium", "httpclient"
#    OR navigator.webdriver=true, OR no languages, OR screen.width=0:
#    → The script REVERSES the chap-challenge string
#    → This causes Awing Connect to receive a WRONG challenge
#    → The generated login form will have WRONG password hash
#    → MikroTik login FAILS
#
# 2. If it's a real browser user:
#    → Sends the CORRECT chap-challenge to Awing
#    → Awing returns the correct login form with correct password
#    → MikroTik login SUCCEEDS
#
# ===================== FIX STRATEGY =====================
#
# Option A: Use Playwright with NON-headless Chrome (channel='chrome')
#           and inject mouse events to pass bot detection.
#           Set navigator.webdriver=false, ensure languages exist.
#
# Option B: Since we know the mechanism, we can replicate the flow:
#   Step 1: GET http://192.168.200.1/login -> parse chap params
#   Step 2: Build the Awing URL with CORRECT (not reversed) chap_challenge
#           using a REAL browser User-Agent
#   Step 3: GET the Awing URL -> it returns HTML with the login form containing
#           username="inet_15m-15m" and password="<CHAP_HASH>"
#   Step 4: POST http://192.168.200.1/login with that username+password
#
# The key insight: the password hash is computed SERVER-SIDE by Awing,
# so we just need to fetch it from Awing with the correct challenge.
