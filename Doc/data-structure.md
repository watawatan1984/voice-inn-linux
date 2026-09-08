# Voice In - データ構造 & モデリング設計書

**文書バージョン**: 1.0.0  
**作成日**: 2026-09-09  
**対象領域**: 永続化データ (`settings.json`, `history.json`, `.env`)、メモリ内データ構造 (`WindowInfo`, `AudioStats`, etc.)  

---

## 1. データアーキテクチャ概要

Voice In は、外部データベース（SQLite や RDBMS）を必要とせず、ファイルベースの自己完結型ストレージ構造を採用している。
これにより、**ポータブル動作（USBメモリ等での持ち運び）や、ユーザーごとの設定分離、OS標準バックアップとの親和性**を実現している。

```
[OS Config Dir (CONFIG_DIR)]
  ├── settings.json       # アプリケーション全設定（階層化構造）
  └── .env                # 外部APIキー・環境変数
[OS State Dir (STATE_DIR)]
  ├── history.json        # 文字起こし履歴（直近50件リングバッファ）
  └── app.log             # 実行ログ
```

---

## 2. 設定データ仕様 (`settings.json`)

### 2.1 JSON Schema 定義 (抜粋)

```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "title": "VoiceInSettings",
  "type": "object",
  "required": ["audio", "ui", "prompts", "app_categories", "category_prompts"],
  "properties": {
    "audio": {
      "type": "object",
      "properties": {
        "input_device": { "type": ["integer", "null"] },
        "input_gain_db": { "type": "number", "default": 0.0 },
        "max_record_seconds": { "type": "integer", "default": 60 },
        "auto_paste": { "type": "boolean", "default": true },
        "paste_delay_ms": { "type": "integer", "default": 60 },
        "hold_key": { "type": "string", "enum": ["alt_l", "alt_r", "ctrl_l", "ctrl_r"], "default": "alt_l" },
        "vad_energy_threshold": { "type": "number", "default": 0.005 },
        "vad_peak_threshold": { "type": "number", "default": 0.02 },
        "min_duration": { "type": "number", "default": 0.2 }
      }
    },
    "ui": {
      "type": "object",
      "properties": {
        "overlay_pos": {
          "type": ["array", "null"],
          "items": { "type": "integer" },
          "minItems": 2,
          "maxItems": 2
        },
        "language": { "type": "string", "enum": ["ja", "en", "fr", "es", "ko"], "default": "ja" }
      }
    },
    "prompts": {
      "type": "object",
      "properties": {
        "groq_whisper_prompt": { "type": "string" },
        "groq_refine_system_prompt": { "type": "string" },
        "gemini_transcribe_prompt": { "type": "string" }
      }
    },
    "dictionary": {
      "type": "object",
      "additionalProperties": { "type": "string" }
    },
    "local": {
      "type": "object",
      "properties": {
        "model_size": { "type": "string", "default": "large-v3" },
        "device": { "type": "string", "enum": ["cuda", "cpu"], "default": "cuda" },
        "compute_type": { "type": "string", "default": "float16" }
      }
    },
    "app_categories": {
      "type": "object",
      "properties": {
        "DEV": { "type": "array", "items": { "type": "string" } },
        "BIZ": { "type": "array", "items": { "type": "string" } },
        "DOC": { "type": "array", "items": { "type": "string" } },
        "STD": { "type": "array", "items": { "type": "string" } }
      }
    },
    "category_prompts": {
      "type": "object",
      "properties": {
        "DEV": { "type": "string" },
        "BIZ": { "type": "string" },
        "DOC": { "type": "string" },
        "STD": { "type": "string" }
      }
    },
    "detected_apps": {
      "type": "object",
      "additionalProperties": {
        "type": "object",
        "properties": {
          "title_sample": { "type": "string" },
          "auto_category": { "type": "string" },
          "user_category": { "type": ["string", "null"] }
        }
      }
    },
    "context_aware_enabled": { "type": "boolean", "default": true }
  }
}
```

---

## 3. 履歴データ仕様 (`history.json`)

### 3.1 データフォーマット
直近 50 件の文字起こし結果を新しい順（降順）で管理する。

```json
{
  "version": 1,
  "items": [
    {
      "id": "1725838800123",
      "created_at": "2026-09-09T07:00:00+09:00",
      "provider": "gemini",
      "text": "本日の進捗報告です。リファクタリングが完了しました。",
      "error": null
    },
    {
      "id": "1725838700456",
      "created_at": "2026-09-09T06:58:20+09:00",
      "provider": "groq",
      "text": "",
      "error": "API Timeout error"
    }
  ]
}
```

### 3.2 フィールド仕様

| フィールド | 型 | 必須 | 説明 |
| :--- | :---: | :---: | :--- |
| `id` | string | ○ | ミリ秒タイムスタンプ文字列（一意キー） |
| `created_at` | string | ○ | ISO 8601 形式のタイムスタンプ（タイムゾーン情報付き） |
| `provider` | string | ○ | 使用プロバイダ識別子 (`gemini`, `groq`, `local`) |
| `text` | string | ○ | 文字起こし結果本文（辞書置換後の最終確定テキスト） |
| `error` | string / null | ○ | 失敗時のエラーメッセージ要約。成功時は `null` |

### 3.3 Atomic Write (破損耐性設計)
電源断や強制終了による JSON ファイルの破損を完全に防ぐため、以下の手順でアトミックに書き込む。

```python
# 1. 同一ディレクトリ内に一時ファイル (.tmp) として書き出し
with tempfile.NamedTemporaryFile(..., dir=STATE_DIR) as f:
    json.dump(payload, f, ensure_ascii=False, indent=2)
# 2. OS レベルのアトミックなファイル置換 (POSIX rename / Windows ReplaceFile)
os.replace(tmp_path, HISTORY_PATH)
```

---

## 4. 環境変数仕様 (`.env`)

API キーやランタイム動作環境を定義する。

| キー名 | 型 | デフォルト値 | 説明 |
| :--- | :---: | :---: | :--- |
| `AI_PROVIDER` | string | `"gemini"` | 現在アクティブな AI プロバイダ (`gemini`, `groq`, `local`) |
| `GEMINI_API_KEY` | string | `""` | Google Gemini API キー |
| `GEMINI_MODEL` | string | `"gemini-2.0-flash"` | 使用する Gemini モデル名 |
| `GROQ_API_KEY` | string | `""` | Groq Cloud API キー |
| `GROQ_WHISPER_MODEL`| string | `"whisper-large-v3"` | Groq 音声認識モデル |
| `GROQ_REFINE_MODEL` | string | `"llama-3.3-70b-versatile"` | Groq 文章整形モデル |
| `VOICEIN_PORTABLE` | string | `"0"` | `"1"` の場合、設定・状態をアプリ実行ディレクトリに集約 |
| `VOICEIN_CONFIG_DIR`| string | `""` | 設定保存ディレクトリの強制指定パス |
| `VOICEIN_STATE_DIR` | string | `""` | 状態保存ディレクトリの強制指定パス |

---

## 5. メモリ内データ構造 (In-Memory Data Models)

### 5.1 `WindowInfo` (`src/core/window_detector.py`)
```python
class WindowInfo(TypedDict):
    title: str       # ウィンドウの完全タイトル (例: "main.py - Visual Studio Code")
    process: str     # 実行可能ファイル名 (Windows のみ, 例: "Code.exe")
    app_name: str    # 抽出されたクリーンなアプリ名 (例: "Visual Studio Code")
```

### 5.2 `AudioStats` (`src/audio/recorder.py`)
```python
{
    "peak": float,      # 録音期間中の最大 PCM 振幅値 (0.0 〜 1.0)
    "avg_rms": float,   # 平均二乗平方根 (RMS) エネルギー
    "duration": float   # 録音継続時間 (秒)
}
```

### 5.3 `AIProvider` 抽象インターフェース (`src/ai/providers/base.py`)
```python
class AIProvider(ABC):
    @abstractmethod
    def transcribe(self, audio_path: str, prompts: dict) -> str:
        """
        WAV 音声ファイルとプロンプト辞書を受け取り、
        フィラー除去・整形済みのテキストを返す。
        """
        pass
```
