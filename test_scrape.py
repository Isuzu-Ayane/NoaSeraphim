import urllib.request
import urllib.parse
import re

def search(q):
    url = f'https://www.h-suki.com/en/search?q={urllib.parse.quote(q)}'
    req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'})
    try:
        resp = urllib.request.urlopen(req)
        html = resp.read().decode('utf-8')
        
        with open('temp_search.html', 'w', encoding='utf-8') as f:
            f.write(html)
            
        print("Done writing to temp_search.html")
    except Exception as e:
        print(f"Error: {e}")

search('RJ432000')
