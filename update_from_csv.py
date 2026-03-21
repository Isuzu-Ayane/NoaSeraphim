import os
import re
import csv
from collections import defaultdict

csv_path = r'K:\GoogleAI\tool\data\checkpoint_data.csv'
html_ja_path = r'K:\GoogleAI\NoaSeraphim\models\ai-checkpoints\index.html'
html_en_path = r'K:\GoogleAI\NoaSeraphim\models\ai-checkpoints\index_en.html'
gallery_data_path = r'K:\GoogleAI\NoaSeraphim\models\ai-checkpoints\gallery_data.js'

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
        
        # handle quotes in size
        # e.g. animaCatTower_v02.safetensors,Anima_Checkpoint,"4,182,219,262 bytes",https://civitai.com/...
        # We can use the csv module to parse this line properly
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
            
            # format size to match HTML if needed, it contains bytes
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

# 2. Extract existing descriptions from index.html
with open(html_ja_path, 'r', encoding='utf-8') as f:
    html_ja_content = f.read()

descriptions = {}
# Regex to find cards and extract their file and description
card_pattern = re.compile(r'<div class="cp-card">(.*?)</div>\s*</div>', re.DOTALL)
for card_match in card_pattern.finditer(html_ja_content):
    card_html = card_match.group(1)
    file_match = re.search(r'<strong><i class="fas fa-file"></i> ファイル:</strong>\s*(.*?\.safetensors)', card_html)
    desc_match = re.search(r'<div class="cp-description">(.*?)</div>', card_html, re.DOTALL)
    if file_match and desc_match:
        f_name = file_match.group(1).strip()
        desc = desc_match.group(1).strip()
        descriptions[f_name] = desc

# Generate New HTML for Categories
def generate_cards_html(category, models):
    sections = []
    sections.append(f'<div class="category-section" id="{category}">')
    sections.append(f'  <h2><i class="fas fa-cube"></i> {category}</h2>')
    sections.append('  <div class="cp-list">')
    
    for m in models:
        f_name = m['file_name']
        title = f_name.replace('.safetensors', '').replace('.pt', '')
        size = m['size']
        url = m['url']
        preview_img = title + '.preview.jpg'
        
        # check if .png exists instead, defaulting to jpg
        if os.path.exists(rf'K:\GoogleAI\NoaSeraphim\models\ai-checkpoints\image_master\{title}.preview.png'):
            preview_img = title + '.preview.png'
            
        desc = descriptions.get(f_name)
        if not desc:
            desc = f"新しく追加されたモデル「{title}」。AI画像生成において、安定した高品質なイメージを出力します。様々な画風の探求や表現力の検証に最適です。"
            
        link_html = ''
        if url and url != 'URL不明':
            link_html = f'<a href="{url}" target="_blank" class="btn btn-dl"><i class="fas fa-download"></i> ダウンロード元</a>'
        else:
            link_html = f'<a href="https://civitai.com/search/models?query={title}" target="_blank" class="btn btn-dl"><i class="fas fa-download"></i> ダウンロード元</a>'
            
        card_html = f'''
            <div class="cp-card">
                <div class="cp-image">
                    <img src="./image_master/{preview_img}" alt="{f_name}" onclick="openModal(this.src)" onerror="this.onerror=null; this.src='../../web_image/no_image.jpg';">
                </div>
                <div class="cp-info">
                    <div class="cp-title">{title}</div>
                    <div class="cp-detail"><strong><i class="fas fa-tag"></i> ジャンル:</strong> {category}</div>
                    <div class="cp-detail"><strong><i class="fas fa-hdd"></i> 容量:</strong> {size}</div>
                    <div class="cp-detail"><strong><i class="fas fa-file"></i> ファイル:</strong> {f_name}</div>
                    
                    <div class="cp-description">
                        {desc}
                    </div>
                    
                    <div class="cp-actions">
                        {link_html}
                        <a href="https://www.google.com/search?q={title}+civitai" target="_blank" class="btn btn-google"><i class="fab fa-google"></i> Google検索</a>
                        <a href="../../models/ai-lora/index.html" class="btn btn-lora"><i class="fas fa-magic"></i> 対応LoRA一覧へ</a>
                    </div>
                </div>
            </div>'''
        sections.append(card_html)
        
    sections.append('  </div>\n</div>\n')
    return '\n'.join(sections)

def build_category_nav(counts):
    nav = ['<div class="category-nav">']
    for cat in sorted(counts.keys()):
        nav.append(f'<a href="#{cat}">{cat} ({counts[cat]})</a>')
    nav.append('</div>')
    return '\n'.join(nav)

# Read index.html again to replace parts
section_marker_start = '<!-- Category Nav -->'
section_marker_end = '</main>'

parts = html_ja_content.split(section_marker_start)
head_part = parts[0]
tail_part = parts[1].split(section_marker_end)[1]

# Rebuild body part
body_part = section_marker_start + '\n' + build_category_nav(counts) + '\n\n'
for cat in sorted(models_by_category.keys()):
    body_part += generate_cards_html(cat, models_by_category[cat])

# Build top table counts regex replacement
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

# Flux.1 Kontext / Krea / S
c_kontext = counts.get('Flux.1 Kontext_Checkpoint', 0)
c_krea = counts.get('Flux.1 Krea_Checkpoint', 0)
c_s = counts.get('Flux.1 S_Checkpoint', 0)
c_flux_other = c_kontext + c_krea + c_s
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
# Also handling English version Unmeasurable
head_part_en = head_part # wait, head_part is currently from index.html!

with open(html_ja_path, 'w', encoding='utf-8') as f:
    f.write(head_part + body_part + '\n</main>\n' + tail_part)

# Do English
with open(html_en_path, 'r', encoding='utf-8') as f:
    html_en_content = f.read()

en_head_part = replace_top_table_count(html_en_content, 'Illustrious', 'Illustrious_Checkpoint')
en_head_part = replace_top_table_count(en_head_part, 'NoobAI', 'NoobAI_Checkpoint')
en_head_part = replace_top_table_count(en_head_part, 'Flux.1 D', 'Flux.1 D_Checkpoint')
en_head_part = replace_top_table_count(en_head_part, 'Anima', 'Anima_Checkpoint')
en_head_part = replace_top_table_count(en_head_part, 'Pony', 'Pony_Checkpoint')
en_head_part = replace_top_table_count(en_head_part, 'SDXL 1.0', 'SDXL 1.0_Checkpoint')

if c_flux_other > 0:
    en_head_part = re.sub(r'Flux.1 Kontext / Krea / S \(\d+\)', f'Flux.1 Kontext / Krea / S ({c_flux_other})', en_head_part)
if c_sd15 > 0:
    en_head_part = re.sub(r'SD 1\.5 / Hyper \(\d+\)', f'SD 1.5 / Hyper ({c_sd15})', en_head_part)
if c_z > 0:
    en_head_part = re.sub(r'ZImageBase / Turbo \(\d+\)', f'ZImageBase / Turbo ({c_z})', en_head_part)
if c_unknown_total > 0:
    en_head_part = re.sub(r'Unknown / Other \(\d+\)', f'Unknown / Other ({c_unknown_total})', en_head_part)

with open(html_en_path, 'w', encoding='utf-8') as f:
    f.write(en_head_part)

print("Successfully written main HTML files.")

# Generate gallery_data.js for _en page
import json
with open(gallery_data_path, 'r', encoding='utf-8') as f:
    gallery_raw = f.read()
    
# parse JSON safely if it's assigned to variable
gallery_json_str = re.search(r'const checkpointData = (\[.*\]);', gallery_raw, re.DOTALL)
if gallery_json_str:
    try:
        gallery_data = json.loads(gallery_json_str.group(1))
    except:
        gallery_data = []
else:
    gallery_data = []

# Update gallery data with new models
# For models that don't have files listed, create generic
existing_names = {x['name']: x for x in gallery_data}
new_gallery_data = []

for m in models_flat:
    name = m['file_name'].replace('.safetensors', '').replace('.pt', '')
    url = m['url'] if m['url'] and m['url'] != 'URL不明' else '不明'
    
    if name in existing_names:
        # preserve their files array
        new_gallery_data.append({
            "name": name,
            "files": existing_names[name]["files"],
            "url": url
        })
    else:
        # no images for new ones right now besides preview, but English page looks for creative/NoaSeraphim_AI/image/checkpoints/{name}/...
        # so we leave files empty for now, user can add them later
        new_gallery_data.append({
            "name": name,
            "files": [],
            "url": url
        })

js_content = f"const checkpointData = {json.dumps(new_gallery_data, separators=(',', ':'))};\n"
with open(gallery_data_path, 'w', encoding='utf-8') as f:
    f.write(js_content)

print(f"Updated gallery_data.js with {len(new_gallery_data)} models.")
