import os
from PIL import Image

# --- 設定 ---
TARGET_DIR = "thumbnails"
SIZE_LIMIT_MB = 1.0  # 1MB以上のファイルを対象にする
TARGET_SIZE_KB = 500 # 500KB以下を目指す
QUALITY_START = 95   # 圧縮の初期品質

def compress_image(file_path, target_kb):
    """画像を指定したサイズ以下になるまで品質を下げて保存する"""
    try:
        # 画像を開く
        img = Image.open(file_path)
        
        # もしRGBA（透明度あり）ならRGBに変換（JPGで保存するため）
        if img.mode in ("RGBA", "P"):
            img = img.convert("RGB")
            
        quality = QUALITY_START
        temp_path = file_path + ".tmp"
        
        while quality > 10:
            # 指定した品質で一旦保存してみる
            img.save(temp_path, "JPEG", quality=quality, optimize=True)
            
            # 保存したファイルのサイズを確認
            if os.path.getsize(temp_path) <= target_kb * 1024:
                break
            
            # まだ大きい場合は品質を5下げる
            quality -= 5
            
        # 最終的なファイルを元の場所に上書き
        os.replace(temp_path, file_path)
        return True, quality
    except Exception as e:
        return False, str(e)

def main():
    if not os.path.exists(TARGET_DIR):
        print(f"エラー: {TARGET_DIR} フォルダが見つかりません。")
        return

    # フォルダ内の画像ファイルをリストアップ
    files = [f for f in os.listdir(TARGET_DIR) if f.lower().endswith(('.jpg', '.jpeg', '.png'))]
    limit_bytes = SIZE_LIMIT_MB * 1024 * 1024
    
    print(f"📁 {TARGET_DIR} 内の巨大な画像を圧縮します...")

    count = 0
    for filename in files:
        file_path = os.path.join(TARGET_DIR, filename)
        file_size = os.path.getsize(file_path)
        
        # 指定サイズ（1MB）以上のものだけ処理
        if file_size > limit_bytes:
            print(f"⚡ 圧縮中: {filename} ({file_size/1024/1024:.2f} MB) -> ", end="", flush=True)
            
            success, result = compress_image(file_path, TARGET_SIZE_KB)
            
            if success:
                new_size = os.path.getsize(file_path)
                print(f"✅完了 ({new_size/1024:.1f} KB / Quality: {result})")
                count += 1
            else:
                print(f"❌失敗 ({result})")

    print(f"\n✨ 処理完了！ 合計 {count} 個の画像をダイエットさせました。")

if __name__ == "__main__":
    main()


