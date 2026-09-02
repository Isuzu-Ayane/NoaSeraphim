import os
import re
import json
import time
import urllib.request
import html as html_lib

CACHE_FILE = r'R:\Gamelist\h_suki_cache.json'
TARGET_DIR = r'R:\Gamelist'
SOURCE_DIR = 'R:\\\\'

def ensure_dir():
    if not os.path.exists(TARGET_DIR):
        os.makedirs(TARGET_DIR)

def load_cache():
    if os.path.exists(CACHE_FILE):
        try:
            with open(CACHE_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except:
            return {}
    return {}

def save_cache(cache):
    with open(CACHE_FILE, 'w', encoding='utf-8') as f:
        json.dump(cache, f, ensure_ascii=False, indent=2)

def fetch_html(url):
    req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/120.0.0.0 Safari/537.36'})
    try:
        html = urllib.request.urlopen(req).read().decode('utf-8', 'ignore')
        return html
    except Exception as e:
        print(f"Error fetching {url}: {e}")
        return ""

def get_text(match):
    if not match: return ''
    text = re.sub(r'<[^>]+>', ' ', match.group(1))
    text = re.sub(r'\s+', ' ', text).strip()
    return html_lib.unescape(text)

def parse_game_page(html):
    info = {
        'image': '',
        'title': '',
        'aliases': '',
        'release_date': '',
        'audio': '',
        'text': '',
        'found': True
    }
    
    m_img = re.search(r'<link\s+rel="image_src"\s+href="([^"]+)"', html)
    if m_img: info['image'] = m_img.group(1)

    m_title = re.search(r'<h1[^>]*>.*?<span class="h1-special-title"><span>(.*?)</span>', html, re.DOTALL)
    if m_title: info['title'] = m_title.group(1).strip()
    
    m_aliases = re.search(r'>Aliases<.+?<div[^>]*>(.*?)</div>', html, re.DOTALL | re.IGNORECASE)
    if m_aliases: info['aliases'] = get_text(m_aliases)

    m_date = re.search(r'<td id="releaseDate">(.*?)</td>', html)
    if m_date: info['release_date'] = m_date.group(1).strip()
    
    m_audio = re.search(r'<div class="t1-data-title-t1">Lang Audio:</div><div class="t1-data-value-t1">(.*?)</div></div>', html, re.DOTALL)
    if m_audio: info['audio'] = get_text(m_audio)
        
    m_text = re.search(r'<div class="t1-data-title-t1">Lang Text:</div><div class="t1-data-value-t1">(.*?)</div></div>', html, re.DOTALL)
    if m_text: info['text'] = get_text(m_text)
        
    return info

def search_game(release_id):
    search_url = f"https://www.h-suki.com/en/search?stype=searchRid&sq={release_id}"
    html = fetch_html(search_url)
    if not html:
        return None
    
    # Extract the actual game link avoiding the 'random title' link (usually ends with digit and appears after the list starts)
    # The random title link has <i class="icon-random"...> so let's match links that don't have that right inside.
    # We can just collect all /games/\d+ links and try to find the one matching our ID, or simply skip the 'icon-random' ones.
    matches = re.findall(r'<a[^>]+href=[\'\"](?:https://www.h-suki.com|)(/en/games/\d+)[\'\"][^>]*>(.*?)</a>', html, re.IGNORECASE | re.DOTALL)
    
    game_url_path = None
    for url, content in matches:
        if 'icon-random' not in content and 'Random' not in content:
            game_url_path = url
            break
            
    if not game_url_path:
        return {'found': False}
        
    # Introduce delay
    time.sleep(1.5)
    
    game_url = f"https://www.h-suki.com{game_url_path}"
    game_html = fetch_html(game_url)
    if not game_html:
        return {'found': False}
        
    return parse_game_page(game_html)

def main(limit=None):
    ensure_dir()
    cache = load_cache()
    
    files = []
    try:
        files = os.listdir(SOURCE_DIR)
    except:
        pass
        
    release_ids = set()
    for f in files:
        if f.startswith('RJ') or f.startswith('RA'):
            parts = f.split('_')
            rid = parts[0]
            # Verify numbering format
            if re.match(r'^(RJ|RA)\d+$', rid, re.IGNORECASE):
                release_ids.add(rid.upper())
                
    print(f"Found {len(release_ids)} unique release IDs in {SOURCE_DIR}")
    
    processed = 0
    for rid in release_ids:
        if limit is not None and processed >= limit:
            break
            
        if rid in cache:
            continue
            
        print(f"Searching for {rid}...")
        info = search_game(rid)
        
        if info:
            cache[rid] = info
            save_cache(cache)
            if info.get('found'):
                print(f" -> Found: {info.get('title')}")
            else:
                print(f" -> Not Found on H-Suki.")
        else:
            print(f" -> Network error, skipping {rid}")
            
        processed += 1
        time.sleep(1.5) # Wait between different games to avoid rate limit

if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('--limit', type=int, default=None, help='Number of new items to fetch')
    args = parser.parse_args()
    
    print("Starting H-Suki Scraper...")
    main(limit=args.limit)
    print("Scraping completed!")
