# Nao Local System (ナオ・ローカルシステム)

## 概要 / Overview

Nao Local Systemは、Rust (Tauri) と JavaScript をベースに構築された、ローカル環境向けのAIアシスタント・クライアントです。Google Gemini（無料・有料版）および OpenAI GPT（有料版）の API を統合し、名古屋弁で話すAI「ナオ」との対話や、ローカルファイルシステムの操作、Webデザインの自動生成などを行うことができます。

Nao Local System is a local AI assistant client built with Rust (Tauri) and JavaScript. It integrates Google Gemini (Free/Paid) and OpenAI GPT (Paid) APIs, allowing users to chat with the Nagoya-dialect AI "Nao," manage local file systems, and automate web design generation.

---

## 主な機能 / Key Features

### 1. マルチLLM対応 (Multi-LLM Support)

- **Google Gemini**: 無料版および有料版のAPIキーに対応。
- **OpenAI GPT**: 有料版（GPT-4o, o1, o3-mini等）のAPIキーに対応。
- 選択したモデルに応じて、バックエンドが自動的に適切なエンドポイントへルーティングを行います。

### 2. 3窓構成の直感的なUI (3-Pane Intuitive UI)

- **Explorer**: ローカルドライブ（C:〜Z:）をスキャンし、遅延評価によるツリー構造でファイルシステムを表示。
- **Projects**: 頻繁にアクセスするフォルダをプロジェクトとして登録し、ワンクリックでワープが可能。
- **Chat**: AIとの対話、および開発モード（プラン提案型）のインターフェース。

### 3. 高度なセキュリティ (Advanced Security)

- **APIキーの暗号化**: 設定ファイル（settings.ini）内のAPIキーは AES-256-GCM アルゴリズムで強力に暗号化。
- **マスキング表示**: 設定画面では入力済みのキーを「********」で隠蔽。
- **INI健全性チェック**: 起動時に設定ファイルの破損を自動診断し、修復を提案。

### 4. 開発支援機能 (Development Support)

- **開発モード**: AIが実行プラン（JSON形式）を提案し、ユーザーの承認後に処理を実行。
- **Web生成**: HTML/CSS/JSの3層構造を自動生成し、ローカルディレクトリへ分離保存。
- **PowerShell連携**: 安全なサンドボックス環境下でのコマンド実行支援。

---

## 【重要】APIキーとセキュリティについて / API Keys & Security

### 日本語

- **自己負担の原則**: APIキーの使用に伴う各事業者（Google、OpenAI）への課金は、すべて利用者の自己負担となります。管理画面で使用制限を設定するなど、使いすぎには注意してください。
- **機密保持**: APIキーおよび設定ファイルは、クレジットカード情報と同様に厳重に管理してください。絶対に他人に渡したり、公開したりしないでください。
- **流出時の措置**: 万が一流出した場合は、直ちに各事業者のダッシュボードからキーを削除・無効化してください。

### English

- **Billing Responsibility**: All charges from AI providers (Google, OpenAI) incurred via API keys are the sole responsibility of the user. Please monitor your usage limits carefully in each provider's dashboard.
- **Confidentiality**: Treat your API keys and configuration files with the same level of security as a credit card. Never share or publish them.
- **Emergency Actions**: If a leak is suspected, immediately revoke or delete the affected API keys from the provider's dashboard.

---

## ヘルプ：モデルが表示されない場合 / Help: Missing Models

APIで見えるモデル一覧が、必ずしも最新のドキュメントと一致しない場合があります。これは以下の理由による正常な挙動です。

1. **段階的ロールアウト**: 新モデルはAPI経由で全員に同時開放されるわけではありません。
2. **利用ランク(Tier)**: 過去の課金実績に応じて、利用可能なモデルが制限される場合があります。
3. **プルダウンが全て**: 本アプリのモデル選択リストに表示されているものが、そのAPIキーで「今使える全て」です。

The list of available models may not always match the latest documentation. This is normal behavior due to:

1. **Gradual Rollout**: New models are often released to API users in phases.
2. **Usage Tier**: Access to certain models may be restricted based on your billing history and Tier rank.
3. **Dropdown as Truth**: Only the models listed in the application's selection menu are currently accessible with your key.

---

## 権利・連絡先 / Rights & Contact

### 日本語

- **著作権**: 本プログラムの著作権および一切の権利は **NoaSeraphim** に帰属します。
- **改変の禁止**: 本プログラムを無断で改変・配布することは禁止されています。改変が必要な場合や商用利用の相談は、以下の連絡先までお問い合わせください。
- **連絡先**: X (旧Twitter) - [@isuzu_ayan76331](https://twitter.com/isuzu_ayan76331)

### English

- **Ownership**: All copyrights and intellectual property rights of this program belong to **NoaSeraphim**.
- **Prohibition of Modification**: Unauthorized modification or distribution of this program is strictly prohibited. If you require modifications or commercial use, please contact the developer.
- **Contact**: X (formerly Twitter) - [@isuzu_ayan76331](https://twitter.com/isuzu_ayan76331)

---
(C) 2026 NoaSeraphim All Rights Reserved.

－－－－－

# Nao Local System

## Overview

Nao Local System is a local AI assistant client built with Rust (Tauri) and JavaScript (Vite). It provides an integrated interface for Google Gemini and OpenAI GPT, featuring a Nagoya-dialect AI character "Nao."

## Features

- **Multi-API Support**: Handles Gemini Free/Paid and OpenAI GPT Paid models.
- **3-Pane Layout**: Integrated File Explorer, Project Manager, and Chat Workspace.
- **Project Warp**: Register local folders to quickly jump between development contexts.
- **Dev Mode**: Autonomous agent capabilities that propose execution plans via JSON.
- **Encrypted Config**: Protects API keys using AES-256-GCM encryption within a standard INI format.
- **Web Generation**: Specialized engine for generating and saving HTML/CSS/JS file structures.

## Security & Billing Warning

- **API Charges**: Users are responsible for all costs incurred through their respective API providers.
- **Data Protection**: API keys are masked in the UI and encrypted on disk. However, the `settings.ini` file should never be shared.

## Version Info

- **Version**: 2.00 (Updated: March 25, 2026)
- **Latest Updates**: Added support for Paid Gemini and OpenAI GPT models.

## Contact & License

This software is the property of **NoaSeraphim**. Redistribution or modification without permission is prohibited. For inquiries, contact via X: [@isuzu_ayan76331](https://twitter.com/isuzu_ayan76331).

(C) 2026 NoaSeraphim All Rights Reserved.
