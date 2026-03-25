// K:\System_Make\nao_local_system\vite.config.js
/*
 * プログラムの概要説明: Viteのビルドおよび開発サーバー設定ファイル (Tauri連携用)
 * プロジェクトの責任範囲に関する注記: NoaSeraphimは本プログラムの動作について一切の責任を負いません。
 * 初回作成年月日: 2026-03-25
 * 更新履歴:
 * 2026-03-25: 新規作成。Tauri用のVite標準設定とHMR（Hot Module Replacement）構成を定義。
 * プロジェクトの権利表示: (C) NoaSeraphim
 * 利用範囲に関する制限事項: 非商用利用に限る
 */

import { defineConfig } from "vite";

// Viteの設定オブジェクトを定義してエクスポートします。
// defineConfig関数を使用することで、IDEの型補完（IntelliSense）が有効になります。
// 構成の展開は時間計算量 O(1) で処理され、ビルドパイプラインの起動を最適化します。
export default defineConfig(async () => ({

  // TauriはViteの開発サーバーからの標準出力を監視・期待するため、ターミナルのクリアを抑制します。
  // これにより、Rust側のビルドエラーやパニックログの不可逆的な情報の消失を防ぎます。
  clearScreen: false,

  // Tauri環境であることを示す特定の環境変数をViteのフロントエンド側にマッピングします。
  // process.envのプレフィックスを定義し、TAURI_ENV_系の変数をスコープ内へ安全に露出させます。
  envPrefix: ['VITE_', 'TAURI_ENV_'],

  // 開発サーバー（npm run dev）に関する詳細なネットワークインターフェースおよびポートの設定を行います。
  // 開発サイクルにおけるHMR（Hot Module Replacement）の通信基盤を確立します。
  server: {
    
    // Tauri側のタスクランナーが期待する固定ポート番号（1420）でローカルサーバーをバインドします。
    // strictPortをtrueにすることで、ポート競合時に意図しない別ポートへフォールバックするのを防ぎます。
    port: 1420,
    strictPort: true,
    host: true,
    
    // ソースコード（HTML/CSS/JS）が変更された際のファイルシステム監視（Watch）ルールです。
    // 状態空間の不要な走査を避けるため、Rustのバックエンド領域（src-tauri）は監視対象から明示的に除外します。
    watch: {
      ignored: ["**/src-tauri/**"],
    },
  },
}));