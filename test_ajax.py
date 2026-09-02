import cloudscraper
import re

scraper = cloudscraper.create_scraper()
html = scraper.get('https://www.h-suki.com/en/games/18401').text

# Search for support links table row or div
m = re.search(r'Support links.*?</tr>', html, re.I | re.DOTALL)
if m:
    print("Support links as TR:", m.group(0))
else:
    print("No TR found.")
    
m2 = re.search(r'>Support links<.*?</div>\s*</div>', html, re.I | re.DOTALL)
if m2:
    print("Support links as DIV:", m2.group(0))
else:
    print("No DIV found.")
