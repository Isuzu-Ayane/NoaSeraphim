// src-tauri/src/models.rs
/*
 * プログラムの概要説明: アプリケーション全体のデータ構造（モデル）定義
 * プロジェクトの責任範囲に関する注記: NoaSeraphimは本プログラムの動作について一切の責任を負いません。
 * 初回作成年月日: 2026-03-16
 * 更新履歴:
 * 2026-03-25: サービス別（Gemini無料/有料、GPT有料）に構造を分割。
 * 2026-03-25: プロジェクト一覧を保存するための projects フィールドを追加。
 * プロジェクトの権利表示: (C) NoaSeraphim
 * 利用範囲に関する制限事項: 非商用利用に限る
 */

use serde::{Deserialize, Serialize};

// 構成ファイルとアプリケーション間で共有されるデータ構造体です。
#[derive(Debug, Serialize, Deserialize, Clone)]
pub struct Config {
    // プロジェクトのパス一覧をカンマ区切りの文字列として保持します。
    pub projects: String,

    // 各サービス・プランに応じたAPIキーを個別に管理します。
    pub api_key_gemini_free: String,
    pub api_key_gemini_pro: String,
    pub api_key_gpt_pro: String,

    // 各サービス・プランに応じたコンテキスト（システムプロンプト）を個別に管理します。
    pub context_gemini_free: String,
    pub context_gemini_pro: String,
    pub context_gpt_pro: String,

    // 選択されたモデルIDやUI設定のプロパティ群です。
    pub model_id: String,
    pub background_path: String,
    pub background_color: String,
    pub ai_name: String,
    pub user_name: String,
}

impl Default for Config {
    fn default() -> Self {
        // 設定ファイルが存在しない場合の安全なフォールバック状態を提供します。
        Self {
            projects: "".to_string(),
            api_key_gemini_free: "".to_string(),
            api_key_gemini_pro: "".to_string(),
            api_key_gpt_pro: "".to_string(),
            context_gemini_free: "あなたは名古屋弁で話すAI「ナオ」だて。".to_string(),
            context_gemini_pro: "あなたは名古屋弁で話すAI「ナオ」だて。".to_string(),
            context_gpt_pro: "あなたは名古屋弁で話すAI「ナオ」だて。".to_string(),
            model_id: "gemini-3.0-flash-preview".to_string(),
            background_path: "".to_string(),
            background_color: "#f4f9fc".to_string(),
            ai_name: "Nao".to_string(),
            user_name: "セラ".to_string(),
        }
    }
}

// チャット応答のテキストとトークン使用量を格納する構造体です。
#[derive(Serialize)]
pub struct ChatResponse {
    pub text: String,
    pub usage: String,
}

// 動的に取得したAIモデルのIDと表示名を紐付けるための構造体です。
#[derive(Serialize, Deserialize)]
pub struct ModelInfo {
    pub id: String,
    pub name: String,
}

// 開発モードにおける個々の実行タスクを表現する構造体です。
#[derive(Debug, Serialize, Deserialize, Clone)]
pub struct Task {
    pub id: i32,
    pub action: String,
    pub desc: String,
    pub is_finished: bool,
}

// 解析されたユーザーの意図と、それに伴うタスクの集合（キュー）を管理する構造体です。
#[derive(Debug, Serialize, Deserialize, Clone)]
pub struct TaskQueue {
    pub status: String,
    pub intent: String,
    pub tasks: Vec<Task>,
    pub message: String,
    #[serde(default)]
    pub target_path: String,
}