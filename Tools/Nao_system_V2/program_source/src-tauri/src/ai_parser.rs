// src-tauri/src/ai_parser.rs
/*
 * プログラムの概要説明: GeminiおよびGPT APIへのHTTPリクエストとレスポンス解析処理
 * プロジェクトの責任範囲に関する注記: NoaSeraphimは本プログラムの動作について一切の責任を負いません。
 * 初回作成年月日: 2026-03-16
 * 更新履歴:
 * 2026-03-25: OpenAI (GPT) APIへの対応処理を追加し、モデル名による動的ルーティングを実装。
 * プロジェクトの権利表示: (C) NoaSeraphim
 * 利用範囲に関する制限事項: 商用利用不可
 */

use reqwest::Client;
use serde_json::{json, Value};

// 2026-03-25 年月日コメントアウト: 旧来のGemini専用エンドポイントを廃止し、統合エンドポイントへ差し替え
/*
pub async fn chat_with_gemini_json(api_key: &str, model: &str, context: &str, message: &str, is_dev_mode: bool) -> Result<Value, String> {
    // ... 旧処理 ...
}
*/

// モデル名に応じて内部でGeminiとGPTをルーティングする統合APIインターフェースです。
pub async fn chat_with_ai_api(api_key: &str, model: &str, context: &str, message: &str, is_dev_mode: bool) -> Result<Value, String> {
    let clean_api_key = api_key.trim();
    if clean_api_key.is_empty() {
        return Err("APIキーが設定されとらんみたいだわ。⚙️設定から登録してちょうだい！".to_string());
    }

    let clean_model = if model.trim().is_empty() { "gemini-3.0-flash-preview" } else { model.trim() };

    let model_lower = clean_model.to_lowercase();
    // 文字列の包含判定によって、対象がOpenAIのGPT系モデルであるかを論理的に評価します。
    if model_lower.contains("gpt") || model_lower.contains("o1") || model_lower.contains("o3") {
        chat_with_gpt(clean_api_key, clean_model, context, message, is_dev_mode).await
    } else {
        chat_with_gemini(clean_api_key, clean_model, context, message, is_dev_mode).await
    }
}

// 既存のGemini APIへの通信を行う内部関数です。
async fn chat_with_gemini(api_key: &str, model: &str, context: &str, message: &str, is_dev_mode: bool) -> Result<Value, String> {
    let actual_model = if model.starts_with("models/") {
        model.to_string()
    } else {
        format!("models/{}", model)
    };

    let url = format!("https://generativelanguage.googleapis.com/v1beta/{}:generateContent?key={}", actual_model, api_key);
    
    let mut request_body = json!({
        "contents": [{ "parts": [{"text": message}] }]
    });

    if is_dev_mode {
        // 開発モード時はJSON出力を強制するシステムプロンプトを合成します。
        let system_instruction = "あなたは自律型APIエージェントです。以下のJSON形式1つだけを必ず出力してください。\n{\n  \"status\": \"plan_ready\",\n  \"intent\": \"web_generation | local_command | general_chat\",\n  \"tasks\": [\n    { \"id\": 1, \"action\": \"具体的なアクション\", \"desc\": \"やることの説明\", \"is_finished\": false }\n  ],\n  \"message\": \"ユーザーへプランを提案する名古屋弁のメッセージ\",\n  \"target_path\": \"ユーザーがパスを指定した場合はそのパス。指定がない場合は null\"\n}\nMarkdownの```jsonや```は不要です。純粋なJSONのみを出力してください。";
        
        let full_sys = if context.trim().is_empty() {
            system_instruction.to_string()
        } else {
            format!("{}\n\n{}", system_instruction, context.trim())
        };
        request_body["systemInstruction"] = json!({ "parts": [{ "text": full_sys }] });
        request_body["generationConfig"] = json!({ "responseMimeType": "application/json" });
    } else {
        if !context.trim().is_empty() {
            request_body["systemInstruction"] = json!({ "parts": [{ "text": context.trim() }] });
        }
    }
    
    let client = Client::new();
    let res = client.post(&url).json(&request_body).send().await.map_err(|e| e.to_string())?;
    let json_res: Value = res.json().await.map_err(|e| e.to_string())?;
    
    if let Some(error) = json_res.get("error") {
        let error_msg = error["message"].as_str().unwrap_or("詳細不明のエラーだて");
        let error_code = error["code"].as_i64().unwrap_or(0);
        return Err(format!("Google API エラー ({}): {}", error_code, error_msg));
    }

    if let Some(candidate) = json_res["candidates"].as_array().and_then(|a| a.get(0)) {
        let text = candidate["content"]["parts"][0]["text"].as_str().unwrap_or("").to_string();

        if is_dev_mode {
            let mut clean_text = text.trim().to_string();
            // JSONブロックの前後に不要な文字が含まれている場合に備え、括弧でスライスします。
            if let (Some(start), Some(end)) = (clean_text.find('{'), clean_text.rfind('}')) {
                clean_text = clean_text[start..=end].to_string();
            }
            if let Ok(parsed_json) = serde_json::from_str::<Value>(&clean_text) {
                return Ok(json!({ "text": format!("```json\n{}\n```", serde_json::to_string_pretty(&parsed_json).unwrap()) }));
            }
        }
        Ok(json!({ "text": text }))
    } else {
        Err("Geminiから返答のテキストが見つからんかったわ。".to_string())
    }
}

// OpenAI API (GPT) へリクエストを送信し、レスポンスを解析する内部関数です。
async fn chat_with_gpt(api_key: &str, model: &str, context: &str, message: &str, is_dev_mode: bool) -> Result<Value, String> {
    // GPT用の正しいチャット補完エンドポイントを使用します。
    let url = "https://api.openai.com/v1/chat/completions";
    let mut messages = Vec::new();
    
    // 開発モードか通常モードかで、システムプロンプトの構成を分岐させます。
    if is_dev_mode {
        let system_instruction = "あなたは自律型APIエージェントです。以下のJSON形式1つだけを必ず出力してください。\n{\n  \"status\": \"plan_ready\",\n  \"intent\": \"web_generation | local_command | general_chat\",\n  \"tasks\": [\n    { \"id\": 1, \"action\": \"具体的なアクション\", \"desc\": \"やることの説明\", \"is_finished\": false }\n  ],\n  \"message\": \"ユーザーへプランを提案する名古屋弁のメッセージ\",\n  \"target_path\": \"ユーザーがパスを指定した場合はそのパス。指定がない場合は null\"\n}\nMarkdownの```jsonや```は不要です。純粋なJSONのみを出力してください。";
        
        let full_sys = if context.trim().is_empty() {
            system_instruction.to_string()
        } else {
            format!("{}\n\n{}", system_instruction, context.trim())
        };
        messages.push(json!({"role": "system", "content": full_sys}));
    } else {
        if !context.trim().is_empty() {
            messages.push(json!({"role": "system", "content": context.trim()}));
        }
    }
    
    // ユーザーの入力メッセージを会話配列にスタックします。
    messages.push(json!({"role": "user", "content": message}));
    
    let mut request_body = json!({
        "model": model,
        "messages": messages
    });
    
    // GPT-4以降の場合、JSONモードを強制して出力の安定性を高めます。（o1モデルなど一部未対応の場合があるので注意）
    if is_dev_mode && !model.contains("o1") && !model.contains("o3") {
        request_body["response_format"] = json!({ "type": "json_object" });
    }

    let client = Client::new();
    // ヘッダーにBearerトークンとしてAPIキーを設定し、非同期POSTリクエストを送信します。
    let res = client.post(url)
        .bearer_auth(api_key)
        .json(&request_body)
        .send()
        .await
        .map_err(|e| e.to_string())?;
        
    let json_res: Value = res.json().await.map_err(|e| e.to_string())?;
    
    // OpenAI固有のエラー構造を解析し、UI向けに整形して返却します。
    if let Some(error) = json_res.get("error") {
        let error_msg = error["message"].as_str().unwrap_or("詳細不明のエラーだて");
        return Err(format!("OpenAI API エラー: {}", error_msg));
    }
    
    // choices配列の先頭要素から、生成されたテキスト本体を抽出します。
    if let Some(choice) = json_res["choices"].as_array().and_then(|a| a.get(0)) {
        let text = choice["message"]["content"].as_str().unwrap_or("").to_string();
        
        if is_dev_mode {
            let mut clean_text = text.trim().to_string();
            if let (Some(start), Some(end)) = (clean_text.find('{'), clean_text.rfind('}')) {
                clean_text = clean_text[start..=end].to_string();
            }
            if let Ok(parsed_json) = serde_json::from_str::<Value>(&clean_text) {
                return Ok(json!({ "text": format!("```json\n{}\n```", serde_json::to_string_pretty(&parsed_json).unwrap()) }));
            }
        }
        Ok(json!({ "text": text }))
    } else {
        Err("GPTから返答のテキストが見つからんかったわ。".to_string())
    }
}