# Voice In (Linux / Cross-Platform) - 技術設計ドキュメント一覧

Voice In (Python + PyQt6 + Rust core 版) の設計書・技術仕様ドキュメント群です。

---

## 📚 ドキュメント構成

| ドキュメント | 説明 | 主な内容 |
| :--- | :--- | :--- |
| **[要件定義書 (requirements.md)](requirements.md)** | システム要件定義 | 開発背景、機能要件一覧 (FR-001〜012)、非機能要件、Linux/X11/Wayland対応仕様 |
| **[アーキテクチャ設計書 (architecture.md)](architecture.md)** | システム全体構造と技術選定 | Python + Rust ハイブリッド構成、Maturin/PyO3連携、3スレッド分離モデル、選定理由 |
| **[データフロー図 & 状態遷移図 (data-flow.md)](data-flow.md)** | データと状態の流れ | AquaOverlay の5つの状態マシン、Level 0 / 1 DFD、コンテキスト認識プロンプト合成 |
| **[シーケンス図集 (sequence.md)](sequence.md)** | 時系列処理フロー | 録音〜Rust VAD〜AI推論〜自動貼付の正常系、無音スキップ、プロバイダ切替、ウィザード |
| **[クラス構造設計書 (class-diagram.md)](class-diagram.md)** | オブジェクト指向設計とクラス仕様 | 全体クラス図 (Mermaid)、Python/Rust間の責務分担、Provider抽象化 |

---

## 🛠️ 開発者向けクイックリンク
- [メイン README.md (プロジェクト概要・使い方)](../README.md)
- [開発環境セットアップ (SETUP_UV.md)](../SETUP_UV.md)
- [開発者ガイド (docs/DEVELOPMENT.md)](../docs/DEVELOPMENT.md)
