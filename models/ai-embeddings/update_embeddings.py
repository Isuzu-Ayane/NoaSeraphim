import csv
import os
import re

# Paths
CSV_PATH = r'K:\GoogleAI\embeddings_effects.csv'
BASE_DIR = r'k:\GoogleAI\NoaSeraphim\models\ai-embeddings'
PAGES_DIR = os.path.join(BASE_DIR, 'pages')

# Category mapping
CATEGORY_MAP = {
    'SD 1.5': 'sd15',
    'SDXL 1.0': 'sdxl',
    'Pony': 'pony',
    'Illustrious': 'illustrious',
    'SD 1.4': 'sd15',
    'SD 2.1 768': 'others',
    'SD 2.1': 'others',
    'SD 2.0 768': 'others',
    'Other': 'others',
    'ZImageTurbo': 'others'
}

FRIENDLY_NAMES = {
    'sd15': 'Stable Diffusion 1.5',
    'sdxl': 'SDXL 1.0',
    'pony': 'Pony Diffusion',
    'illustrious': 'Illustrious XL',
    'others': 'Other Models (SD 1.4 / 2.x)'
}

HTML_TEMPLATE = """<!DOCTYPE html>
<html lang="ja">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{title} - Embeddings List | Noa AI Labs</title>
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
    <link href="https://fonts.googleapis.com/css2?family=M+PLUS+Rounded+1c:wght@300;400;700&family=Nunito:wght@400;800&family=Inter:wght@400;700;900&display=swap" rel="stylesheet">
    <link rel="stylesheet" href="../../styles.css">
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">
    <style>
        :root {{
            --primary-cyan: #3a7bd5;
            --secondary-cyan: #00d2ff;
            --accent-blue: #0284c7;
            --bg-light: #e0f2fe;
            --bg-card: rgba(255, 255, 255, 0.7);
            --text-dark: #0f172a;
            --text-muted: #475569;
        }}

        body {{
            margin: 0;
            padding: 0;
            font-family: 'Inter', 'Nunito', sans-serif;
            background: linear-gradient(135deg, #e0f2fe 0%, #bae6fd 100%);
            color: var(--text-dark);
            background-attachment: fixed;
            min-height: 100vh;
            position: relative;
            overflow-x: hidden;
        }}

        /* Decorative Background Illustration */
        body::before {{
            content: "";
            position: fixed;
            bottom: -5%;
            right: -5%;
            width: 40%;
            height: 60%;
            background-image: url('../../../web_image/image_00001_.png');
            background-repeat: no-repeat;
            background-size: contain;
            background-position: bottom right;
            opacity: 0.15;
            pointer-events: none;
            z-index: -1;
        }}

        body::after {{
            content: "";
            position: fixed;
            top: 10%;
            left: -5%;
            width: 30%;
            height: 50%;
            background-image: url('../../../web_image/image_00002_.png');
            background-repeat: no-repeat;
            background-size: contain;
            background-position: top left;
            opacity: 0.1;
            pointer-events: none;
            z-index: -1;
            filter: scaleX(-1);
        }}

        .container {{
            max-width: 1200px;
            margin: 40px auto;
            padding: 0 20px;
            position: relative;
            z-index: 2;
        }}

        .header-panel {{
            background: var(--bg-card);
            backdrop-filter: blur(10px);
            padding: 40px;
            border-radius: 30px;
            border: 3px solid white;
            text-align: center;
            margin-bottom: 30px;
            box-shadow: 0 10px 30px rgba(58, 123, 213, 0.15);
        }}

        h1 {{
            font-size: 2.5rem;
            font-weight: 900;
            margin-bottom: 10px;
            background: linear-gradient(135deg, var(--primary-cyan), var(--secondary-cyan));
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            font-family: 'M PLUS Rounded 1c', sans-serif;
        }}

        .breadcrumb {{
            display: flex;
            justify-content: center;
            list-style: none;
            padding: 0;
            gap: 10px;
            font-size: 0.9rem;
            margin-bottom: 20px;
        }}

        .breadcrumb a {{ color: var(--accent-blue); text-decoration: none; font-weight: bold; }}
        .breadcrumb li::after {{ content: '>'; margin-left: 10px; color: var(--text-muted); }}
        .breadcrumb li:last-child::after {{ content: ''; }}

        .nav-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(130px, 1fr));
            gap: 10px;
            margin-bottom: 30px;
        }}

        .nav-item {{
            background: rgba(255,255,255,0.6);
            padding: 12px;
            border-radius: 15px;
            text-decoration: none;
            color: var(--accent-blue);
            font-weight: 800;
            text-align: center;
            transition: all 0.3s;
            border: 2px solid white;
            font-size: 0.9rem;
        }}

        .nav-item:hover, .nav-item.active {{
            background: var(--primary-cyan);
            color: white;
            transform: translateY(-2px);
            box-shadow: 0 5px 15px rgba(58, 123, 213, 0.3);
        }}

        .table-container {{
            background: var(--bg-card);
            backdrop-filter: blur(10px);
            border-radius: 30px;
            border: 3px solid white;
            overflow: hidden;
            box-shadow: 0 10px 30px rgba(0,0,0,0.05);
        }}

        table {{
            width: 100%;
            border-collapse: collapse;
            text-align: left;
        }}

        th {{
            background: rgba(58, 123, 213, 0.1);
            padding: 20px;
            font-weight: 800;
            font-size: 0.9rem;
            text-transform: uppercase;
            letter-spacing: 1px;
            border-bottom: 2px solid white;
            color: var(--primary-cyan);
        }}

        td {{
            padding: 18px 20px;
            border-bottom: 1px solid rgba(255,255,255,0.5);
            vertical-align: middle;
            font-size: 0.95rem;
        }}

        tr:hover td {{
            background: rgba(255,255,255,0.4);
        }}

        .file-name {{
            font-family: 'Inter', sans-serif;
            font-size: 0.8rem;
            color: var(--text-muted);
            background: rgba(255, 255, 255, 0.5);
            padding: 2px 6px;
            border-radius: 4px;
            display: inline-block;
            margin-top: 4px;
        }}

        .trigger-badge {{
            display: inline-block;
            background: linear-gradient(135deg, var(--primary-cyan), var(--secondary-cyan));
            color: white;
            padding: 8px 16px;
            border-radius: 25px;
            font-weight: 800;
            font-size: 0.85rem;
            cursor: pointer;
            transition: all 0.2s;
            border: 2px solid white;
            box-shadow: 0 4px 10px rgba(58, 123, 213, 0.2);
        }}

        .trigger-badge:hover {{
            transform: scale(1.05);
            box-shadow: 0 6px 15px rgba(58, 123, 213, 0.4);
        }}

        .effect-text {{
            color: var(--text-dark);
            font-size: 0.9rem;
            line-height: 1.6;
            font-weight: 500;
        }}

        .model-tag {{
            font-size: 0.7rem;
            background: white;
            padding: 2px 8px;
            border-radius: 10px;
            color: var(--primary-cyan);
            border: 1px solid var(--primary-cyan);
            font-weight: 800;
        }}

        @media (max-width: 768px) {{
            th:nth-child(2), td:nth-child(2), th:nth-child(3), td:nth-child(3) {{
                display: none;
            }}
            h1 {{ font-size: 1.8rem; }}
        }}

        /* Back button */
        .back-btn {{
            position: fixed;
            bottom: 30px;
            right: 30px;
            background: var(--primary-cyan);
            color: white;
            width: 50px;
            height: 50px;
            border-radius: 50%;
            display: flex;
            align-items: center;
            justify-content: center;
            text-decoration: none;
            font-size: 1.5rem;
            box-shadow: 0 10px 20px rgba(0,0,0,0.3);
            transition: all 0.3s;
            z-index: 100;
        }}
        .back-btn:hover {{
            transform: scale(1.1) rotate(-10deg);
        }}
    </style>
</head>
<body>
    <div class="container">
        <nav class="breadcrumb">
            <li><a href="../../../index.html">Home</a></li>
            <li><a href="../../index.html">Models</a></li>
            <li><a href="../index.html">Embeddings</a></li>
            <li>{title}</li>
        </nav>

        <div class="header-panel">
            <h1 class="bounce-text">{title} Embeddings</h1>
            <p style="color: var(--text-muted);">AI画像生成の品質を劇的に向上させる、{title}向けのおすすめEmbeddings一覧です。</p>
        </div>

        <div class="nav-grid">
            <a href="sd15.html" class="nav-item {active_sd15}">SD 1.5</a>
            <a href="sdxl.html" class="nav-item {active_sdxl}">SDXL</a>
            <a href="pony.html" class="nav-item {active_pony}">Pony</a>
            <a href="illustrious.html" class="nav-item {active_illustrious}">Illustrious</a>
            <a href="others.html" class="nav-item {active_others}">Others</a>
        </div>

        <div class="table-container">
            <table>
                <thead>
                    <tr>
                        <th>名前 / ファイル</th>
                        <th>モデル</th>
                        <th>効果 / 特徴</th>
                        <th>トリガーワード</th>
                    </tr>
                </thead>
                <tbody>
                    {table_rows}
                </tbody>
            </table>
        </div>
    </div>

    <a href="../index.html" class="back-btn"><i class="fas fa-chevron-left"></i></a>

    <script>
        document.querySelectorAll('.trigger-badge').forEach(button => {{
            button.onclick = function() {{
                const text = this.innerText;
                navigator.clipboard.writeText(text).then(() => {{
                    const originalText = text;
                    this.innerText = 'COPIED!';
                    setTimeout(() => {{
                        this.innerText = originalText;
                    }}, 1000);
                }});
            }};
        }});
    </script>
</body>
</html>
"""

def get_category(row):
    model = row['ベースモデル']
    return CATEGORY_MAP.get(model, 'others')

def process():
    data_by_cat = {cat: [] for cat in FRIENDLY_NAMES.keys()}
    
    with open(CSV_PATH, 'r', encoding='utf-8-sig') as f:
        reader = csv.DictReader(f)
        for row in reader:
            cat = get_category(row)
            data_by_cat[cat].append(row)
            
    for cat, items in data_by_cat.items():
        if not items:
            continue
            
        rows_html = ""
        for item in items:
            rows_html += f"""
                    <tr>
                        <td>
                            <div style="font-weight: bold; margin-bottom: 5px;">{item['正式名称']}</div>
                            <span class="file-name">{item['ファイル名']}</span>
                        </td>
                        <td><span class="model-tag">{item['ベースモデル']}</span></td>
                        <td><div class="effect-text">{item['効果(タグ)']}</div></td>
                        <td><button class="trigger-badge">{item['トリガーワード']}</button></td>
                    </tr>"""
        
        full_html = HTML_TEMPLATE.format(
            title=FRIENDLY_NAMES[cat],
            active_sd15='active' if cat == 'sd15' else '',
            active_sdxl='active' if cat == 'sdxl' else '',
            active_pony='active' if cat == 'pony' else '',
            active_illustrious='active' if cat == 'illustrious' else '',
            active_others='active' if cat == 'others' else '',
            table_rows=rows_html
        )
        
        output_path = os.path.join(PAGES_DIR, f"{cat}.html")
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(full_html)
        print(f"Generated {output_path}")

if __name__ == "__main__":
    process()
