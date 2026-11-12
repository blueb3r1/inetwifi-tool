import re

with open(r'C:\Users\Admin\Documents\wifi\jquery-3.6.1.min.js', 'r', encoding='utf-8', errors='ignore') as f:
    content = f.read()

# Extract the anti-bot script from jquery
idx = content.find('(function(){if(window[\'\\x5f\\x76\\x72\'])')
if idx != -1:
    end_idx = content.find(';!function', idx)
    script = content[idx:end_idx]
    print('=== EXTRACTED ANTI-BOT SCRIPT ===')
    print(script)
else:
    print('Script block not found!')
