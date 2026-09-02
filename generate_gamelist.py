import os
import re
import json
import time
import cloudscraper
from bs4 import BeautifulSoup

TARGET_DIR = r"R:\\"
OUTPUT_DIR = r"R:\Gamelist"
CACHE_FILE = os.path.join(OUTPUT_DIR, "cache.json")
OUTPUT_HTML = os.path.join(OUTPUT_DIR, "index.html")

scraper = cloudscraper.create_scraper()

def ensure_dir():
    if not os.path.exists(OUTPUT_DIR):
        os.makedirs(OUTPUT_DIR)

def load_cache():
    if os.path.exists(CACHE_FILE):
        try:
            with open(CACHE_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception:
            pass
    return {}

def save_cache(cache):
    with open(CACHE_FILE, 'w', encoding='utf-8') as f:
        json.dump(cache, f, ensure_ascii=False, indent=2)

def extract_id(filename):
    match = re.match(r'^((RJ|RA|stm|v)\d+)_', filename, re.IGNORECASE)
    if match:
        orig = match.group(1)
        if orig.upper().startswith('RJ') or orig.upper().startswith('RA'):
            return orig.upper()
        elif orig.upper().startswith('STM'):
            return orig.lower()
        elif orig.upper().startswith('V'):
            return orig.lower()
        return orig
    return None

def fetch_html(url):
    try:
        resp = scraper.get(url, timeout=10)
        return resp.text
    except Exception as e:
        print(f"Error fetching {url}: {e}")
        return None

def search_game(game_id):
    print(f"Searching {game_id}...")
    
    stype = "searchRid"
    sq = game_id

    if game_id.upper().startswith('RJ'):
        stype = 'searchRid'
        sq = game_id 
    elif game_id.upper().startswith('RA'):
        stype = 'searchRid'
        sq = game_id 
    elif game_id.lower().startswith('stm'):
        stype = 'searchRid'
        sq = game_id[3:] 
    elif game_id.lower().startswith('v'):
        stype = 'searchVndb'
        sq = game_id[1:] 
        
    search_url = f'https://www.h-suki.com/en/search?stype={stype}&sq={sq}'
    html = fetch_html(search_url)
    if not html: return None

    soup = BeautifulSoup(html, 'html.parser')
    main = soup.find(id="main-content")
    if not main:
        return None
        
    links = [a['href'] for a in main.find_all('a', href=True) if '/en/games/' in a['href']]
    links = list(set([l for l in links if 'comments' not in l]))
    
    if links:
        link = links[0]
        full_url = link if link.startswith('http') else f"https://www.h-suki.com{link}"
        game_html = fetch_html(full_url)
        if game_html:
            return extract_details(game_html, full_url)
            
    if game_id.upper().startswith('RJ0'):
        alt_id = 'RJ' + game_id[3:]
        print(f"Retrying with {alt_id}...")
        search_url = f'https://www.h-suki.com/en/search?stype=searchRid&sq={alt_id}'
        html = fetch_html(search_url)
        if html:
            soup = BeautifulSoup(html, 'html.parser')
            main = soup.find(id="main-content")
            if main:
                links = [a['href'] for a in main.find_all('a', href=True) if '/en/games/' in a['href']]
                links = list(set([l for l in links if 'comments' not in l]))
                if links:
                    link = links[0]
                    full_url = link if link.startswith('http') else f"https://www.h-suki.com{link}"
                    game_html = fetch_html(full_url)
                    if game_html:
                        return extract_details(game_html, full_url)

    return None

def resolve_urls(soup_obj):
    # Fix relative urls found inside html payloads
    for img in soup_obj.find_all('img', src=True):
        if img['src'].startswith('/'):
            img['src'] = f"https://www.h-suki.com{img['src']}"
    for a in soup_obj.find_all('a', href=True):
        if a['href'].startswith('/'):
            a['href'] = f"https://www.h-suki.com{a['href']}"
        # Target blank for safe clicking
        a['target'] = '_blank'
    return soup_obj

def extract_details(html, page_url):
    details = {
        'url': page_url,
        'Title': '',
        'Aliases': '',
        'Image': '',
        'Initial release date': '',
        'Genres': '',
        'OS': '',
        'Lang Audio': '',
        'Lang Text': '',
        'Support links': ''
    }
    
    soup = BeautifulSoup(html, 'html.parser')
    
    title_tag = soup.find('title')
    if title_tag:
        details['Title'] = title_tag.text.replace('| HSuki', '').strip()
        
    for img in soup.find_all('img', src=True):
        src = img['src']
        if 'cover' in src or 'screens/jeux' in src:
            details['Image'] = src if src.startswith('http') else f"https://www.h-suki.com{src}"
            break

    def get_row_value(label, html=False):
        for tr in soup.find_all('tr'):
            tds = tr.find_all('td')
            if len(tds) >= 2 and label.lower() in tds[0].text.lower():
                val_td = tds[1]
                if html:
                    val_td = resolve_urls(val_td)
                    return val_td.decode_contents().strip()
                else:
                    return val_td.text.strip()
        return None

    def get_div_value(label, html=False):
        for div in soup.find_all('div', class_='t1-data-title-t1'):
            if label.lower() in div.text.lower():
                parent = div.find_parent('div')
                val_div = parent.find('div', class_='t1-data-value-t1') if parent else None
                if val_div:
                    if html:
                        val_div = resolve_urls(val_div)
                        return val_div.decode_contents().strip()
                    else:
                        return val_div.text.strip()
        return None

    date_val = get_row_value('Initial release date')
    if date_val: details['Initial release date'] = date_val
    
    aliases_val = get_row_value('Aliases')
    if aliases_val: details['Aliases'] = ' '.join(aliases_val.split())

    genres_val = get_row_value('Genres')
    if genres_val: details['Genres'] = ' '.join(genres_val.split())
    
    os_val = get_row_value('OS')
    if os_val: details['OS'] = ' '.join(os_val.split())
    
    audio_val = get_div_value('Lang Audio', html=True)
    if audio_val: details['Lang Audio'] = audio_val
    
    text_val = get_div_value('Lang Text', html=True)
    if text_val: details['Lang Text'] = text_val
    
    support_val = get_row_value('Support links', html=True)
    if support_val: details['Support links'] = support_val
        
    return details

def generate_html(cache, all_game_ids):
    html_content = """<!DOCTYPE html>
<html lang="ja">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Game List - Premium Theme</title>
    <meta name="referrer" content="no-referrer">
    <link href="https://fonts.googleapis.com/css2?family=Outfit:wght@400;600;800&family=Noto+Sans+JP:wght@400;700&display=swap" rel="stylesheet">
    <style>
        :root {
            /* Elegant Pink Base Theme */
            --bg-color: #2b1021;
            --surface-color: #3b172d;
            --border-color: #5c2044;
            --text-primary: #ffe6f0;
            --text-secondary: #ffb3d1;
            --accent-color: #ff529a;
            --accent-color-2: #ff8abf;
            --gradient-bg: linear-gradient(145deg, #3d162f, #230c1a);
        }
        body {
            background-color: var(--bg-color);
            color: var(--text-primary);
            font-family: 'Outfit', 'Noto Sans JP', sans-serif;
            margin: 0;
            padding: 0;
            line-height: 1.6;
            overflow-y: scroll;
        }
        .header {
            text-align: center;
            padding: 4rem 2rem;
            background: linear-gradient(180deg, #1f0b18 0%, #2b1021 100%);
            border-bottom: 2px solid var(--border-color);
            position: relative;
            overflow: hidden;
        }
        .header::before {
            content: '';
            position: absolute;
            top: -50%; left: -50%; width: 200%; height: 200%;
            background: radial-gradient(circle, rgba(255,82,154,0.1) 0%, transparent 60%);
            pointer-events: none;
        }
        .header h1 {
            font-size: 3.5rem;
            font-weight: 800;
            margin: 0;
            background: -webkit-linear-gradient(45deg, var(--accent-color), var(--accent-color-2));
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            letter-spacing: -1px;
            position: relative;
        }
        .header p {
            color: var(--text-secondary);
            font-size: 1.2rem;
            margin-top: 1rem;
            font-weight: 600;
        }
        .container {
            max-width: 1400px;
            margin: 0 auto;
            padding: 3rem 2rem;
            display: grid;
            grid-template-columns: repeat(auto-fill, minmax(320px, 1fr));
            gap: 2.5rem;
        }
        .card {
            background: var(--gradient-bg);
            border: 1px solid var(--border-color);
            border-radius: 12px;
            overflow: hidden;
            transition: transform 0.3s ease, box-shadow 0.3s ease;
            display: flex;
            flex-direction: column;
            position: relative;
        }
        .card:hover {
            transform: translateY(-8px);
            box-shadow: 0 12px 30px rgba(255, 82, 154, 0.25), 0 0 0 1px var(--accent-color);
        }
        .card-img-wrap {
            position: relative;
            width: 100%;
            height: 250px;
            background: #11050d;
            overflow: hidden;
            display: flex;
            align-items: center;
            justify-content: center;
            border-bottom: 2px solid rgba(255,82,154,0.2);
        }
        .card-img-wrap img {
            max-width: 100%;
            max-height: 100%;
            object-fit: contain;
            transition: transform 0.6s cubic-bezier(0.165, 0.84, 0.44, 1);
        }
        .card:hover .card-img-wrap img {
            transform: scale(1.08);
        }
        .card-content {
            padding: 1.5rem;
            flex-grow: 1;
            display: flex;
            flex-direction: column;
        }
        .card-id {
            position: absolute;
            top: 1rem;
            right: 1rem;
            background: rgba(43, 16, 33, 0.85);
            backdrop-filter: blur(4px);
            color: #fff;
            padding: 0.35rem 1rem;
            border-radius: 20px;
            font-size: 0.85rem;
            font-weight: 800;
            border: 1px solid rgba(255,82,154,0.3);
            z-index: 2;
            letter-spacing: 1px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.5);
        }
        .card-title {
            font-size: 1.25rem;
            font-weight: 700;
            margin: 0 0 0.5rem 0;
            color: #fff;
            display: -webkit-box;
            -webkit-line-clamp: 2;
            -webkit-box-orient: vertical;
            overflow: hidden;
            text-decoration: none;
            transition: color 0.2s ease;
        }
        .card-title:hover {
            color: var(--accent-color-2);
        }
        .aliases {
            font-size: 0.85rem;
            color: var(--accent-color-2);
            margin-bottom: 1rem;
            display: -webkit-box;
            -webkit-line-clamp: 2;
            -webkit-box-orient: vertical;
            overflow: hidden;
            opacity: 0.9;
        }
        .info-grid {
            display: grid;
            grid-template-columns: 1fr;
            gap: 0.75rem;
            margin-top: auto;
            font-size: 0.9rem;
        }
        .info-item {
            display: flex;
            align-items: flex-start;
            border-bottom: 1px solid rgba(255, 138, 191, 0.1);
            padding-bottom: 0.75rem;
        }
        .info-item:last-child {
            border-bottom: none;
            padding-bottom: 0;
        }
        .info-label {
            color: var(--text-secondary);
            width: 100px;
            flex-shrink: 0;
            font-weight: 600;
            font-size: 0.85rem;
            text-transform: uppercase;
            letter-spacing: 0.5px;
        }
        .info-value {
            color: var(--text-primary);
            flex-grow: 1;
            word-break: break-word;
            display: flex;
            align-items: center;
            flex-wrap: wrap;
            gap: 4px;
        }
        .info-value a {
            color: var(--accent-color);
            text-decoration: none;
            transition: color 0.2s;
            display: flex;
            align-items: center;
            gap: 4px;
        }
        .info-value a:hover {
            color: var(--accent-color-2);
            text-decoration: underline;
        }
        .info-value img {
            height: 16px;
            vertical-align: middle;
            border-radius: 2px;
        }
        .badge {
            display: inline-block;
            background: rgba(255, 82, 154, 0.15);
            color: var(--accent-color-2);
            padding: 3px 10px;
            border-radius: 6px;
            font-size: 0.8rem;
            margin-right: 6px;
            margin-bottom: 6px;
            font-weight: 600;
            border: 1px solid rgba(255,82,154,0.2);
        }
        .not-found {
            display: flex;
            align-items: center;
            justify-content: center;
            height: 100%;
            color: #ffb3d1;
            font-weight: bold;
            font-size: 1.2rem;
            background: rgba(0,0,0,0.5);
        }
        @media (max-width: 768px) {
            .container {
                grid-template-columns: 1fr;
            }
        }
    </style>
</head>
<body>

<div class="header">
    <h1>Game Library</h1>
    <p>R:\ Drive Extracted Collection - Pink Theme</p>
</div>

<div class="container">
"""
    
    for game_id in sorted(all_game_ids):
        data = cache.get(game_id)
        if not data or not data.get('Title'):
            continue
            
        title = data.get('Title', 'No Title')
        aliases = data.get('Aliases', '')
        img = data.get('Image', '')
        date = data.get('Initial release date', 'N/A')
        if not date: date = 'N/A'
        genres = data.get('Genres', 'N/A')
        os_text = data.get('OS', 'N/A')
        if not os_text: os_text = 'N/A'
        audio = data.get('Lang Audio', 'N/A')
        if not audio: audio = 'N/A'
        ltext = data.get('Lang Text', 'N/A')
        if not ltext: ltext = 'N/A'
        support_links = data.get('Support links', '')
        url = data.get('url', '#')
        
        genre_html = ""
        for g in genres.split():
            if g.strip() and g != 'N/A':
                genre_html += f'<span class="badge">{g.strip()}</span>'
        if not genre_html:
            genre_html = "N/A"

        aliases_html = f'<div class="aliases">{aliases}</div>' if aliases else ''

        support_html = ""
        if support_links:
            support_html = f"""
                <div class="info-item">
                    <span class="info-label">Links</span>
                    <span class="info-value">{support_links}</span>
                </div>
            """

        html_content += f"""
    <div class="card">
        <div class="card-id">{game_id}</div>
        <a href="{url}" target="_blank" class="card-img-wrap">
            <img src="{img}" alt="{title}" onerror="this.src=''" referrerpolicy="no-referrer" loading="lazy">
        </a>
        <div class="card-content">
            <a href="{url}" target="_blank" class="card-title" title="{title}">{title}</a>
            {aliases_html}
            <div class="info-grid">
                <div class="info-item">
                    <span class="info-label">Release</span>
                    <span class="info-value">{date}</span>
                </div>
                <div class="info-item">
                    <span class="info-label">Genres</span>
                    <span class="info-value">{genre_html}</span>
                </div>
                <div class="info-item">
                    <span class="info-label">OS</span>
                    <span class="info-value">{os_text}</span>
                </div>
                <div class="info-item">
                    <span class="info-label">Audio</span>
                    <span class="info-value">{audio}</span>
                </div>
                <div class="info-item">
                    <span class="info-label">Text</span>
                    <span class="info-value">{ltext}</span>
                </div>
                {support_html}
            </div>
        </div>
    </div>
"""

    html_content += """
</div>
</body>
</html>
"""
    with open(OUTPUT_HTML, 'w', encoding='utf-8') as f:
        f.write(html_content)


def main():
    ensure_dir()
    cache = load_cache()
    
    # Refresh everything
    cache.clear()
    save_cache(cache)
    
    if os.path.exists(TARGET_DIR):
        files = os.listdir(TARGET_DIR)
    else:
        print("R:\\ not found!")
        return

    all_game_ids = set()
    ids_to_process = []
    
    for f in files:
        game_id = extract_id(f)
        if game_id:
            all_game_ids.add(game_id)
            if game_id not in cache or cache[game_id].get('Title') is None:
                ids_to_process.append(game_id)
            
    ids_to_process = list(set(ids_to_process))
    print(f"Total IDs extracted: {len(all_game_ids)}")
    print(f"Found {len(ids_to_process)} new/failed IDs to process.")
    
    processed_count = 0
    
    for game_id in ids_to_process:
        try:
            details = search_game(game_id)
            if details:
                cache[game_id] = details
                print(f"  -> Found: {details.get('Title')}")
            else:
                cache[game_id] = {"Title": None}
                print(f"  -> No data found for {game_id}.")
                
            save_cache(cache)
            generate_html(cache, all_game_ids)
            
            processed_count += 1
            if processed_count < len(ids_to_process):
                # Request 4 "slow wait"
                time.sleep(1.5)
        except Exception as e:
            print(f"Error processing {game_id}: {e}")

    generate_html(cache, all_game_ids)
    print(f"All processing complete. Generated {OUTPUT_HTML}")


if __name__ == "__main__":
    main()
