/*
 * プログラムの概要説明: システム操作、ファイル読み書き、ディレクトリ走査などの機能を提供するTauriコマンド群
 * プロジェクトの責任範囲に関する注記: NoaSeraphimは本プログラムの動作について一切の責任を負いません。
 * 初回作成年月日: 2026-03-16
 * 更新履歴:
 * 2026-03-25: エクスプローラ用のディレクトリリスト取得機能(list_directory)を追加。コメント規約の適用。
 * 2026-03-25: カレントディレクトリ取得機能(get_current_dir)を追加。
 * プロジェクトの権利表示: (C) NoaSeraphim
 * 利用範囲に関する制限事項: 商用利用不可
 */

use std::process::Command;
use std::fs::{self, File};
use std::io::Write;
use std::path::Path;
use serde::Serialize;

// 画面のエクスプローラにファイルやディレクトリの情報を渡すための構造体です。
#[derive(Debug, Serialize)]
pub struct FileEntry {
    name: String,
    path: String,
    is_dir: bool,
}

// UIから渡されたPowerShellスクリプトを実行し、結果を返すコマンド処理です。
#[tauri::command]
pub fn run_powershell(script: String) -> Result<String, String> {
    // セキュリティや環境に依存しないよう、プロファイルなしでコマンドを実行します。
    let output = Command::new("powershell")
        .args(["-NoProfile", "-Command", &script])
        .output()
        .map_err(|e| e.to_string())?;
    
    // 実行結果の標準出力と標準エラー出力をそれぞれ文字列として取得します。
    let stdout = String::from_utf8_lossy(&output.stdout).to_string();
    let stderr = String::from_utf8_lossy(&output.stderr).to_string();
    
    // エラーが存在する場合は、通常の出力にエラー内容を結合して返却します。
    let mut final_output = stdout;
    if !stderr.is_empty() {
        final_output = format!("{}\n[エラー発生]\n{}", final_output, stderr);
    }
    Ok(final_output)
}

// 指定されたパスのファイル内容を読み込み、文字列として返すコマンド処理です。
#[tauri::command]
pub fn read_file_content(path: String) -> Result<String, String> {
    fs::read_to_string(path).map_err(|e| e.to_string())
}

/*
// 2026-03-25 年月日コメントアウト：第三者視点での標準的な完了メッセージに変更するため
#[tauri::command]
pub fn write_file_content(path: String, content: String) -> Result<String, String> {
    let mut file = File::create(path).map_err(|e| e.to_string())?;
    file.write_all(content.as_bytes()).map_err(|e| e.to_string())?;
    Ok("ファイルの書き込みが完了しただて。".to_string())
}
*/
// 指定されたパスにテキストファイルを作成または上書き保存するコマンド処理です。
#[tauri::command]
pub fn write_file_content(path: String, content: String) -> Result<String, String> {
    // ファイルを生成し、失敗した場合はエラーメッセージを文字列化して返します。
    let mut file = File::create(path).map_err(|e| e.to_string())?;
    file.write_all(content.as_bytes()).map_err(|e| e.to_string())?;
    Ok("ファイルの書き込みが完了しました。".to_string())
}

// ディレクトリ内を再帰的に走査し、ファイルパスのリストを取得するヘルパー関数です。
fn visit_dirs(dir: &Path, prefix: &Path, result: &mut Vec<String>) -> std::io::Result<()> {
    if dir.is_dir() {
        // ディレクトリ内のすべてのエントリに対して反復処理を行います。
        for entry in fs::read_dir(dir)? {
            let entry = entry?;
            let path = entry.path();
            
            // サブディレクトリが見つかった場合は再帰的に本関数を呼び出します。
            if path.is_dir() {
                visit_dirs(&path, prefix, result)?;
            } else {
                // ファイルの場合は相対パスに変換し、リストに追加します。
                if let Ok(stripped) = path.strip_prefix(prefix) {
                    result.push(stripped.display().to_string());
                } else {
                    result.push(path.display().to_string());
                }
            }
            // システムのメモリ超過を防ぐため、取得上限を500件に制限します。
            if result.len() >= 500 {
                break;
            }
        }
    }
    Ok(())
}

// 指定パス以下の全ファイルをスキャンし、結果を文字列で返すコマンド処理です。
#[tauri::command]
pub fn scan_directory(path: String) -> Result<String, String> {
    let mut files = Vec::new();
    let root = Path::new(&path);
    
    // 対象パスが存在しない場合は即座にエラーとして処理を中断します。
    if !root.exists() {
        return Err(format!("指定されたパス({})が見つかりません。", path));
    }

    let _ = visit_dirs(root, root, &mut files);
    
    // スキャン結果が0件だった場合の専用メッセージを返却します。
    if files.is_empty() {
        return Ok("(ファイルが見つかりませんでした)".to_string());
    }
    
    // 結果を改行区切りで結合し、文字数上限を超える場合は末尾を切り詰めます。
    let mut output = files.join("\n");
    if output.len() > 3000 {
        output = output[..3000].to_string() + "\n...（ファイル数が多すぎるため以降省略）";
    }
    Ok(output)
}

// UI側のエクスプローラ表示用として、直下のファイルとフォルダの一覧を取得します。
#[tauri::command]
pub async fn list_directory(path: String) -> Result<Vec<FileEntry>, String> {
    let root_path = Path::new(&path);
    // 対象パスがディレクトリとして存在するかを最初に検証します。
    if !root_path.exists() || !root_path.is_dir() {
        return Err("無効なパスです。".to_string());
    }

    let mut entries = Vec::new();
    // フォルダの直下にあるエントリのみを走査し、リスト化します。
    match fs::read_dir(root_path) {
        Ok(read_dir) => {
            // 各エントリの名前とパス、フォルダ判定を取得して構造体に詰めます。
            for entry_result in read_dir {
                if let Ok(entry) = entry_result {
                    let file_type = entry.file_type().unwrap();
                    entries.push(FileEntry {
                        name: entry.file_name().to_string_lossy().into_owned(),
                        path: entry.path().to_string_lossy().into_owned(),
                        is_dir: file_type.is_dir(),
                    });
                }
            }
            // 表示を見やすくするため、フォルダを上に、名前順でソートします。
            entries.sort_by(|a, b| {
                b.is_dir.cmp(&a.is_dir).then_with(|| a.name.to_lowercase().cmp(&b.name.to_lowercase()))
            });
            Ok(entries)
        }
        Err(e) => Err(e.to_string()),
    }
}

// アプリケーションの現在の作業ディレクトリを取得するコマンド処理です。
#[tauri::command]
pub fn get_current_dir() -> Result<String, String> {
    // OSの環境変数から現在の作業ディレクトリを取得し、文字列に変換して返します。
    std::env::current_dir()
        .map(|path| path.display().to_string())
        .map_err(|e| e.to_string())
}