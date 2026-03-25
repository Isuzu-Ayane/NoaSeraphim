// src-tauri/src/file_reader.rs
use std::fs;
use std::path::Path;

// 2026-03-16: 新規作成。UNIXの `more` や `cat` のように、指定されたパスのファイルの中身をテキストとして読み込む共通モジュールだて！
pub fn read_file_contents(paths: &[String]) -> String {
    let mut combined_content = String::new();

    for path_str in paths {
        let path = Path::new(path_str);
        
        // パスが存在し、かつ「フォルダ」ではなく「ファイル」である場合のみ処理するだて
        if path.is_file() {
            // テキストとして読み込みを試みる
            match fs::read_to_string(path) {
                Ok(content) => {
                    // Geminiが境界線を認識しやすいように、ヘッダーとフッターをつけてあげるわ
                    combined_content.push_str(&format!("\n\n--- 【ファイル内容: {}】 ---\n{}\n-------------------\n", path_str, content));
                }
                Err(_) => {
                    // 画像やエクセルみたいなバイナリファイル、あるいは読み込み権限がない場合はスキップ。
                    // でも「そこにファイルがあるよ」っていう事実だけはGeminiに伝えておくだて。
                    combined_content.push_str(&format!("\n\n--- 【ファイル: {}】 ---\n(※バイナリデータ、またはテキストとして読み込めませんでした)\n-------------------\n", path_str));
                }
            }
        }
    }

    combined_content
}