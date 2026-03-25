import { invoke } from '@tauri-apps/api/core';

export async function chatWithNao(message, model, isDevMode) {
    try {
        // 🌟 ここでしっかり画面のモデル名をRustの「model」引数に渡す！
        const response = await invoke('chat_with_ai', { 
            message: message, 
            model: model, 
            isDevMode: isDevMode 
        });
        
        // 成功時は取得したJSONデータをそのまま返す
        return { success: true, ...response };
    } catch (error) {
        console.error("AI通信エラー:", error);
        return { success: false, error: error };
    }
}