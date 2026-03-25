// src-tauri/src/web_ops.rs
/*
 * プログラムの概要説明: Webフロントエンド(HTML/CSS/JS)の自動生成およびファイル書き出し機能
 * プロジェクトの責任範囲に関する注記: NoaSeraphimは本プログラムの動作について一切の責任を負いません。
 * 初回作成年月日: 2026-03-16
 * 更新履歴:
 * 2026-03-25: 統合API(chat_with_ai_api)への移行に伴う関数呼び出しの差し替え
 * 2026-03-25: file_analyzer の未使用インポート警告を解消
 * プロジェクトの権利表示: (C) NoaSeraphim
 * 利用範囲に関する制限事項: 非商用利用に限る
 */

use std::fs::{self, OpenOptions};
use std::io::Write;
use std::path::Path;
use tauri::AppHandle;

use crate::ai_parser;
use crate::send_instruction::send_progress;
// 2026-03-25 年月日コメントアウト: 使われていないためコンパイラ警告を回避
// use crate::file_analyzer;

// 生成処理をカプセル化し、APIキーとモデル情報を保持するための構造体です。
pub struct WebStyleManager {
    api_key: String,
    model: String,
}

// 確率的な生成結果のブレを検証するため、送信プロンプトを外部ファイルへ逐次記録します。
fn write_prompt_log(msg: &str) {
    let log_path = r"K:\System_Make\nao_local_system\nao_debug_progress.log";
    // 既存ファイルへの追記モードでオープンし、IOロックの競合を避けます。
    if let Ok(mut file) = OpenOptions::new().create(true).append(true).open(log_path) {
        let _ = writeln!(file, "[WebOps Debug] {}", msg);
    }
}

impl WebStyleManager {
    // 構造体の初期化メソッドです。状態空間の初期ベクトルを設定します。
    pub fn new(api_key: String, model: String) -> Self {
        Self { api_key, model }
    }

    // ユーザーの要件に基づき、HTML、CSS、JSの3層構造を非同期で段階的に生成・保存します。
    pub async fn generate_theme_css(&self, app_handle: &AppHandle, user_request: &str, output_path: Option<String>) -> Result<String, String> {
        let out_dir = output_path.unwrap_or_else(|| r"C:\ai_generated_styles".to_string());
        let dir_path = Path::new(&out_dir);

        // 出力先ディレクトリが存在しない場合、木構造のノードとして新規作成します。
        if !dir_path.exists() {
            fs::create_dir_all(dir_path).map_err(|e| e.to_string())?;
        }

        let system_prompt = "あなたは優秀なWebデザイナーです。要件を満たすHTML、CSS、JSを生成してください。";
        
        // 第1段階: HTMLの生成。DOMツリーの骨組みとなる静的構造を要求します。
        let html_prompt = format!("{}\n要件: {}\n\nこの要件を満たすHTMLのみを生成してください。```html などの装飾は不要です。", system_prompt, user_request);
        send_progress(app_handle, "🌐 HTMLの構造を設計しとるわ...");
        write_prompt_log(&html_prompt);
        let html_res = self.call_gemini_with_retry(app_handle, &html_prompt, user_request).await?;
        
        // 不要なマークダウン記法を正規表現等でフィルタリングし、純粋なHTML文字列を抽出します。
        let html_clean = html_res.replace("```html", "").replace("```", "").trim().to_string();
        let html_path = dir_path.join("index.html");
        fs::write(&html_path, &html_clean).map_err(|e| e.to_string())?;

        // 第2段階: CSSの生成。HTMLに対する装飾情報（スタイルベクトル）を要求します。
        let css_prompt = format!("{}\n以下のHTMLに対するCSSのみを生成してください。\n{}\n\n```css などの装飾は不要です。", system_prompt, html_clean);
        send_progress(app_handle, "🎨 CSSでデザインを整えとるよ...");
        write_prompt_log(&css_prompt);
        let css_res = self.call_gemini_with_retry(app_handle, &css_prompt, user_request).await?;
        
        // CSSの文字列を正規化し、物理ファイルシステムへ書き込みます。
        let css_clean = css_res.replace("```css", "").replace("```", "").trim().to_string();
        let css_path = dir_path.join("style.css");
        fs::write(&css_path, &css_clean).map_err(|e| e.to_string())?;

        // 第3段階: JSの生成。状態遷移（動的振る舞い）を制御するスクリプトを要求します。
        let js_prompt = format!("{}\n以下のHTMLとCSSに対するJavaScriptのみを生成してください。\nHTML:\n{}\nCSS:\n{}\n\n```javascript などの装飾は不要です。", system_prompt, html_clean, css_clean);
        send_progress(app_handle, "⚙️ JavaScriptで動きを付けとるでね...");
        write_prompt_log(&js_prompt);
        let js_res = self.call_gemini_with_retry(app_handle, &js_prompt, user_request).await?;
        
        // JSのコードブロックをクレンジングし、最終ファイルとして保存します。
        let js_clean = js_res.replace("```javascript", "").replace("```js", "").replace("```", "").trim().to_string();
        let js_path = dir_path.join("script.js");
        fs::write(&js_path, &js_clean).map_err(|e| e.to_string())?;
        
        send_progress(app_handle, "✅ JavaScriptの生成・保存が完了しただて！");
        send_progress(app_handle, "🎉 全てのビルドが完了したわ！");

        Ok(format!("{} に HTML、CSS、JS を分けて綺麗に生成しただて！", out_dir))
    }

    // 2026-03-25 年月日コメントアウト: 旧Gemini専用呼び出しを廃止
    /*
    async fn call_gemini_with_retry(&self, app_handle: &AppHandle, prompt: &str, user_request: &str) -> Result<String, String> {
        let max_retries = 3;
        let mut attempt = 0;

        loop {
            attempt += 1;
            match ai_parser::chat_with_gemini_json(&self.api_key, &self.model, prompt, user_request, false).await { ... }
    */
    // ネットワーク層の不確実性を考慮し、指数的バックオフではなく一定間隔での再試行(Retry)を行います。
    async fn call_gemini_with_retry(&self, app_handle: &AppHandle, prompt: &str, user_request: &str) -> Result<String, String> {
        let max_retries = 3;
        let mut attempt = 0;

        loop {
            attempt += 1;
            // 統合API関数へ差し替え、再試行ロジック内で安全にコールします。GPTモデルもこれで透過的に処理可能です。
            match ai_parser::chat_with_ai_api(&self.api_key, &self.model, prompt, user_request, false).await {
                Ok(res) => {
                    // JSONレスポンス構造からテキストフィールドを抽出し、Stringとして返却します。
                    let text = res.get("text").and_then(|v| v.as_str()).unwrap_or("").to_string();
                    return Ok(text);
                },
                Err(e) => {
                    send_progress(app_handle, &format!("⚠️ APIエラー ({}回目): {}", attempt, e));
                    // 最大試行回数に達した場合、エラーを上位レイヤーへ伝播させます。
                    if attempt >= max_retries {
                        return Err(format!("{}回試したけどダメだったわ。エラー: {}", max_retries, e));
                    }
                    // リクエスト間のインターバルを設け、APIレートリミットを回避します。
                    tokio::time::sleep(std::time::Duration::from_secs(3)).await;
                }
            }
        }
    }
}