import csv
import re

input_file = r"K:\GoogleAI\model_list.txt"
output_file = r"K:\GoogleAI\checkpoint_seo_descriptions.csv"

models = []
current_model = {}

with open(input_file, 'r', encoding='utf-8') as f:
    for line in f:
        line = line.strip()
        if line.startswith("Model:"):
            current_model = {"name": line.replace("Model: ", "").strip()}
        elif line.startswith("Category:"):
            cat = line.replace("Category: ", "").strip()
            if "_Checkpoint" in cat:
                current_model["category"] = cat.replace("_Checkpoint", "")
                models.append(current_model)
                current_model = {}

print(f"Found {len(models)} checkpoint models.")

# Generate SEO descriptions
templates = {
    "Anima": "Stable Diffusionの「Anima」環境で高品質な2Dアニメテイストを描き出す「{model_name}」。AI画像生成において、繊細なラインと鮮やかな塗りが特徴でキャラの魅力を引き出します。SNS映えする可愛いイラストや、VTuber風の立ち絵を求めるクリエイターにおすすめのモデルです。",
    "Flux.1 D": "圧倒的なディテールを誇る「Flux.1」系の「{model_name}」。Stable DiffusionのAI画像生成を活用し、透明感あふれる色彩と柔らかなタッチを描力豊かに表現可能です。精細な背景とキャラクターが溶け込む、ハイクオリティな一枚を生成したいイラストレーターに最適なモデルです。",
    "Flux.1 S": "軽量かつ高速な「Flux.1 S」対応モデル「{model_name}」。Stable DiffusionのAI画像生成において、速度と品質のバランスが良く、高精細なイラストを圧倒的なスピードで出力可能です。アイデア出しの段階から手軽でスピーディに美しいビジュアルを作成したいクリエイターにおすすめです。",
    "Flux.1 Krea": "アート性の高さで注目される「Flux.1 Krea」モデル「{model_name}」。Stable DiffusionのAI画像生成の中でも、独創的で柔らかいトーンと温かいイラスト調表現が特徴。ファンタジー世界観の表現や、コンセプチュアルで独自のアートスタイルを求める方に強くおすすめします。",
    "Flux.1 Kontext": "「Flux.1 Kontext」特化モデルの「{model_name}」。Stable DiffusionのAI画像生成技術を活かし、被写体と背景の文脈を深く理解したシネマティックな空間表現を得意とします。ライティングが際立つドラマチックな作品や、物語性を感じる一枚を生み出したいクリエイターに最適です。",
    "Illustrious": "「Illustrious」アーキテクチャを採用した「{model_name}」は、Stable DiffusionでのAI画像生成を新次元へ引き上げます。リッチな塗りと緻密な書き込みを誇る圧倒的な美麗2Dアートを生成可能。ライトノベルの表紙や美麗な一枚絵など、商業レベルの作品制作におすすめです。",
    "NoobAI": "「NoobAI」ジャンルを牽引する大人気モデル「{model_name}」。Stable DiffusionのAI画像生成においてプロンプトへの追従性が高く、メリハリある色彩とダイナミックな構図を素直に再現します。思い描いたポーズや構図のアニメ調キャラクターアートを正確に生成したい方にイチオシです。",
    "Pony": "高い表現力で大人気の「Pony」系モデル「{model_name}」。Stable DiffusionのAI画像生成において、アニメ調から様々なテイストまで幅広い画風を網羅する柔軟性とプロンプト理解力が最大の特徴。画風指定や細かな表現にこだわったコンセプトアートを作りたい全クリエイター必携のモデルです。",
    "SD 1.5": "「SD 1.5」ベースの定番・派生モデル「{model_name}」。AI画像生成黎明期から多くのユーザーに愛される、親しみやすい2Dアニメスタイルや多彩な表現が特徴です。Stable Diffusion初心者でも扱いやすく、低スペックPCでも素早く高品質な画像を生成したいユーザーに最適です。",
    "SDXL 1.0": "「SDXL 1.0」ベースの高解像度モデル「{model_name}」。実写のようなフォトリアル表現から美麗なデジタルアートまで幅広く網羅する現代AI画像生成のスタンダード。Stable Diffusionを用いた多彩な表現や、細部まで描き込まれた非常に高精細な画像を生成したい本格派クリエイターにおすすめです。",
    "ZImage": "「ZImage」ジャンルで実写表現を極限まで追求した「{model_name}」。Stable DiffusionのAI画像生成を用い、人物の繊細な肌の質感やリアルで生命力のある表情を息を呑むクオリティで描き出します。プロが撮影したような高品質な実写風ポートレートを作りたい方に強くおすすめのモデルです。",
    "Other": "Stable Diffusionの可能性を広げる独自モデル「{model_name}」。AI画像生成において、他にない独自の画風や特定シーンに特化したチューニングが施されており、一味違う表現を引き出します。いつもと違うテイストのイラストや、新しい表現スタイルを模索しているクリエイターにおすすめです。"
}

# Fallbacks for specific categories
category_map = {
    "Flux.1 D": ["Flux.1 D", "Flux", "Flux1"],
    "Flux.1 S": ["Flux.1 S"],
    "Flux.1 Krea": ["Flux.1 Krea"],
    "Flux.1 Kontext": ["Flux.1 Kontext"],
    "ZImage": ["ZImage"]
}

def get_template(cat):
    for key, aliases in category_map.items():
        if cat in aliases:
            return templates[key]
    if cat in templates:
        return templates[cat]
    
    # Try partial match
    for k in templates.keys():
        if k.lower() in cat.lower():
            return templates[k]
            
    return templates["Other"]

with open(output_file, 'w', encoding='utf-8', newline='') as f:
    writer = csv.writer(f)
    writer.writerow(["モデル名", "ジャンル", "説明文"])
    for m in models:
        model_name = m["name"].replace(".safetensors", "").replace(".pt", "")
        cat = m["category"]
        desc = get_template(cat).format(model_name=model_name)
        writer.writerow([model_name, cat, desc])

print(f"Descriptions generated and saved to {output_file}")
