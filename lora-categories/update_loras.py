import csv
import os
import requests
import json
from bs4 import BeautifulSoup

def download_image(url, filename):
    if not url or url == '不明':
        return False
    
    thumb_dir = 'thumbnails'
    os.makedirs(thumb_dir, exist_ok=True)
    
    # Save as .jpg even if it might be another format, to match existing code style
    # or keep original extension. Let's use the provided filename + .jpg
    save_path = os.path.join(thumb_dir, filename + '.jpg')
    
    if os.path.exists(save_path):
        return True
        
    try:
        print(f"Downloading {url} to {save_path}")
        response = requests.get(url, timeout=10)
        if response.status_code == 200:
            with open(save_path, 'wb') as f:
                f.write(response.content)
            return True
    except Exception as e:
        print(f"Failed to download {url}: {e}")
        
    return False

def generate_html(csv_file='data.csv'):
    items_by_category = {}
    total_items = 0
    
    with open(csv_file, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            cat = row['Category']
            if cat not in items_by_category:
                items_by_category[cat] = []
            items_by_category[cat].append(row)
            total_items += 1
            
            # Start downloading thumbnail in the background or sequentially
            download_image(row['ImageURL'], row['FileName'])

    # Build category navigation
    nav_html = '<div class="category-nav">\n'
    # Define nice colors for known categories, default for others
    colors = {
        'loras': ('#ecfdf5', '#34d399', '#065f46'),
        'Flux': ('#ecfdf5', '#34d399', '#065f46'),
        'Pony': ('#ecfdf5', '#34d399', '#065f46'),
        'Illustrious': ('#faf5ff', '#c084fc', '#6b21a8'),
        'SDXL': ('#f0f9ff', '#7dd3fc', '#0369a1'),
        'WanVideo': ('#fef2f2', '#f87171', '#991b1b'),
        'SD1.5': ('#f1f5f9', '#94a3b8', '#334155'),
    }
    
    for cat, items in items_by_category.items():
        bg, border, text = colors.get(cat, ('#ffffff', '#ccc', '#333'))
        nav_html += f'    <a href="#{cat}" style="background: {bg}; border-color: {border}; color: {text};"><i class="fas fa-cube"></i> {cat} ({len(items)})</a>\n'
    nav_html += '</div>\n'
    
    sections_html = ""
    for cat, items in items_by_category.items():
        bg, border, text = colors.get(cat, ('#ffffff', '#ccc', '#333'))
        
        sections_html += f'''
        <div class="lora-section" id="{cat}">
            <h2 style="color: {border}; border-color: {border}; text-shadow: 0 0 10px rgba(0, 0, 0, 0.2);">
                <i class="fas fa-layer-group"></i> {cat}
                <span style="font-size:1.2rem;color:var(--text-muted); font-weight:normal; margin-left: 10px;">({len(items)} items)</span>
            </h2>
            <div class="lora-grid">
'''
        for row in items:
            filename = row['FileName']
            size = row['Size(Bytes)']
            file_url = row['FileURL']
            image_url = row['ImageURL']
            
            # Google Search processing (remove .safetensors)
            search_query = filename.replace('.safetensors', '').replace('.pt', '')
            google_search_url = f"https://www.google.com/search?q={search_query}+civitai"
            
            # Link for Civitai
            if file_url and file_url != '不明':
                onclick_js = f"onclick=\"window.open('{file_url}', '_blank')\""
                author_link = f'<a href="{file_url}" target="_blank" class="author-link known" title="配信元で開く"><i class="fas fa-link"></i> Link</a>'
            else:
                onclick_js = ""
                author_link = f'<span class="author-link unknown"><i class="fas fa-unlink"></i> なし</span>'
            
            # Image source
            img_src = f"thumbnails/{filename}.jpg"
            if not os.path.exists(img_src):
                # If downloading failed or no image, fallback to No Image template
                img_src = 'data:image/svg+xml;charset=UTF-8,%3Csvg%20xmlns%3D%22http%3A%2F%2Fwww.w3.org%2F2000%2Fsvg%22%20width%3D%22100%25%22%20height%3D%22100%25%22%20viewBox%3D%220%200%20300%20200%22%3E%3Crect%20fill%3D%22%232a2a2a%22%20width%3D%22300%22%20height%3D%22200%22%2F%3E%3Ctext%20fill%3D%22%23555%22%20x%3D%2250%25%22%20y%3D%2250%25%22%20dominant-baseline%3D%22middle%22%20text-anchor%3D%22middle%22%20font-family%3D%22sans-serif%22%20font-size%3D%2216%22%20font-weight%3D%22bold%22%3ENo%20Image%3C%2Ftext%3E%3C%2Fsvg%3E'

            sections_html += f'''
                <div class="lora-card" style="border-top: 3px solid {border};">
                    <div class="lora-card-img" {onclick_js}>
                        <img src="{img_src}" alt="{filename}">
                        <div style="position: absolute; bottom: 10px; right: 10px; background: rgba(0,0,0,0.6); padding: 4px 8px; border-radius: 4px; font-size: 0.75rem; color: #fff; pointer-events: none;">
                            <i class="fas fa-external-link-alt"></i>
                        </div>
                    </div>
                    <div class="lora-card-content">
                        <div>
                            <span class="lora-tag" style="background: {bg}; color: {text}; border: 1px solid {border};">{cat}</span>
                        </div>
                        <div class="lora-name" title="{filename}">{filename}</div>
                        <div class="lora-desc">
                            Size: {size}
                        </div>
                        <div class="lora-author">
                            <a href="{google_search_url}" target="_blank" class="author-link unknown" title="Googleで検索">
                                Google <i class="fab fa-google" style="font-size: 0.8em;"></i>
                            </a>
                            {author_link}
                        </div>
                    </div>
                </div>
'''
        sections_html += '''
            </div>
        </div>
'''

    # Read the skeleton of index.html
    # We will replace the container content.
    with open('index.html', 'r', encoding='utf-8') as f:
        html_content = f.read()

    # We need to find the <div class="lora-container"> and replace its contents or specifically the sections
    soup = BeautifulSoup(html_content, 'html.parser')
    
    container = soup.find('div', class_='lora-container')
    
    # Remove existing nav and sections
    if container:
        for nav in container.find_all('div', class_='category-nav'):
            nav.decompose()
        for section in container.find_all('div', class_='lora-section'):
            section.decompose()
            
        # Update total count text
        p_tag = container.find('p')
        if p_tag:
            p_tag.clear()
            p_tag.append(BeautifulSoup(f'対応モデルごとに分類されたLoRA一覧です。各カードから作者ページや配信元へアクセスできます。全 <strong style="color: var(--primary-cyan); font-size: 1.3rem;">{total_items}</strong> ファイル。', 'html.parser'))
            
        # Append new nav and sections
        container.append(BeautifulSoup(nav_html, 'html.parser'))
        container.append(BeautifulSoup(sections_html, 'html.parser'))
        
        # Now fix the CSS for the hover effect (whole image displayed)
        # Find style tag and replace the specific CSS block
        style_tag = soup.find('style')
        if style_tag:
            css = style_tag.string
            # Check if .lora-card:hover .lora-card-img img is there
            if '.lora-card:hover .lora-card-img img' in css:
                import re
                css = re.sub(r'\.lora-card:hover \.lora-card-img img\s*\{\s*transform:\s*scale\(1\.05\);\s*\}', 
                             '.lora-card:hover .lora-card-img img { object-fit: contain; transform: scale(1); background-color: #000; }', css)
                style_tag.string = css

    with open('index.html', 'w', encoding='utf-8') as f:
        f.write(str(soup))
        
    print(f"Update complete! Total items: {total_items}")

if __name__ == '__main__':
    generate_html(r'K:\GoogleAI\output.csv')
