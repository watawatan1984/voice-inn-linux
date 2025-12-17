# Voice In (Rust Enhanced)

Linux環境で動作する、高速・安定なミニマム音声入力アプリです。
コアロジックの一部（録音、VAD、デバイス管理）をRustで再実装し、Python (PyQt6) と統合しました。

`Left Alt` キーを押している間の音声を認識し、AI（Groq Whisper + Llama 3 / Gemini / **Local Whisper**）で文字起こし・整形して、現在アクティブなウィンドウに入力します。

## 最新のアップデート (v0.3.0)
- **Rust Core導入**: 音声録音とVAD（無音検知）をRust (`cpal`, `hound`) で再実装し、GILの影響を受けない安定した録音を実現。
- **デバイス機能強化**: 入力デバイスの正確な選択と、最適なサンプルレートの自動検出をサポート。
- **ビルドシステムの刷新**: `maturin` を採用し、Rust拡張モジュールのビルドとPythonパッケージ管理を統合。

## 特徴
- **安定した録音**: Rustによるネイティブスレッドでの音声処理。
- **選べるAIプロバイダ**: Groq, Gemini, Local (faster-whisper)。
- **マルチプラットフォーム対応**: GitHub Actionsにより Linux, Windows, macOS 用のビルドを自動生成。
- **高精度な文字起こし**: Whisper Large v3 モデルを使用。

## 動作環境
- OS: Linux (Ubuntu/Debian系推奨)
  - Windows / macOS はCIビルドにて実験的サポート
- Python: 3.12以上
- Rust: 最新の安定版 (ビルド時のみ必要)

## セットアップ手順

### 1. 必要なツールのインストール (Linux)
```bash
# システムパッケージ (ALSA開発ヘッダ等が必要)
sudo apt update
sudo apt install -y python3-pip python3-venv libasound2-dev libportaudio2 libxcb-cursor0 libxcb-xinerama0 pkg-config

# Rustツールチェーンのインストール
curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh
source $HOME/.cargo/env

# UV のインストール
curl -LsSf https://astral.sh/uv/install.sh | sh
```

### 2. プロジェクトのビルドとセットアップ
```bash
git clone https://github.com/watawatan1984/voice-inn-linux.git
cd voice-inn-linux

# 仮想環境作成
uv venv

# 依存関係インストールとRust拡張のビルド
# (maturinが自動的にrust_coreをビルドしてインストールします)
uv pip install maturin
uv run maturin develop
uv pip sync pyproject.toml
```

### 3. APIキーの設定
`.env` ファイルを作成し、APIキーを設定してください。（`SETUP_UV.md` 参照）

## 実行方法

```bash
uv run src/main.py
```
(または `PYTHONPATH=. uv run src/main.py`)

## マルチプラットフォーム・ビルド

GitHub Actions により、Linux, Windows, macOS 向けの Wheel ファイルが自動的にビルドされます。
Releases ページからダウンロード可能です。

## トラブルシューティング
- **ビルドエラー (ALSA)**: `libasound2-dev` と `pkg-config` がインストールされているか確認してください。
- **Rustエラー**: `rustc` のバージョンが古い可能性があります。 `rustup update` を実行してください。

## 開発者向け
`rust_core/` ディレクトリにRustのソースコードがあります。
変更を加えた場合は `uv run maturin develop` で再ビルドしてください。
