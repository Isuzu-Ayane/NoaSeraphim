// K:\System_Make\nao_local_system\src\ui_renderer.js
/*
 * プログラムの概要説明: フロントエンドのイベントハンドリング、API呼び出し、UI更新処理
 * プロジェクトの責任範囲に関する注記: NoaSeraphimは本プログラムの動作について一切の責任を負いません。
 * 初回作成年月日: 2026-03-16
 * 更新履歴:
 * 2026-03-25: UIを3窓構成に変更し、プロジェクトの登録機能とワープ（特定パスのルート化）機能を実装。
 * 2026-03-25: ヘルプ文章の長文化に伴い、外部ファイルへのモジュール分割を実施。
 * 2026-03-25: 開発モードへの切り替え時にプロジェクトの選択状態を検証する機能を追加。
 * プロジェクトの権利表示: (C) NoaSeraphim
 * 利用範囲に関する制限事項: 非商用利用に限る
 */

import { invoke } from '@tauri-apps/api/core';
import { listen } from '@tauri-apps/api/event';
// 長文のヘルプドキュメントを外部ファイルから読み込みます。空間計算量の節約と可読性向上を目的としています。
import { getHelpModelsHtml, getHelpApiKeyHtml, getHelpVersionHtml, getHelpApiKeyGuideHtml, getHelpDevModeHtml } from './help_docs.js';

// バックエンドからの進捗イベントをリッスンしてステータスバーをリアルタイムに更新します。
// Tauriのイベントシステムを利用してRust側の非同期処理状況をフロントに反映します。
listen('thinking-progress', (event) => {
    const statusText = event.payload.message;
    console.log("[AI Progress]:", statusText);
    
    const statusBarContainer = document.getElementById('status-bar-container');
    const statusBar = document.getElementById('status-bar');
    
    // ステータスバーが存在する場合にテキストを追加し、最下部へ自動スクロールさせます。
    if (statusBarContainer && statusBar) {
        statusBarContainer.style.display = 'block'; 
        statusBar.innerHTML += `<br>[AI Progress] ${statusText}`;
        statusBarContainer.scrollTop = statusBarContainer.scrollHeight;
    }
});

// UI上の主要なDOM要素への参照を定数としてキャッシュし、DOMアクセスによるオーバーヘッドを削減します。
const chatBox = document.getElementById('chat-box');
const userInput = document.getElementById('user-input');
const modelSelect = document.getElementById('model-select');
const modalOverlay = document.getElementById('modal-overlay');
const modalTitle = document.getElementById('modal-title');
const modalInput = document.getElementById('modal-input');
const nameSettings = document.getElementById('name-settings');
const bgOptions = document.getElementById('bg-options');

// イベントハンドラをバインドするためのボタン要素を取得します。
const btnSend = document.getElementById('btn-send');
const btnModeChat = document.getElementById('btn-mode-chat');
const btnModeDev = document.getElementById('btn-mode-dev');

// アプリケーションの内部状態を管理するためのグローバル変数群です。
let isDevMode = false;
let currentMode = '';
let aiName = 'Nao', userName = 'User';

// 開発モードにおけるタスクプランやファイルパスのコンテキストを保持します。
let pendingPlan = null;
let currentTargetPath = null;
let selectedPathForContext = null;
let currentSelectedPath = null;

// アプリケーション起動時の初期化処理を非同期で実行します。
// 設定の読み込みやUIの初期構築を順次行います。
async function initApp() {
  try {
    // ユーザー名やAI名などの基本設定を構成ファイルから読み込みます。
    aiName = await invoke('get_setting', { key: 'ai_name' }) || 'Nao';
    userName = await invoke('get_setting', { key: 'user_name' }) || 'User';

    const savedBgColor = await invoke('get_setting', { key: 'bg_color' });
    if (savedBgColor) document.body.style.backgroundColor = savedBgColor;

    // 背景画像が設定されていれば、DOMに対して視覚プロパティを適用します。
    const savedBgImage = await invoke('get_setting', { key: 'bg_image' });
    if (savedBgImage && savedBgImage.trim() !== "") {
      await applyBackground(savedBgImage);
    }

    // 各種UIコンポーネント（モデル一覧、エクスプローラ、プロジェクト一覧）の初期化を行います。
    await loadAvailableModels();
    await setupExplorer();
    await loadProjects();
  } catch(e) { console.error("初期化エラー:", e); }
}

// 利用可能なモデル一覧をバックエンドから取得し、プルダウンに動的設定します。
// APIキーに応じて取得されるモデルリストが変化する仕組みに対応しています。
async function loadAvailableModels() {
  try {
    const models = await invoke('get_clean_models');
    // 取得したモデル群をセレクトボックスの選択肢要素としてマウントします。
    if (models && models.length > 0) {
      const current = modelSelect.value;
      modelSelect.innerHTML = models.map(m => `<option value="${m.id}">${m.name}</option>`).join('');
      if (current && models.some(m => m.id === current)) modelSelect.value = current;
      else modelSelect.selectedIndex = 0;
    }
  } catch (e) { console.warn("モデル取得失敗:", e); }
}

// 背景画像をBase64形式で読み込み、body要素のスタイルに適用します。
// 物理ファイルからデータを取得し、インラインCSSプロパティとしてブラウザに解釈させます。
async function applyBackground(filePath) {
  try {
    const b64Data = await invoke('read_image_base64', { path: filePath });
    // データストリームが正しく取得できた場合、背景画像として全画面にセットします。
    if (b64Data) {
      document.body.style.backgroundImage = `url('${b64Data}')`;
      document.body.style.backgroundSize = 'cover';
      document.body.style.backgroundAttachment = 'fixed';
      document.body.style.backgroundPosition = 'center';
    }
  } catch (e) { console.error(e); }
}

// エクスプローラツリーの初期化と描画を行います。引数により特定のパスをルート化（ワープ）可能です。
// DOMツリーの再構築を行うため、既存の要素をリセットします。
async function setupExplorer(warpPath = null) {
  const explorerTree = document.getElementById('explorer-tree');
  const contextMenu = document.getElementById('custom-context-menu');
  const copyPathBtn = document.getElementById('copy-path-btn');
  if(!explorerTree) return;

  // ツリー領域のDOM要素をリセットして初期状態に戻します。
  explorerTree.innerHTML = '';

  // 遅延評価によるツリー構造の部分木展開を行う再帰的描画関数です。空間計算量を最小化します。
  // 指定されたパス配下のディレクトリ情報をRust層から非同期取得します。
  async function renderDir(path, container) {
      try {
          // 非同期で対象パスの直下エントリをバックエンドから取得します。
          const entries = await invoke('list_directory', { path: path });
          container.innerHTML = ''; 
          
          if (entries.length === 0) {
              container.innerHTML = '<div style="padding-left:20px; color:#666;">(empty)</div>';
              return;
          }

          // 取得したエントリ群を反復処理し、階層構造を持つDOMノードを構築します。
          entries.forEach(entry => {
              const wrapper = document.createElement('div');
              wrapper.style.paddingLeft = '15px';

              // 実際のファイル/フォルダ名を表示し、クラスでアイコンを制御する要素です。
              const entryEl = document.createElement('div');
              entryEl.textContent = entry.name;
              entryEl.className = `explorer-entry ${entry.is_dir ? 'directory' : 'file'}`;
              
              // 要素の左クリックで選択状態を記憶し、UI上のハイライトを更新します。
              // プロジェクト登録のための対象パスとしてグローバル変数に保持させます。
              entryEl.addEventListener('click', () => {
                  document.querySelectorAll('.explorer-entry').forEach(el => el.classList.remove('selected'));
                  entryEl.classList.add('selected');
                  currentSelectedPath = entry.path;
              });

              // コンテキストメニュー呼び出し時はイベント伝播を停止し、パスをキャッシュします。
              entryEl.oncontextmenu = (e) => {
                  e.preventDefault();
                  e.stopPropagation(); 
                  selectedPathForContext = entry.path;
                  contextMenu.style.display = 'block';
                  contextMenu.style.left = `${e.pageX}px`;
                  contextMenu.style.top = `${e.pageY}px`;
              };

              wrapper.appendChild(entryEl);

              // フォルダの場合は、子要素を格納する非表示のコンテナを生成し、遅延読み込みをバインドします。
              // パフォーマンス最適化のため、ユーザーのアクションがあるまでサブディレクトリは展開しません。
              if (entry.is_dir) {
                  const childrenContainer = document.createElement('div');
                  childrenContainer.style.display = 'none'; 
                  wrapper.appendChild(childrenContainer);

                  let isLoaded = false; 

                  // フォルダクリック時に表示状態をトグルし、未ロードであれば再帰的にAPIを呼び出します。
                  entryEl.addEventListener('click', async (e) => {
                      e.stopPropagation(); 
                      if (childrenContainer.style.display === 'none') {
                          childrenContainer.style.display = 'block';
                          if (!isLoaded) {
                              // 子ディレクトリの展開。再帰呼び出しによる非同期処理の連鎖です。
                              childrenContainer.innerHTML = '<div style="padding-left:20px; color:#666;">⏳ 読み込み中...</div>';
                              await renderDir(entry.path, childrenContainer);
                              isLoaded = true;
                          }
                      } else {
                          // 折りたたみ処理。DOM構造は維持したまま非表示に遷移させます。
                          childrenContainer.style.display = 'none';
                      }
                  });
              } else {
                  // ファイルの場合はクリック時のイベント伝播のみを停止します。
                  entryEl.addEventListener('click', (e) => e.stopPropagation());
              }

              container.appendChild(wrapper);
          });
      } catch (error) {
          console.error('Failed to list directory:', error);
          container.innerHTML = `<div style="padding-left:20px; color:red;">エラー: アクセス拒否または無効なパスです。</div>`;
      }
  }

  // 木構造の根（Root）として論理的な「PC」ノードを定義し、ドライブ一覧を子ノードとして連結します。
  // システム上の全物理ドライブを走査してツリーの最上位階層を形成します。
  async function renderPC(container) {
      container.innerHTML = '<div style="padding-left:20px; color:#666;">⏳ ドライブを走査中だて...</div>';
      
      let currentDir = "C:\\";
      try { currentDir = await invoke('get_current_dir'); } catch(e) {}

      // 有向グラフの初期エッジとして、現在の作業ディレクトリを定義します。
      const pcEntries = [
          { name: `📂 カレント (${currentDir})`, path: currentDir, is_dir: true }
      ];

      // アルファベット集合による総当たり探索で、アクティブな物理ボリュームを非同期スキャンします。
      // Windowsのファイルシステム構造に依存した実装方針です。
      const letters = "CDEFGHIJKLMNOPQRSTUVWXYZ".split("");
      const checks = letters.map(async (letter) => {
          const path = `${letter}:\\`;
          try {
              // アクセス権限テストとして直下リストの取得を試み、成功すればノードとして採択します。
              await invoke('list_directory', { path: path });
              return { name: `💽 ローカルディスク (${letter}:)`, path: path, is_dir: true, valid: true };
          } catch (e) {
              return { valid: false };
          }
      });

      // 全非同期スキャンが完了するまで待機し、有効なドライブノードのみをフィルタリングします。
      const results = await Promise.all(checks);
      results.forEach(r => {
          if (r.valid) pcEntries.push({ name: r.name, path: r.path, is_dir: true });
      });

      container.innerHTML = '';
      
      // 構築された論理ノードリストに基づき、DOMツリーを展開します。
      pcEntries.forEach(entry => {
          const wrapper = document.createElement('div');
          wrapper.style.paddingLeft = '5px';

          const entryEl = document.createElement('div');
          entryEl.textContent = entry.name;
          entryEl.className = `explorer-entry directory`;
          
          // ルート要素クリック時も選択状態を記憶させます。
          // プロジェクトのルート自体を対象パスとして扱うための処理です。
          entryEl.addEventListener('click', () => {
              document.querySelectorAll('.explorer-entry').forEach(el => el.classList.remove('selected'));
              entryEl.classList.add('selected');
              currentSelectedPath = entry.path;
          });
          
          // 右クリックによるコンテキストメニューの呼び出しイベントをバインドします。
          entryEl.oncontextmenu = (e) => {
              e.preventDefault(); e.stopPropagation();
              selectedPathForContext = entry.path;
              contextMenu.style.display = 'block';
              contextMenu.style.left = `${e.pageX}px`;
              contextMenu.style.top = `${e.pageY}px`;
          };

          wrapper.appendChild(entryEl);

          // サブツリーの遅延評価用コンテナを定義し、初期状態は非表示とします。
          const childrenContainer = document.createElement('div');
          childrenContainer.style.display = 'none';
          wrapper.appendChild(childrenContainer);

          let isLoaded = false;

          // ノードクリック時に子要素の展開または折りたたみを状態機械的に制御します。
          entryEl.addEventListener('click', async (e) => {
              e.stopPropagation();
              if (childrenContainer.style.display === 'none') {
                  childrenContainer.style.display = 'block';
                  if (!isLoaded) {
                      childrenContainer.innerHTML = '<div style="padding-left:20px; color:#666;">⏳ 読み込み中だて...</div>';
                      await renderDir(entry.path, childrenContainer);
                      isLoaded = true;
                  }
              } else {
                  childrenContainer.style.display = 'none';
              }
          });

          container.appendChild(wrapper);
      });
  }

  // メニュー内のコピーボタンがクリックされた時の処理です。
  // ユーザーのチャット入力欄に対してパス文字列を安全にインジェクトします。
  copyPathBtn.onclick = () => {
      if (selectedPathForContext) {
          // 選択されたパスをテキスト入力欄に追記します。
          userInput.value += `\n[Analyze Directory: ${selectedPathForContext}]\n`;
          hideContextMenu();
      }
  };

  // メニュー領域外へのインタラクションでメニューを安全に破棄します。
  window.addEventListener('click', () => hideContextMenu());
  window.addEventListener('keydown', (e) => { if (e.key === 'Escape') hideContextMenu(); });
  function hideContextMenu() { contextMenu.style.display = 'none'; selectedPathForContext = null; }

  // ワープパスが指定されている場合、プロジェクトのフォルダをルートとして展開します。
  // ナビゲーションの利便性を高めるためのコンテキストスコープ制限機能です。
  if (warpPath) {
      const rootWrapper = document.createElement('div');
      
      // PCルート階層へ回帰するためのナビゲーションボタンを生成します。
      const backBtn = document.createElement('div');
      backBtn.innerHTML = '🔙 <span style="text-decoration:underline;">PCルートに戻る</span>';
      backBtn.style.cursor = 'pointer';
      backBtn.style.color = '#0099cc';
      backBtn.style.marginBottom = '10px';
      backBtn.onclick = () => setupExplorer(null);
      
      // プロジェクトの絶対パスを明示するヘッダを付与します。
      const title = document.createElement('div');
      title.innerHTML = `<div style="font-weight: bold; margin-bottom: 5px; border-bottom: 1px solid #ccc; padding-bottom: 3px; font-size: 0.9em; word-break: break-all; color: #555;">🚀 ワープ中: ${warpPath}</div>`;
      
      const childrenContainer = document.createElement('div');
      
      rootWrapper.appendChild(backBtn);
      rootWrapper.appendChild(title);
      rootWrapper.appendChild(childrenContainer);
      explorerTree.appendChild(rootWrapper);
      
      // 指定されたプロジェクトパスを基点として部分木を再構築します。
      await renderDir(warpPath, childrenContainer);
  } else {
      // DOM上に絶対的なルートとなる「💻 PC」ノードを静的に配置します。
      // 通常のエクスプローラビューの初期描画状態を形成します。
      const rootWrapper = document.createElement('div');
      const rootEl = document.createElement('div');
      rootEl.textContent = '💻 PC (マイコンピュータ)';
      rootEl.className = 'explorer-entry directory';
      
      // 視覚的階層を明示するため、インラインスタイルで下線と強調を付与します。
      rootEl.style.fontWeight = 'bold';
      rootEl.style.color = '#333';
      rootEl.style.borderBottom = '1px solid #ccc';
      rootEl.style.marginBottom = '5px';
      
      // PCノード直下の子要素コンテナは初期状態で展開済みに設定します。
      const pcContainer = document.createElement('div');
      pcContainer.style.display = 'block'; 
      
      rootWrapper.appendChild(rootEl);
      rootWrapper.appendChild(pcContainer);
      explorerTree.appendChild(rootWrapper);

      // ルートノードの配下に対して、物理ドライブとカレントディレクトリの情報をマウントします。
      await renderPC(pcContainer);
  }
}

// INIファイルに保存されたプロジェクトのリストを読み込み、パネルに描画する関数です。
// 永続化されたプロジェクト情報をフロントエンドに反映させます。
async function loadProjects() {
    const projContainer = document.getElementById('project-tree');
    if (!projContainer) return;
    projContainer.innerHTML = '';
    
    // バックエンドからカンマ区切りのプロジェクト一覧を非同期でフェッチします。
    let currentProjects = await invoke('get_setting', { key: 'projects' });
    if (!currentProjects || currentProjects.trim() === "") {
        projContainer.innerHTML = '<div style="padding-left:20px; color:#666;">(登録なし)</div>';
        return;
    }
    
    // 文字列を分割し、配列として反復処理を行います。
    // 各プロジェクトエントリに対応するDOM要素を動的に構築します。
    let projList = currentProjects.split(',');
    projList.forEach(projPath => {
        if (!projPath.trim()) return;
        
        const wrapper = document.createElement('div');
        wrapper.style.paddingLeft = '5px';
        wrapper.style.marginBottom = '5px';

        const entryEl = document.createElement('div');
        // ユーザーの視認性を高めるため、末尾のディレクトリ名のみを抽出して表示します。
        const folderName = projPath.split('\\').pop() || projPath;
        entryEl.textContent = `📂 ${folderName}`;
        entryEl.title = projPath; 
        entryEl.className = 'explorer-entry directory';
        entryEl.style.cursor = 'pointer';
        
        // 要素クリック時に、エクスプローラ全体を指定したプロジェクトパスへワープさせます。
        // コンテキストの切り替えをスムーズに行うための処理です。
        entryEl.onclick = async () => {
            document.querySelectorAll('.explorer-entry').forEach(el => el.classList.remove('selected'));
            entryEl.classList.add('selected');
            currentSelectedPath = projPath;
            await setupExplorer(projPath);
        };

        wrapper.appendChild(entryEl);
        projContainer.appendChild(wrapper);
    });
}

// ユーザーからの入力をAIへ送信し、レスポンスを処理します。
// 通信状態の管理および非同期例外の捕捉を行います。
async function processGeminiResponse(fullText, targetPath) {
  const msgId = "thinking-" + Date.now();
  currentTargetPath = targetPath; 

  try {
    // 処理中のプレースホルダーメッセージを表示します。
    chatBox.innerHTML += `<div id="${msgId}" class="message nao-msg" style="align-self: flex-start; background: rgba(255, 255, 255, 0.95); padding:10px; border-radius:10px; margin:5px; border:1px solid #ddd;"><b>${aiName}</b><br><span style="color:#00e5ff; font-weight:bold;">⏳ ${isDevMode ? 'プランを練っとるよ...' : '考えとるよ...'}</span></div>`;
    chatBox.scrollTop = chatBox.scrollHeight;

    // Rustレイヤーをプロキシとして、設定情報の付与とAPIへの外部通信を実施します。
    const res = await invoke('chat_with_ai', {
        message: fullText,
        model: modelSelect.value,
        isDevMode: isDevMode
    });

    // 処理完了に伴い、テンポラリのプレースホルダをDOMから破棄します。
    document.getElementById(msgId)?.remove();

    if (res && res.text) {
        // AIの応答内容からJSONブロックを正規表現で走査し、プラン定義を抽出します。
        // モードに応じた情報のパースと分岐処理を実行します。
        const jsonMatch = res.text.match(/```json\n([\s\S]*?)\n```/);
        if (isDevMode && jsonMatch) {
            try {
                const planData = JSON.parse(jsonMatch[1]);
                renderPlanUI(planData);
            } catch (parseErr) {
                appendMessage(aiName, "プランの解析に失敗したわ...\n" + res.text);
            }
        } else {
            // 通常のテキスト応答として、HTMLエスケープを施してチャットログに追記します。
            appendMessage(aiName, res.text);
        }
    } else {
        appendMessage(aiName, "応答が空だったわ。");
    }
    
    // トランザクションの正常終了をステータスバーに反映させます。
    const statusBarContainer = document.getElementById('status-bar-container');
    const statusBar = document.getElementById('status-bar');
    if (statusBarContainer && statusBar) {
        statusBar.innerHTML += `<br>[AI Progress] ✅ 処理完了だて！`;
        statusBarContainer.scrollTop = statusBarContainer.scrollHeight;
    }

  } catch (e) {
    document.getElementById(msgId)?.remove();
    appendMessage("SYSTEM", `⚠️ エラーだて: ${e}`, "error");
  }
}

// 開発モード時に取得されたJSON構造を解析し、プラン承認用の対話型ウィジェットを生成します。
// ユーザーがアクションを確認してから実行できる安全装置を提供します。
function renderPlanUI(planData) {
    pendingPlan = planData;
    let tasksHtml = '<ul class="task-list">';
    planData.tasks.forEach(task => {
        tasksHtml += `<li class="task-item"><b>[${task.action}]</b> ${task.desc}</li>`;
    });
    tasksHtml += '</ul>';

    const planHtml = `
        <div class="plan-box">
            <div class="plan-title">📋 実行プランの提案だて！</div>
            <p>${planData.message.replace(/\n/g, '<br>')}</p>
            ${tasksHtml}
            <div class="plan-actions">
                <button class="btn-approve" onclick="executePlan()">✅ 承認して実行</button>
                <button class="btn-reject" onclick="rejectPlan()">❌ やり直し / 中止</button>
            </div>
        </div>
    `;
    
    const align = "flex-start";
    const bg = "background: rgba(255, 255, 255, 0.95);";
    chatBox.innerHTML += `<div class="message" style="align-self: ${align}; ${bg}; padding:10px; border-radius:10px; margin:5px; max-width:80%; border:1px solid #ddd; box-shadow: 0 2px 4px rgba(0,0,0,0.1);"><b>${aiName}</b><br>${planHtml}</div>`;
    chatBox.scrollTop = chatBox.scrollHeight;
}

// ユーザーがプランを承認した際の実行プロセスをハンドルします。
// バックエンドに対して、合意済みのプランデータと出力パスを送信します。
window.executePlan = async function() {
    if (!pendingPlan) return;
    appendMessage(userName, "このプランで実行してちょうだい！", "user");
    
    const statusBarContainer = document.getElementById('status-bar-container');
    const statusBar = document.getElementById('status-bar');
    if (statusBarContainer && statusBar) {
        statusBarContainer.style.display = 'block';
        statusBar.innerHTML = "[AI Progress] ⚙️ プランの実行を開始するわ...";
    }

    if (currentTargetPath) {
        appendMessage(aiName, "了解だて！とりあえず従来のWeb生成を走らせるわね！");
        try {
            // 対象パスと要求を含むペイロードで生成系コマンドをコールします。
            const res = await invoke('generate_theme', {
                userRequest: JSON.stringify(pendingPlan),
                model: modelSelect.value,
                outputPath: currentTargetPath
            });
            // PowerShellの実行結果などをチャット欄に表示します。
            appendMessage(aiName, res || "生成完了だて！");
        } catch(e) {
            appendMessage("SYSTEM", `エラー: ${e}`, "error");
        }
    } else {
        appendMessage(aiName, "了解だて！でもパスが指定されとらんもんで保留するね！");
    }
    pendingPlan = null;
};

// プランが拒否された際のキャンセル処理です。
// ペンディング状態の変数をクリアし、処理を安全に中断します。
window.rejectPlan = function() {
    appendMessage(userName, "このプランは中止で！", "user");
    appendMessage(aiName, "わかったわ！もう一回指示し直してちょうだいね。");
    pendingPlan = null;
};

// XSS攻撃を防止するため、描画前のプレーンテキストから特殊文字を変換します。
// セキュリティ担保のための基本的なサニタイズ処理です。
function escapeHtml(unsafe) {
    return (unsafe || "")
        .replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;").replace(/"/g, "&quot;").replace(/'/g, "&#039;");
}

// 出力元に応じたスタイリングを適用し、対話ログへの要素追加を行います。
// Markdownのコードブロックを解析してHTMLに置換する機能も担います。
function appendMessage(sender, text, type = "") {
  const align = type === "user" ? "flex-end" : "flex-start";
  const bg = type === "user" ? "background: #e0f7fa;" : (type === "error" ? "background: #ffebee; color: red;" : "background: rgba(255, 255, 255, 0.95);");
  
  let formattedText = escapeHtml(text);
  // Markdownのコードブロック構文をHTMLのpreタグとシンタックスハイライト枠に置換します。
  formattedText = formattedText.replace(/```([a-zA-Z0-9]*)\n([\s\S]*?)```/g, (match, lang, code) => {
      const languageLabel = lang ? lang.toUpperCase() : 'CODE';
      return `<div style="background:#282c34; color:#abb2bf; padding:10px; border-radius:5px; margin:10px 0; overflow-x:auto; font-family: 'Consolas', 'Monaco', monospace; text-align: left; box-shadow: inset 0 0 5px rgba(0,0,0,0.5);">
                <div style="font-size:0.8em; color:#61afef; margin-bottom:5px; border-bottom:1px solid #5c6370; padding-bottom:3px; font-weight:bold;">${languageLabel}</div>
                <pre style="margin:0; white-space: pre-wrap; font-family: inherit;">${code}</pre>
              </div>`;
  });
  
  formattedText = formattedText.replace(/\n/g, '<br>');
  chatBox.innerHTML += `<div class="message" style="align-self: ${align}; ${bg}; padding:10px; border-radius:10px; margin:5px; max-width:80%; border:1px solid #ddd; box-shadow: 0 2px 4px rgba(0,0,0,0.1);"><b>${sender}</b><br>${formattedText}</div>`;
  chatBox.scrollTop = chatBox.scrollHeight;
}

// メッセージ送信ボタンが押下された際のイベントをトラップして通信を開始します。
// UIの状態をリセットし、ローディングインジケータを起動します。
btnSend.onclick = async () => {
  const text = userInput.value.trim();
  if (!text) return;

  appendMessage(userName, text, "user");
  // ユーザー入力内からローカルファイルシステムのパスと推定されるパターンを走査抽出します。
  const pathMatch = text.match(/[a-zA-Z]:\\[^\s　"']+/);
  const targetPath = pathMatch ? pathMatch[0] : null;

  userInput.value = '';
  // 4行固定サイズに復帰させることで行列形状を維持します。
  userInput.style.height = '6em'; 

  const statusBarContainer = document.getElementById('status-bar-container');
  const statusBar = document.getElementById('status-bar');
  if (statusBarContainer && statusBar) {
      statusBarContainer.style.display = 'block';
      statusBar.innerHTML = "[AI Progress] 🚀 通信を開始するわ...";
      statusBarContainer.scrollTop = statusBarContainer.scrollHeight;
  }

  await processGeminiResponse(text, targetPath);
};

// モード切り替えボタンのクリックイベントを設定します。
// アクティブなモードを視覚的に表現するため、インラインスタイルを直接上書きします。
btnModeChat.onclick = () => { 
    isDevMode = false; 
    btnModeChat.style.background = '#00e5ff'; 
    btnModeChat.style.color = 'white';
    btnModeChat.style.border = 'none';
    
    btnModeDev.style.background = '#f9f9f9'; 
    btnModeDev.style.color = '#555';
    btnModeDev.style.border = '1px solid #ccc';
};

// 2026-03-25 年月日コメントアウト: 古い開発モード切り替え処理（無条件で切り替え可能だったもの）
/*
btnModeDev.onclick = () => { 
    isDevMode = true; 
    btnModeDev.style.background = '#00e5ff'; 
    btnModeDev.style.color = 'white';
    btnModeDev.style.border = 'none';
    
    btnModeChat.style.background = '#f9f9f9'; 
    btnModeChat.style.color = '#555';
    btnModeChat.style.border = '1px solid #ccc';
};
*/
// 2026-03-25 追加: プロジェクトが選択状態であるかを検証してから開発モードを有効化します。
btnModeDev.onclick = async () => { 
    // 構成ファイルから登録済みのプロジェクト一覧を非同期で取得します。
    let currentProjects = await invoke('get_setting', { key: 'projects' });
    // カンマ区切りの文字列を配列に変換し、検証用のリストを構築します。
    let projList = currentProjects ? currentProjects.split(',') : [];
    
    // 現在選択中のパスが存在しない、またはプロジェクト一覧に含まれていない場合は警告を出します。
    if (!currentSelectedPath || !projList.includes(currentSelectedPath)) {
        // ユーザーにプロジェクト選択の必要性を促すアラートを表示します。
        alert("プロジェクトを選択してください。\n左下の「🚀 Projects」からプロジェクトを選ぶか、フォルダをプロジェクト登録してください。");
        // 検証に失敗したため、モード切り替えの処理をここで中断します。
        return; 
    }

    // 検証を通過した場合、グローバル変数を更新して開発モードを有効化します。
    isDevMode = true; 
    
    // 開発モードボタンのインラインスタイルを上書きし、アクティブ状態（青色）にします。
    btnModeDev.style.background = '#00e5ff'; 
    btnModeDev.style.color = 'white';
    btnModeDev.style.border = 'none';
    
    // チャットモードボタンのインラインスタイルを上書きし、非アクティブ状態（灰色）にします。
    btnModeChat.style.background = '#f9f9f9'; 
    btnModeChat.style.color = '#555';
    btnModeChat.style.border = '1px solid #ccc';
};

// ドロップダウンメニューの表示状態をブール代数的に制御する関数です。
// メニューの排他制御を行い、UIの崩れを防ぎます。
function setupDropdownMenus() {
    const menuConfigs = [
        { btnId: 'menu-file', dropId: 'dropdown-file' },
        { btnId: 'menu-settings', dropId: 'dropdown-settings' },
        { btnId: 'menu-help', dropId: 'dropdown-help' }
    ];

    menuConfigs.forEach(config => {
        const btn = document.getElementById(config.btnId);
        const drop = document.getElementById(config.dropId);
        if (btn && drop) {
            btn.onclick = (e) => {
                e.stopPropagation(); 
                menuConfigs.forEach(other => {
                    if (other.dropId !== config.dropId) {
                        const otherDrop = document.getElementById(other.dropId);
                        if (otherDrop) otherDrop.style.display = 'none';
                    }
                });
                drop.style.display = drop.style.display === 'block' ? 'none' : 'block';
            };
        }
    });

    window.addEventListener('click', () => {
        menuConfigs.forEach(config => {
            const drop = document.getElementById(config.dropId);
            if (drop) drop.style.display = 'none';
        });
    });
}

setupDropdownMenus();

// ファイルメニュー関連のアクションをバインドし、選択パスの検証と登録プロセスを実行します。
// エクスプローラで選択されたパスをINIファイルに追記して永続化します。
const btnProjectRegister = document.getElementById('btn-project-register');
if (btnProjectRegister) {
    btnProjectRegister.onclick = async () => {
        if (!currentSelectedPath) {
            alert("プロジェクトに登録するフォルダをエクスプローラから選んでちょうだい！");
            return;
        }
        const userAgrees = confirm(`『${currentSelectedPath}』をプロジェクトとして登録するだて？`);
        if (userAgrees) {
            let currentProjects = await invoke('get_setting', { key: 'projects' });
            let projList = currentProjects ? currentProjects.split(',') : [];
            
            // 集合への追加操作として、重複排除を適用します。
            if (!projList.includes(currentSelectedPath)) {
                projList.push(currentSelectedPath);
                await invoke('save_setting', { key: 'projects', value: projList.join(',') });
                alert("プロジェクトを登録しただて！");
                await loadProjects(); 
            } else {
                alert("そのパスはもう登録されとるよ！");
            }
        }
    };
}

// 細分化された各APIキー入力のモーダル呼び出しをバインドします。
const btnApiGeminiFree = document.getElementById('btn-settings-api-gemini-free');
if (btnApiGeminiFree) btnApiGeminiFree.onclick = () => openModal('api_key_gemini_free', '⚙️ APIキー (Gemini 無料)');

const btnApiGeminiPro = document.getElementById('btn-settings-api-gemini-pro');
if (btnApiGeminiPro) btnApiGeminiPro.onclick = () => openModal('api_key_gemini_pro', '⚙️ APIキー (Gemini 有料)');

const btnApiGptPro = document.getElementById('btn-settings-api-gpt-pro');
if (btnApiGptPro) btnApiGptPro.onclick = () => openModal('api_key_gpt_pro', '⚙️ APIキー (GPT 有料)');

// 細分化された各コンテキスト設定のモーダル呼び出しをバインドします。
const btnCtxGeminiFree = document.getElementById('btn-settings-context-gemini-free');
if (btnCtxGeminiFree) btnCtxGeminiFree.onclick = () => openModal('context_gemini_free', '🧠 コンテキスト (Gemini 無料)');

const btnCtxGeminiPro = document.getElementById('btn-settings-context-gemini-pro');
if (btnCtxGeminiPro) btnCtxGeminiPro.onclick = () => openModal('context_gemini_pro', '🧠 コンテキスト (Gemini 有料)');

const btnCtxGptPro = document.getElementById('btn-settings-context-gpt-pro');
if (btnCtxGptPro) btnCtxGptPro.onclick = () => openModal('context_gpt_pro', '🧠 コンテキスト (GPT 有料)');

const btnSettingsBg = document.getElementById('btn-settings-bg');
if (btnSettingsBg) btnSettingsBg.onclick = () => openModal('bg', '🌌 画面設定');

const btnSettingsNames = document.getElementById('btn-settings-names');
if (btnSettingsNames) btnSettingsNames.onclick = () => openModal('names', '🏷️ 呼び名設定');

const btnHelpApiGuide = document.getElementById('btn-help-apiguide');
if (btnHelpApiGuide) btnHelpApiGuide.onclick = () => openModal('help_apiguide', '🔑 APIキーの取得方法');

const btnHelpApiKey = document.getElementById('btn-help-apikey');
if (btnHelpApiKey) btnHelpApiKey.onclick = () => openModal('help_apikey', '⚠️ APIキーについて（必読）');

const btnHelpModels = document.getElementById('btn-help-models');
if (btnHelpModels) btnHelpModels.onclick = () => openModal('help_models', '❓ モデルが使えない場合（必読）');

const btnHelpVersion = document.getElementById('btn-help-version');
if (btnHelpVersion) btnHelpVersion.onclick = () => openModal('help_version', 'ℹ️ バージョン情報');

// 開発モードの要件を説明するヘルプボタンのイベントをバインドします。
const btnHelpDevMode = document.getElementById('btn-help-devmode');
if (btnHelpDevMode) btnHelpDevMode.onclick = () => openModal('help_devmode', '🛠️ 開発モードについて');

document.getElementById('btn-close').onclick = () => modalOverlay.style.display = 'none';

// 要求されたモードに基づき、モーダルウィンドウの可視性と入力フィールドの表示を切り替えます。
// 適切なコンテンツモジュールを呼び出してDOMツリーに動的バインドします。
async function openModal(mode, title) {
  currentMode = mode; 
  modalTitle.innerText = title; 
  modalOverlay.style.display = 'flex';
  
  // 各要素の取得と初期化（リセット）を行います。
  const helpContent = document.getElementById('help-content');
  const btnSave = document.getElementById('btn-save');
  const btnClose = document.getElementById('btn-close');

  modalInput.style.display = 'none';
  nameSettings.style.display = 'none';
  bgOptions.style.display = 'none';
  helpContent.style.display = 'none';
  btnSave.style.display = 'inline-block';
  btnClose.innerText = 'キャンセル';

  if (mode.startsWith('api_key') || mode.startsWith('context')) {
    modalInput.style.display = 'block';
    const actualValue = await invoke('get_setting', { key: mode });
    
    if (mode.startsWith('api_key')) {
        modalInput.value = actualValue ? "********" : "";
    } else {
        modalInput.value = actualValue;
    }
  } else if (mode === 'names') {
    nameSettings.style.display = 'flex';
    document.getElementById('ai-name-input').value = aiName;
    document.getElementById('user-name-input').value = userName;
  } else if (mode === 'bg') {
    bgOptions.style.display = 'flex';
  } else if (mode === 'help_apiguide') {
    helpContent.style.display = 'block';
    btnSave.style.display = 'none';
    btnClose.innerText = '閉じる';
    helpContent.innerHTML = getHelpApiKeyGuideHtml();
  } else if (mode === 'help_models') {
    helpContent.style.display = 'block';
    btnSave.style.display = 'none';
    btnClose.innerText = '閉じる';
    helpContent.innerHTML = getHelpModelsHtml();
  } else if (mode === 'help_apikey') {
    helpContent.style.display = 'block';
    btnSave.style.display = 'none';
    btnClose.innerText = '閉じる';
    helpContent.innerHTML = getHelpApiKeyHtml();
  } else if (mode === 'help_version') {
    helpContent.style.display = 'block';
    btnSave.style.display = 'none';
    btnClose.innerText = '閉じる';
    helpContent.innerHTML = getHelpVersionHtml();
  } else if (mode === 'help_devmode') {
    helpContent.style.display = 'block';
    btnSave.style.display = 'none';
    btnClose.innerText = '閉じる';
    helpContent.innerHTML = getHelpDevModeHtml();
  }
}

// モーダルダイアログでの保存アクションを監視し、バックエンドへデータの永続化を要請します。
// 入力されたマスキング文字列の除外や、設定保存後のリロード処理を含みます。
document.getElementById('btn-save').onclick = async () => {
  if (currentMode === 'names') {
    aiName = document.getElementById('ai-name-input').value;
    userName = document.getElementById('user-name-input').value;
    await invoke('save_setting', { key: 'ai_name', value: aiName });
    await invoke('save_setting', { key: 'user_name', value: userName });
  } else if (currentMode === 'bg') {
    const c = document.getElementById('bg-color').value;
    await invoke('save_setting', { key: 'bg_color', value: c });
    document.body.style.backgroundColor = c;
    
    // 選択された背景画像をDataURLストリームとしてパースし、バックエンドへ転送します。
    const bgFileInput = document.getElementById('bg-file');
    if (bgFileInput.files[0]) {
      const reader = new FileReader();
      reader.onload = async (e) => {
        await invoke('save_setting', { key: 'bg_image', value: e.target.result });
        document.body.style.backgroundImage = `url('${e.target.result}')`;
        document.body.style.backgroundSize = 'cover';
      };
      reader.readAsDataURL(bgFileInput.files[0]);
    }
  } else {
    // APIキーやコンテキスト等の汎用テキストデータの保存を委譲します。
    await invoke('save_setting', { key: currentMode, value: modalInput.value });
    
    // APIキーが更新された場合、強制的にモデルリストを再取得してUIのプルダウンに即座に反映させます。
    if (currentMode.startsWith('api_key') && modalInput.value !== "********") {
        await loadAvailableModels();
        alert("APIキーを保存して、使えるモデル一覧を更新しただて！");
    }
  }
  // 全フローの完了をもってモーダルを非表示状態へ遷移させます。
  modalOverlay.style.display = 'none';
};

// テキストエリア上でのEnterキー押下を捕捉し、意図せぬ改行を防ぎつつ送信ボタンのクリックイベントをエミュレートします。
userInput.addEventListener('keydown', (e) => {
  if (e.key === 'Enter' && !e.shiftKey && !e.isComposing) {
    e.preventDefault();
    btnSend.click();
  }
});

// スクリプトロードの最終段階でシステム全体の初期化シーケンスを開始します。
initApp();