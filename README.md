# Voice In (Linux / Cross-Platform)

<div align="center">

![Python](https://img.shields.io/badge/Python-3.10%2B-3776AB?style=for-the-badge&logo=python&logoColor=white)
![Rust](https://img.shields.io/badge/Audio%20Core-Rust%20(cpal)-black?style=for-the-badge&logo=rust&logoColor=white)
![UI](https://img.shields.io/badge/GUI-PyQt6-41CD52?style=for-the-badge&logo=qt&logoColor=white)
![Platform](https://img.shields.io/badge/Platform-Linux%20%7C%20Windows%20%7C%20macOS-blue?style=for-the-badge&logo=linux&logoColor=white)
![Display](https://img.shields.io/badge/Display-X11%20%2F%20Wayland-orange?style=for-the-badge)
![License](https://img.shields.io/badge/License-MIT-green.svg?style=for-the-badge)

### **あなたの声を、あらゆる場所でスマートにテキスト化。**
**キーを長押しして話すだけ。Linux・Windows・macOS のあらゆるアプリへ直接流し込む、次世代 AI 音声入力アシスタント。**

[ドキュメント一覧 (Doc/)](Doc/README.md) | [要件定義書](Doc/requirements.md) | [アーキテクチャ設計](Doc/architecture.md) | [シーケンス図](Doc/sequence.md) | [クラス図](Doc/class-diagram.md) | [English](docs/README_en.md)

</div>

---

## 📖 目次
1. [サービス概要](#-サービス概要)
2. [開発の背景と解決したい課題](#-開発の背景と解決したい課題)
3. [なぜ Python + Rust なのか？（技術選定の核心）](#-なぜ-python--rust-なのか技術選定の核心)
4. [主要機能一覧](#-主要機能一覧)
5. [詳細な技術スタック & 選定理由](#-詳細な技術スタック--選定理由)
6. [システムアーキテクチャ](#-システムアーキテクチャ)
7. [設計・実装のこだわり (Engineering Highlights)](#-設計実装のこだわり-engineering-highlights)
8. [ディレクトリ構成](#-ディレクトリ構成)
9. [環境構築 & 使い方 (uv による爆速セットアップ)](#-環境構築--使い方-uv-による爆速セットアップ)
10. [ドキュメント一覧 (Doc/)](#-ドキュメント一覧-doc)
11. [トラブルシューティング](#-トラブルシューティング)
12. [今後のロードマップ](#-今後のロードマップ)
13. [ライセンス & 著者](#-ライセンス--著者)

---

## 💡 サービス概要

**Voice In** は、Linux をメインに Windows / macOS でもシームレスに動作する、AI 搭載の次世代音声入力ツールです。
エディタ（VSCode、Cursor、Vim）、ブラウザ、Slack、Discord、端末（Terminal）など、**現在アクティブになっている任意のウィンドウへ、キーを長押し（Hold-to-Talk）して話すだけで、整形された美しいテキストを自動入力（Auto Paste）**します。

クラウド AI（Google Gemini, Groq）による超高速・高精度な文字起こしに加え、**完全オフラインで機密情報を外部送信しない Local Whisper** にも対応しています。

```
[発話: "えーっとパイソンでスクリプト書いてギットハブにプッシュしといて"]
                 ⬇️ (Gemini 2.5 Flash / Groq LLaMA 3.3 による文脈解析)
[自動入力: "Pythonでスクリプトを作成し、GitHubへプッシュしてください。"]
```

---

## 🎯 開発の背景と解決したい課題

### 1. 開発の背景: Linux デスクトップにおける「音声入力の空白」
Linux は世界中のエンジニア・研究者にとって最も強力な開発環境でありながら、**「実用に耐える快適な日本語音声入力ツールが存在しない」** という長年の課題を抱えていました。
Windows の「Windows 音声認識」や macOS の「音声入力」に相当するネイティブな統合機能がなく、多くの Linux ユーザーがタイピング作業に縛られていました。

### 2. 解決すべき課題
- **OS標準の音声認識の欠如**: Linux デスクトップ環境（Ubuntu, Fedora, Arch 等）で、どのアプリからでも手軽に使えるグローバル音声入力が存在しなかった。
- **フィラーや言い淀みの混入**: 「えーっと」「あー」などの発話ノイズがそのまま入ってしまい、後からの消去作業にストレスがかかる。
- **専門用語・IT用語の誤変換**: カタカナ言葉で出力されたり、誤った漢字に変換され、プログラミングや技術文書で使い物にならない。
- **セキュリティ・プライバシー制約**: 社内機密や未公開コードを扱う開発現場では、外部クラウドに音声を送信できない場合がある。

### 3. Voice In が提供する価値
- **Linux でも「押して話すだけ」**: 画面のどこでも `Left Alt` を長押しするだけで、思考の速度で直接テキストが入力される。
- **脱カタカナ・文脈補正**: AI が前後の文脈から専門用語を判別し、正しい英語スペル（`Python`, `Linux`, `GitHub` 等）へ自動変換。
- **クラウド & オフライン両対応**: 超高速クラウド（Groq/Gemini）と、完全プライベートなローカル GPU/CPU 推論（Local Whisper）をワンクリックで切り替え可能。

---

## ⚡ なぜ Python + Rust なのか？（技術選定の核心）

Voice In は、高水準な GUI・AI 統合に優れた **Python (PyQt6)** と、低レイヤのハードウェア制御・極低遅延 I/O に優れた **Rust (`cpal`)** を融合させたハイブリッドアーキテクチャを採用しています。

```
+--------------------------------------------------------------------------------------------------+
|                            Python + Rust ハイブリッド選定の理由                                  |
+--------------------------+---------------------+--------------------+----------------------------+
| 評価項目                 | Pure Python 実装    | Pure C/C++ 実装    | 本アーキテクチャ (Py+Rust) |
+--------------------------+---------------------+--------------------+----------------------------+
| GUI / アニメーション開発 | ◎ PyQt6 で容易      | △ Qt C++ (難解)    | ◎ PyQt6 による美麗なUI     |
| 最先端 AI SDK との統合   | ◎ 迅速に追従可能    | △ C++ ラッパー必須 | ◎ 最新 SDK を即時利用可能  |
| オーディオ低遅延・安定性 | ✕ GIL/クラッシュ懸念| ◎ 高速だが危険     | ◎ Rust (cpal) で安全・超低遅延 |
| メモリ安全性・並行性     | ✕ 参照カウンタ      | ✕ ポインタ起因バグ | ◎ 所有権モデルでゼロクラッシュ|
| 配布とバインディング     | ◎ スクリプト        | △ ビルドが複雑     | ◎ Maturin/PyO3 で透過利用   |
+--------------------------+---------------------+--------------------+----------------------------+
```

1. **Python の強み（GUI & AI 連携）**:
   - PyQt6 により、透過背景、角丸、動的グラデーション、不透明度パルスアニメーションなど、デスクトップを邪魔しない洗練されたフローティング UI を短期間で構築。
   - `google-genai`、`groq`、`faster-whisper` 等、進化の激しい AI ライブラリを即座に導入可能。
2. **Rust の強み（低レイヤ音声録音 & VAD）**:
   - Python のオーディオライブラリ（PyAudio / sounddevice）は、Linux の ALSA / PulseAudio / PipeWire 環境下でのバッファアンダーランやクラッシュが頻発しやすい。
   - Rust のオーディオライブラリ `cpal` により、OS のオーディオハードウェアから直接ストリーミング録音を実施。
   - 録音波形の RMS エネルギーおよびピーク計算（VAD: 無音判定）を Rust 側で並列実行し、Python 側に有効な WAV のみを引き渡すことで、**GIL の影響を受けない極限の低遅延と堅牢性を達成**。

---

## 🚀 主要機能一覧

```
+-----------------------------------------------------------------------------------+
|                               Voice In (Linux) 機能群                             |
+-----------------------------------------------------------------------------------+
|  [🎙️ ホットキー録音]       [🤖 3大 AI プロバイダ]     [⚡ 自動ペースト (AutoPaste)] |
|   Left Alt 長押しで録音     Gemini / Groq /           xdotool (Linux) / pynput     |
|   離すと自動推論開始        Local Whisper (オフライン) アクティブアプリへ直接送信  |
+-----------------------------------------------------------------------------------+
|  [🎯 コンテキスト認識]     [🛡️ Rust 高速 VAD]        [📚 ユーザー強制辞書]         |
|   DEV / BIZ / DOC / STD     無音・誤タッチ自動キャンセル 専門用語・社内用語を       |
|   アプリに応じたプロンプト  API 課金 & 時間を削減     確実に強制置換               |
+-----------------------------------------------------------------------------------+
|  [💫 フローティングUI]      [🧙 セットアップウィザード] [⚙️ 充実の設定画面]        |
|   半透明・丸型・パルス      初回導入・マイクテスト    プロンプト・マイク・ゲイン   |
|   ドラッグ移動・座標保存    Localモデルダウンロード   ホットキーの自由な変更       |
+-----------------------------------------------------------------------------------+
```

1. **グローバルホットキー (Hold-to-Talk)**:
   - バックグラウンドでキーボードイベントを監視。設定されたキー（`Left Alt`, `Right Alt`, `Left Ctrl`, `Right Ctrl`）を押している間だけ録音。
2. **3 つの選べる AI プロバイダ**:
   - **Google Gemini**: 高精度かつ長文に強い最新モデル（デフォルト: `gemini-2.5-flash` / `gemini-2.0-flash`）。
   - **Groq**: 超高速 Whisper Large v3 ＋ LLaMA 3.3 70B による 1 秒前後の爆速文字起こし＆整形。
   - **Local Whisper**: `faster-whisper` (CTranslate2) を活用し、PC 内の GPU (CUDA) または CPU で推論完結。インターネット不要・完全プライベート。
3. **コンテキスト認識プロンプト最適化**:
   - アクティブなウィンドウ（`xdotool getactivewindow`）を自動監視：
     - `DEV`: VSCode, Cursor, ターミナル等。コードコメント、変数名キャメル/スネークケース、専門用語英単語化。
     - `BIZ`: Slack, Teams, メール等。丁寧なビジネス敬語（です・ます調）、適切な改行。
     - `DOC`: Word, Notion, テキストエディタ等。論理構成重視の書き言葉、Markdown 箇条書き。
     - `STD`: 標準プロンプト。フィラー完全除去。
4. **Rust ネイティブ VAD (無音検出)**:
   - 0.2秒未満の誤タッチや無音発話を Rust 側で瞬時に検知・破棄。無駄な API リクエストをゼロにします。
5. **初回セットアップウィザード**:
   - 初回起動時に自動起動。表示言語の選択、API キー入力、マイクの接続テスト、Local Whisper モデルのダウンロードまでを対話形式で完全サポート。
6. **ユーザー辞書強制置換**:
   - 「From → To」のペアを登録し、認識結果を確定前に強制置換。

---

## 🛠️ 詳細な技術スタック & 選定理由

| レイヤー | 採用技術 | 選定理由 |
| :--- | :--- | :--- |
| **言語** | **Python 3.10+** / **Rust 2021** | 迅速な GUI・AI 統合（Python）と、安全かつ極低遅延なオーディオ・VAD 処理（Rust）の最良の組み合わせ。 |
| **GUI フレームワーク** | **PyQt6 (Qt 6.x)** | Linux (X11/Wayland) 上で半透明・角丸・アニメーション付きウィンドウをクロスプラットフォームで安定描画可能。 |
| **オーディオコア** | **Rust `cpal` + `hound`** | ALSA, PulseAudio, PipeWire, WASAPI, CoreAudio を抽象化し、バッファアンダーランを起こさない堅牢な WAV キャプチャ。 |
| **Python-Rust 結合** | **PyO3 + Maturin** | C FFI よりも安全で、Rust の構造体をネイティブ Python モジュール（`rust_core`）としてゼロオーバーヘッドで透過利用。 |
| **キーボード監視** | **`pynput`** | X11 および Windows/macOS で動作する実績あるグローバルイベントリスナー。 |
| **テキスト自動注入** | **`xdotool` (Linux) / `pynput`** | Linux X11 におけるウィンドウ再アクティブ化と `Ctrl+V` キーストローク送信のデファクトスタンダード。 |
| **クラウド AI** | **`google-genai` / `groq`** | 最新の Google 公式 SDK および Groq Cloud SDK を採用。 |
| **ローカル AI** | **`faster-whisper`** | OpenAI 純正 Whisper に比べ最大 4 倍高速かつ省メモリな CTranslate2 実装。 |
| **パッケージ管理** | **`uv` (Astral)** | pip に比べ 10〜100 倍高速な Python パッケージマネージャー。C 拡張のビルド環境もスムーズに管理。 |

---

## 🏗️ システムアーキテクチャ

```mermaid
flowchart TB
    subgraph Presentation ["GUI プレゼンテーション層 (PyQt6)"]
        Overlay[AquaOverlay <br/> 半透明丸型フローティング]
        Settings[SettingsDialog <br/> タブ付き設定画面]
        Setup[SetupWizardDialog <br/> 初回導入ウィザード]
        History[HistoryDialog <br/> 履歴管理画面]
        Tray[QSystemTrayIcon <br/> タスクトレイ常駐]
    end

    subgraph AppCore ["制御・非同期層"]
        Main[src/main.py]
        Worker[AIWorker <br/> QThread 非同期ワーカ]
        Listener[pynput.keyboard.Listener <br/> バックグラウンド監視]
    end

    subgraph Domain ["ドメイン・ビジネス層"]
        AudioRec[AudioRecorder]
        WinDetect[window_detector.py]
        CtxPrompt[context_prompt.py]
        Config[config_manager]
        AIInterface[<<base>> AIProvider]
    end

    subgraph NativeCore ["ネイティブ音声コア (Rust / PyO3)"]
        PyRec[PyAudioRecorder]
        CPAL[cpal 音声入力]
        Hound[hound WAV 書込]
        VAD[RMS/Peak VAD 判定]
    end

    subgraph Backends ["AI バックエンド & OS"]
        Gemini[GeminiProvider]
        Groq[GroqProvider]
        Local[LocalProvider <br/> faster-whisper]
        X11[xdotool / OS クリップボード]
    end

    Main --> Overlay
    Main --> Tray
    Overlay --> Listener
    Overlay --> AudioRec
    Overlay --> Worker
    Overlay --> WinDetect
    Overlay --> CtxPrompt

    AudioRec --> PyRec
    PyRec --> CPAL
    PyRec --> Hound
    PyRec --> VAD

    Worker --> AIInterface
    AIInterface <|-- Gemini
    AIInterface <|-- Groq
    AIInterface <|-- Local

    Overlay --> X11
```

---

## 💎 設計・実装のこだわり (Engineering Highlights)

### 1. Rust ネイティブ音声処理によるゼロクラッシュ
Python のオーディオ録音スレッドでよく発生するセグメンテーション違反やサスペンド時のフリーズを根本から排除。Rust のメモリ安全性と所有権モデルにより、長時間の常駐でも一切のメモリリークを起こしません。

### 2. QThread による完全非同期 AI パイプライン
GUI イベントループと推論処理を `QThread` (`AIWorker`) で完全に分離。Gemini や Groq の API 通信中や Local Whisper の高負荷推論中であっても、オーバーレイのパルスアニメーション（`QPropertyAnimation`）やトレイメニューの描画が一切カクつきません。

### 3. Linux X11 における安定したペースト制御
Linux のウィンドウマネージャー（GNOME, KDE 等）では、フォーカスの切り替え時に修飾キー（Alt や Ctrl）が押されたまま認識され、ペーストに失敗することがあります。
Voice In では、`xdotool` の `--clearmodifiers` オプションおよび `pynput` のキー解放を組み合わせ、ターゲットウィンドウを同期アクティブ化（`windowactivate --sync`）してから確実に `Ctrl+V` を送信します。

---

## 📂 ディレクトリ構成

```text
voice-in/
├── pyproject.toml              # プロジェクト設定 & 依存関係 (uv)
├── uv.lock                     # 依存ライブラリの厳密なロックファイル
├── VoiceIn.spec                # PyInstaller ビルド仕様書
├── .env.exsmple                # 環境変数設定テンプレート
├── README.md                   # 本ドキュメント
│
├── rust_core/                  # Rust ネイティブ音声コア (PyO3)
│   ├── Cargo.toml              # Rust 依存関係 (cpal, hound, pyo3)
│   └── src/
│       └── lib.rs              # PyAudioRecorder 実装 & VAD アルゴリズム
│
├── src/                        # Python アプリケーション
│   ├── main.py                 # エントリーポイント & トレイアイコン管理
│   │
│   ├── ai/                     # AI プロバイダ層
│   │   ├── worker.py           # QThread 非同期ワーカ (AIWorker)
│   │   └── providers/
│   │       ├── base.py         # AIProvider 抽象基底クラス
│   │       ├── gemini.py       # Google Gemini SDK 実装
│   │       ├── groq.py         # Groq Whisper + LLaMA 3.3 実装
│   │       └── local.py        # faster-whisper ローカル推論実装
│   │
│   ├── audio/                  # 音声制御
│   │   └── recorder.py         # Rust PyAudioRecorder ラッパー
│   │
│   ├── core/                   # コアドメインロジック
│   │   ├── config.py           # 設定・環境変数マネージャー
│   │   ├── const.py            # 多言語辞書 (日/英/仏/西/韓) & 定数
│   │   ├── context_prompt.py   # コンテキスト自動判定 & プロンプト合成
│   │   ├── window_detector.py  # X11 / Win32 アクティブウィンドウ検知
│   │   ├── history.py          # 履歴永続化 (history.json)
│   │   └── utils.py            # ディレクトリパス解決 & 辞書マージ
│   │
│   └── ui/                     # PyQt6 プレゼンテーション層
│       ├── overlay.py          # フローティング丸型オーバーレイ (AquaOverlay)
│       ├── settings.py         # 設定ダイアログ (4タブ構成)
│       ├── setup.py            # 初回セットアップウィザード
│       ├── history.py          # 履歴閲覧ダイアログ
│       └── widgets.py          # 動的トレイアイコン生成
│
├── Doc/                        # 詳細技術ドキュメント
│   ├── README.md               # ドキュメント目次
│   ├── requirements.md         # システム要件定義書
│   ├── architecture.md         # アーキテクチャ設計書
│   ├── data-flow.md            # データフロー図 & 状態遷移図
│   ├── sequence.md             # シーケンス図集
│   └── class-diagram.md        # クラス構造設計書
│
└── docs/                       # 多言語ドキュメント
    ├── README_en.md / _fr.md / _ko.md / _zh.md
    └── DEVELOPMENT.md
```

---

## 🚀 環境構築 & 使い方 (uv による爆速セットアップ)

### 1. 必要要件
- OS: **Linux (Ubuntu / Fedora / Arch 等)**, Windows, macOS
- ツール: **Python 3.10+**, **Rust (Cargo)**, **uv**
- Linux の場合: `xdotool` (自動貼り付け用)
  ```bash
  sudo apt-get install -y xdotool libasound2-dev
  ```

### 2. インストール手順

```bash
# 1. リポジトリのクローン
git clone https://github.com/watawatan1984/voice-inn-linux.git
cd voice-inn-linux

# 2. uv を使用した仮想環境の構築 & 依存関係の同期
uv sync

# 3. Rust ネイティブコアのビルド (Maturin)
uv run maturin develop -m rust_core/Cargo.toml

# 4. 環境変数の作成
cp .env.exsmple .env
# .env を編集して API キーを入力 (Gemini / Groq)
```

### 3. 起動

```bash
uv run python -m src.main
```
※ 初回起動時は自動的に**セットアップウィザード**が立ち上がります。

---

## 🎙️ 使い方

1. 入力したい場所（VSCode、ブラウザ、Slack等）をクリックしてカーソルを置きます。
2. **`Left Alt` キー（または設定キー）を押し続けます**。
3. オーバーレイが赤色（🎙️）になり、パルス点滅したらマイクに向かって話します。
4. 話し終わったらキーを離します。
5. オーバーレイが黄色（⏳）になり、AI 整形後、緑色（✅）に変わると**自動的にテキストが流し込まれます**。

---

## 📚 ドキュメント一覧 (Doc/)

詳細なシステム設計については、以下のドキュメントをご参照ください。

- 📋 **[要件定義書 (Doc/requirements.md)](Doc/requirements.md)**: 業務背景、機能要件一覧、非機能要件、Linux/X11対応仕様。
- 🏛️ **[アーキテクチャ設計書 (Doc/architecture.md)](Doc/architecture.md)**: Python + Rust ハイブリッド構成、Maturin/PyO3連携、3スレッド分離。
- 🔄 **[データフロー図 & 状態遷移図 (Doc/data-flow.md)](Doc/data-flow.md)**: AquaOverlay の5つの状態マシン、Level 0/1 DFD。
- ⏱️ **[シーケンス図集 (Doc/sequence.md)](Doc/sequence.md)**: 録音〜Rust VAD〜推論〜自動貼り付け、ウィザードフロー。
- 🧩 **[クラス構造設計書 (Doc/class-diagram.md)](Doc/class-diagram.md)**: 全体クラス図 (Mermaid)、Python/Rust責務分担。

---

## 🔧 トラブルシューティング

| 現象 | 原因 | 対処法 |
| :--- | :--- | :--- |
| `Failed to import rust_core` | Rust コアが未ビルド | `uv run maturin develop -m rust_core/Cargo.toml` を実行してください。 |
| 自動貼り付けが行われない (Linux) | `xdotool` が未インストール | `sudo apt-get install xdotool` をインストールしてください。Wayland の場合は X11 セッションでの利用を推奨します。 |
| Local Whisper が動かない | `faster-whisper` が未導入 | `uv pip install faster-whisper` を実行するか、ウィザードからモデルをダウンロードしてください。 |
| ホットキーが反応しない | 権限不足またはキー競合 | 設定画面で別のキー（`Right Alt` や `Left Ctrl`）に変更してください。Linux の場合、ユーザーを `input` グループに追加することが推奨されます。 |

---

## 🔮 今後のロードマップ

- [ ] **Wayland ネイティブ対応**: `ydotool` / `wtype` 連携による Wayland 環境での自動貼り付け強化。
- [ ] **リアルタイム・ストリーミング入力**: WebSocket を用いた発話中の逐次テキスト表示。
- [ ] **AppImage / Flatpak 配布**: Linux 各ディストリビューション向けの単一パッケージ配布。

---

## 📄 ライセンス & 著者

- **ライセンス**: [MIT License](LICENSE)
- **開発者**: [watawatan1984](https://github.com/watawatan1984)
- **リポジトリ**: [https://github.com/watawatan1984/voice-inn-linux](https://github.com/watawatan1984/voice-inn-linux)
