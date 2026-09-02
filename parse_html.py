import re

def extract_game_info(html):
    info = {
        'image': '',
        'title': '',
        'aliases': '',
        'release_date': '',
        'audio': '',
        'text': ''
    }
    
    # Image
    m_img = re.search(r'<link\s+rel="image_src"\s+href="([^"]+)"', html)
    if m_img: info['image'] = m_img.group(1)

    # Title
    m_title = re.search(r'<h1[^>]*>.*?<span class="h1-special-title"><span>(.*?)</span>', html, re.DOTALL)
    if m_title: info['title'] = m_title.group(1).strip()
    
    # Aliases
    m_aliases = re.search(r'<tr><td>Aliases</td>.*?<td>(.*?)</td></tr>', html, re.DOTALL | re.IGNORECASE)
    if m_aliases:
        info['aliases'] = re.sub(r'<[^>]+>', ' ', m_aliases.group(1)).strip()

    # Release Date
    m_date = re.search(r'<td id="releaseDate">(.*?)</td>', html)
    if m_date: info['release_date'] = m_date.group(1).strip()
    
    # Lang Audio
    m_audio = re.search(r'<div class="t1-data-title-t1">Lang Audio:</div><div class="t1-data-value-t1">(.*?)</div></div>', html, re.DOTALL)
    if m_audio:
        audio_text = re.sub(r'<[^>]+>', ' ', m_audio.group(1)).strip()
        info['audio'] = re.sub(r'\s+', ' ', audio_text)
        
    # Lang Text
    m_text = re.search(r'<div class="t1-data-title-t1">Lang Text:</div><div class="t1-data-value-t1">(.*?)</div></div>', html, re.DOTALL)
    if m_text:
        text_text = re.sub(r'<[^>]+>', ' ', m_text.group(1)).strip()
        info['text'] = re.sub(r'\s+', ' ', text_text)
        
    return info

if __name__ == '__main__':
    with open('test_game.html', 'r', encoding='utf-8') as f:
        html = f.read()
    print(extract_game_info(html))
