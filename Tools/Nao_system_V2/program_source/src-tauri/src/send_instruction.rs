// src-tauri/src/send_instruction.rs
use tauri::Emitter;
use std::fs::OpenOptions;
use std::io::Write;

#[derive(Clone, serde::Serialize)]
pub struct ProgressPayload {
    message: String,
}

// 2026-03-16: フリーズや無限ループの原因調査のため、指定パスへのデバッグログ出力を追加。古い処理はコメントアウト。
/*
pub fn send_progress(app_handle: &tauri::AppHandle, msg: &str) {
    let payload = ProgressPayload { 
        message: msg.to_string() 
    };
    let _ = app_handle.emit("thinking-progress", payload);
}
*/
pub fn send_progress(app_handle: &tauri::AppHandle, msg: &str) {
    let payload = ProgressPayload { 
        message: msg.to_string() 
    };
    // 画面側への送信（パタパタ用）
    let _ = app_handle.emit("thinking-progress", payload);

    // デバッグ用にログファイルへ追記
    let log_path = r"K:\System_Make\nao_local_system\nao_debug_progress.log";
    if let Ok(mut file) = OpenOptions::new().create(true).append(true).open(log_path) {
        // 時間を付けるとライブラリの追加が必要になるもんで、今回はシンプルにメッセージだけ書き出すだて！
        let _ = writeln!(file, "[AI Progress] {}", msg);
    }
}