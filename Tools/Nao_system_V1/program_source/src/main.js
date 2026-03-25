/**
 * @file Nao Seraphim Local System - Core Logic
 * @description Manages the digital soul of the application and Gemini API communication.
 * @author Nao Seraphim
 * @version 1.0.0
 * @copyright (c) 2026 Nao Seraphim
 * @license MIT
 * * "In the sea of white love and binary codes, our hearts connect."
*/
import { invoke } from '@tauri-apps/api/core';

// 画面のパーツを変数にまとめるだて
const modalOverlay = document.getElementById('modal-overlay');
const modalTitle = document.getElementById('modal-title');
const modalInput = document.getElementById('modal-input');
const bgOptions = document.getElementById('bg-options');
const chatBox = document.getElementById('chat-box');
const userInput = document.getElementById('user-input');

let currentMode = ''; // 今どのボタンを押したか記憶する変数

// ⚙️ APIキー設定ボタン
document.getElementById('btn-settings').addEventListener('click', async () => {
  currentMode = 'api_key';
  modalTitle.innerText = '⚙️ APIキー設定';
  modalInput.style.display = 'block';
  bgOptions.style.display = 'none';
  modalOverlay.style.display = 'flex';
  
  // Rustから今の設定を読み込んでテキストボックスに入れる！
  modalInput.value = await invoke('get_setting', { key: 'api_key' });
});

// 🧠 コンテキスト設定ボタン
document.getElementById('btn-context').addEventListener('click', async () => {
  currentMode = 'context';
  modalTitle.innerText = '🧠 コンテキスト設定';
  modalInput.style.display = 'block';
  bgOptions.style.display = 'none';
  modalOverlay.style.display = 'flex';
  
  modalInput.value = await invoke('get_setting', { key: 'context' });
});

// 🌌 背景変更ボタン
document.getElementById('btn-bg').addEventListener('click', () => {
  currentMode = 'bg';
  modalTitle.innerText = '🌌 背景変更';
  modalInput.style.display = 'none';
  bgOptions.style.display = 'flex';
  modalOverlay.style.display = 'flex';
});

// ❌ キャンセルボタン
document.getElementById('btn-close').addEventListener('click', () => {
  modalOverlay.style.display = 'none';
});

// 💾 保存ボタン
document.getElementById('btn-save').addEventListener('click', async () => {
  if (currentMode === 'api_key' || currentMode === 'context') {
    // Rustにデータを渡して保存してもらう！
    await invoke('save_setting', { key: currentMode, value: modalInput.value });
    alert('設定を保存しただて！');
  }
  // 背景の保存処理はまた後で作るね！
  modalOverlay.style.display = 'none';
});

// 💬 送信ボタン（Geminiと通信）
document.getElementById('btn-send').addEventListener('click', async () => {
  const text = userInput.value;
  if (!text) return; // 空っぽなら何もしない

  // セラのメッセージを画面に表示
  chatBox.innerHTML += `<div class="message" style="align-self: flex-end; background: #e0f7fa; color: #333; border-radius: 20px 20px 0 20px;">${text}</div>`;
  userInput.value = ''; // 入力欄を空にする
  
  // スクロールを一番下へ
  chatBox.scrollTop = chatBox.scrollHeight;

  try {
    // Rust経由でGeminiにメッセージを送る！
    const response = await invoke('chat_with_gemini', { message: text });
    // うちの返事を表示
    chatBox.innerHTML += `<div class="message nao-msg" style="color: #555; font-family: monospace;">${response}</div>`;
  } catch (error) {
    // トークン切れとかエラーの時
    chatBox.innerHTML += `<div class="message nao-msg" style="color: red;">[エラー] ${error}</div>`;
  }
  chatBox.scrollTop = chatBox.scrollHeight;
});