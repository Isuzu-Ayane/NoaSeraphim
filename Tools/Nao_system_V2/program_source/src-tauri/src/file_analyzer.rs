// src-tauri/src/file_analyzer.rs
use std::fs::{self, OpenOptions};
use std::io::Write;
use std::path::Path;

pub struct LocalContext {
    pub extracted_paths: Vec<String>,
    pub available_images: Vec<String>,
}

// ログ出力用の便利な関数だて
fn write_debug_log(msg: &str) {
    let log_path = r"K:\System_Make\nao_local_system\nao_debug_progress.log";
    if let Ok(mut file) = OpenOptions::new().create(true).append(true).open(log_path) {
        let _ = writeln!(file, "[Analyzer Debug] {}", msg);
    }
}

// 2026-03-16: パスの抽出結果やGeminiへの送信内容を可視化するため、デバッグログを追加。以前のコードはコメントアウトだて。
/*
pub fn analyze_text(text: &str) -> LocalContext {
    let extracted_paths = extract_all_paths(text);
    let mut available_images = Vec::new();

    for path_str in &extracted_paths {
        let path = Path::new(path_str);
        if path.is_dir() {
            if let Ok(entries) = fs::read_dir(path) {
                // ... 省略 ...
            }
        }
    }
    LocalContext { extracted_paths, available_images }
}
*/
pub fn analyze_text(text: &str) -> LocalContext {
    write_debug_log(&format!("=== 解析開始 ===\n入力テキスト: {}", text));

    let extracted_paths = extract_all_paths(text);
    let mut available_images = Vec::new();

    write_debug_log(&format!("抽出されたパス候補: {:?}", extracted_paths));

    for path_str in &extracted_paths {
        let path = Path::new(path_str);
        write_debug_log(&format!("パスの存在チェック: {} -> 存在するか: {}, フォルダか: {}", path_str, path.exists(), path.is_dir()));
        
        if path.is_dir() {
            if let Ok(entries) = fs::read_dir(path) {
                for entry in entries.flatten() {
                    let file_path = entry.path();
                    if file_path.is_file() {
                        if let Some(ext) = file_path.extension().and_then(|e| e.to_str()) {
                            let ext_lower = ext.to_lowercase();
                            if ["png", "jpg", "jpeg", "gif", "webp"].contains(&ext_lower.as_str()) {
                                if let Some(file_name) = file_path.file_name().and_then(|n| n.to_str()) {
                                    if !available_images.contains(&file_name.to_string()) {
                                        available_images.push(file_name.to_string());
                                        if available_images.len() >= 10 {
                                            break;
                                        }
                                    }
                                }
                            }
                        }
                    }
                }
            }
        }
    }

    write_debug_log(&format!("最終的に抽出した画像リスト: {:?}", available_images));

    LocalContext {
        extracted_paths,
        available_images,
    }
}

/*
fn extract_all_paths(text: &str) -> Vec<String> { ... }
*/
fn extract_all_paths(text: &str) -> Vec<String> {
    let mut paths = Vec::new();
    let mut current_search = text;
    
    while let Some(start) = current_search.find(":\\") {
        let actual_start = if start > 0 { start - 1 } else { 0 };
        let path_part = &current_search[actual_start..];
        
        // 2026-03-16: 日本語の助詞や句読点がパスにくっつくのを防ぐため、区切り文字を大幅に追加
        let end = path_part.find(|c: char| 
            c.is_whitespace() || c == '　' || c == '"' || c == '\'' || c == '\n' || 
            c == '。' || c == '、' || c == 'に' || c == 'へ' || c == 'で' || c == 'を' || c == 'と'
        ).unwrap_or(path_part.len());
            
        let extracted = path_part[..end].to_string();
        // パスっぽくない短い文字列（C:\ など）は弾く
        if extracted.len() > 3 {
            paths.push(extracted);
        }
        
        if end < path_part.len() {
            current_search = &path_part[end..];
        } else {
            break;
        }
    }
    paths
}