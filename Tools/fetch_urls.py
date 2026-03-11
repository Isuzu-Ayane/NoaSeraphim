import json
import urllib.request
import urllib.parse
import re
import time
import os

def check_civitai(query):
    try:
        url = f"https://civitai.com/api/v1/models?query={urllib.parse.quote(query)}&limit=1"
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req, timeout=5) as response:
            data = json.loads(response.read().decode())
            if data.get('items') and len(data['items']) > 0:
                mid = data['items'][0]['id']
                return f"https://civitai.com/models/{mid}"
    except Exception as e:
        print(f"Civitai error for {query}: {e}")
    return None

def check_huggingface(query):
    try:
        url = f"https://huggingface.co/api/models?search={urllib.parse.quote(query)}&limit=1"
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req, timeout=5) as response:
            data = json.loads(response.read().decode())
            if len(data) > 0:
                mid = data[0]['id']
                return f"https://huggingface.co/{mid}"
    except Exception as e:
        print(f"HF error for {query}: {e}")
    return None

def process_file(filepath, var_name):
    print(f"Processing {filepath}...")
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()

    # extract json
    match = re.search(r'const\s+' + var_name + r'\s*=\s*(\[.*\]);', content, re.DOTALL)
    if not match:
        print(f"Could not parse var {var_name}")
        return

    data = json.loads(match.group(1))
    
    for item in data:
        if 'url' in item:
            continue
        
        name = item['name']
        print(f"Searching for {name}...")
        
        # 1. Civitai
        link = check_civitai(name)
        if not link:
            # wait a bit and try huggingface
            time.sleep(0.5)
            # Remove V version strings or underscores for better HF search sometimes, but let's try direct first
            link = check_huggingface(name)
        
        if link:
            item['url'] = link
            print(f"  -> Found: {link}")
        else:
            item['url'] = "不明"
            print("  -> Not found")
            
        time.sleep(0.5) # rate limit

    new_content = f"const {var_name} = {json.dumps(data, separators=(',', ':'))};\n"
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(new_content)
    print(f"Saved {filepath}")

base_dir = r"K:\GoogleAI\NoaSeraphim"

process_file(os.path.join(base_dir, "ai-checkpoints", "gallery_data.js"), "checkpointData")
process_file(os.path.join(base_dir, "ai-tools", "gallery_data.js"), "loraData")
print("Done!")
