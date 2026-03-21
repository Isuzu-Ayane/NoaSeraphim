import os
import re
import shutil

html_path_ja = r'K:\GoogleAI\NoaSeraphim\models\ai-checkpoints\index.html'
html_path_en = r'K:\GoogleAI\NoaSeraphim\models\ai-checkpoints\index_en.html'
new_img_dir = r'K:\GoogleAI\tool\image\image_master_1'
dest_img_dir = r'K:\GoogleAI\NoaSeraphim\models\ai-checkpoints\image_master'

with open(html_path_ja, "r", encoding="utf-8") as f:
    html_content_ja = f.read()
    
# Find existing images
existing_imgs = re.findall(r'<img src="\./image_master/([^"]+)"', html_content_ja)
existing_imgs_set = set(existing_imgs)

new_imgs_to_add = []
for file in os.listdir(new_img_dir):
    if (file.endswith('.jpg') or file.endswith('.png')) and file not in existing_imgs_set:
        new_imgs_to_add.append(file)

print(f"Adding {len(new_imgs_to_add)} new images...")

def generate_card(file, is_en=False):
    title = file.replace('.preview.jpg', '').replace('.preview.png', '')
    safetensors_file = title + '.safetensors'
    src_path = os.path.join(new_img_dir, file)
    size_bytes = os.path.getsize(src_path)
    
    # Description based on language
    if is_en:
        desc = f"Newly added Stable Diffusion model '{title}'. Generates high-quality AI images safely. Perfect for exploring different art styles and verifying rendering performance."
    else:
        desc = f"新しく追加されたモデル「{title}」。AI画像生成において、安定した高品質なイメージを出力します。様々な画風の探求や表現力の検証に最適です。"
        
    return f'''
            <div class="cp-card">
                <div class="cp-image">
                    <img src="./image_master/{file}" alt="{safetensors_file}" onclick="openModal(this.src)">
                </div>
                <div class="cp-info">
                    <div class="cp-title">{title}</div>
                    <div class="cp-detail"><strong><i class="fas fa-tag"></i> ジャンル:</strong> Unknown</div>
                    <div class="cp-detail"><strong><i class="fas fa-hdd"></i> 容量:</strong> {size_bytes:,} bytes</div>
                    <div class="cp-detail"><strong><i class="fas fa-file"></i> ファイル:</strong> {safetensors_file}</div>
                    
                    <div class="cp-description">
                        {desc}
                    </div>
                    
                    <div class="cp-actions">
                        <a href="https://civitai.com/search/models?query={title}" target="_blank" class="btn btn-dl"><i class="fas fa-download"></i> ダウンロード元</a>
                        <a href="https://www.google.com/search?q={title}+civitai" target="_blank" class="btn btn-google"><i class="fab fa-google"></i> Google検索</a>
                        <a href="../../models/ai-lora/index.html" class="btn btn-lora"><i class="fas fa-magic"></i> 対応LoRA一覧へ</a>
                    </div>
                </div>
            </div>
'''

new_cards_ja = []
new_cards_en = []

for file in new_imgs_to_add:
    # Copy file over
    shutil.copy2(os.path.join(new_img_dir, file), os.path.join(dest_img_dir, file))
    
    new_cards_ja.append(generate_card(file, False))
    new_cards_en.append(generate_card(file, True))

# Insert into HTML right before the ending </div> of Unknown category
def insert_into_html(html_path, cards, count_to_add):
    with open(html_path, "r", encoding="utf-8") as f:
        content = f.read()
        
    # Find Unknown section
    marker = r'(<div class="category-section" id="Unknown">.*?<div class="cp-list">)(.*?)(</div>\s*</div>)'
    match = re.search(marker, content, re.DOTALL)
    if not match:
        print(f"Error: Could not find Unknown section in {html_path}")
        return
        
    before = match.group(1)
    middle = match.group(2)
    after = match.group(3)
    
    # Append new cards inside the cp-list
    middle_new = middle + "".join(cards)
    
    new_content = content[:match.start()] + before + middle_new + after + content[match.end():]
    
    # Update Unknown count in nav: <a href="#Unknown">Unknown (52)</a>
    def replace_nav_count(m):
        old_count = int(m.group(1))
        return f'<a href="#Unknown">Unknown ({old_count + count_to_add})</a>'
    new_content = re.sub(r'<a href="#Unknown">Unknown \((\d+)\)</a>', replace_nav_count, new_content)
    
    # Update Unknown count in table: Unknown / Other (53)
    def replace_table_count(m):
        old_count = int(m.group(1))
        return f'Unknown / Other ({old_count + count_to_add})'
    new_content = re.sub(r'Unknown / Other \((\d+)\)', replace_table_count, new_content)
    
    with open(html_path, "w", encoding="utf-8") as f:
        f.write(new_content)
        
insert_into_html(html_path_ja, new_cards_ja, len(new_imgs_to_add))
insert_into_html(html_path_en, new_cards_en, len(new_imgs_to_add))

print("Successfully updated both index.html and index_en.html files.")
