import os
import re
import csv
import json
import bs4
from collections import defaultdict

csv_path = r'K:\GoogleAI\tool\data\checkpoint_data.csv'
base_dir = r'K:\GoogleAI\NoaSeraphim\models\ai-checkpoints'
html_ja_path = os.path.join(base_dir, 'index.html')
html_en_path = os.path.join(base_dir, 'index_en.html')
gallery_data_path = os.path.join(base_dir, 'gallery_data.js')
pages_dir = os.path.join(base_dir, 'pages')

if not os.path.exists(pages_dir):
    os.makedirs(pages_dir)

# 1. Parse CSV
counts = {}
models_by_category = defaultdict(list)
models_flat = []

with open(csv_path, 'r', encoding='utf-8-sig') as f:
    lines = f.readlines()

parsing_counts = False
parsing_models = False

for line in lines:
    line = line.strip()
    if not line: continue
    
    if line.startswith('■ カテゴリ別モデル件数'):
        parsing_counts = True
        parsing_models = False
        continue
    elif line.startswith('■ モデル詳細リスト'):
        parsing_counts = False
        parsing_models = True
        continue
        
    if parsing_counts:
        if line.startswith('カテゴリ'): continue
        parts = line.split(',')
        if len(parts) >= 2:
            cat = parts[0].strip()
            num_str = parts[1].strip().replace('件', '')
            try:
                counts[cat] = int(num_str)
            except:
                pass

    elif parsing_models:
        if line.startswith('ファイル名'): continue
        
        import io
        reader = csv.reader(io.StringIO(line))
        try:
            parts = next(reader)
        except StopIteration:
            continue
            
        if len(parts) >= 4:
            file_name = parts[0].strip()
            cat = parts[1].strip()
            size = parts[2].strip()
            url = parts[3].strip()
            
            if 'bytes' not in size:
                size = size + ' bytes'
                
            model_info = {
                'file_name': file_name,
                'category': cat,
                'size': size,
                'url': url
            }
            models_by_category[cat].append(model_info)
            models_flat.append(model_info)

# 2. Extract existing descriptions from pages/*.html
descriptions = {}
for f in os.listdir(pages_dir):
    if f.endswith('.html'):
        p = os.path.join(pages_dir, f)
        with open(p, 'r', encoding='utf-8') as file:
            soup = bs4.BeautifulSoup(file, 'html.parser')
            title_el = soup.find("div", class_="cp-title")
            desc_el = soup.find("div", class_="cp-description")
            if title_el and desc_el:
                title = title_el.get_text(strip=True)
                desc = desc_el.decode_contents().strip()
                descriptions[title] = desc

# 3. Read index_backup.html to use as a template (since index.html is modified)
# If index_backup.html doesn't exist, we fallback to index.html and hope it has the structure 
# But wait, index.html now has a grid structure. The template for pages should have the head and styles.
# We generated individual pages already, so we can just use the first page as a base template.
template_page_path = os.path.join(pages_dir, os.listdir(pages_dir)[0])
with open(template_page_path, 'r', encoding='utf-8') as f:
    template_soup = bs4.BeautifulSoup(f, 'html.parser')
    
# clear main container
t_main = template_soup.find("main", class_="container")
if t_main:
    t_main.clear()

# 4. Generate individual pages and grid items
def safe_title_fn(t):
    safet = "".join([c for c in t if c.isalpha() or c.isdigit() or c in (' ', '-', '_')]).replace(' ', '_')
    return safet if safet else "model_" + str(hash(t))

grid_sections_html = []
grid_sections_html.append('<div class="category-nav">')
for cat in sorted(counts.keys()):
    grid_sections_html.append(f'<a href="#{cat}">{cat} ({counts[cat]})</a>')
grid_sections_html.append('</div>\n')

for cat in sorted(models_by_category.keys()):
    grid_sections_html.append(f'<div class="category-section" id="{cat}">')
    grid_sections_html.append(f'  <h2><i class="fas fa-cube"></i> {cat}</h2>')
    grid_sections_html.append('  <div class="model-grid">')
    
    for m in models_by_category[cat]:
        f_name = m['file_name']
        title = f_name.replace('.safetensors', '').replace('.pt', '')
        size = m['size']
        url = m['url']
        safe_t = safe_title_fn(title)
        page_name = f"{safe_t}.html"
        page_path = os.path.join(pages_dir, page_name)
        
        preview_img = title + '.preview.jpg'
        if os.path.exists(os.path.join(base_dir, 'image_master', title + '.preview.png')):
            preview_img = title + '.preview.png'
            
        desc = descriptions.get(title)
        if not desc:
            desc = f"新しく追加されたモデル「{title}」。AI画像生成において、安定した高品質なイメージを出力します。様々な画風の探求や表現力の検証に最適です。"
            
        # Write individual page
        indiv_soup = bs4.BeautifulSoup(str(template_soup), 'html.parser')
        i_main = indiv_soup.find("main", class_="container")
        
        # update breadcrumb
        bcrumb = indiv_soup.find('nav', {'aria-label': 'breadcrumb'})
        if bcrumb:
            ol = bcrumb.find('ol')
            if ol:
                li_cur = ol.find('li', {'aria-current': 'page'})
                if li_cur:
                    li_cur.string = title
        
        page_h2 = indiv_soup.new_tag("h2", style="margin-top:0;")
        page_h2.string = title
        i_main.append(page_h2)
        
        link_html = ''
        if url and url != 'URL不明':
            link_html = f'<a href="{url}" target="_blank" class="btn btn-dl"><i class="fas fa-download"></i> ダウンロード元</a>'
        else:
            link_html = f'<span style="color:var(--text-muted);">リンク不明</span>'
            
        card_html = f'''
        <div class="cp-card-single">
            <div class="cp-image">
                <img src="../image_master/{preview_img}" alt="{f_name}" onclick="openModal(this.src)" onerror="this.onerror=null; this.src='../../../web_image/no_image.jpg';">
            </div>
            <div class="cp-info">
                <div class="cp-title">{title}</div>
                <div class="cp-detail"><strong><i class="fas fa-tag"></i> ジャンル:</strong> {cat}</div>
                <div class="cp-detail"><strong><i class="fas fa-hdd"></i> 容量:</strong> {size}</div>
                <div class="cp-detail"><strong><i class="fas fa-file"></i> ファイル:</strong> {f_name}</div>
                
                <div class="cp-description">
                    {desc}
                </div>
                
                <div class="cp-actions">
                    {link_html}
                    <a href="https://www.google.com/search?q={title}+civitai" target="_blank" class="btn btn-google"><i class="fab fa-google"></i> Google検索</a>
                    <a href="../../../models/ai-lora/index.html" class="btn btn-lora"><i class="fas fa-magic"></i> 対応LoRA一覧へ</a>
                </div>
            </div>
        </div>'''
        
        card_soup = bs4.BeautifulSoup(card_html, 'html.parser')
        i_main.append(card_soup)
        
        with open(page_path, 'w', encoding='utf-8') as pf:
            pf.write(str(indiv_soup))
            
        # Add to portal grid
        grid_html = f'''
        <a href="pages/{page_name}" class="model-grid-item">
            <img src="./image_master/{preview_img}" class="model-grid-image" onerror="this.onerror=null; this.src='../../web_image/no_image.jpg';">
            <div class="model-grid-info">
                <div class="model-grid-title">{title}</div>
                <div class="model-grid-size">{size}</div>
            </div>
        </a>'''
        grid_sections_html.append(grid_html)
        
    grid_sections_html.append('  </div>\n</div>\n')

# 5. Read index.html and replace main content
with open(html_ja_path, 'r', encoding='utf-8') as f:
    ja_html = f.read()

# We need to replace everything inside <main class="container"> after <div style="background... About Checkpoint Tests... Model Types & Features
# Or simply use string replacement since the structure is somewhat known.
# Actually, the best way to replace body is to find <div class="category-nav"> and replace from there to </main>
# But wait, we previously just replaced from <!-- Category Nav --> to </main>. 
# Let's search for '<div class="category-nav">' to the end.
sep_nav = '<div class="category-nav">'
if sep_nav in ja_html:
    parts = ja_html.split(sep_nav)
    head_part = parts[0]
    # tail is just </main>...
    tail_part = '\n</main>\n' + '\n</main>\n'.join(ja_html.split('</main>')[1:])
else:
    print("Could not find <div class=\"category-nav\"> in index.html, skipping update of main page body.")
    head_part = ja_html
    tail_part = ""

# Build top table counts regex replacement (Same as old update_from_csv.py)
def replace_top_table_count(html_content, cat_name_in_html, count_key):
    if count_key in counts:
        c = counts[count_key]
        html_content = re.sub(rf'({cat_name_in_html}) \(\d+\)', rf'\1 ({c})', html_content)
    return html_content

head_part = replace_top_table_count(head_part, 'Illustrious', 'Illustrious_Checkpoint')
head_part = replace_top_table_count(head_part, 'NoobAI', 'NoobAI_Checkpoint')
head_part = replace_top_table_count(head_part, 'Flux.1 D', 'Flux.1 D_Checkpoint')
head_part = replace_top_table_count(head_part, 'Anima', 'Anima_Checkpoint')
head_part = replace_top_table_count(head_part, 'Pony', 'Pony_Checkpoint')
head_part = replace_top_table_count(head_part, 'SDXL 1.0', 'SDXL 1.0_Checkpoint')

c_flux_other = counts.get('Flux.1 Kontext_Checkpoint', 0) + counts.get('Flux.1 Krea_Checkpoint', 0) + counts.get('Flux.1 S_Checkpoint', 0)
if c_flux_other > 0:
    head_part = re.sub(r'Flux.1 Kontext / Krea / S \(\d+\)', f'Flux.1 Kontext / Krea / S ({c_flux_other})', head_part)

c_sd15 = counts.get('SD 1.5_Checkpoint', 0) + counts.get('SD 1.5 Hyper_Checkpoint', 0)
if c_sd15 > 0:
    head_part = re.sub(r'SD 1\.5 / Hyper \(\d+\)', f'SD 1.5 / Hyper ({c_sd15})', head_part)

c_z = counts.get('ZImageBase_Checkpoint', 0) + counts.get('ZImageTurbo_Checkpoint', 0)
if c_z > 0:
    head_part = re.sub(r'ZImageBase / Turbo \(\d+\)', f'ZImageBase / Turbo ({c_z})', head_part)

c_unknown_total = (counts.get('Unknown_Models', 0) + counts.get('Other_Checkpoint', 0) + 
                   counts.get('Illustrious_LORA', 0) + counts.get('SDXL Lightning_Checkpoint', 0) +
                   counts.get('Wan Video 1.3B t2v_Checkpoint', 0) + counts.get('Wan Video 14B i2v 720p_Checkpoint', 0) +
                   counts.get('Wan Video 14B t2v_Checkpoint', 0) + counts.get('Wan Video 2.2 I2V-A14B_Checkpoint', 0) +
                   counts.get('Wan Video 2.2 TI2V-5B_Checkpoint', 0) + counts.get('Flux.2 Klein 4B_Checkpoint', 0) +
                   counts.get('Flux.2 Klein 9B-base_Checkpoint', 0))

if c_unknown_total > 0:
    head_part = re.sub(r'Unknown / Other \(\d+\)', f'Unknown / Other ({c_unknown_total})', head_part)

if tail_part:
    with open(html_ja_path, 'w', encoding='utf-8') as f:
        f.write(head_part + '\n'.join(grid_sections_html) + tail_part)

# 6. Update English page counts
with open(html_en_path, 'r', encoding='utf-8') as f:
    en_content = f.read()

en_content = replace_top_table_count(en_content, 'Illustrious', 'Illustrious_Checkpoint')
en_content = replace_top_table_count(en_content, 'NoobAI', 'NoobAI_Checkpoint')
en_content = replace_top_table_count(en_content, 'Flux.1 D', 'Flux.1 D_Checkpoint')
en_content = replace_top_table_count(en_content, 'Anima', 'Anima_Checkpoint')
en_content = replace_top_table_count(en_content, 'Pony', 'Pony_Checkpoint')
en_content = replace_top_table_count(en_content, 'SDXL 1.0', 'SDXL 1.0_Checkpoint')
if c_flux_other > 0: en_content = re.sub(r'Flux.1 Kontext / Krea / S \(\d+\)', f'Flux.1 Kontext / Krea / S ({c_flux_other})', en_content)
if c_sd15 > 0: en_content = re.sub(r'SD 1\.5 / Hyper \(\d+\)', f'SD 1.5 / Hyper ({c_sd15})', en_content)
if c_z > 0: en_content = re.sub(r'ZImageBase / Turbo \(\d+\)', f'ZImageBase / Turbo ({c_z})', en_content)
if c_unknown_total > 0: en_content = re.sub(r'Unknown / Other \(\d+\)', f'Unknown / Other ({c_unknown_total})', en_content)

with open(html_en_path, 'w', encoding='utf-8') as f:
    f.write(en_content)

# 7. Update gallery_data.js
with open(gallery_data_path, 'r', encoding='utf-8') as f:
    gallery_raw = f.read()

gallery_json_str = re.search(r'const checkpointData = (\[.*\]);', gallery_raw, re.DOTALL)
if gallery_json_str:
    try:
        gallery_data = json.loads(gallery_json_str.group(1))
    except:
        gallery_data = []
else:
    gallery_data = []

existing_names = {x['name']: x for x in gallery_data}
new_gallery_data = []

for m in models_flat:
    name = m['file_name'].replace('.safetensors', '').replace('.pt', '')
    url = m['url'] if m['url'] and m['url'] != 'URL不明' else '不明'
    
    if name in existing_names:
        new_gallery_data.append({
            "name": name,
            "files": existing_names[name].get("files", []),
            "url": url
        })
    else:
        new_gallery_data.append({
            "name": name,
            "files": [],
            "url": url
        })

js_content = f"const checkpointData = {json.dumps(new_gallery_data, separators=(',', ':'))};\n"
with open(gallery_data_path, 'w', encoding='utf-8') as f:
    f.write(js_content)

print(f"Updated successfully! Processed {len(models_flat)} models.")
