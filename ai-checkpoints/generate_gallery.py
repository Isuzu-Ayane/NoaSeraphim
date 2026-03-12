import os
import re
import glob

def get_lora_link(cat):
    cat_lower = cat.lower()
    if 'flux' in cat_lower: return '../ai-lora/Flux.html'
    if 'illustrious' in cat_lower or 'noobai' in cat_lower: return '../ai-lora/Illustrious.html'
    if 'pony' in cat_lower: return '../ai-lora/Pony.html'
    if 'sdxl' in cat_lower: return '../ai-lora/SDXL.html'
    if 'sd1.5' in cat_lower or 'sd 1.5' in cat_lower: return '../ai-lora/SD1.5.html'
    if 'wan' in cat_lower: return '../ai-lora/WanVideo.html'
    return '../ai-lora/index.html'

def parse_model_list(filepath):
    models = {}
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()

    blocks = content.split('------------------------------')
    for block in blocks:
        lines = block.strip().split('\n')
        if len(lines) >= 4:
            name, link, size, cat = "", "", "", ""
            for line in lines:
                if line.startswith('Model: '): name = line[7:].strip()
                elif line.startswith('Link: '): link = line[6:].strip()
                elif line.startswith('Size: '): size = line[6:].strip()
                elif line.startswith('Category: '): cat = line[10:].strip()

            base_name = re.sub(r'\.(safetensors|pt|ckpt)$', '', name, flags=re.IGNORECASE)
            
            # Use base_name as dict key, but also store lower version for fuzzy matching if needed
            models[base_name] = {
                'name': name,
                'link': link,
                'size': size,
                'category': cat,
                'base_name': base_name
            }
            models[base_name.lower()] = models[base_name]  # lowercase fallback
    return models

def generate_html():
    model_list_path = r'K:\GoogleAI\model_list.txt'
    image_dir = r'K:\GoogleAI\NoaSeraphim\ai-checkpoints\image_master'
    output_html = r'K:\GoogleAI\NoaSeraphim\ai-checkpoints\index.html'

    models_info = parse_model_list(model_list_path)

    # Read image files
    images = glob.glob(os.path.join(image_dir, '*.*'))

    # Build category dictionary
    # Checkpoints mapped by category
    categorized_checkpoints = {}

    for img_path in images:
        filename = os.path.basename(img_path)
        base_name = re.sub(r'\.(preview\.jpg|preview\.png|jpg|png|jpeg)$', '', filename, flags=re.IGNORECASE)

        info = models_info.get(base_name)
        if not info:
            info = models_info.get(base_name.lower())
        
        if not info:
            # Fallback if not found in list
            info = {
                'name': base_name,
                'link': '不明',
                'size': '不明',
                'category': 'Unknown',
                'base_name': base_name
            }

        cat = info['category']
        if cat not in categorized_checkpoints:
            categorized_checkpoints[cat] = []
        
        categorized_checkpoints[cat].append({
            'img_name': filename,
            'info': info
        })

    # Read the existing index.html up to the <main> or generate a fresh robust one
    
    html_template = """<!DOCTYPE html>
<html lang="ja">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Stable Diffusion Checkpoints Gallery | Noa Seraphim</title>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;600;800&display=swap" rel="stylesheet">
    <link href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css" rel="stylesheet" />
    <link rel="stylesheet" href="../styles.css">
    <style>
        :root {
            --bg-dark: #0f172a;
            --bg-card: #1e293b;
            --text-main: #f8fafc;
            --text-muted: #94a3b8;
            --accent: #38bdf8;
            --accent-glow: rgba(56, 189, 248, 0.4);
            --gradient: linear-gradient(135deg, #0284c7, #38bdf8);
        }
        body {
            margin: 0; padding: 0;
            font-family: 'Inter', system-ui, sans-serif;
            background-color: var(--bg-dark);
            color: var(--text-main);
            line-height: 1.6;
        }
        .container {
            max-width: 1000px;
            margin: 0 auto;
            padding: 0 20px;
        }
        .header-title {
            text-align: center;
            padding: 60px 20px 40px;
        }
        .header-title h1 {
            font-size: 2.8rem;
            margin-bottom: 10px;
            background: var(--gradient);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
        }
        
        /* Category Nav */
        .category-nav {
            display: grid;
            grid-template-columns: repeat(4, 1fr);
            gap: 15px;
            margin-bottom: 40px;
            padding: 24px;
            background: rgba(255, 255, 255, 0.05);
            border-radius: 12px;
            border: 1px solid rgba(255, 255, 255, 0.1);
        }
        .category-nav a {
            padding: 14px 20px;
            border-radius: 12px;
            background: rgba(56, 189, 248, 0.15);
            border: 1px solid rgba(56, 189, 248, 0.3);
            color: #3b82f6;
            font-size: 1.1rem;
            text-align: center;
            text-decoration: none;
            font-weight: 800;
            transition: all 0.2s;
        }
        .category-nav a:hover {
            background: rgba(56, 189, 248, 0.3);
        }

        /* Checkpoint Single Card Layout (Vertical) */
        .category-section {
            margin-bottom: 60px;
        }
        .category-section h2 {
            border-bottom: 2px solid var(--accent);
            padding-bottom: 10px;
            margin-bottom: 30px;
            font-size: 2rem;
            display: flex;
            align-items: center;
            gap: 10px;
        }
        .cp-list {
            display: flex;
            flex-direction: column;
            gap: 30px;
        }
        .cp-card {
            display: flex;
            background: rgba(0,0,0,0.4);
            border: 1px solid rgba(255,255,255,0.1);
            border-radius: 16px;
            overflow: hidden;
            transition: transform 0.2s, box-shadow 0.2s;
        }
        .cp-card:hover {
            transform: translateY(-3px);
            box-shadow: 0 10px 25px rgba(0,0,0,0.5);
            border-color: rgba(56, 189, 248, 0.4);
        }
        .cp-image {
            width: 350px;
            min-width: 350px;
            background: #111;
            display: flex;
            align-items: center;
            justify-content: center;
            overflow: hidden;
        }
        .cp-image img {
            width: 100%;
            height: 100%;
            object-fit: cover;
            cursor: pointer;
            transition: transform 0.4s;
        }
        .cp-card:hover .cp-image img {
            transform: scale(1.05);
        }
        .cp-info {
            padding: 25px;
            flex-grow: 1;
            display: flex;
            flex-direction: column;
        }
        .cp-title {
            font-size: 1.6rem;
            font-weight: 800;
            color: #3b82f6;
            text-shadow: 0 2px 6px rgba(0,0,0,0.8);
            margin: 0 0 15px 0;
            word-break: break-all;
        }
        .cp-detail {
            font-size: 1.05rem;
            color: var(--text-muted);
            margin: 4px 0;
            display: flex;
            align-items: center;
            gap: 8px;
        }
        .cp-detail strong {
            color: var(--text-main);
            min-width: 80px;
        }
        
        .cp-actions {
            margin-top: auto;
            padding-top: 20px;
            display: flex;
            flex-wrap: wrap;
            gap: 12px;
        }
        
        .btn {
            display: inline-flex;
            align-items: center;
            gap: 6px;
            padding: 10px 18px;
            border-radius: 8px;
            font-weight: bold;
            font-size: 0.95rem;
            text-decoration: none;
            transition: all 0.2s;
        }
        .btn-dl { background: linear-gradient(135deg, #10b981, #059669); color: white; }
        .btn-dl:hover { filter: brightness(1.2); box-shadow: 0 4px 12px rgba(16,185,129,0.3); }
        .btn-dl.disabled { background: #475569; pointer-events: none; opacity: 0.7; }
        
        .btn-google { background: linear-gradient(135deg, #3b82f6, #2563eb); color: white; }
        .btn-google:hover { filter: brightness(1.2); box-shadow: 0 4px 12px rgba(59,130,246,0.3); }

        .btn-lora { background: linear-gradient(135deg, #f43f5e, #be123c); color: white; }
        .btn-lora:hover { filter: brightness(1.2); box-shadow: 0 4px 12px rgba(244,63,94,0.3); }

        /* Modal styling */
        .modal {
            display: none; position: fixed; z-index: 1000;
            padding-top: 50px; left: 0; top: 0; width: 100%; height: 100%;
            overflow: auto; background-color: rgba(0, 0, 0, 0.9);
        }
        .modal-content {
            margin: auto; display: block; width: 80%; max-width: 1000px;
        }
        .modal-close {
            position: absolute; top: 15px; right: 35px; color: #f1f1f1;
            font-size: 40px; font-weight: bold; cursor: pointer;
        }
        
        @media (max-width: 768px) {
            .category-nav { grid-template-columns: repeat(2, 1fr); }
            .cp-card { flex-direction: column; }
            .cp-image { width: 100%; height: 300px; min-width: auto; }
        }
    </style>
</head>
<body>
    <div style="position: absolute; top: 20px; right: 20px; z-index: 1000;">
        <a href="../index.html" class="btn" style="background: rgba(255,255,255,0.1); border: 1px solid rgba(255,255,255,0.2);">
            <i class="fas fa-home"></i> Home
        </a>
    </div>

    <!-- Image Modal -->
    <div id="imageModal" class="modal">
        <span class="modal-close" id="modalClose">&times;</span>
        <img class="modal-content" id="modalImg">
    </div>

    <div class="header-title">
        <h1>Checkpoints Gallery</h1>
        <p style="color:var(--text-muted); font-size:1.1rem;">AI画像生成モデル（Checkpoints）の出力サンプルと分類情報</p>
    </div>

    <main class="container">
        <!-- Category Nav -->
"""
    
    # Sort categories
    categories = sorted(categorized_checkpoints.keys())
    nav_html = '<div class="category-nav">\n'
    for c in categories:
        nav_html += f'<a href="#{c}">{c} ({len(categorized_checkpoints[c])})</a>\n'
    nav_html += '</div>\n\n'
    
    html_template += nav_html

    sections_html = ""
    for cat in categories:
        items = categorized_checkpoints[cat]
        sections_html += f'<div class="category-section" id="{cat}">\n'
        sections_html += f'  <h2><i class="fas fa-cube"></i> {cat}</h2>\n'
        sections_html += f'  <div class="cp-list">\n'
        
        # sort items by base_name
        items.sort(key=lambda x: x['info']['base_name'].lower())
        
        for item in items:
            info = item['info']
            img_path = f"./image_master/{item['img_name']}"
            
            g_search = f"https://www.google.com/search?q={info['base_name']}+civitai"
            lora_link = get_lora_link(cat)
            
            link_btn = f'<a href="{info["link"]}" target="_blank" class="btn btn-dl"><i class="fas fa-download"></i> ダウンロード元</a>'
            if info["link"] == '不明' or not info["link"]:
                link_btn = f'<span class="btn btn-dl disabled"><i class="fas fa-unlink"></i> リンク不明</span>'
                
            sections_html += f'''
            <div class="cp-card">
                <div class="cp-image">
                    <img src="{img_path}" alt="{info['name']}" onclick="openModal(this.src)">
                </div>
                <div class="cp-info">
                    <div class="cp-title">{info['base_name']}</div>
                    <div class="cp-detail"><strong><i class="fas fa-tag"></i> ジャンル:</strong> {cat}</div>
                    <div class="cp-detail"><strong><i class="fas fa-hdd"></i> 容量:</strong> {info['size']}</div>
                    <div class="cp-detail"><strong><i class="fas fa-file"></i> ファイル:</strong> {info['name']}</div>
                    
                    <div class="cp-actions">
                        {link_btn}
                        <a href="{g_search}" target="_blank" class="btn btn-google"><i class="fab fa-google"></i> Google検索</a>
                        <a href="{lora_link}" class="btn btn-lora"><i class="fas fa-magic"></i> 対応LoRA一覧へ</a>
                    </div>
                </div>
            </div>
            '''
            
        sections_html += '  </div>\n</div>\n\n'
        
    html_template += sections_html

    html_template += """
    </main>
    
    <script>
        function openModal(src) {
            document.getElementById('imageModal').style.display = 'block';
            document.getElementById('modalImg').src = src;
        }
        document.getElementById('modalClose').onclick = function() {
            document.getElementById('imageModal').style.display = 'none';
        }
        window.onclick = function(e) {
            if (e.target == document.getElementById('imageModal')) {
                document.getElementById('imageModal').style.display = 'none';
            }
        }
    </script>
</body>
</html>
"""

    with open(output_html, 'w', encoding='utf-8') as f:
        f.write(html_template)
        
    print(f"Generated successfully to {output_html}")


if __name__ == '__main__':
    generate_html()
