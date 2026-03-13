import csv
import os
import requests
import json
import math
from bs4 import BeautifulSoup

def download_image(url, filename):
    if not url or url == '不明':
        return False
    
    thumb_dir = 'thumbnails'
    os.makedirs(thumb_dir, exist_ok=True)
    
    base_filename = filename.replace('.safetensors', '').replace('.pt', '')
    save_path = os.path.join(thumb_dir, base_filename + '.jpg')
    
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

def load_lora_seo(filepath):
    seo_data = {}
    if not os.path.exists(filepath):
        print(f"Warning: LoRA SEO file not found at {filepath}")
        return seo_data
    
    with open(filepath, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            filename = row.get('LoRA名', '').strip()
            if filename:
                seo_data[filename] = {
                    'category': row.get('特徴カテゴリ', 'その他'),
                    'description': row.get('説明文', '')
                }
    return seo_data

def generate_html(csv_file='data.csv', items_per_page=100, seo_csv=''):
    items_by_category = {}
    total_items = 0
    
    seo_data = load_lora_seo(seo_csv) if seo_csv else {}
    
    with open(csv_file, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            cat = row['Category']
            if cat not in items_by_category:
                items_by_category[cat] = []
            items_by_category[cat].append(row)
            total_items += 1
            
            # Start downloading thumbnail in the background or sequentially
            # download_image(row['ImageURL'], row['FileName'])

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

    # Helper function to generate pagination links
    def generate_pagination_html(cat, current_page, total_pages, total_items_cat):
        if total_pages <= 1:
            return ""
        
        pagination_html = f'<div class="pagination" style="text-align: center; margin-top: 30px; margin-bottom: 20px;">\n'
        for p in range(1, total_pages + 1):
            if p == 1:
                page_url = f"{cat}.html"
            else:
                page_url = f"{cat}_{p}.html"
                
            active_style = "background: rgba(56, 189, 248, 1); color: white; border-color: rgba(56, 189, 248, 1);" if p == current_page else "background: rgba(255, 255, 255, 0.5); color: var(--text-main); border-color: rgba(255, 255, 255, 0.2);"
            pagination_html += f'<a href="{page_url}" style="display: inline-block; margin: 0 5px; padding: 8px 16px; border-radius: 20px; text-decoration: none; border: 1px solid; {active_style} transition: all 0.2s ease;">{p}</a>\n'
        
        pagination_html += '</div>\n'
        return pagination_html

    # Helper function to process item cards
    def process_item_cards(items, cat, bg, border, text, seo_lookup):
        sections_html = ""
        for row in items:
            filename = row['FileName']
            size = row['Size(Bytes)']
            file_url = row['FileURL']
            
            # Lookup SEO info
            item_seo = seo_lookup.get(filename, {'category': 'その他', 'description': ''})
            feature_cat = item_seo['category']
            description = item_seo['description']
            
            search_query = filename.replace('.safetensors', '').replace('.pt', '')
            google_search_url = f"https://www.google.com/search?q={search_query}+civitai"
            
            if file_url and file_url != '不明':
                onclick_js = f"onclick=\"window.open('{file_url}', '_blank')\""
                author_link = f'<a href="{file_url}" target="_blank" class="author-link known" title="配信元で開く"><i class="fas fa-link"></i> Link</a>'
            else:
                onclick_js = ""
                author_link = f'<span class="author-link unknown"><i class="fas fa-unlink"></i> なし</span>'
            
            base_filename = filename.replace('.safetensors', '').replace('.pt', '')
            img_src = f"thumbnails/{base_filename}.jpg"
            
            # Check if file exists relative to the script directory
            script_dir = os.path.dirname(os.path.abspath(__file__))
            disk_path = os.path.join(script_dir, "thumbnails", f"{base_filename}.jpg")
            
            if not os.path.exists(disk_path):
                img_src = 'data:image/svg+xml;charset=UTF-8,%3Csvg%20xmlns%3D%22http%3A%2F%2Fwww.w3.org%2F2000%2Fsvg%22%20width%3D%22100%25%22%20height%3D%22100%25%22%20viewBox%3D%220%200%20300%20200%22%3E%3Crect%20fill%3D%22%232a2a2a%22%20width%3D%22300%22%20height%3D%22200%22%2F%3E%3Ctext%20fill%3D%22%23555%22%20x%3D%2250%25%22%20y%3D%2250%25%22%20dominant-baseline%3D%22middle%22%20text-anchor%3D%22middle%22%20font-family%3D%22sans-serif%22%20font-size%3D%2216%22%20font-weight%3D%22bold%22%3ENo%20Image%3C%2Ftext%3E%3C%2Fsvg%3E'

            sections_html += f'''
                <div class="lora-card" style="border-top: 3px solid {border};">
                    <div class="lora-card-img" {onclick_js}>
                        <img src="{img_src}" alt="{base_filename}">
                        <div style="position: absolute; bottom: 10px; right: 10px; background: rgba(0,0,0,0.6); padding: 4px 8px; border-radius: 4px; font-size: 0.75rem; color: #fff; pointer-events: none;">
                            <i class="fas fa-external-link-alt"></i>
                        </div>
                    </div>
                    <div class="lora-card-content">
                        <div style="display: flex; justify-content: space-between; align-items: flex-start;">
                            <span class="lora-tag" style="background: {bg}; color: {text}; border: 1px solid {border};">{cat}</span>
                            <span class="lora-tag" style="background: rgba(58, 123, 213, 0.05); color: var(--text-main); border: 1px solid rgba(58, 123, 213, 0.2); font-size: 0.7rem;">{feature_cat}</span>
                        </div>
                        <div class="lora-name" title="{base_filename}">{base_filename}</div>
                        <div class="lora-desc">
                            {description if description else f"Stable Diffusionで利用可能な{feature_cat}系の追加学習モデル。高品質なAI画像生成をLoRAでサポートします。"}
                            <div style="margin-top: 8px; font-size: 0.8rem; opacity: 0.6;">Size: {size}</div>
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
        return sections_html

    # Script HTML (included in every page)
    script_html = '''
    <script>
        document.addEventListener('DOMContentLoaded', () => {
            const searchInput = document.getElementById('loraSearchInput');
            if (!searchInput) return;
            const loraCards = document.querySelectorAll('.lora-card');
            const loraSections = document.querySelectorAll('.lora-section');

            searchInput.addEventListener('input', (e) => {
                const query = e.target.value.toLowerCase().trim();
                const terms = query.split(/\s+/);

                let visibleCount = 0;
                loraCards.forEach(card => {
                    const text = card.textContent.toLowerCase();
                    const isMatch = terms.every(term => text.includes(term));
                    if (isMatch || query === '') {
                        card.style.display = 'flex';
                        visibleCount++;
                    } else {
                        card.style.display = 'none';
                    }
                });

                loraSections.forEach(section => {
                    const header = section.querySelector('h2');
                    if (header) {
                        const countSpan = header.querySelector('span');
                        if (countSpan) {
                            if (query) {
                                countSpan.textContent = `(表示中: ${visibleCount} items)`;
                            } else {
                                // Reset to original total (need to store it or extract it) - for simplicity, we keep it as "found" when searching
                                // In paginated context, searching only applies to the CURRENT page.
                                countSpan.textContent = `(${loraCards.length} items on this page)`;
                            }
                        }
                    }
                });
            });
            
            searchInput.addEventListener('focus', () => {
                searchInput.style.borderColor = 'rgba(56, 189, 248, 1)';
                searchInput.style.boxShadow = '0 0 15px rgba(56, 189, 248, 0.3)';
            });
            searchInput.addEventListener('blur', () => {
                searchInput.style.borderColor = 'rgba(56, 189, 248, 0.4)';
                searchInput.style.boxShadow = '0 4px 15px rgba(0,0,0,0.05)';
            });
        });
    </script>
    '''

    # --- Read the base template ---
    # We use template.html to read the initial UI, but we'll create independent HTML files.
    with open('template.html', 'r', encoding='utf-8') as f:
        html_content = f.read()

    soup = BeautifulSoup(html_content, 'html.parser')
    
    # Fix CSS for the hover effect once
    style_tag = soup.find('style')
    if style_tag:
        css = style_tag.string
        if css and '.lora-card:hover .lora-card-img img' in css:
            import re
            css = re.sub(r'\.lora-card:hover \.lora-card-img img\s*\{\s*transform:\s*scale\(1\.05\);\s*\}', 
                         '.lora-card:hover .lora-card-img img { object-fit: contain; transform: scale(1); background-color: #000; }', css)
            style_tag.string = css

    # Generate Pages for each Category
    categories = list(items_by_category.keys())
    
    # Let's set the first category to be the new index.html (or redirect)
    # We will just generate index.html as a duplicate of the first category, or a redirect.
    # To keep the UI seamless, we'll let index.html be the first category's first page.
    default_cat = categories[0] if categories else None
    
    for cat, items in items_by_category.items():
        bg, border, text = colors.get(cat, ('#ffffff', '#ccc', '#333'))
        total_items_cat = len(items)
        total_pages = math.ceil(total_items_cat / items_per_page)
        
        for p in range(1, total_pages + 1):
            
            # --- Build Navigation for Current Page ---
            nav_html = f'''
                <div class="search-container" style="margin-bottom: 30px; margin-top: 10px;">
                    <div style="position: relative; max-width: 600px;">
                        <input type="text" id="loraSearchInput" placeholder="現在のページ内を検索... (例: lora名、サイズ)" 
                               style="width: 100%; padding: 15px 20px 15px 45px; border-radius: 30px; border: 2px solid rgba(58, 123, 213, 0.4); 
                                      background: rgba(255, 255, 255, 0.8); font-size: 1.1rem; outline: none; -webkit-backdrop-filter: blur(10px); backdrop-filter: blur(10px);
                                      box-shadow: 0 4px 15px rgba(58, 123, 213, 0.05); transition: all 0.3s ease; box-sizing: border-box;">
                        <i class="fas fa-search" style="position: absolute; left: 18px; top: 50%; transform: translateY(-50%); color: #3a7bd5; font-size: 1.2rem;"></i>
                    </div>
                </div>
            <div class="category-nav">\n'''
            
            # Add buttons for all categories
            for iter_cat in categories:
                iter_bg, iter_border, iter_text = colors.get(iter_cat, ('#ffffff', '#ccc', '#333'))
                # If it's the current category, highlight it or use active class conceptually
                target_url = f"{iter_cat}.html"
                
                # Dim the non-active categories slightly
                if iter_cat != cat:
                    bg_color = "rgba(255, 255, 255, 0.4)"
                    border_color = "rgba(255, 255, 255, 0.6)"
                    text_color = "#475569"
                    opacity_style = "opacity: 0.7; transition: all 0.3s;"
                else:
                    bg_color = iter_bg
                    border_color = iter_border
                    text_color = iter_text
                    opacity_style = "opacity: 1; filter: none; box-shadow: 0 4px 10px rgba(0,0,0,0.2); transform: translateY(-2px);"
                    
                nav_html += f'    <a href="{target_url}" style="background: {bg_color}; border-color: {border_color}; color: {text_color}; {opacity_style}"><i class="fas fa-cube"></i> {iter_cat} ({len(items_by_category[iter_cat])})</a>\n'
            
            nav_html += '</div>\n'
            
            # --- Get Items for Current Page ---
            start_idx = (p - 1) * items_per_page
            end_idx = start_idx + items_per_page
            page_items = items[start_idx:end_idx]
            
            # --- Build Main Content Section ---
            pagination_top = generate_pagination_html(cat, p, total_pages, total_items_cat)
            
            sections_html = f'''
            <div class="lora-section" id="{cat}">
                <h2 style="color: {border}; border-color: {border}; text-shadow: 0 0 10px rgba(0, 0, 0, 0.2);">
                    <i class="fas fa-layer-group"></i> {cat}
                    <span style="font-size:1.2rem;color:var(--text-muted); font-weight:normal; margin-left: 10px;">({len(page_items)} items on this page / Total {total_items_cat} items)</span>
                </h2>
                {pagination_top}
                <div class="lora-grid">
            '''
            
            sections_html += process_item_cards(page_items, cat, bg, border, text, seo_data)
            
            sections_html += '''
                </div>
            '''
            
            pagination_bottom = generate_pagination_html(cat, p, total_pages, total_items_cat)
            sections_html += pagination_bottom
            sections_html += "</div>\n"
            
            sections_html += script_html
            
            # --- Inject into Template Soup ---
            # We copy the soup to avoid mutating it across iterations
            import copy
            page_soup = copy.copy(soup)
            
            container = page_soup.find('div', class_='lora-container')
            if container:
                for nav in container.find_all('div', class_='category-nav'):
                    nav.decompose()
                for search in container.find_all('div', class_='search-container'):
                    search.decompose()
                for section in container.find_all('div', class_='lora-section'):
                    section.decompose()
                for script in container.find_all('script'):
                    # remove old inline scripts that might interfere
                    if script.string and 'loraSearchInput' in script.string:
                        script.decompose()
                    
                p_tag = container.find('p')
                if p_tag:
                    p_tag.clear()
                    p_tag.append(BeautifulSoup(f'対応モデルごとに分類されたLoRA一覧です。各カテゴリーを選択してください。全 <strong style="color: var(--primary-cyan); font-size: 1.3rem;">{total_items}</strong> ファイル。', 'html.parser'))
                    
                container.append(BeautifulSoup(nav_html, 'html.parser'))
                container.append(BeautifulSoup(sections_html, 'html.parser'))
            
            # Determine output filename
            if p == 1:
                out_filename = f"{cat}.html"
            else:
                out_filename = f"{cat}_{p}.html"
                
            out_filepath = os.path.join(os.path.dirname(os.path.abspath(__file__)), out_filename)
            
            html_out = str(page_soup).replace('{{ CATEGORY }}', cat)
            
            with open(out_filepath, 'w', encoding='utf-8') as f:
                f.write(html_out)
                
            print(f"Generated {out_filename} with {len(page_items)} items.")

    # Generate an index.html that immediately redirects to the first category
    if default_cat:
        index_filepath = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'index.html')
        redirect_html = f'''<!DOCTYPE html>
<html>
<head>
    <meta http-equiv="refresh" content="0; url={default_cat}.html">
    <title>Redirecting...</title>
</head>
<body>
    <p>Loading LoRA Categories... <a href="{default_cat}.html">Click here if not redirected.</a></p>
</body>
</html>'''
        with open(index_filepath, 'w', encoding='utf-8') as f:
            f.write(redirect_html)
        print(f"Generated index.html (redirects to {default_cat}.html)")

    print(f"Update complete! Total items processed: {total_items}")

if __name__ == '__main__':
    generate_html(r'K:\GoogleAI\output.csv', items_per_page=100, seo_csv=r'K:\GoogleAI\lora_seo_descriptions.csv')
