# 環境構築ガイド (UV + Poetry)

本プロジェクトでは、依存関係の管理と環境の再現性を担保するために、**UV** と **Poetry** を使用します。
これにより、どのPCで実行しても同じライブラリのバージョンが使用され、不具合を防ぐことができます。

## 前提条件

- **UV** がインストールされていること
  ```bash
  # Linux / macOS
  curl -LsSf https://astral.sh/uv/install.sh | sh
  ```

## セットアップ手順

プロジェクトディレクトリで以下のコマンドを実行するだけで、高速に環境構築が完了します。

1.  **仮想環境の作成と依存関係のインストール**:
    UVを使用して、Poetry形式の定義ファイル (`pyproject.toml`) から直接インストールを行います。

    ```bash
    # 仮想環境 (.venv) の作成と同期
    uv venv
    uv pip sync pyproject.toml
    ```
    
    > **Note**: `faster-whisper` 等の大きなライブラリも UV なら高速にダウンロードされます。

2.  **ロックファイルの生成 (推奨)**:
    バージョンを完全に固定する場合（チーム開発や別PCへの移行時）、`poetry.lock` または `uv.lock` を生成して共有します。
    今回は UV をメインで使用するため、効率的な `uv.lock` の生成も可能ですが、Poetry互換性を維持する場合は以下のようにします。

    ** Poetry を使う場合 (厳密)**:
    ```bash
    # Poetry自体のインストールは uv tool install poetry が高速です
    uv tool install poetry
    poetry lock
    poetry install
    ```

    ** UV だけですませる場合 (高速・推奨)**:
    ```bash
    # requirements.txt を生成して固定する場合
    uv pip compile pyproject.toml -o requirements.txt
    uv pip sync requirements.txt
    ```

## アプリケーションの実行

作成された仮想環境を使用してアプリを起動します。

```bash
# 仮想環境の python を直接指定
.venv/bin/python main.py

# または uv run 経由 (これが最も簡単です)
uv run main.py
```

## ディレクトリ構成
- `pyproject.toml`: 依存ライブラリの定義
- `.venv/`: 仮想環境（このディレクトリは git に含めないでください）
- `src/`: ソースコード
