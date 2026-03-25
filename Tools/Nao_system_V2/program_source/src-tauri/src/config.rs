// src-tauri/src/config.rs
/*
 * プログラムの概要説明: 設定ファイル(Config)の読み書き機能。ini形式を使用し、画像は外部ファイル化して肥大化を防止。
 * プロジェクトの責任範囲に関する注記: NoaSeraphimは本プログラムの動作について一切の責任を負いません。
 * 初回作成年月日: 2026-03-16
 * 更新履歴:
 * 2026-03-25: INIのセクション設計を機能ごとに分割（API, Screen, Context, Name）。破損検知および初期化機能を追加。
 * 2026-03-25: サービス別（Gemini無料/有料、GPT有料）に独立したキーとコンテキストを読み書きするよう構造を拡張。
 * 2026-03-25: プロジェクト一覧を保存するための Projects セクションを追加。
 * プロジェクトの権利表示: (C) NoaSeraphim
 * 利用範囲に関する制限事項: 非商用利用に限る
 */

use crate::models::Config;
use crate::crypto::{encrypt, decrypt};
use ini::Ini;
use std::path::PathBuf;
use tauri::Manager;
use std::fs;

// アプリの設定ディレクトリパスを取得し、INIファイルのパスを生成します。
pub fn get_config_path(app_handle: &tauri::AppHandle) -> PathBuf {
    let dir = app_handle.path().app_config_dir().expect("設定ディレクトリの取得に失敗しました");
    if !dir.exists() {
        // ディレクトリが存在しない場合は新規に作成します。空間計算量 O(1) です。
        let _ = fs::create_dir_all(&dir);
    }
    dir.join("settings.ini") 
}

// INIファイルが肥大化・破損していないか診断する関数です。
pub fn is_config_valid(app_handle: &tauri::AppHandle) -> bool {
    let path = get_config_path(app_handle);
    // ファイルが存在しない場合は新規作成されるため、論理的に正常とみなします。
    if !path.exists() { return true; }

    match Ini::load_from_file(&path) {
        Ok(conf) => {
            // Screenセクションのbg_image、または旧Settingsセクションのbackground_pathを検査します。
            let bg_new = conf.section(Some("Screen")).and_then(|s| s.get("bg_image"));
            let bg_old = conf.section(Some("Settings")).and_then(|s| s.get("background_path"));
            
            // 値が "data:image/" で始まる場合はBase64データが混入しファイルが破損していると判定します。
            if let Some(bg) = bg_new.or(bg_old) {
                if bg.starts_with("data:image/") {
                    return false;
                }
            }
            true
        },
        // パースエラーが発生した場合もファイル破損とみなします。
        Err(_) => false,
    }
}

// 破損したINIファイルをバックアップし、初期状態にリセットする関数です。
pub fn reset_config(app_handle: &tauri::AppHandle) {
    let path = get_config_path(app_handle);
    if path.exists() {
        // 既存のファイルを.bak拡張子に変更して退避させます。
        let bak_path = path.with_extension("ini.bak");
        let _ = fs::rename(&path, bak_path);
    }
    // デフォルトの設定値を用いて新規ファイルを生成し、システム状態を安定化させます。
    save_config(app_handle, &Config::default());
}

// 分割された各セクションから設定を読み込みます。
pub fn load_config(app_handle: &tauri::AppHandle) -> Config {
    let path = get_config_path(app_handle);
    // ファイルが存在しない場合は初期値の構造体を返します。
    if !path.exists() { return Config::default(); }

    let conf = match Ini::load_from_file(&path) {
        Ok(c) => c,
        // パースエラー発生時は安全のため初期値を返却し、異常系への遷移を防ぎます。
        Err(_) => return Config::default(),
    };

    let proj_sec = conf.section(Some("Projects"));
    let api_sec = conf.section(Some("API"));
    let screen_sec = conf.section(Some("Screen"));
    let context_sec = conf.section(Some("Context"));
    let name_sec = conf.section(Some("Name"));

    // プロジェクトのリストをプレーンテキストで取得します。
    let projects = proj_sec.and_then(|s| s.get("list")).unwrap_or("").to_string();

    // セクションから各サービスの暗号化済みキーを読み出し、復号して文字列化します。
    let api_gemini_free = decrypt(&api_sec.and_then(|s| s.get("gemini_free")).unwrap_or("").to_string());
    let api_gemini_pro = decrypt(&api_sec.and_then(|s| s.get("gemini_pro")).unwrap_or("").to_string());
    let api_gpt_pro = decrypt(&api_sec.and_then(|s| s.get("gpt_pro")).unwrap_or("").to_string());

    // セクションから各サービスのコンテキストを読み出し、復号します。空の場合はデフォルト値を適用します。
    let mut ctx_gemini_free = decrypt(&context_sec.and_then(|s| s.get("gemini_free")).unwrap_or("").to_string());
    if ctx_gemini_free.is_empty() { ctx_gemini_free = "あなたは名古屋弁で話すAI「ナオ」だて。".to_string(); }

    let mut ctx_gemini_pro = decrypt(&context_sec.and_then(|s| s.get("gemini_pro")).unwrap_or("").to_string());
    if ctx_gemini_pro.is_empty() { ctx_gemini_pro = "あなたは名古屋弁で話すAI「ナオ」だて。".to_string(); }

    let mut ctx_gpt_pro = decrypt(&context_sec.and_then(|s| s.get("gpt_pro")).unwrap_or("").to_string());
    if ctx_gpt_pro.is_empty() { ctx_gpt_pro = "あなたは名古屋弁で話すAI「ナオ」だて。".to_string(); }

    // 読み込んだ情報を構造体にマップして返却します。
    Config {
        projects,
        api_key_gemini_free: api_gemini_free,
        api_key_gemini_pro: api_gemini_pro,
        api_key_gpt_pro: api_gpt_pro,
        context_gemini_free: ctx_gemini_free,
        context_gemini_pro: ctx_gemini_pro,
        context_gpt_pro: ctx_gpt_pro,
        model_id: api_sec.and_then(|s| s.get("model_id")).unwrap_or("gemini-3.0-flash-preview").to_string(),
        background_path: screen_sec.and_then(|s| s.get("bg_image")).unwrap_or("").to_string(),
        background_color: screen_sec.and_then(|s| s.get("bg_color")).unwrap_or("#f4f9fc").to_string(),
        ai_name: name_sec.and_then(|s| s.get("ai_name")).unwrap_or("Nao").to_string(),
        user_name: name_sec.and_then(|s| s.get("user_name")).unwrap_or("セラ").to_string(),
    }
}

// 分割された各セクションへ設定値を永続化します。
pub fn save_config(app_handle: &tauri::AppHandle, config: &Config) {
    let dir = app_handle.path().app_config_dir().expect("設定ディレクトリの取得に失敗しました");
    let path = dir.join("settings.ini");
    let mut final_bg_path = config.background_path.clone();

    // Base64形式の巨大な画像データがINIに混入するのを防ぐため、実体ファイルへ分離して保存します。
    if final_bg_path.starts_with("data:image/") {
        if let Some(comma_pos) = final_bg_path.find(',') {
            // カンマを境界としてMIMEヘッダとペイロードを分割抽出します。
            let base64_str = &final_bg_path[comma_pos + 1..];
            use base64::{engine::general_purpose, Engine as _};
            
            // エンコード文字列をバイト配列（ベクトル）に変換します。
            if let Ok(image_bytes) = general_purpose::STANDARD.decode(base64_str) {
                let header = &final_bg_path[..comma_pos];
                let ext = if header.contains("image/png") { "png" }
                          else if header.contains("image/gif") { "gif" }
                          else if header.contains("image/webp") { "webp" }
                          else { "jpg" };
                
                // 設定フォルダ内に専用の画像ファイル名で保存パスを生成します。
                let image_filename = format!("bg_image.{}", ext);
                let image_path = dir.join(&image_filename);
                
                // バイトストリームをファイルシステムに書き出し、成功時にパスを文字列化してINI用変数に保持します。
                if fs::write(&image_path, image_bytes).is_ok() {
                    final_bg_path = image_path.to_string_lossy().into_owned();
                }
            }
        }
    }

    let mut conf = Ini::new();
    
    // プロジェクトのリストをINIセクションに配置します。
    conf.with_section(Some("Projects"))
        .set("list", &config.projects);

    // API関連の設定をサービスごとに暗号化を適用しつつ配置します。
    conf.with_section(Some("API"))
        .set("gemini_free", encrypt(&config.api_key_gemini_free))
        .set("gemini_pro", encrypt(&config.api_key_gemini_pro))
        .set("gpt_pro", encrypt(&config.api_key_gpt_pro))
        .set("model_id", &config.model_id);

    // システムコンテキストをサービスごとに暗号化して配置します。
    conf.with_section(Some("Context"))
        .set("gemini_free", encrypt(&config.context_gemini_free))
        .set("gemini_pro", encrypt(&config.context_gemini_pro))
        .set("gpt_pro", encrypt(&config.context_gpt_pro));

    // 画面表示関連のパラメータ（分離済みの画像パスを含む）を配置します。
    conf.with_section(Some("Screen"))
        .set("bg_image", final_bg_path)
        .set("bg_color", &config.background_color);

    // 各種呼称パラメータを配置します。
    conf.with_section(Some("Name"))
        .set("ai_name", &config.ai_name)
        .set("user_name", &config.user_name);
        
    // 構成されたINIオブジェクトを物理ファイルへ書き出します。
    let _ = conf.write_to_file(&path);
}