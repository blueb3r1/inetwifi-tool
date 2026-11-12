import requests
from bs4 import BeautifulSoup
import re
import json

# Step 1: GET login page from MikroTik router, parse chap params
r = requests.get('http://192.168.200.1/login', timeout=5)
soup = BeautifulSoup(r.text, 'html.parser')

def val(fid):
    tag = soup.find('input', {'id': fid})
    return tag['value'] if tag else ''

serial = val('serial')
client_mac = val('client_mac')
client_ip = val('client_ip')
userurl = val('userurl')
login_url_val = val('login_url')
chap_id = val('chap-id')
chap_challenge = val('chap-challenge')

print('serial:', serial)
print('client_mac:', client_mac)
print('client_ip:', client_ip)
print('chap_id:', repr(chap_id))
print('chap_challenge:', repr(chap_challenge))

# Step 2: Build Awing URL with CORRECT challenge (not reversed!)
awing_url = (
    'http://v1.awingconnect.vn/login?'
    f'serial={serial}'
    f'&client_mac={client_mac}'
    f'&client_ip={client_ip}'
    f'&userurl={userurl}'
    f'&login_url={login_url_val}'
    f'&chap_id={chap_id}'
    f'&chap_challenge={chap_challenge}'
)
print()
print('Awing URL:', awing_url[:150], '...')

# Step 3: GET Awing page with real browser User-Agent
headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
}
r2 = requests.get(awing_url, headers=headers, timeout=10)
print()
print('Awing status:', r2.status_code)
print('Awing response length:', len(r2.text))

# Save full Awing response
with open(r'C:\Users\Admin\Documents\wifi\awing_response.html', 'w', encoding='utf-8') as f:
    f.write(r2.text)
print('Saved awing_response.html')

# Step 4: Search for frmLogin form with username/password
soup2 = BeautifulSoup(r2.text, 'html.parser')
form = soup2.find('form', {'id': 'frmLogin'})
if form:
    print()
    print('=== Found frmLogin! ===')
    for inp in form.find_all('input'):
        print(f'  {inp.get("name")}: {inp.get("value")}')
else:
    print()
    print('frmLogin not in direct HTML, searching in page scripts/json...')
    # The form may be inside a JSON response from AJAX calls
    # Let's look for username and password patterns
    for pattern in ['inet_15m', 'frmLogin', 'contentAuthenForm']:
        idx = r2.text.find(pattern)
        if idx != -1:
            print(f'Found "{pattern}" at index {idx}')
            snippet = r2.text[max(0, idx-100):idx+300]
            print(f'  Context: ...{snippet}...')
            print()
