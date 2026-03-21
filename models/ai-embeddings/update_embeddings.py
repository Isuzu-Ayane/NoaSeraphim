import csv
import os

CSV_PATH = r"K:\GoogleAI\embeddings_effects.csv"
OUTPUT_DIR = r"K:\GoogleAI\NoaSeraphim\models\ai-embeddings\pages"

def parse_csv(filepath):
    embeddings = []
    with open(filepath, 'r', encoding='utf-8') as f:
        reader = csv.reader(f)
        header = next(reader)
        for row in reader:
            if not row or len(row) < 5:
                continue
            fname, base_model, formal_name, effects, trigger = row[0:5]
            if fname.strip() == "":
                continue
            embeddings.append({
                "fname": fname.strip(),
                "base_model": base_model.strip(),
                "formal_name": formal_name.strip(),
                "effects": effects.strip(),
                "trigger": trigger.strip()
            })
    return embeddings

def categorize(embeddings):
    categories = {
        "sd15": [],
        "sdxl": [],
        "pony": [],
        "illustrious": [],
        "others": []
    }
    
    for emb in embeddings:
        bm = emb["base_model"]
        if bm in ["SD 1.4", "SD 1.5", "SD 2.0 768", "SD 2.1", "SD 2.1 768"]:
            categories["sd15"].append(emb)
        elif bm == "SDXL 1.0":
            categories["sdxl"].append(emb)
        elif bm == "Pony":
            categories["pony"].append(emb)
        elif bm == "Illustrious":
            categories["illustrious"].append(emb)
        else: # Other
            categories["others"].append(emb)
    
    return categories

HTML_TEMPLATE = """<!DOCTYPE html>
<html lang="{LANG}">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{TITLE} - Embeddings List | Noa AI Labs</title>
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
    <link href="https://fonts.googleapis.com/css2?family=M+PLUS+Rounded+1c:wght@300;400;700&family=Nunito:wght@400;800&family=Inter:wght@400;700;900&display=swap" rel="stylesheet">
    <link rel="stylesheet" href="../../../styles.css">
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
            padding-top: 60px; /* Spacer for fixed nav */
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
            word-break: break-all;
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
            border-style: none; /* overrides browser default button border if badge is a button */
            text-align: left;
            word-break: break-all;
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
            display: inline-block;
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
    <div class="cursor-dot"></div>
    <div class="cursor-outline"></div>

    <!-- Language Toggle -->
    <div style="position: absolute; top: 20px; right: 20px; z-index: 1000;">
        <a href="{LANG_LINK}"
            style="background: rgba(255,255,255,0.7); backdrop-filter: blur(10px); border: 2px solid white; color: var(--primary-cyan); text-decoration: none; padding: 6px 14px; border-radius: 20px; font-weight: bold; font-size: 0.9rem; transition: background 0.3s, transform 0.2s; display: inline-block; box-shadow: 0 4px 10px rgba(58, 123, 213, 0.1);">
            <i class="fas fa-globe"></i> {LANG_TEXT}
        </a>
    </div>

    <nav class="glass-panel centered-nav" style="position: fixed; top: 0; left: 0; width: 100%; z-index: 999; background: rgba(255, 255, 255, 0.8); backdrop-filter: blur(10px); border-bottom: 2px solid white; display: flex; justify-content: center; align-items: center; padding: 10px 0; box-shadow: 0 5px 20px rgba(0,0,0,0.05);">
        <ul style="display: flex; list-style: none; gap: 20px; margin: 0; padding: 0;">
            {NAV_LINKS}
        </ul>
    </nav>

    <div class="container">
        <nav class="breadcrumb">
            {BREADCRUMB_LINKS}
        </nav>

        <div class="header-panel">
            <h1 class="bounce-text">{PAGE_DESC_HEADER}</h1>
            <p style="color: var(--text-muted);">{PAGE_DESC}</p>
        </div>

        <div class="nav-grid">
            {CAT_LINKS}
        </div>

        <div class="table-container">
            <table>
                <thead>
                    <tr>
                        {TABLE_HEADERS}
                    </tr>
                </thead>
                <tbody>
                    {TABLE_ROWS}
                </tbody>
            </table>
        </div>
    </div>

    <a href="{MODELS_TOP_LINK}" class="back-btn"><i class="fas fa-chevron-left"></i></a>

    <script src="../../../script.js"></script>
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
</html>"""

def generate_pages(categories):
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    
    meta_data = {
        "sd15": {
            "title": "Stable Diffusion 1.5",
            "desc_ja": "SD 1.5系統向けのおすすめEmbeddings一覧です。手や指の崩れ修正や画質向上など様々な効果があります。",
            "desc_en": "A list of recommended Embeddings for SD 1.5 models. These have various effects such as correcting hand and finger corruption and improving image quality.",
        },
        "sdxl": {
            "title": "SDXL 1.0",
            "desc_ja": "SDXL 1.0モデル専用のEmbeddingsです。構図崩れを防ぐネガティブや高品質化をサポートします。",
            "desc_en": "Embeddings exclusively for SDXL 1.0 models. Negative parameters to prevent bad compositions and support high quality.",
        },
        "pony": {
            "title": "Pony Diffusion",
            "desc_ja": "Pony Diffusionモデル特化のEmbeddings集です。独自のタグ学習を最適化し品質を底上げします。",
            "desc_en": "Embeddings specifically for Pony Diffusion models. Optimizes unique tag learning and boosts quality.",
        },
        "illustrious": {
            "title": "Illustrious XL",
            "desc_ja": "最新のIllustrious XL向けEmbeddingsです。細部のディテールアップに非常に効果的です。",
            "desc_en": "Embeddings for the latest Illustrious XL models. Highly effective for increasing fine details.",
        },
        "others": {
            "title": "Other Models",
            "desc_ja": "その他のベースモデル（SD 1.4, 2.Xなど）や特定用途のEmbeddings一覧です。",
            "desc_en": "A list of embeddings for other base models (SD 1.4, 2.X, etc.) and specific purposes.",
        }
    }

    cats = ["sd15", "sdxl", "pony", "illustrious", "others"]
    
    for lang in ["ja", "en"]:
        is_en = (lang == "en")
        
        home_text = "Home" if is_en else "Top"
        models_text = "Models"
        embeddings_text = "Embeddings"
        
        nav_home = "../../../index_en.html" if is_en else "../../../index.html"
        nav_guide = "../../../ai-guide/index_en.html" if is_en else "../../../ai-guide/index.html"
        nav_models = "../../../models/index_en.html" if is_en else "../../../models/index.html"
        nav_tools = "../../../Tools/index_en.html" if is_en else "../../../Tools/index.html"
        nav_gallery = "../../../creative/index_en.html" if is_en else "../../../creative/index.html"
        
        nav_links = f'''
            <li><a href="{nav_home}" style="color: var(--text-main); text-decoration: none; font-weight: bold;">HOME</a></li>
            <li><a href="{nav_guide}" style="color: var(--text-main); text-decoration: none; font-weight: bold;">AI-GUIDE</a></li>
            <li><a href="{nav_models}" style="color: var(--accent-blue); text-decoration: none; font-weight: bold;">MODELS</a></li>
            <li><a href="{nav_tools}" style="color: var(--text-main); text-decoration: none; font-weight: bold;">TOOLS</a></li>
            <li><a href="{nav_gallery}" style="color: var(--text-main); text-decoration: none; font-weight: bold;">GALLERY</a></li>
        '''
        
        th_name = "Name / File" if is_en else "名前 / ファイル"
        th_model = "Model" if is_en else "モデル"
        th_effect = "Effects / Description" if is_en else "効果 / 特徴"
        th_trigger = "Trigger Word" if is_en else "トリガーワード"
        
        table_headers = f"<th>{th_name}</th><th>{th_model}</th><th>{th_effect}</th><th>{th_trigger}</th>"
        
        for curr_cat in cats:
            info = meta_data[curr_cat]
            title = info["title"]
            
            # Generate breadcrumbs
            bc = f'''
            <li><a href="{nav_home}">{home_text}</a></li>
            <li><a href="{nav_models}">{models_text}</a></li>
            <li><a href="../../index{'_en' if is_en else ''}.html">{embeddings_text}</a></li>
            <li>{title}</li>
            '''
            
            # Category Nav Links
            cat_links = ""
            for c in cats:
                active = "active" if c == curr_cat else ""
                href = f"{c}{'_en' if is_en else ''}.html"
                cname = meta_data[c]["title"]
                cat_links += f'<a href="{href}" class="nav-item {active}">{cname}</a>\n'
                
            # Table Rows
            rows_html = ""
            for row in categories[curr_cat]:
                # Replace < and > in trigger to avoid HTML breaking
                trigger = row["trigger"].replace("<", "&lt;").replace(">", "&gt;")
                effects = row["effects"].replace("<", "&lt;").replace(">", "&gt;")
                formal = row["formal_name"].replace("<", "&lt;").replace(">", "&gt;")
                bm = row["base_model"].replace("<", "&lt;").replace(">", "&gt;")
                fname = row["fname"].replace("<", "&lt;").replace(">", "&gt;")
                
                tr = f'''<tr>
                        <td>
                            <div style="font-weight: bold; margin-bottom: 5px;">{formal}</div>
                            <span class="file-name">{fname}</span>
                        </td>
                        <td><span class="model-tag">{bm}</span></td>
                        <td><div class="effect-text">{effects}</div></td>
                        <td><button class="trigger-badge">{trigger}</button></td>
                    </tr>
                '''
                rows_html += tr
                
            lang_link = f"{curr_cat}_en.html" if not is_en else f"{curr_cat}.html"
            lang_text = "English" if not is_en else "日本語"
            
            html_content = HTML_TEMPLATE.format(
                LANG="en" if is_en else "ja",
                TITLE=title,
                LANG_LINK=lang_link,
                LANG_TEXT=lang_text,
                NAV_LINKS=nav_links,
                BREADCRUMB_LINKS=bc,
                PAGE_DESC_HEADER=f"{title} Embeddings",
                PAGE_DESC=info[f"desc_{lang}"],
                CAT_LINKS=cat_links,
                TABLE_HEADERS=table_headers,
                TABLE_ROWS=rows_html,
                MODELS_TOP_LINK=f"../../index{'_en' if is_en else ''}.html"
            )
            
            out_file = os.path.join(OUTPUT_DIR, f"{curr_cat}{'_en' if is_en else ''}.html")
            with open(out_file, 'w', encoding='utf-8') as f:
                f.write(html_content)
                
            print(f"Generated {out_file}")

if __name__ == "__main__":
    embs = parse_csv(CSV_PATH)
    cats = categorize(embs)
    generate_pages(cats)
    print("Done generating pages.")
