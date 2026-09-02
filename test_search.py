import urllib.request
import re

req = urllib.request.Request('https://www.h-suki.com/en/search?stype=searchRid&sq=RJ01004403', headers={'User-Agent': 'Mozilla/5.0'})
html = urllib.request.urlopen(req).read().decode('utf-8', 'ignore')

# The main content probably is inside <main> or a specific div.
# Let's just find the link that comes after some specific text or isn't the random title.
matches = re.findall(r'<a[^>]+href=[\'\"](?:https://www.h-suki.com|)(/en/games/\d+)[\'\"][^>]*>(.*?)</a>', html, re.IGNORECASE | re.DOTALL)
for match in matches:
    print('Link:', match[0], 'Text:', match[1].strip())
