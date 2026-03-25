// K:\System_Make\nao_local_system\src\main.js
/*
 * プログラムの概要説明: フロントエンドのイベント制御、UI操作、および起動時の健全性診断
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

// バックグラウンドからのリアルタイム進行状況通知を監視し、ステータスUIにレンダリングします。
listen('thinking-progress', (event) => {
    const statusText = event.payload.message;
    const statusBarContainer = document.getElementById('status-bar-container');
    const statusBar = document.getElementById('status-bar');
    if (statusBarContainer && statusBar) {
        statusBarContainer.style.display = 'block'; 
        statusBar.innerHTML += `<br>[AI Progress] ${statusText}`;
        statusBarContainer.scrollTop = statusBarContainer.scrollHeight;
    }
});

const chatBox = document.getElementById('chat-box');
const userInput = document.getElementById('user-input');
const modelSelect = document.getElementById('model-select');
const modalOverlay = document.getElementById('modal-overlay');
const modalTitle = document.getElementById('modal-title');
const modalInput = document.getElementById('modal-input');
const nameSettings = document.getElementById('name-settings');
const bgOptions = document.getElementById('bg-options');

const btnSend = document.getElementById('btn-send');
const btnModeChat = document.getElementById('btn-mode-chat');
const btnModeDev = document.getElementById('btn-mode-dev');

let isDevMode = false;
let currentMode = '';
let aiName = 'Nao', userName = 'セラ';
let pendingPlan = null;
let currentTargetPath = null;
let selectedPathForContext = null;
let currentSelectedPath = null;

// アプリケーション起動時に構成ファイル（INI）の整合性をチェックする防波堤関数です。
async function checkConfigIntegrity() {
  try {
    const isHealthy = await invoke('check_config_health');
    if (!isHealthy) {
      const userAgrees = confirm("⚠️ 設定ファイル(INI)が壊れとるみたいだわ。画像データが原因かもしれんね。\n\n修復のためにファイルを初期化してもええかな？ (OK=Yes / Cancel=No)");
      if (userAgrees) {
        await invoke('force_reset_config');
        alert("✅ 初期化が完了しただて！アプリを再読み込みするわね。");
        window.location.reload(); 
        return false; 
      } else {
        alert("❌ 初期化をキャンセルしたわ。一部の設定が読み込めない可能性があるもんで気をつけてね。");
      }
    }
  } catch (e) {
    console.error("INIチェック中に異常が発生しました:", e);
  }
  return true; 
}

function truncatePsOutput(output) {
  const limit = 2000;
  if (output.length <= limit) return output;
  return output.substring(0, limit) + "\n\n... (Output truncated for performance)";
}

async function initApp() {
  const canContinue = await checkConfigIntegrity();
  if (!canContinue) return;

  try {
    aiName = await invoke('get_setting', { key: 'ai_name' }) || 'Nao';
    userName = await invoke('get_setting', { key: 'user_name' }) || 'セラ';

    const savedBgColor = await invoke('get_setting', { key: 'bg_color' });
    if (savedBgColor) document.body.style.backgroundColor = savedBgColor;

    const savedBgImage = await invoke('get_setting', { key: 'bg_image' });
    if (savedBgImage && savedBgImage.trim() !== "") {
      await applyBackground(savedBgImage);
    }

    await loadAvailableModels();
    await setupExplorer();
    await loadProjects();
  } catch(e) { console.error("初期化時例外補足:", e); }
}

async function loadAvailableModels() {
  try {
    const models = await invoke('get_clean_models');
    if (models && models.length > 0) {
      const current = modelSelect.value;
      modelSelect.innerHTML = models.map(m => `<option value="${m.id}">${m.name}</option>`).join('');
      if (current && models.some(m => m.id === current)) modelSelect.value = current;
      else modelSelect.selectedIndex = 0;
    }
  } catch (e) { console.warn("モデル取得失敗:", e); }
}

async function applyBackground(filePath) {
  try {
    const b64Data = await invoke('read_image_base64', { path: filePath });
    if (b64Data) {
      document.body.style.backgroundImage = `url('${b64Data}')`;
      document.body.style.backgroundSize = 'cover';
      document.body.style.backgroundAttachment = 'fixed';
      document.body.style.backgroundPosition = 'center';
    }
  } catch (e) { console.error(e); }
}

async function setupExplorer(warpPath = null) {
  const explorerTree = document.getElementById('explorer-tree');
  const contextMenu = document.getElementById('custom-context-menu');
  const copyPathBtn = document.getElementById('copy-path-btn');
  if(!explorerTree) return;

  explorerTree.innerHTML = '';

  async function renderDir(path, container) {
      try {
          const entries = await invoke('list_directory', { path: path });
          container.innerHTML = ''; 
          
          if (entries.length === 0) {
              container.innerHTML = '<div style="padding-left:20px; color:#666;">(empty)</div>';
              return;
          }

          entries.forEach(entry => {
              const wrapper = document.createElement('div');
              wrapper.style.paddingLeft = '15px';

              const entryEl = document.createElement('div');
              entryEl.textContent = entry.name;
              entryEl.className = `explorer-entry ${entry.is_dir ? 'directory' : 'file'}`;
              
              entryEl.addEventListener('click', () => {
                  document.querySelectorAll('.explorer-entry').forEach(el => el.classList.remove('selected'));
                  entryEl.classList.add('selected');
                  currentSelectedPath = entry.path;
              });

              entryEl.oncontextmenu = (e) => {
                  e.preventDefault();
                  e.stopPropagation(); 
                  selectedPathForContext = entry.path;
                  contextMenu.style.display = 'block';
                  contextMenu.style.left = `${e.pageX}px`;
                  contextMenu.style.top = `${e.pageY}px`;
              };

              wrapper.appendChild(entryEl);

              if (entry.is_dir) {
                  const childrenContainer = document.createElement('div');
                  childrenContainer.style.display = 'none'; 
                  wrapper.appendChild(childrenContainer);

                  let isLoaded = false; 

                  entryEl.addEventListener('click', async (e) => {
                      e.stopPropagation(); 
                      if (childrenContainer.style.display === 'none') {
                          childrenContainer.style.display = 'block';
                          if (!isLoaded) {
                              childrenContainer.innerHTML = '<div style="padding-left:20px; color:#666;">⏳ 読み込み中...</div>';
                              await renderDir(entry.path, childrenContainer);
                              isLoaded = true;
                          }
                      } else {
                          childrenContainer.style.display = 'none';
                      }
                  });
              } else {
                  entryEl.addEventListener('click', (e) => e.stopPropagation());
              }

              container.appendChild(wrapper);
          });
      } catch (error) {
          console.error('Failed to list directory:', error);
          container.innerHTML = `<div style="padding-left:20px; color:red;">エラー: アクセス拒否または無効なパスです。</div>`;
      }
  }

  async function renderPC(container) {
      container.innerHTML = '<div style="padding-left:20px; color:#666;">⏳ ドライブを走査中だて...</div>';
      
      let currentDir = "C:\\";
      try { currentDir = await invoke('get_current_dir'); } catch(e) {}

      const pcEntries = [
          { name: `📂 カレント (${currentDir})`, path: currentDir, is_dir: true }
      ];

      const letters = "CDEFGHIJKLMNOPQRSTUVWXYZ".split("");
      const checks = letters.map(async (letter) => {
          const path = `${letter}:\\`;
          try {
              await invoke('list_directory', { path: path });
              return { name: `💽 ローカルディスク (${letter}:)`, path: path, is_dir: true, valid: true };
          } catch (e) {
              return { valid: false };
          }
      });

      const results = await Promise.all(checks);
      results.forEach(r => {
          if (r.valid) pcEntries.push({ name: r.name, path: r.path, is_dir: true });
      });

      container.innerHTML = '';
      
      pcEntries.forEach(entry => {
          const wrapper = document.createElement('div');
          wrapper.style.paddingLeft = '5px';

          const entryEl = document.createElement('div');
          entryEl.textContent = entry.name;
          entryEl.className = `explorer-entry directory`;
          
          entryEl.addEventListener('click', () => {
              document.querySelectorAll('.explorer-entry').forEach(el => el.classList.remove('selected'));
              entryEl.classList.add('selected');
              currentSelectedPath = entry.path;
          });
          
          entryEl.oncontextmenu = (e) => {
              e.preventDefault(); e.stopPropagation();
              selectedPathForContext = entry.path;
              contextMenu.style.display = 'block';
              contextMenu.style.left = `${e.pageX}px`;
              contextMenu.style.top = `${e.pageY}px`;
          };

          wrapper.appendChild(entryEl);

          const childrenContainer = document.createElement('div');
          childrenContainer.style.display = 'none';
          wrapper.appendChild(childrenContainer);

          let isLoaded = false;

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

  copyPathBtn.onclick = () => {
      if (selectedPathForContext) {
          userInput.value += `\n[Analyze Directory: ${selectedPathForContext}]\n`;
          hideContextMenu();
      }
  };

  window.addEventListener('click', () => hideContextMenu());
  window.addEventListener('keydown', (e) => { if (e.key === 'Escape') hideContextMenu(); });
  function hideContextMenu() { contextMenu.style.display = 'none'; selectedPathForContext = null; }

  if (warpPath) {
      const rootWrapper = document.createElement('div');
      
      const backBtn = document.createElement('div');
      backBtn.innerHTML = '🔙 <span style="text-decoration:underline;">PCルートに戻る</span>';
      backBtn.style.cursor = 'pointer';
      backBtn.style.color = '#0099cc';
      backBtn.style.marginBottom = '10px';
      backBtn.onclick = () => setupExplorer(null);
      
      const title = document.createElement('div');
      title.innerHTML = `<div style="font-weight: bold; margin-bottom: 5px; border-bottom: 1px solid #ccc; padding-bottom: 3px; font-size: 0.9em; word-break: break-all; color: #555;">🚀 ワープ中: ${warpPath}</div>`;
      
      const childrenContainer = document.createElement('div');
      
      rootWrapper.appendChild(backBtn);
      rootWrapper.appendChild(title);
      rootWrapper.appendChild(childrenContainer);
      explorerTree.appendChild(rootWrapper);
      
      await renderDir(warpPath, childrenContainer);
  } else {
      const rootWrapper = document.createElement('div');
      const rootEl = document.createElement('div');
      rootEl.textContent = '💻 PC (マイコンピュータ)';
      rootEl.className = 'explorer-entry directory';
      
      rootEl.style.fontWeight = 'bold';
      rootEl.style.color = '#333';
      rootEl.style.borderBottom = '1px solid #ccc';
      rootEl.style.marginBottom = '5px';
      
      const pcContainer = document.createElement('div');
      pcContainer.style.display = 'block'; 
      
      rootWrapper.appendChild(rootEl);
      rootWrapper.appendChild(pcContainer);
      explorerTree.appendChild(rootWrapper);

      await renderPC(pcContainer);
  }
}

async function loadProjects() {
    const projContainer = document.getElementById('project-tree');
    if (!projContainer) return;
    projContainer.innerHTML = '';
    
    let currentProjects = await invoke('get_setting', { key: 'projects' });
    if (!currentProjects || currentProjects.trim() === "") {
        projContainer.innerHTML = '<div style="padding-left:20px; color:#666;">(登録なし)</div>';
        return;
    }
    
    let projList = currentProjects.split(',');
    projList.forEach(projPath => {
        if (!projPath.trim()) return;
        
        const wrapper = document.createElement('div');
        wrapper.style.paddingLeft = '5px';
        wrapper.style.marginBottom = '5px';

        const entryEl = document.createElement('div');
        const folderName = projPath.split('\\').pop() || projPath;
        entryEl.textContent = `📂 ${folderName}`;
        entryEl.title = projPath; 
        entryEl.className = 'explorer-entry directory';
        entryEl.style.cursor = 'pointer';
        
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

async function processGeminiResponse(fullText, targetPath) {
  const msgId = "thinking-" + Date.now();
  currentTargetPath = targetPath; 

  try {
    chatBox.innerHTML += `<div id="${msgId}" class="message nao-msg" style="align-self: flex-start; background: rgba(255, 255, 255, 0.95); padding:10px; border-radius:10px; margin:5px; border:1px solid #ddd;"><b>${aiName}</b><br><span style="color:#00e5ff; font-weight:bold;">⏳ ${isDevMode ? 'プランを練っとるよ...' : '考えとるよ...'}</span></div>`;
    chatBox.scrollTop = chatBox.scrollHeight;

    const res = await invoke('chat_with_ai', {
        message: fullText,
        model: modelSelect.value,
        isDevMode: isDevMode
    });

    document.getElementById(msgId)?.remove();

    if (res && res.text) {
        const jsonMatch = res.text.match(/```json\n([\s\S]*?)\n```/);
        if (isDevMode && jsonMatch) {
            try {
                const planData = JSON.parse(jsonMatch[1]);
                renderPlanUI(planData);
            } catch (parseErr) {
                appendMessage(aiName, "プランの解析に失敗したわ...\n" + res.text);
            }
        } else {
            appendMessage(aiName, res.text);
        }
    } else {
        appendMessage(aiName, "応答が空だったわ。");
    }
    
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
            const res = await invoke('generate_theme', {
                userRequest: JSON.stringify(pendingPlan),
                model: modelSelect.value,
                outputPath: currentTargetPath
            });
            const safeOutput = truncatePsOutput(res || "生成完了だて！");
            appendMessage(aiName, safeOutput);
        } catch(e) {
            appendMessage("SYSTEM", `エラー: ${e}`, "error");
        }
    } else {
        appendMessage(aiName, "了解だて！でもパスが指定されとらんもんで保留するね！");
    }
    pendingPlan = null;
};

window.rejectPlan = function() {
    appendMessage(userName, "このプランは中止で！", "user");
    appendMessage(aiName, "わかったわ！もう一回指示し直してちょうだいね。");
    pendingPlan = null;
};

function escapeHtml(unsafe) {
    return (unsafe || "")
        .replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;").replace(/"/g, "&quot;").replace(/'/g, "&#039;");
}

function appendMessage(sender, text, type = "") {
  const align = type === "user" ? "flex-end" : "flex-start";
  const bg = type === "user" ? "background: #e0f7fa;" : (type === "error" ? "background: #ffebee; color: red;" : "background: rgba(255, 255, 255, 0.95);");
  
  let formattedText = escapeHtml(text);
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

btnSend.onclick = async () => {
  const text = userInput.value.trim();
  if (!text) return;

  appendMessage(userName, text, "user");
  const pathMatch = text.match(/[a-zA-Z]:\\[^\s　"']+/);
  const targetPath = pathMatch ? pathMatch[0] : null;

  userInput.value = '';
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

const btnApiGeminiFree = document.getElementById('btn-settings-api-gemini-free');
if (btnApiGeminiFree) btnApiGeminiFree.onclick = () => openModal('api_key_gemini_free', '⚙️ APIキー (Gemini 無料)');

const btnApiGeminiPro = document.getElementById('btn-settings-api-gemini-pro');
if (btnApiGeminiPro) btnApiGeminiPro.onclick = () => openModal('api_key_gemini_pro', '⚙️ APIキー (Gemini 有料)');

const btnApiGptPro = document.getElementById('btn-settings-api-gpt-pro');
if (btnApiGptPro) btnApiGptPro.onclick = () => openModal('api_key_gpt_pro', '⚙️ APIキー (GPT 有料)');

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

const btnHelpDevMode = document.getElementById('btn-help-devmode');
if (btnHelpDevMode) btnHelpDevMode.onclick = () => openModal('help_devmode', '🛠️ 開発モードについて');

document.getElementById('btn-close').onclick = () => modalOverlay.style.display = 'none';

async function openModal(mode, title) {
  currentMode = mode; 
  modalTitle.innerText = title; 
  modalOverlay.style.display = 'flex';
  
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
    await invoke('save_setting', { key: currentMode, value: modalInput.value });
    
    if (currentMode.startsWith('api_key') && modalInput.value !== "********") {
        await loadAvailableModels();
        alert("APIキーを保存して、使えるモデル一覧を更新しただて！");
    }
  }
  modalOverlay.style.display = 'none';
};

userInput.addEventListener('keydown', (e) => {
  if (e.key === 'Enter' && !e.shiftKey && !e.isComposing) {
    e.preventDefault();
    btnSend.click();
  }
});

initApp();