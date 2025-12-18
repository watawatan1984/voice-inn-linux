# 環境構築ガイド (UV)
 
 本プロジェクトでは、依存関係の管理と環境の再現性を担保するために **UV** を使用します。
 これにより、どのPCで実行しても同じライブラリのバージョンが使用され、不具合を防ぐことができます。

 ## 前提条件
 
 - **UV** がインストールされていること
  ```bash
  # Linux / macOS
  curl -LsSf https://astral.sh/uv/install.sh | sh
  ```

 ## セットアップ手順
 
 プロジェクトディレクトリで以下のコマンドを実行するだけで、高速に環境構築が完了します。
 
 1.  **依存関係の同期**:
     `pyproject.toml` と `uv.lock` を使って依存を同期します。
 
     ```bash
     # 依存の同期（uv.lock を優先して再現性を担保）
     uv sync
     ```
     
     > **Note**: `faster-whisper` 等の大きなライブラリも UV なら高速にダウンロードされます。
 
 2.  **ロックファイルの生成/更新**:
     バージョンを固定する場合（チーム開発や別PCへの移行時）、`uv.lock` を生成・更新して共有します。

     ```bash
     uv lock
     ```

 3.  **（任意）ローカルに `.venv` を作る場合**:
     IDEの補完やデバッグで「プロジェクト配下のPython」を固定したい場合は `.venv` を作ってもOKです。

     ```bash
     uv venv
     uv pip sync pyproject.toml
     ```

 ## アプリケーションの実行
 
 アプリを起動します。
 
 ```bash
 # uv run 経由（推奨）
 uv run python main.py
 ```

 > Rust拡張（`rust_core`）を開発中にビルドしたい場合は `maturin` を使います。
 > 
 > ```bash
 > uv run maturin develop
 > ```

 ## ディレクトリ構成
 - `pyproject.toml`: 依存ライブラリの定義
 - `uv.lock`: 依存のロックファイル
 - `.venv/`: 仮想環境（作る場合。git に含めないでください）
 - `src/`: ソースコード
