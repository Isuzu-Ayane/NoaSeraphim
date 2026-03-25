// src-tauri/src/lib.rs
/*
 * プログラムの概要説明: Tauriアプリケーションのコアライブラリおよびコマンドハンドラ定義
 * プロジェクトの責任範囲に関する注記: NoaSeraphimは本プログラムの動作について一切の責任を負いません。
 * 初回作成年月日: 2026-03-16
 * 更新履歴:
 * 2026-03-25: OpenAI GPTモデルのメニュー追加および統合API呼び出しへの変更。
 * 2026-03-25: UIからのプロジェクト保存要求に対応するためコマンドを拡張。
 * 2026-03-25: APIキー保護のため、"********"が送信された場合は保存処理をスキップする安全装置を実装。
 * プロジェクトの権利表示: (C) NoaSeraphim
 * 利用範囲に関する制限事項: 非商用利用に限る
 */

pub mod models;
pub mod crypto;
pub mod config;
pub mod system_ops;
pub mod ai_parser;
pub mod web_ops;
pub mod send_instruction; 
pub mod decode;
pub mod file_analyzer;
pub mod file_reader;
pub mod program_ops;

use serde_json::{json, Value};

// Tauriマクロのスコープエラーを防ぐため、必要なコマンド関数を直接現在のスコープにインポートします。
use crate::system_ops::{run_powershell, read_file_content, write_file_content, scan_directory, list_directory, get_current_dir};

// 構成ファイルから現在の設定値を取得するためのコマンド処理です。
#[tauri::command]
fn get_setting(app_handle: tauri::AppHandle, key: String) -> String {
    let conf = config::load_config(&app_handle);
    match key.as_str() {
        "projects" => conf.projects,
        "api_key_gemini_free" => conf.api_key_gemini_free,
        "api_key_gemini_pro" => conf.api_key_gemini_pro,
        "api_key_gpt_pro" => conf.api_key_gpt_pro,
        "context_gemini_free" => conf.context_gemini_free,
        "context_gemini_pro" => conf.context_gemini_pro,
        "context_gpt_pro" => conf.context_gpt_pro,
        "model_id" => conf.model_id,
        "background_path" | "bg_image" => conf.background_path,
        "background_color" | "bg_color" => conf.background_color,
        "ai_name" => conf.ai_name,
        "user_name" => conf.user_name,
        _ => "".to_string(),
    }
}

// 2026-03-25 年月日コメントアウト: 旧保存処理(空欄のみスキップ)
/*
#[tauri::command]
fn save_setting(app_handle: tauri::AppHandle, key: String, value: String) -> Result<(), String> {
    if value.trim().is_empty() && key != "projects" {
        return Ok(());
    }
    // ...
}
*/

// UIからの変更要求を受け、構成設定を保存するためのコマンド処理です。
#[tauri::command]
fn save_setting(app_handle: tauri::AppHandle, key: String, value: String) -> Result<(), String> {
    let trim_val = value.trim();
    // APIキー等が空欄、またはUIからのマスキング文字列(********)の場合は、
    // 既存の設定を保護するため処理を安全にスキップします。
    // ただし、プロジェクト一覧だけは空(全削除)になる場合があるため許可します。
    if (trim_val.is_empty() || trim_val == "********") && key != "projects" {
        return Ok(());
    }

    let mut conf = config::load_config(&app_handle);
    // 更新対象のキーを特定し、新しい値で構造体を上書きします。
    match key.as_str() {
        "projects" => conf.projects = value,
        "api_key_gemini_free" => conf.api_key_gemini_free = value,
        "api_key_gemini_pro" => conf.api_key_gemini_pro = value,
        "api_key_gpt_pro" => conf.api_key_gpt_pro = value,
        "context_gemini_free" => conf.context_gemini_free = value,
        "context_gemini_pro" => conf.context_gemini_pro = value,
        "context_gpt_pro" => conf.context_gpt_pro = value,
        "model_id" => conf.model_id = value,
        "background_path" | "bg_image" => conf.background_path = value,
        "background_color" | "bg_color" => conf.background_color = value,
        "ai_name" => conf.ai_name = value,
        "user_name" => conf.user_name = value,
        _ => return Err(format!("Unknown key: {}", key)),
    }
    config::save_config(&app_handle, &conf);
    Ok(())
}

// 登録されているAPIキーを使用して、利用可能なAIモデル一覧を取得します。
#[tauri::command]
async fn get_clean_models(app_handle: tauri::AppHandle) -> Result<Vec<Value>, String> {
    let conf = config::load_config(&app_handle);
    let mut dynamic_models = Vec::new();

    // GPT用のキーが設定されている場合、固定でGPTモデル群をプルダウンに追加します。
    if !conf.api_key_gpt_pro.trim().is_empty() {
        dynamic_models.push(json!({ "id": "gpt-4o", "name": "GPT-4o (OpenAI)" }));
        dynamic_models.push(json!({ "id": "gpt-4o-mini", "name": "GPT-4o-mini (OpenAI)" }));
        dynamic_models.push(json!({ "id": "o1", "name": "o1 (OpenAI)" }));
        dynamic_models.push(json!({ "id": "o3-mini", "name": "o3-mini (OpenAI)" }));
    }

    let api_key = if !conf.api_key_gemini_free.trim().is_empty() {
        conf.api_key_gemini_free.trim().to_string()
    } else {
        conf.api_key_gemini_pro.trim().to_string()
    };

    if !api_key.is_empty() {
        let client = reqwest::Client::new();
        let url = format!("https://generativelanguage.googleapis.com/v1/models?key={}", api_key);
        // 外部APIへHTTP GETリクエストを非同期で送信し、Geminiのモデルを結合します。
        if let Ok(res) = client.get(&url).send().await {
            if let Ok(json_res) = res.json::<Value>().await {
                if let Some(models_array) = json_res["models"].as_array() {
                    for m in models_array {
                        let id = m["name"].as_str().unwrap_or("").replace("models/", "");
                        let display_name = m["displayName"].as_str().unwrap_or(&id);
                        if id.starts_with("gemini-") && !id.contains("-exp") {
                            dynamic_models.push(json!({ "id": id, "name": format!("{} (Google)", display_name) }));
                        }
                    }
                }
            }
        }
    }

    if !dynamic_models.is_empty() {
        Ok(dynamic_models)
    } else {
        Err("APIキーが未設定か、モデルの取得に失敗しました。".to_string())
    }
}

// AIへの質問リクエストを処理し、コンテキストを追加して応答を返します。
#[tauri::command]
async fn chat_with_ai(app_handle: tauri::AppHandle, message: String, model: String, is_dev_mode: bool) -> Result<Value, String> {
    let conf = config::load_config(&app_handle);
    let target_model = if model.trim().is_empty() { conf.model_id } else { model };
    
    // 選択されたモデル名に応じて、使用するAPIキーとコンテキストを動的に切り替えます。
    let (active_api_key, active_context) = {
        let model_lower = target_model.to_lowercase();
        if model_lower.contains("gpt") || model_lower.contains("o1") || model_lower.contains("o3") {
            (conf.api_key_gpt_pro, conf.context_gpt_pro)
        } else if model_lower.contains("pro") {
            (conf.api_key_gemini_pro, conf.context_gemini_pro)
        } else {
            (conf.api_key_gemini_free, conf.context_gemini_free)
        }
    };

    let local_ctx = file_analyzer::analyze_text(&message);
    let file_contents = file_reader::read_file_contents(&local_ctx.extracted_paths);
    
    let mut enhanced_message = message.clone();

    // プログラミング関連の質問であるかを判定し、言語固有の指示を付与します。
    if let Some(prog_ctx) = program_ops::analyze_programming_request(&message) {
        crate::send_instruction::send_progress(&app_handle, &format!("{}の開発依頼として専門知識をロードします。", prog_ctx.target_language));
        enhanced_message.push_str("\n\n");
        enhanced_message.push_str(&prog_ctx.specific_instructions);
    }

    // 抽出したローカルファイルの内容が存在する場合、プロンプトの末尾に追記します。
    if !file_contents.is_empty() {
        crate::send_instruction::send_progress(&app_handle, "テキストファイルの内容をコンテキストにロードしました。");
        enhanced_message.push_str("\n\n【指定されたファイル内容】");
        enhanced_message.push_str(&file_contents);
    }

    if is_dev_mode {
        match decode::analyze_intent(&app_handle, &enhanced_message).await {
            Ok(plan) => {
                return Ok(serde_json::json!({ "text": format!("```json\n{}\n```", serde_json::to_string_pretty(&plan).unwrap()) }));
            },
            Err(_) => {}
        }
    }

    crate::send_instruction::send_progress(&app_handle, "応答を生成中です...");
    ai_parser::chat_with_ai_api(&active_api_key, &target_model, &active_context, &enhanced_message, is_dev_mode).await
}

// 開発モードにおけるタスク自動生成とファイル出力を担当するコマンドです。
#[tauri::command]
async fn generate_theme(app_handle: tauri::AppHandle, user_request: String, model: String, output_path: Option<String>) -> Result<String, String> {
    let conf = config::load_config(&app_handle);
    let target_model = if model.trim().is_empty() { conf.model_id.clone() } else { model };
    
    // 生成処理は主にGeminiを使用するため、無料キーまたは有料キーを選択します。（必要ならGPTも可能）
    let active_api_key = if !conf.api_key_gemini_free.trim().is_empty() { conf.api_key_gemini_free } else { conf.api_key_gemini_pro };
    
    let manager = web_ops::WebStyleManager::new(active_api_key, target_model);
    manager.generate_theme_css(&app_handle, &user_request, output_path).await
}

// 指定された画像ファイルのバイナリをBase64文字列に変換して返します。
#[tauri::command]
fn read_image_base64(path: String) -> String {
    if path.starts_with("data:image") { return path; }
    use base64::{engine::general_purpose, Engine as _};
    
    if let Ok(bytes) = std::fs::read(&path) {
        let b64 = general_purpose::STANDARD.encode(&bytes);
        let ext = path.split('.').last().unwrap_or("").to_lowercase();
        let mime = if ext == "png" { "image/png" } else if ext == "gif" { "image/gif" } else { "image/jpeg" };
        format!("data:{};base64,{}", mime, b64)
    } else { "".to_string() }
}

// Tauriアプリケーションのメインループを起動するためのエントリポイントです。
#[cfg_attr(mobile, tauri::mobile_entry_point)]
pub fn run() {
    tauri::Builder::default()
        .invoke_handler(tauri::generate_handler![
            get_setting,
            save_setting,
            get_clean_models,
            chat_with_ai,       
            generate_theme,     
            read_image_base64,
            run_powershell,
            read_file_content,
            write_file_content,
            scan_directory,
            list_directory,
            get_current_dir
        ])
        .run(tauri::generate_context!())
        .expect("error while running tauri application");
}