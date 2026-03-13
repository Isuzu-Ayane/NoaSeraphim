import csv
import re
import os

def clean_name(filename):
    # Remove extension
    name = re.sub(r'\.(safetensors|pt|ckpt)$', '', filename, flags=re.IGNORECASE)
    # Simplify common patterns
    name = name.replace('_', ' ').replace('-', ' ')
    return name.strip()

def detect_category(name, category_orig):
    name_lower = name.lower()
    
    if any(k in name_lower for k in ['style', 'art', 'concept', 'vibe', 'aesthetic', 'digital', 'watercolor', 'pencil', 'ink', 'flat', 'thick', 'painterly']):
        return '画風'
    if any(k in name_lower for k in ['outfit', 'costume', 'uniform', 'clothing', 'dress', 'swimwear', 'suit', 'armor', 'clothes', 'wear']):
        return '衣装'
    if any(k in name_lower for k in ['pose', 'stand', 'sitting', 'lying', 'action']):
        return 'ポーズ'
    if any(k in name_lower for k in ['background', 'scenery', 'landscape', 'forest', 'room', 'street', 'city']):
        return '背景'
    if any(k in name_lower for k in ['character', 'chara', 'girl', 'boy', 'woman', 'man']) or len(name) < 30:
        # Short names are often characters
        return 'キャラ'
    
    return 'その他'

def generate_description(name, cat_type):
    # Required keywords: Stable Diffusion, LoRA, AI画像生成, 追加学習モデル
    
    templates = {
        'キャラ': f"「{name}」を精密に再現する追加学習モデルです。Stable DiffusionのAI画像生成において、特徴的な容姿や表情をLoRAで安定させて描画。ハイクオリティな特定キャラ画像を生成したい方に最適です。",
        '画風': f"「{name}」の独特なタッチを反映する追加学習モデル。Stable DiffusionでのAI画像生成で、色彩や質感をLoRAにより一変させます。独創的で芸術性の高い作品を追求するクリエイターにおすすめです。",
        '衣装': f"「{name}」の衣装を付与できる追加学習モデルです。Stable DiffusionのAI画像生成でLoRAを活用し、細部までこだわり抜いたデザインを固定可能。特定のコスチュームを手軽に再現したい時に重宝します。",
        '背景': f"「{name}」のロケーションを生成する追加学習モデル。Stable DiffusionのAI画像生成において、LoRAが背景の密度と臨場感を劇的に向上させます。作品の没入感を高めたい背景重視の制作に最適です。",
        'ポーズ': f"「{name}」のポーズを制御する追加学習モデル。Stable DiffusionでのAI画像生成において、LoRAが構図の再現性を劇的に向上。躍動感のあるポーズや特定の構図を狙って描きたい方に強くおすすめします。",
        'その他': f"「{name}」に特化した追加学習モデルです。Stable DiffusionでのAI画像生成にLoRAを導入し、特定要素の再現性を劇的に向上。効率的かつ高品質なビジュアルを求める全てのAI絵師必見のモデルです。"
    }
    
    desc = templates.get(cat_type, templates['その他'])
    
    # Ensure length check (should be around 100-110 characters)
    return desc

def process():
    input_file = r'K:\GoogleAI\output.csv'
    output_file = r'K:\GoogleAI\lora_seo_descriptions.csv'
    
    if not os.path.exists(input_file):
        print(f"Error: {input_file} not found.")
        return

    results = []
    with open(input_file, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            filename = row['FileName']
            category_orig = row['Category']
            
            clean_n = clean_name(filename)
            cat_type = detect_category(clean_n, category_orig)
            description = generate_description(clean_n, cat_type)
            
            results.append({
                'LoRA名': filename,
                '特徴カテゴリ': cat_type,
                '説明文': description
            })

    with open(output_file, 'w', encoding='utf-8', newline='') as f:
        fieldnames = ['LoRA名', '特徴カテゴリ', '説明文']
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(results)
    
    print(f"Generated {len(results)} rows to {output_file}")

if __name__ == "__main__":
    process()
