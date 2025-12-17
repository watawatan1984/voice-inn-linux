# 🚀 Voice Command Agent (Rust-Integrated Edition)

## 1. プロジェクト概要
*   **目的**: 音声対話のみで、IDEのようなファイル操作・PC操作・コーディングを実現する。
*   **コンセプト**: 「ファイル名や場所を忘れても、曖昧な指示で瞬時に見つけ出し、操作する」
*   **ターゲット**: Linux Mint (開発機) → Windows / macOS / Linux (配布)

## 2. テクノロジースタック (ハイブリッド構成)
適材適所で言語とAIを使い分けます。

| 機能 | 担当技術 | 選定理由 |
| :--- | :--- | :--- |
| **耳 (聴覚)** | **Groq API** (`whisper-large-v3`) | 圧倒的な応答速度（低遅延）。 |
| **脳 (思考)** | **OpenRouter API**<br>(`DeepSeek V3` or `Claude 3.5`) | コスパ最強かつコーディング・推論能力が高い。表記揺れの吸収担当。 |
| **手 (実行)** | **Open Interpreter** (Python) | 柔軟なコマンド実行、コード生成、自己修復。 |
| **足 (高速化)** | **Rust** (`PyO3` + `Maturin`) | ファイルシステム走査、PDF全文検索、システム監視。 |
| **口 (発話)** | OS標準TTS / 軽量ライブラリ | 低スペックPCでも動作させるため。 |

---

## 3. 推奨ディレクトリ構成

PythonとRustが共存する構成です。

```text
VoiceAgent/
├── Cargo.toml             # Rust設定 (依存: walkdir, rayon, pdf-extract, sysinfo)
├── pyproject.toml         # Maturin設定
├── .env                   # APIキー (GROQ, OPENROUTER)
├── src/                   # 【Rust】 高速化ロジック
│   └── lib.rs             # ファイル検索・PDF読取・システム情報取得
├── voice_agent/           # 【Python】 アプリ本体
│   ├── main.py            # 起動エントリーポイント
│   ├── core/
│   │   ├── listener.py    # 音声入力 (VAD + Groq)
│   │   ├── brain.py       # LLM連携・プロンプト管理
│   │   └── executor.py    # Open Interpreterラッパー
│   └── utils/
│       ├── system_profiler.py # Rustから情報を得てプロンプトを作る
│       └── path_adapter.py    # OS間のパス差異吸収 (pathlib)
└── tests/                 # テストコード
```

---

## 4. 開発ロードマップ

### 【Phase 1】 PoC: Linux Mintでのコア体験確立
**目標**: 「音声 → 文字起こし → コマンド実行」の基本ループを完成させる。

*   **実装**:
    1.  **VAD (音声区間検出)**: ユーザーが喋り終わった瞬間を検知してGroqに投げる。
    2.  **専門用語辞書**: Groqのprompt引数に `["Linux Mint", "nemo", "sudo", "grep"]` 等を設定し、誤認識を防ぐ。
    3.  **OI連携**: Open Interpreterに「あなたはLinux Mintのアシスタントです」と定義して接続。

### 【Phase 2】 Rust統合と検索革命（最重要）
**目標**: ファイル名が適当でも、中身まで読んで爆速で探し出す機能を実装。

*   **Rust実装 (`src/lib.rs`)**:
    *   **全文検索機能**: `pdf-extract` と `rayon` (並列処理) を使い、PDFの中身を高速スキャン。
    *   **ロジック**: 「グループAND検索」を実装（後述の技術詳細を参照）。
*   **LLM実装**:
    *   **表記揺れ吸収プロンプト**: 「高橋」と言われたら `["高橋", "髙橋", "takahashi"]` に展開するロジックを注入。

### 【Phase 3】 OS抽象化とマルチプラットフォーム対応
**目標**: WindowsやMacに持っていってもコード修正なしで動くようにする。

*   **システムプロファイル (RAG)**:
    *   起動時にRust (`sysinfo`) でOS・メモリ・アプリ一覧を取得。
    *   LLMへのSystem Messageを動的に書き換える。
        *   Linux: 「Bashを使って。ファイラーはnemo」
        *   Win: 「PowerShellを使って。区切り文字はバックスラッシュ」
*   **パスの抽象化**: Pythonの `pathlib` を全面採用。

### 【Phase 4】 配布パッケージ化
**目標**: Python環境がないPCでも動くexe/appを作る。

*   **ビルド**: `PyInstaller` を使用。Rustのコンパイル済みライブラリ (`.pyd` / `.so`) を同梱設定。
*   **安全装置**: 配布用に `auto_run=False` (実行前確認) をデフォルト化。

---

## 5. 技術詳細：表記揺れ対応「検索ロジック」の決定版

「高橋さんの見積書」を探す際、最も精度が出る実装仕様です。

### A. LLM (Python) 側の処理
ユーザーの音声「たかはしさんのみつもり」を受け、LLMは検索キーワードを**「必須グループ」**に分解してRustに渡します。

**LLMが生成するツール引数 (JSON):**
```json
{
  "search_groups": [
    // グループ1: 人名（どれか1つあればOK）
    ["高橋", "髙橋", "takahashi", "TAKAHASHI", "タカハシ"],
    // グループ2: 書類種別（どれか1つあればOK）
    ["見積", "estimate", "quote", "invoice", "請求書"]
  ]
}
```

### B. Rust (`src/lib.rs`) 側の処理
Rustはフォルダ内のPDFを並列で開き、以下のロジックで判定します。

```rust
// 概念コード
fn match_content(text: &str, groups: &Vec<Vec<String>>) -> bool {
    // 全てのグループについて、「そのグループ内のキーワードが少なくとも1つ」含まれているか？
    // (Group A OR ...) AND (Group B OR ...)
    for group in groups {
        let group_hit = group.iter().any(|keyword| text.to_lowercase().contains(keyword));
        if !group_hit {
            return false; // 1つでも満たさないグループがあれば不合格
        }
    }
    true // 全グループの条件をクリア
}
```

これにより、「高橋ランチメモ（見積なし）」や「佐藤さんの見積書（高橋なし）」を弾き、**「高橋さんの見積書」だけをピンポイントで抽出**できます。

---

## 6. リスク管理とチェックリスト

手戻りを防ぐための確認項目です。

| カテゴリ | チェック項目 | 対策 |
| :--- | :--- | :--- |
| **性能** | PDF 1000件の検索が3秒以内に終わるか？ | Rustの `rayon` (並列化) が効いているか確認。インデックス化(DB保存)への移行も検討。 |
| **精度** | 「タカハシ」のカタカナ検索でヒットするか？ | LLMのプロンプトでカタカナ・ローマ字展開を強制する。 |
| **互換性** | Windowsでパスエラーが出ないか？ | `os.path.join` ではなく `pathlib` を徹底する。 |
| **安全性** | `rm -rf` 等のコマンドが実行されないか？ | Rust側またはPython側でコマンド文字列のブラックリスト判定を入れる。 |
| **コスト** | LLMとの会話が長引いて課金が増えないか？ | 1回の命令で解決できなかった場合、自動で会話履歴を要約・短縮する処理を入れる。 |

