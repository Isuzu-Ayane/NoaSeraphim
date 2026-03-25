/*
 * プログラムの概要説明: ヘルプ画面や規約などの長文HTMLコンテンツを一元管理するモジュール
 * プロジェクトの責任範囲に関する注記: NoaSeraphimは本プログラムの動作について一切の責任を負いません。
 * 初回作成年月日: 2026-03-25
 * 更新履歴:
 * 2026-03-25: 新規作成。APIモデルの仕組みと、APIキーのセキュリティ警告文を定義。
 * 2026-03-25: APIキーに関する課金責任（自己負担）の免責事項を追記。
 * 2026-03-25: 開発モードの利用条件（プロジェクト登録必須）に関する説明文を新規追加。
 * プロジェクトの権利表示: (C) NoaSeraphim
 * 利用範囲に関する制限事項: 非商用利用に限る
 */

// APIキーの取得方法に関するヘルプHTMLを返却します。
export function getHelpApiKeyGuideHtml() {
    return `
      <h4 style="color: #1e88e5; border-bottom: 2px solid #e3f2fd; padding-bottom: 5px; margin-bottom: 10px;">🔑 APIキーの取得方法</h4>
      <p>このシステムでAIを使うために必要な「APIキー」の取得手順だて！<br>無料で試せるモデルもあるもんで、まずは作ってみてちょうだい。</p>

      <h5 style="color: #0099cc; margin-top: 20px; border-left: 4px solid #0099cc; padding-left: 8px;">■ Gemini APIキーの取得方法（Google）</h5>
      <ol style="margin-left: 20px; line-height: 1.6;">
        <li><a href="https://aistudio.google.com/app/apikey" target="_blank" style="color: #1e88e5;">Google AI Studio</a> にアクセスして、Googleアカウントでログインする。</li>
        <li>左側のメニューから <b>「Get API key」</b> または <b>「API keys」</b> をクリックする。</li>
        <li>画面右上の <b>「Create API key」</b> ボタンをクリックする。</li>
        <li>「Create key」を選んで、新しいプロジェクトでキーを生成する。（無料枠で使えるよ！）</li>
        <li>表示されたAPIキーを「Copy」して、このアプリの設定画面に貼り付ける。</li>
      </ol>
      <p style="margin-top: 10px; font-size: 0.9em;">
        👉 詳細はこちら（Google検索）: <a href="https://www.google.com/search?q=Gemini+API%E3%82%AD%E3%83%BC+%E5%8F%96%E5%BE%97%E6%96%B9%E6%B3%95" target="_blank" style="color: #1e88e5;">Gemini APIキーの取得方法</a>
      </p>

      <h5 style="color: #10a37f; margin-top: 25px; border-left: 4px solid #10a37f; padding-left: 8px;">■ OpenAI APIキーの取得方法（ChatGPTの会社）</h5>
      <ol style="margin-left: 20px; line-height: 1.6;">
        <li><a href="https://platform.openai.com/" target="_blank" style="color: #10a37f;">OpenAI Platform</a> にアクセスして、アカウントを作成・ログインする。</li>
        <li>左側のメニュー（鍵のマーク）から <b>「API keys」</b> を選択する。</li>
        <li><b>「+ Create new secret key」</b> をクリックする。</li>
        <li>名前（任意）をつけて <b>「Create secret key」</b> を押す。</li>
        <li>発行されたAPIキーをコピーして、アプリに貼り付ける。<br><span style="color: #d32f2f; font-size: 0.9em;">※セキュリティのため一度しか表示されんもんで、必ずコピーしてね！</span></li>
        <li>※APIを使うには「Settings」→「Billing」からクレジットカードの登録とクレジット購入（最低5ドル）が必要な場合があるよ。</li>
      </ol>
      <p style="margin-top: 10px; font-size: 0.9em;">
        👉 詳細はこちら（Google検索）: <a href="https://www.google.com/search?q=OpenAI+API%E3%82%AD%E3%83%BC+%E5%8F%96%E5%BE%97%E6%96%B9%E6%B3%95" target="_blank" style="color: #10a37f;">OpenAIのAPIキー取得方法</a>
      </p>
    `;
}

// APIキーのセキュリティおよび課金に関するヘルプHTMLを返却します。
export function getHelpApiKeyHtml() {
    return `
      <h4 style="color: #d32f2f; border-bottom: 2px solid #ffebee; padding-bottom: 5px; margin-bottom: 10px;">⚠️ 【最重要】APIキーとセキュリティについて</h4>
      <p style="font-weight: bold; color: #b71c1c;">APIキーは、あなたのクレジットカードと同じくらい重要な機密情報だて！</p>
      
      <h5 style="color: #b71c1c; margin-top: 15px;">■ 利用料と課金に関するご注意</h5>
      <p>APIキーの使用には、各事業者（Google、OpenAI）への<b>「課金（利用料の支払い）」</b>が発生する場合があるんだわ。</p>
      <ul style="margin-left: 20px; line-height: 1.6;">
        <li>API使用に伴うすべての課金については、<b>利用者本人の自己負担</b>となるもんで承知しておいてね。</li>
        <li>GoogleやOpenAIの管理画面から、利用額の上限設定（Usage Limit）を自分で行うなど、うっかり使いすぎんようにしっかり管理してちょうだい！</li>
      </ul>

      <h5 style="color: #b71c1c; margin-top: 15px;">■ 流出リスクと取り扱い厳守</h5>
      <ul style="margin-left: 20px; margin-bottom: 10px; line-height: 1.6;">
        <li style="margin-bottom: 10px;"><b>設定ファイルの取り扱い厳守</b><br>
        APIキーはこのシステムの設定ファイル（<code>settings.ini</code>）に保存されるもんで、このファイル自体も<b>絶対に他人に渡したらアカン</b>よ。</li>
        
        <li style="margin-bottom: 10px;"><b>流出時の莫大なリスク</b><br>
        もし悪意のある第三者の手に渡ると、あなたが知らない間にAPIを大量使用され、<b>莫大な課金額（数十万〜数百万円規模）</b>が請求される恐れがあるんだわ。</li>
        
        <li style="margin-bottom: 10px;"><b>万が一の緊急措置</b><br>
        「もしかして漏れたかも？」と思ったら、即座に各社のダッシュボードから該当のAPIキーを<b>削除（Revoke/Delete）</b>して無効化してちょうだい！</li>
      </ul>
      
      <p style="font-size: 0.9em; color: #2e7d32; background: #e8f5e9; padding: 10px; border-radius: 4px; border-left: 4px solid #4caf50; margin-top: 15px;">
      ※なお、このシステムでは安全のため、設定ファイル内のAPIキーは<b>強力な暗号化（AES-256-GCMアルゴリズム）</b>を施して保存されとるでね。でも、物理的なファイルの管理は自分でしっかりやるんだよ！
      </p>
    `;
}

// 開発モードの機能要件（プロジェクト登録の必須化）に関するヘルプHTMLを返却します。
export function getHelpDevModeHtml() {
    return `
      <h4 style="color: #673ab7; border-bottom: 2px solid #ede7f6; padding-bottom: 5px; margin-bottom: 10px;">🛠️ 開発モード（エージェント機能）について</h4>
      <p>開発モードは、AIが実行プランを考えて自動でファイルを作成・修正してくれる強力な機能だて！<br>でも、この機能を使うためには<b>「プロジェクト登録」が絶対に必要</b>なんだわ。</p>

      <h5 style="color: #512da8; margin-top: 15px;">■ なんでプロジェクト登録が必要なの？</h5>
      <p>それは、<b>AIが「ローカルコンピューターのどのフォルダを修正してよいか」を判断するため</b>だて。</p>
      <p>プロジェクト登録がされとらんと、AIはどこにファイルを作っていいか分からず、パソコン内の関係ないデータを間違って消したり書き換えたりしてしまう危険があるんだわ。<br>安全のために、「あらかじめ許可された場所以外はいじらない」っていう設計になっとるでね！</p>

      <h5 style="color: #512da8; margin-top: 15px;">■ プロジェクト登録の手順</h5>
      <ol style="margin-left: 20px; line-height: 1.6;">
        <li>左側の <b>「📁 Explorer」</b> から、作業したいフォルダ（開発の拠点にしたい場所）を見つける。</li>
        <li>そのフォルダを1回クリックして、<b>選択状態（ハイライトされた状態）</b>にする。</li>
        <li>画面上部のメニューから <b>「ファイル(F)」→「📁 プロジェクト登録」</b> を選ぶ。</li>
        <li>確認メッセージが出るもんで、<b>「OK」</b> を押せば登録完了だて！</li>
      </ol>
      
      <p style="margin-top: 15px; padding: 10px; background: #e1f5fe; border-radius: 5px; font-size: 0.95em;">
      👉 登録が完了すると、左下の <b>「🚀 Projects」</b> 欄にフォルダ名が出るようになるよ。<br>そこをクリックして「🚀 ワープ中」の状態になれば、開発モードがバッチリ動くようになるわ！
      </p>
    `;
}

// モデル表示の仕組みに関するヘルプHTMLを返却します。
export function getHelpModelsHtml() {
    return `
      <h4 style="color: #1e88e5; border-bottom: 2px solid #e3f2fd; padding-bottom: 5px; margin-bottom: 10px;">■ 結論（重要だて！）</h4>
      <p>👉 <b>「課金した＝全モデル使える」ではない</b></p>
      <p>👉 最新モデル（gpt-5.4-nanoや最新のGeminiなど）は、<b>“見えていても使えない状態”</b>が普通にあるんだわ。</p>

      <h4 style="color: #43a047; border-bottom: 2px solid #e8f5e9; padding-bottom: 5px; margin-top: 20px; margin-bottom: 10px;">■ なんで出てこんの？（主な原因3つ）</h4>
      <p><b>① 段階的ロールアウト（これが一番の理由だて）</b><br>
      最新モデルは「徐々に公開」されとるんだわ。公式のドキュメントには先に載っても、APIは全員にはまだ開放されとらんことが多いでね。</p>
      
      <p style="margin-top: 10px;"><b>② APIキーの「権限・ティア（Tier）」</b><br>
      OpenAIやGoogleは、ユーザーの利用ランク（Tier）で制御しとるよ。<br>
      ・新規課金ユーザー → 制限あり<br>
      ・利用実績（APIの課金額）がある → 順次解放される<br>
      つまり、<span style="background:#ffcdd2; padding: 2px 4px; font-weight: bold;">使えるモデル一覧に出てこない ＝ まだ使えない</span> というのが正解だて。</p>
      
      <p style="margin-top: 10px;"><b>③ Web画面（ChatGPTやGemini Web）とAPIは別世界</b><br>
      ・Web画面 👉 裏でAIが自動でモデルを切り替えて使っとるもんで、直接選べんくても内部で使われとるよ。<br>
      ・API 👉 完全に手動。明示的に指定したモデルで、かつ自分に許可されたモデルしか使えんだて。</p>

      <h4 style="color: #fb8c00; border-bottom: 2px solid #fff3e0; padding-bottom: 5px; margin-top: 20px; margin-bottom: 10px;">■ つまり今の状態は？</h4>
      <p>👉 このアプリのドロップダウンに出とるモデル（GPT-4o や Gemini 1.5 Proなど）が使えるのは<b>正常（標準的な状態）</b>だて。</p>
      
      <p style="margin-top: 10px;"><b>Q. じゃあ最新の軽量モデル（nano系など）は何？</b><br>
      A. 大量処理向けや一部の先行ユーザー、内部用途優先のモデルなんだわ。「誰でもすぐ使えるモデル」じゃないでね。</p>

      <h4 style="color: #8e24aa; border-bottom: 2px solid #f3e5f5; padding-bottom: 5px; margin-top: 20px; margin-bottom: 10px;">■ よくある勘違いと確認方法</h4>
      <p>❌ 公式ドキュメントに載っとる → 使える<br>
      ⭕ <b>このアプリの「使用モデル」のリストに出とる → 使える（これが真実！）</b></p>
      
      <p style="margin-top: 10px;"><b>■ じゃあどうすれば使えるようになるの？</b><br>
      ✔ ① 待つ（一番現実的。そのうちみんな解放されるわ）<br>
      ✔ ② 使用実績（APIの利用額）を増やしてTier（ランク）を上げる<br>
      ✔ ③ 今出とる上位モデル（Proや4oなど）を使う</p>

      <div style="font-size: 1.05em; font-weight: bold; margin-top: 20px; padding: 15px; background: #fff3e0; border-radius: 5px; border-left: 5px solid #ff9800;">
      ■ 一言でまとめ！<br>
      👉 「名前を見たけど使えん」は正常な動作だて！<br>
      👉 「プルダウンに出とるか」が全てだわ！安心して今のモデルを使ってちょうだいね！
      </div>
    `;
}

// バージョン情報および権利表記に関するヘルプHTMLを返却します。
export function getHelpVersionHtml() {
    return `
      <h4 style="color: #1e88e5; border-bottom: 2px solid #e3f2fd; padding-bottom: 5px; margin-bottom: 10px;">ℹ️ Nao Local System</h4>
      <p><b>ヴァージョン：</b> 2.00</p>
      <p><b>更新日：</b> 2026年3月25日</p>
      
      <h4 style="color: #43a047; border-bottom: 2px solid #e8f5e9; padding-bottom: 5px; margin-top: 20px; margin-bottom: 10px;">■ 最新の更新内容</h4>
      <ul style="margin-left: 20px; line-height: 1.6;">
        <li>Gemini 有料版モデルへの対応</li>
        <li>GPT 有料版モデルへの対応</li>
      </ul>
      
      <h4 style="color: #d32f2f; border-bottom: 2px solid #ffebee; padding-bottom: 5px; margin-top: 20px; margin-bottom: 10px;">■ 利用規約と権利表示</h4>
      <p style="margin-bottom: 8px;">本プログラムは <b>NoaSeraphim</b> に帰属しています。</p>
      <p style="margin-bottom: 8px; color: #b71c1c; font-weight: bold;">⚠️ プログラムの無断改変などはしないようにしてください。</p>
      <p style="margin-bottom: 8px;">改変などが必要な場合は、X（旧Twitter）の <a href="https://twitter.com/isuzu_ayan76331" target="_blank" style="color: #1e88e5; text-decoration: none; font-weight: bold;">@isuzu_ayan76331</a> までご連絡をお願いします。</p>
      
      <div style="margin-top: 30px; text-align: center; font-size: 0.9em; color: #666;">
        &copy; 2026 NoaSeraphim All Rights Reserved.
      </div>
    `;
}