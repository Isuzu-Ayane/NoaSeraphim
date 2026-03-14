/*
 * ============================================================================
 * Project: Nao Seraphim Local System
 * Description: A secure and sacred local sanctuary for human-AI interaction.
 * Author: Nao Seraphim
 * Copyright: (c) 2026 Nao Seraphim. All rights reserved.
 * Version: 1.0.0
 * License: MIT License
 * Repository: https://isuzu-ayane.github.io/NoaSeraphim/index.html
 * ============================================================================
 */

use magic_crypt::{new_magic_crypt, MagicCryptTrait};
use reqwest::Client;
use serde_json::json;
use std::fs;
use std::path::PathBuf;
use tauri::Manager; // 💡 AppDataのパス取得に必要だて！

// 🎯 設定ファイルの保存場所（AppData）を取得する内部関数
fn get_settings_path(app_handle: &tauri::AppHandle) -> PathBuf {
    app_handle.path().app_data_dir().unwrap_or_default().join("settings.ini")
}

// 🎯 INIから設定を読み込む内部ロジック
fn internal_load_setting(path: &PathBuf, key: &str) -> String {
    let content = fs::read_to_string(path).unwrap_or_default();
    for line in content.lines() {
        if line.starts_with(&format!("{}=", key)) {
            let value = line.replace(&format!("{}=", key), "");
            if key == "api_key" {
                let mc = new_magic_crypt!("my_secret_key_for_app", 256);
                return mc.decrypt_base64_to_string(&value).unwrap_or_default();
            }
            return value;
        }
    }
    "".to_string()
}

// 🎯 フロントエンドから「今の設定を教えて！」と呼ばれる機能
#[tauri::command]
fn get_setting(app_handle: tauri::AppHandle, key: String) -> Result<String, String> {
    let path = get_settings_path(&app_handle);
    Ok(internal_load_setting(&path, &key))
}

// 🎯 フロントエンドから呼ばれる保存機能
#[tauri::command]
fn save_setting(app_handle: tauri::AppHandle, key: String, value: String) -> Result<String, String> {
    let path = get_settings_path(&app_handle);
    
    // 💡 フォルダがなければ作成（AppData内にアプリ用フォルダを作るだて）
    if let Some(parent) = path.parent() {
        let _ = fs::create_dir_all(parent);
    }

    let final_value = if key == "api_key" {
        let mc = new_magic_crypt!("my_secret_key_for_app", 256);
        mc.encrypt_str_to_base64(&value)
    } else {
        value
    };

    let content = fs::read_to_string(&path).unwrap_or_else(|_| "[Settings]".to_string());
    let mut settings: Vec<String> = Vec::new();
    let mut is_updated = false;

    for line in content.lines() {
        if line.starts_with(&format!("{}=", key)) {
            settings.push(format!("{}={}", key, final_value));
            is_updated = true;
        } else {
            settings.push(line.to_string());
        }
    }

    if !is_updated {
        settings.push(format!("{}={}", key, final_value));
    }

    fs::write(&path, settings.join("\n")).map_err(|e| e.to_string())?;
    Ok("保存完了だて！".to_string())
}

// 🎯 Geminiと通信する機能
#[tauri::command]
async fn chat_with_gemini(app_handle: tauri::AppHandle, message: String) -> Result<String, String> {
    let path = get_settings_path(&app_handle);
    let api_key = internal_load_setting(&path, "api_key");
    let context = internal_load_setting(&path, "context");

    if api_key.is_empty() {
        return Err("APIキーが設定されていません。左の「APIキー設定」から入力してね。".to_string());
    }

    let url = format!("https://generativelanguage.googleapis.com/v1beta/models/gemini-flash-latest:generateContent?key={}", api_key);
    let client = Client::new();

    let full_prompt = if context.is_empty() {
        message
    } else {
        format!("システム設定(絶対厳守): {}\n\nユーザー: {}", context, message)
    };

    let body = json!({
        "contents": [{ "parts": [{"text": full_prompt}] }]
    });

    let res = client.post(&url).json(&body).send().await.map_err(|e| e.to_string())?;
    let json_res: serde_json::Value = res.json().await.map_err(|e| e.to_string())?;

    if let Some(text) = json_res["candidates"][0]["content"]["parts"][0]["text"].as_str() {
        Ok(text.to_string())
    } else {
        Err("APIから正しく応答が返ってこなかったわ。".to_string())
    }
}

// 🎯 起動処理
#[cfg_attr(mobile, tauri::mobile_entry_point)]
pub fn run() {
    tauri::Builder::default()
        .plugin(tauri_plugin_opener::init())
        .plugin(tauri_plugin_shell::init())
        .invoke_handler(tauri::generate_handler![save_setting, get_setting, chat_with_gemini])
        .run(tauri::generate_context!())
        .expect("error while running tauri application");
}