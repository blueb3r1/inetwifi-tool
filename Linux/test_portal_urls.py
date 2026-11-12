import requests

test_urls = [
    'http://www.msftconnecttest.com/redirect',
    'http://detectportal.firefox.com/canonical.html',
    'http://captive.apple.com/hotspot-detect.html',
    'http://connectivitycheck.gstatic.com/generate_204',
]

for u in test_urls:
    try:
        r = requests.get(u, timeout=4, allow_redirects=False)
        print(f"{u} -> {r.status_code}, location: {r.headers.get('Location')}")
    except Exception as e:
        print(f"{u} -> error: {e}")
