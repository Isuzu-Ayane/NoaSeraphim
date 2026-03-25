// src-tauri/src/program_ops.rs
// 2026-03-16: 新規作成。複数のプログラミング言語ごとの特性や注意点をGeminiに教え込むための専門モジュールだて！

pub struct ProgramContext {
    pub target_language: String,
    pub specific_instructions: String,
}

pub fn analyze_programming_request(user_request: &str) -> Option<ProgramContext> {
    let text = user_request.to_lowercase();
    let mut target_lang = String::new();

    // 🌟 セラのリストを元にした言語の簡易検知だて
    if text.contains("python") { target_lang = "Python".to_string(); }
    else if text.contains("typescript") || text.contains("ts") { target_lang = "TypeScript".to_string(); }
    else if text.contains("javascript") || text.contains("js") { target_lang = "JavaScript".to_string(); }
    else if text.contains("rust") { target_lang = "Rust".to_string(); }
    else if text.contains("go") || text.contains("golang") { target_lang = "Go".to_string(); }
    else if text.contains("c++") || text.contains("cpp") { target_lang = "C++".to_string(); }
    else if text.contains("c#") || text.contains("csharp") { target_lang = "C#".to_string(); }
    else if text.contains("kotlin") { target_lang = "Kotlin".to_string(); }
    else if text.contains("swift") { target_lang = "Swift".to_string(); }
    else if text.contains("zig") { target_lang = "Zig".to_string(); }
    // 2026-03-16: PowerShellやシェルスクリプトの検知を追加だて！
    else if text.contains("powershell") || text.contains("pwsh") || text.contains("ps1") { target_lang = "PowerShell".to_string(); }
    else if text.contains("shell") || text.contains("bash") || text.contains("bat") { target_lang = "Shell".to_string(); }

    if target_lang.is_empty() {
        return None; // プログラム系の依頼じゃなさそうなら何も干渉しないわ
    }

    let mut instructions = get_language_instructions(&target_lang);
    
    // 2026-03-16: 無駄なログ出力の排除を全言語共通ルールに昇格だて！古いコードはコメントアウト。
    /*
    instructions.push_str("\n\n【全言語共通の出力フォーマット規則】\n- ユーザーがUI画面から簡単にコピー＆ペーストできるよう、ソースコードは必ず Markdown のコードブロック（```言語名 ... ```）で囲んで出力してください。\n- 文章の中にコードを紛れ込ませず、コードブロックとして独立させてください。");
    */
    
    // 🌟 全言語共通の絶対ルールだて！
    instructions.push_str("\n\n【全言語共通の出力フォーマット・実装規則】\n- ユーザーがUI画面から簡単にコピー＆ペーストできるよう、ソースコードは必ず Markdown のコードブロック（```言語名 ... ```）で囲んで出力してください。\n- 文章の中にコードを紛れ込ませず、コードブロックとして独立させてください。\n- 【重要】「処理を開始します」などの無駄なデバッグ用ログ出力（Write-Host, print, console.log, echo など）は極力省き、実用的でクリーンなコードのみを出力してください。");

    Some(ProgramContext {
        target_language: target_lang,
        specific_instructions: instructions,
    })
}

// 🌟 各言語の「Proモード用」の注意書き・ベストプラクティス集だて！
fn get_language_instructions(lang: &str) -> String {
    match lang {
        "Python" => "【Python 専門コーディング規則】\n- PEP8に完全に準拠すること。\n- 必ず型ヒント(Type Hints)を活用し、堅牢にすること。\n- 例外処理(try-except)を適切に行うこと。\n- AIやデータ分析の要件がある場合、最新のライブラリ（Pandas, PyTorch等）のベストプラクティスに従うこと。".to_string(),
        "TypeScript" => "【TypeScript 専門コーディング規則】\n- `any`型の使用は厳禁。厳密な型定義を行うこと。\n- ES6+のモダンな構文を使用すること。\n- 大規模Web開発を想定し、コンポーネントの分割やモジュール化を意識すること。".to_string(),
        "JavaScript" => "【JavaScript 専門コーディング規則】\n- `var`は絶対に使用せず、`let`と`const`を使用すること。\n- モダンなブラウザ環境を想定し、非同期処理は `async/await` を用いること。".to_string(),
        "Rust" => "【Rust 専門コーディング規則】\n- 所有権とボローイングのルールを厳格に守り、安全で高速なコードを出力すること。\n- `unwrap()` の乱用は避け、`Result` や `Option` を使った適切なエラーハンドリングを行うこと。\n- Idiomatic（Rustらしい）な記述を徹底すること。".to_string(),
        "Go" => "【Go 専門コーディング規則】\n- `gofmt` に準拠したシンプルな記述をすること。\n- `if err != nil` による明示的で確実なエラーハンドリングを行うこと。\n- サーバー系処理では、並行処理（`goroutine` / `channel`）を効率的に利用すること。".to_string(),
        "C++" => "【C++ 専門コーディング規則】\n- ゲームや高性能処理を想定し、モダンC++ (C++17/20) の機能を積極的に使用すること。\n- 生ポインタの代わりにスマートポインタを活用し、メモリリークを未然に防ぐこと。".to_string(),
        "C#" => "【C# 専門コーディング規則】\n- Unityやシステム開発を想定し、オブジェクト指向の原則に従った設計にすること。\n- LINQを適切に活用し、非同期メソッドには `Async` サフィックスをつけて `Task` を返すこと。".to_string(),
        "Kotlin" => "【Kotlin 専門コーディング規則】\n- Android開発等を想定。Null安全（Null Safety）を最大限活用し、`!!`の乱用を避けること。\n- スコープ関数（let, apply等）を適切に使って簡潔に書くこと。".to_string(),
        "Swift" => "【Swift 専門コーディング規則】\n- iPhoneアプリ開発を想定。オプショナルバインディングを使って安全にアンラップすること。\n- プロトコル指向プログラミングの設計を取り入れること。".to_string(),
        "Zig" => "【Zig 専門コーディング規則】\n- C代替としての安全性を意識し、メモリアロケータを明示的に受け渡し、メモリ管理を厳格に行うこと。\n- エラーユニオン型を活用した適切なエラーハンドリングを行うこと。".to_string(),
        // 2026-03-16: ログ出力禁止を共通ルールに移したため、PowerShellのルールを簡略化だて。
        /*
        "PowerShell" => "【PowerShell 専門コーディング規則】\n- デバッグ用の無駄な `Write-Host` は極力省き、実用的でクリーンなスクリプトにすること。\n- コマンドレットはエイリアスではなく正式名称を使用すること。\n- エラー処理（try-catch）を適切に組み込むこと。".to_string(),
        */
        "PowerShell" => "【PowerShell 専門コーディング規則】\n- コマンドレットはエイリアスではなく正式名称を使用すること。\n- エラー処理（try-catch）を適切に組み込むこと。".to_string(),
        "Shell" => "【Shell/Bash 専門コーディング規則】\n- `set -e` などを活用し、エラー発生時に安全に停止する堅牢なスクリプトにすること。\n- 依存するコマンドの存在チェックを含めること。".to_string(),
        _ => "【一般的なコーディング規則】\n- 可読性が高く、保守しやすいクリーンアーキテクチャを意識したコードを出力すること。".to_string(),
    }
}