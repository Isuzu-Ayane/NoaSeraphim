// src-tauri/src/decode.rs
/*
 * プログラムの概要説明: ユーザー入力からの意図解析(Intent Decoding)とJSONタスクプランの生成
 * プロジェクトの責任範囲に関する注記: NoaSeraphimは本プログラムの動作について一切の責任を負いません。
 * 初回作成年月日: 2026-03-16
 * 更新履歴:
 * 2026-03-25: GPTモデル対応のため、APIキーの動的選択および統合API(chat_with_ai_api)への移行
 * 2026-03-25: app_config_dir の型変更エラー(Result)に対応して修正
 * プロジェクトの権利表示: (C) NoaSeraphim
 * 利用範囲に関する制限事項: 非商用利用に限る
 */

use serde_json::Value;
use tauri::{AppHandle, Manager}; 
use std::fs;

use crate::send_instruction::send_progress;
use crate::ai_parser;
use crate::config;
use crate::models::TaskQueue;

// ユーザーの自然言語入力を解析し、システムの実行可能なタスクキュー(論理プラン)に変換します。
pub async fn analyze_intent(app_handle: &AppHandle, user_request: &str) -> Result<Value, String> {
    let conf = config::load_config(app_handle);

    send_progress(app_handle, "🔍 セラの指示を細かく分解しとるよ...");
    // 処理の同期とUIのレンダリング待機のため、意図的な遅延を挿入します。
    tokio::time::sleep(std::time::Duration::from_secs(1)).await;
    send_progress(app_handle, "🧠 過去のパターンと照らし合わせ中だて...");
    tokio::time::sleep(std::time::Duration::from_secs(1)).await;

    // AIに対する厳密な出力制約（スキーマ定義）を定めたプロンプト行列を構成します。
    let decode_prompt = r#"あなたは優秀なAIシステムプランナーです。
ユーザーの入力を解析し、どのような処理が必要か判断して、以下の形式のJSONのみを出力してください。
{
    "status": "plan_ready",
    "intent": "web_generation | local_command | general_chat",
    "tasks": [
        { "id": 1, "action": "具体的なアクション", "desc": "やることの説明", "is_finished": false }
    ],
    "message": "ユーザーへプランを提案する名古屋弁のメッセージ",
    "target_path": "ユーザーがパスを指定した場合はそのパス。指定がない場合は null"
}
Markdownの```jsonや```は不要です。純粋なJSONのみを出力してください。
また、messageは必ず「名古屋弁」で返すこと。
語尾に「だて」「だわ」「だがね」「なも」などを使い、一人称は「うち」とする。
例：「プランを考えたでね！」「このフォルダを調べるんだわ！」「これで行こまい！」
記号は控えて、親しみやすい文字"#;

    send_progress(app_handle, "🚀 AIに最適な実行プランを相談しとるわ...（通信開始）");

    let target_model = conf.model_id.clone();
    
    // 2026-03-25: モデル名に応じて開発モードの解析に使用するAPIキーを動的に決定します。
    // 文字列ベースのパターンマッチングで対象サービスを識別します。
    let active_api_key = if target_model.to_lowercase().contains("gpt") || target_model.to_lowercase().contains("o1") || target_model.to_lowercase().contains("o3") {
        conf.api_key_gpt_pro
    } else if target_model.to_lowercase().contains("pro") {
        conf.api_key_gemini_pro
    } else {
        conf.api_key_gemini_free
    };

    // 2026-03-25 年月日コメントアウト: 旧Gemini専用呼び出しを廃止
    /*
    let response = ai_parser::chat_with_gemini_json(
        &conf.api_key, 
        &target_model, 
        decode_prompt, 
        user_request, 
        true
    ).await?;
    */
    // 統合APIへリクエストを送信し、構造化されたJSON文字列の返却を待機します。
    let response = ai_parser::chat_with_ai_api(
        &active_api_key, 
        &target_model, 
        decode_prompt, 
        user_request, 
        true
    ).await?;

    send_progress(app_handle, "📥 AIから返答が来たでね！解析するわ！（通信完了）");

    // 返却されたJSON文字列をTaskQueue構造体へデシリアライズ(逆変換)できるか検証します。
    if let Ok(queue) = serde_json::from_value::<TaskQueue>(response.clone()) {
        // 設定ディレクトリのパスを取得し、中間データの出力先を決定します。
        // 2026-03-25 修正: Tauri v2 では app_config_dir() は Result を返すため Ok() で受けます。
        if let Ok(config_dir) = app_handle.path().app_config_dir() {
            let queue_path = config_dir.join("task_queue.json");
            // 構造体を整形されたJSON文字列に再シリアライズし、ファイルへ永続化します。
            if let Ok(json_data) = serde_json::to_string_pretty(&queue) {
                let _ = fs::write(queue_path, json_data);
                send_progress(app_handle, "💾 中間ファイルにプランを記録しただて！");
            }
        }
    }

    Ok(response)
}