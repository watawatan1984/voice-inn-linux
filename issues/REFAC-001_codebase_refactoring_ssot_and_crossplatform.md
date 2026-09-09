# コードベース全体のリファクタリング（SSOT原則徹底・クロスプラットフォーム最適化・テストスイート新設）

## メタ情報

| 項目 | 内容 |
|:---|:---|
| イシューID | REFAC-001 |
| ステータス | ✅ 完了 |
| 優先度 | P1 🟠 High |
| 作成日 | 2026-09-09 |
| 更新日 | 2026-09-09 |
| 担当者 | Antigravity |
| 関連イシュー | [BUG-001](./BUG-001_voicein_persistent_idle_i18n_tray_icon.md), [FEAT-001](./FEAT-001_context_aware_prompt_optimization.md) |

---

## 1. 背景・目的

Voice In (Python + PyQt6) のコードベースにおいて、機能追加に伴う定数やプロンプトの二重管理、未インストールパッケージによるインポート時クラッシュ、OS固有（Linux XDG前提）のパス・貼り付け処理、およびUI層での数百行に及ぶQSSスタイルシートの重複が存在していた。
これらを解消し、保守性・堅牢性・可読性を大幅に向上させ、自動テストで品質を担保できる体制を構築する。

---

## 2. 現状の問題点

1. **定数・プロンプトの重複と乖離 (SSOT違反)**:
   - `src/core/config.py` と `src/core/context_prompt.py` に `DEFAULT_CATEGORIES` / `DEFAULT_CATEGORY_PROMPTS` が二重定義されていた。
   - `config.py` 側のプロンプトに `{window_title}` プレースホルダーが欠落し、設定値が優先されるとタイトル置換が効かない状態だった。
2. **ウィンドウカテゴリ判定の誤爆**:
   - `kw in title_lower` の単純部分一致のため、BIZキーワード `"meet"` が `"Meeting Notes"`（DOC系アプリ）に誤マッチしていた。
3. **AIプロバイダ層の密結合**:
   - `AIWorker` 内で `if/elif` 分岐により各プロバイダを直接インスタンス化しており、モデル名も一部ハードコードされていた。
4. **モジュールインポート時のクラッシュ**:
   - `rust_core` や `google-genai` が未インストールの環境で、モジュールインポート時に例外が送出されアプリ全体が起動不可となっていた。
5. **クロスプラットフォーム非対応**:
   - `utils.py` のパス解決が Linux XDG（`~/.config`）固定で、Windows の `%APPDATA%` 等に未対応だった。
   - `overlay.py` の貼り付け処理が `xdotool`（Linux専用）前提だった。
6. **UIスタイルシートの重複と作法違反**:
   - `SettingsDialog` と `SetupWizardDialog` に数百行の同一 QSS がコピペされており、クラス定義内部に `from PyQt6.QtCore import pyqtSignal` が再定義されていた。
7. **テストコードの不在**:
   - 単体テストが存在せず、回帰テストが自動化されていなかった。

---

## 3. 実装方針

- **SSOT原則**: 定数・既定プロンプト・モデル名を `src/core/const.py` に集約し、全モジュールから参照。
- **ファクトリパターン**: `src/ai/factory.py` を新設し、プロバイダ生成を疎結合化。
- **安全な遅延チェック**: 外部パッケージのインポート検証を各クラスの `__init__` で実施し、モジュールロード時のクラッシュを防止。
- **OS判別と標準準拠**: Windows / macOS / Linux それぞれの標準パスおよびペースト方法（Ctrl+V / Cmd+V / xdotool）に分岐。
- **QSS共通化**: `src/ui/styles.py` にダイアログスタイルを集約。
- **自動テスト**: `tests/` に 23 件の単体テストを整備。

---

## 4. 具体的な要件・変更内容

### A. コア層
- `src/core/const.py`:
  - モデル名定数 (`DEFAULT_GEMINI_MODEL`, `DEFAULT_GROQ_WHISPER_MODEL`, `DEFAULT_GROQ_REFINE_MODEL`) 追加
  - プロンプト・カテゴリ定義の一元化 (`DEFAULT_APP_CATEGORIES`, `DEFAULT_CATEGORY_PROMPTS`)
- `src/core/config.py`:
  - 重複定数を削除し `const.py` 参照に統合。`import copy` を先頭に整理。
- `src/core/context_prompt.py`:
  - 重複定数を `const.py` 参照に変更。
  - 正規表現による単語境界マッチ（`_matches_keyword`）を導入し、`meet` が `Meeting` に誤爆しないよう修正。
- `src/core/utils.py`:
  - `get_config_dir()`, `get_state_dir()` を Windows (`%APPDATA%` / `%LOCALAPPDATA%`)、macOS (`~/Library/Application Support`)、Linux (XDG) に対応（下位互換性確保）。

### B. AI層
- `src/ai/factory.py` (新規):
  - `get_provider(name)` によるファクトリ関数を提供。
- `src/ai/worker.py`:
  - ファクトリ経由でプロバイダをインスタンス化。
- `src/ai/providers/gemini.py` & `src/ai/providers/groq.py`:
  - 各 SDK インポートを `__init__` で検証し安全化。
  - Groq のモデル名を設定・定数から動的に取得可能に変更。

### C. 音声層
- `src/audio/recorder.py`:
  - `rust_core` 未ビルド時でもモジュールロードで例外を出さず、クラス初期化時に明示的メッセージを出す安全構造に改修。

### D. UI層
- `src/ui/styles.py` (新規):
  - `COMMON_DIALOG_STYLESHEET`, `DANGER_BUTTON_STYLE`, `SUCCESS_BUTTON_STYLE` を定義。
- `src/ui/settings.py` & `src/ui/setup.py`:
  - 重複していた数百行の QSS を共通モジュール参照に置換。
  - クラス内部の不正な `from PyQt6.QtCore import pyqtSignal` を解消。
- `src/ui/overlay.py`:
  - `do_paste()` を OS ごとに整理（Linux は xdotool、Windows/macOS は pynput）。
  - `print()` を `logging` に統一。
  - ダイアログ起動時に `raise_()` / `activateWindow()` で前面化。

---

## 5. テスト結果

新設した単体テスト（`python -m unittest discover -s tests -p "test_*.py" -v`）を実行。

```
test_available_providers (test_ai_factory.TestAIFactory) ... ok
test_get_gemini_provider (test_ai_factory.TestAIFactory) ... ok
test_get_groq_provider (test_ai_factory.TestAIFactory) ... ok
test_unknown_provider_raises_error (test_ai_factory.TestAIFactory) ... ok
test_app_categories_match_const (test_config.TestConfig) ... ok
test_deep_merge_dict (test_config.TestConfig) ... ok
test_default_settings_structure (test_config.TestConfig) ... ok
test_get_language_fallback (test_config.TestConfig) ... ok
test_detect_category_biz (test_context_prompt.TestContextPrompt) ... ok
test_detect_category_dev (test_context_prompt.TestContextPrompt) ... ok
test_detect_category_doc (test_context_prompt.TestContextPrompt) ... ok
test_detect_category_fallback (test_context_prompt.TestContextPrompt) ... ok
test_generate_context_prompt (test_context_prompt.TestContextPrompt) ... ok
test_get_category_prompt_placeholder_injection (test_context_prompt.TestContextPrompt) ... ok
test_append_and_load_history (test_history.TestHistory) ... ok
test_history_max_items_limit (test_history.TestHistory) ... ok
test_missing_key_fallback (test_i18n.TestI18n) ... ok
test_placeholder_formatting (test_i18n.TestI18n) ... ok
test_translation_en (test_i18n.TestI18n) ... ok
test_translation_ja (test_i18n.TestI18n) ... ok
test_custom_env_config_dir (test_utils.TestUtils) ... ok
test_now_iso_format (test_utils.TestUtils) ... ok
test_portable_mode_config_dir (test_utils.TestUtils) ... ok

----------------------------------------------------------------------
Ran 23 tests in 0.369s

OK
```

全 23 件合格。

---

## 6. 実装完了項目

- [x] `src/core/const.py` - 定数・プロンプト・モデル既定値の一元化
- [x] `src/core/utils.py` - クロスプラットフォームパス解決
- [x] `src/core/config.py` - 重複排除と const.py 参照化
- [x] `src/core/context_prompt.py` - 単語境界マッチングと const.py 参照化
- [x] `src/ai/factory.py` - プロバイダファクトリ新設
- [x] `src/ai/worker.py` - ファクトリ利用リファクタリング
- [x] `src/ai/providers/gemini.py` - SDKチェック安全化・定数適用
- [x] `src/ai/providers/groq.py` - モデル名動的取得・logging統一
- [x] `src/audio/recorder.py` - モジュール安全ロード
- [x] `src/ui/styles.py` - 共通QSSスタイルモジュール新設
- [x] `src/ui/settings.py` - スタイル共通化・インポート整理
- [x] `src/ui/setup.py` - スタイル共通化・インポート整理
- [x] `src/ui/overlay.py` - OS別ペースト分岐・ダイアログ前面化・logging統一
- [x] `tests/` - 6モジュール・計23件の単体テスト作成と全件合格
- [x] `issues/refactor.md` - 包括的リファクタリング報告書の作成

---

## 変更履歴

| 日付 | 変更者 | 内容 |
|:---|:---|:---|
| 2026-09-09 | Antigravity | 初版作成および全改修完了 |
