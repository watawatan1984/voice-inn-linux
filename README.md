# Voice In（ミニマムな音声入力アプリ）

Linux環境で動作する、ミニマムな音声入力アプリです。
`Left Alt` キーを押している間の音声を認識し、AI（Groq Whisper + Llama 3 / Gemini / **Local Whisper**）で文字起こし・整形して、現在アクティブなウィンドウに入力します。

## 最新のアップデート (v0.2.0 - 2024/12)
- **大規模リファクタリング**: コードベースをモジュール構成 (`src/`) に刷新し、堅牢性と拡張性を向上させました。
- **Local Whisper 対応**: ローカルでの高速な文字起こし (`faster-whisper`, Large v3 対応) をサポートしました。
- **環境構築の刷新**: 依存関係管理を **UV + Poetry** に移行し、環境再現性を高めました。

## 特徴
- **選べるAIプロバイダ**: 
  - **Groq**: 超高速クラウド文字起こし。
  - **Gemini**: Googleの高精度モデル。
  - **Local**: ローカルGPU/CPUを使用したプライバシー重視・オフライン対応 (faster-whisper)。
- **高精度な文字起こし**: Whisper Large v3 モデルを使用。
- **文字起こし後の追加修正（プロンプト）**: 文章の整形やスタイル調整が可能。
- **AIによる自動整形**: フィラー除去、句読点付与など。
- **邪魔にならないUI**: オーバーレイUIとトレイアイコンで直感的に操作可能。

## 動作環境
- OS: Linux (Ubuntu/Debian系推奨)
- Python: 3.10以上
- GUI: X11推奨 (Waylandでは一部機能に制限がある場合があります)

## セットアップ手順 (UV + Poetry)

本プロジェクトでは高速なパッケージマネージャ **UV** を推奨しています。

### 1. 前提条件のインストール
```bash
# システムパッケージ (Linux)
sudo apt update
sudo apt install -y python3-pip python3-venv libportaudio2 libxcb-cursor0 libxcb-xinerama0

# UV のインストール (未導入の場合)
curl -LsSf https://astral.sh/uv/install.sh | sh
```

### 2. プロジェクトのセットアップ
```bash
cd /path/to/voice-in

# 仮想環境の作成と依存関係の同期
# pyproject.toml に定義されたライブラリが一括でインストールされます
uv venv
uv pip sync pyproject.toml
```

Local Whisper を使用する場合、`faster-whisper` も自動的にインストールされます。  
GPUを使用する場合は、別途 NVIDIA ドライバと CUDA ツールキットの環境が必要です。

### 3. APIキーの設定
プロジェクトのルートディレクトリに `.env` ファイルを作成し、使用するプロバイダのキーを設定します。
（アプリの「Setup Wizard」または「Settings」からも設定可能です）

```bash
# .env (例)
AI_PROVIDER=gemini  # gemini, groq, local
GEMINI_API_KEY=AIzaSy...
GROQ_API_KEY=gsk_...
```

## 使い方

1.  **起動**:
    作成された仮想環境を使用して起動します。
    `src` ディレクトリ構成になりましたが、エントリーポイントとして `main.py` を引き続き使用できます。

    ```bash
    # uv run を使用する場合 (推奨)
    uv run main.py

    # または直接 python を呼ぶ場合
    .venv/bin/python main.py
    ```

    画面にマイクアイコン（🎤）が表示されます。

2.  **音声入力**:
    - 入力したいテキストボックスをフォーカスします。
    - **`Left Alt` キーを押し続けて** 話します。
    - キーを離すと文字起こしが開始されます。

3.  **設定変更**:
    - トレイアイコンを右クリック → `Settings` または `Setup Wizard` で、AIプロバイダやモデル、音声デバイスを変更できます。

## カスタマイズ

### ログの確認
ログファイルは `~/.local/state/voice-in/app.log` (Linux標準のXDG Stateディレクトリ) に出力されます。
また、ターミナルからも標準出力でログを確認できます。

### 辞書登録
設定画面の `Dictionary` タブから、誤認識しやすい単語の置換ルールを追加・編集できるようになりました。ユーザーによる `main.py` の直接編集は不要です。

## トラブルシューティング
- **ImportError / ModuleNotFoundError**: 仮想環境が正しく有効化されていないか、インストールが不完全です。 `uv pip sync pyproject.toml` を再実行してください。
- **Local Whisper が遅い**: CPUで動作している可能性があります。NVIDIA GPUがある場合、`sys.path` にCUDAライブラリが含まれているか確認してください。
- **起動しない**: `src` ディレクトリが存在し、`main.py` と同じ階層にあることを確認してください。

## 開発者向け
依存関係を追加する場合は `pyproject.toml` を編集し、再度 `uv pip sync pyproject.toml` を実行してください。
再現性を保証するため、`setup_uv.md` も参照してください。
