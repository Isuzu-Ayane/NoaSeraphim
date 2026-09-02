import json
import os

CACHE_FILE = r'R:\Gamelist\h_suki_cache.json'
OUTPUT_FILE = r'R:\Gamelist\index.html'

def build_html():
    if not os.path.exists(CACHE_FILE):
        print(f"Error: Cache file not found at {CACHE_FILE}")
        return

    with open(CACHE_FILE, 'r', encoding='utf-8') as f:
        cache = json.load(f)

    # Filter out entries that were not found on H-Suki
    games = []
    for rid, info in cache.items():
        if info.get('found'):
            info['rid'] = rid
            games.append(info)

    # Sort games by release date descending
    games.sort(key=lambda x: x.get('release_date', ''), reverse=True)

    html_parts = []
    html_parts.append("""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Visual Novel Game List</title>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap" rel="stylesheet">
    <style>
        :root {
            --bg-color: #0d1117;
            --card-bg: #161b22;
            --card-border: #30363d;
            --text-main: #c9d1d9;
            --text-muted: #8b949e;
            --accent: #58a6ff;
            --accent-hover: #79c0ff;
            --success: #2ea043;
            --warning: #d29922;
        }

        * {
            box-sizing: border-box;
            margin: 0;
            padding: 0;
        }

        body {
            font-family: 'Inter', sans-serif;
            background-color: var(--bg-color);
            color: var(--text-main);
            line-height: 1.5;
            padding: 20px;
        }

        .container {
            max-width: 1400px;
            margin: 0 auto;
        }

        header {
            text-align: center;
            margin-bottom: 40px;
            padding: 40px 0;
            border-bottom: 1px solid var(--card-border);
        }

        h1 {
            font-size: 2.5rem;
            font-weight: 700;
            color: var(--accent);
            margin-bottom: 10px;
            text-shadow: 0 0 20px rgba(88, 166, 255, 0.3);
        }

        .stats {
            color: var(--text-muted);
            font-size: 1rem;
        }

        .grid {
            display: grid;
            grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
            gap: 24px;
        }

        .card {
            background-color: var(--card-bg);
            border: 1px solid var(--card-border);
            border-radius: 12px;
            overflow: hidden;
            transition: transform 0.2s ease, box-shadow 0.2s ease, border-color 0.2s ease;
            display: flex;
            flex-direction: column;
        }

        .card:hover {
            transform: translateY(-5px);
            box-shadow: 0 10px 20px rgba(0, 0, 0, 0.4);
            border-color: var(--accent);
        }

        .card-img-wrapper {
            position: relative;
            width: 100%;
            padding-top: 130%; /* Aspect ratio approx 3:4 for VN covers */
            background-color: #21262d;
            overflow: hidden;
        }

        .card-img {
            position: absolute;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            object-fit: cover;
            transition: transform 0.4s ease;
        }
        
        .card:hover .card-img {
            transform: scale(1.05);
        }

        .rid-badge {
            position: absolute;
            top: 10px;
            left: 10px;
            background: rgba(13, 17, 23, 0.85);
            backdrop-filter: blur(4px);
            padding: 4px 8px;
            border-radius: 4px;
            font-size: 0.8rem;
            font-weight: 600;
            color: var(--accent);
            border: 1px solid var(--card-border);
        }

        .card-content {
            padding: 16px;
            flex-grow: 1;
            display: flex;
            flex-direction: column;
        }

        .card-title {
            font-size: 1.1rem;
            font-weight: 600;
            margin-bottom: 8px;
            line-height: 1.4;
            color: #fff;
            display: -webkit-box;
            -webkit-line-clamp: 2;
            -webkit-box-orient: vertical;
            overflow: hidden;
        }

        .card-aliases {
            font-size: 0.85rem;
            color: var(--text-muted);
            margin-bottom: 12px;
            font-style: italic;
            display: -webkit-box;
            -webkit-line-clamp: 1;
            -webkit-box-orient: vertical;
            overflow: hidden;
        }

        .meta-list {
            margin-top: auto;
            border-top: 1px solid var(--card-border);
            padding-top: 12px;
            display: flex;
            flex-direction: column;
            gap: 6px;
        }

        .meta-item {
            font-size: 0.85rem;
            display: flex;
            align-items: flex-start;
        }

        .meta-label {
            color: var(--text-muted);
            width: 70px;
            flex-shrink: 0;
            font-weight: 500;
        }

        .meta-value {
            color: var(--text-main);
            word-break: break-word;
        }
        
        .date { color: var(--accent-hover); }
        .audio { color: var(--success); }
        .text { color: var(--warning); }
        
        /* Empty states */
        .empty-val { color: var(--card-border); font-style: italic; }

    </style>
</head>
<body>
    <div class="container">
        <header>
            <h1>Visual Novel Local Collection</h1>
            <div class="stats">Showing <strong>{len(games)}</strong> games processed from R:\</div>
        </header>

        <div class="grid">
""")

    for game in games:
        img_src = game.get('image') or 'https://via.placeholder.com/300x400/21262d/8b949e?text=No+Cover'
        title = game.get('title') or 'Unknown Title'
        aliases = game.get('aliases') or ''
        rid = game.get('rid')
        date = game.get('release_date') or '<span class="empty-val">Unknown</span>'
        audio = game.get('audio') or '<span class="empty-val">None</span>'
        text = game.get('text') or '<span class="empty-val">None</span>'
        
        if audio.lower() == 'none': audio = '<span class="empty-val">None</span>'
        if text.lower() == 'none': text = '<span class="empty-val">None</span>'

        html_parts.append(f"""
            <div class="card">
                <div class="card-img-wrapper">
                    <img src="{img_src}" alt="Cover" class="card-img" loading="lazy" onerror="this.src='https://via.placeholder.com/300x400/21262d/8b949e?text=Image+Error'">
                    <div class="rid-badge">{rid}</div>
                </div>
                <div class="card-content">
                    <div class="card-title" title="{title}">{title}</div>
                    <div class="card-aliases" title="{aliases}">{aliases}</div>
                    <div class="meta-list">
                        <div class="meta-item">
                            <span class="meta-label">Date</span>
                            <span class="meta-value date">{date}</span>
                        </div>
                        <div class="meta-item">
                            <span class="meta-label">Audio</span>
                            <span class="meta-value audio">{audio}</span>
                        </div>
                        <div class="meta-item">
                            <span class="meta-label">Text</span>
                            <span class="meta-value text">{text}</span>
                        </div>
                    </div>
                </div>
            </div>
        """)

    html_parts.append("""
        </div>
    </div>
</body>
</html>
""")

    with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
        f.write("".join(html_parts))
    
    print(f"Successfully built HTML at {OUTPUT_FILE} with {len(games)} entries.")

if __name__ == '__main__':
    build_html()
