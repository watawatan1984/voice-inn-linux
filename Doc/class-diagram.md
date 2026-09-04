# Voice In (Linux / Cross-Platform) - クラス構造設計書 (Class Diagram)

**文書バージョン**: 1.0.0  
**作成日**: 2026-09-04  
**ステータス**: 正式承認版  

---

## 1. 全体クラス図 (Overview Class Diagram)

```mermaid
classDiagram
    %% GUI Components
    class AquaOverlay {
        -AudioRecorder recorder
        -QSystemTrayIcon _tray
        -string _last_text
        -string _paste_target_window
        -bool _is_processing
        -string _status
        -QPropertyAnimation _pulse_animation
        +pyqtSignal start_recording_signal
        +pyqtSignal stop_recording_signal
        +initUI() void
        +initKeyboard() void
        +update_style() void
        +start_recording() void
        +stop_recording() void
        +do_paste() void
        +on_ai_finished(string text) void
        +on_ai_error(string err) void
        +open_settings() void
        +open_setup_wizard() void
        +show_history() void
    }

    class SettingsDialog {
        -QTabWidget tabs
        +init_general_tab() void
        +init_prompts_tab() void
        +init_dict_tab() void
        +init_categories_tab() void
        +save_settings() void
    }

    class SetupWizardDialog {
        -int current_step
        +init_welcome_page() void
        +init_provider_page() void
        +init_mic_page() void
        +init_controls_page() void
        +download_local_model() void
    }

    class HistoryDialog {
        -QTableWidget table
        +load_history() void
        +copy_selected() void
    }

    %% Audio Subsystem (Python + Rust)
    class AudioRecorder {
        -PyAudioRecorder _native_recorder
        -string _recording_path
        -Thread _monitor_thread
        -Event _stop_event
        +bool is_recording
        +int sample_rate
        +start(int max_seconds, callable on_auto_stop) void
        +stop() string
        +get_stats() dict
        +is_silence(float energy_th, float peak_th, float min_dur) bool
        +cleanup() void
    }

    class PyAudioRecorder {
        <<Rust PyO3 Struct>>
        +start(string path, int? device_index) int
        +stop() void
        +get_stats() tuple
        +is_silence(float energy_th, float peak_th, float min_dur) bool
    }

    %% AI Subsystem
    class AIWorker {
        -string provider
        -string audio_path
        -dict prompts
        +pyqtSignal finished
        +pyqtSignal error
        +run() void
    }

    class AIProvider {
        <<abstract>>
        +transcribe(string audio_path, dict prompts)* string
    }

    class GeminiProvider {
        -Client client
        +transcribe(string audio_path, dict prompts) string
    }

    class GroqProvider {
        -Groq client
        +transcribe(string audio_path, dict prompts) string
    }

    class LocalProvider {
        -WhisperModel model
        +transcribe(string audio_path, dict prompts) string
    }

    %% Core Utilities
    class ConfigManager {
        +dict settings
        +ensure_dirs() void
        +load_env() void
        +load_settings() void
        +update_env(string key, string val) void
        +update_settings(dict new_settings) void
    }

    class WindowDetector {
        <<module>>
        +get_active_window()$ dict
        +get_x11_window()$ dict
        +get_win32_window()$ dict
    }

    class ContextPrompt {
        <<module>>
        +generate_context_prompt(string window_title, dict base_prompts)$ dict
        +classify_window(string window_title, dict categories)$ string
        +add_detected_app(string title, string app_name)$ void
    }

    %% Relationships
    AquaOverlay --> AudioRecorder : owns
    AquaOverlay --> AIWorker : dispatches
    AquaOverlay --> SettingsDialog : opens
    AquaOverlay --> SetupWizardDialog : opens
    AquaOverlay --> HistoryDialog : opens

    AudioRecorder --> PyAudioRecorder : wraps (PyO3)
    AIWorker --> AIProvider : invokes
    AIProvider <|-- GeminiProvider : inherits
    AIProvider <|-- GroqProvider : inherits
    AIProvider <|-- LocalProvider : inherits

    AquaOverlay ..> WindowDetector : detects window
    AquaOverlay ..> ContextPrompt : optimizes prompts
    AquaOverlay ..> ConfigManager : reads/writes
```

---

## 2. コンポーネント責務と設計原則

1. **GUI とバックエンドの完全疎結合**:
   - `AquaOverlay` は UI の描画、キーストロークイベントの受付、シグナルの発信のみを担当。
   - 音声キャプチャの詳細は `AudioRecorder`（さらにその内部の Rust ネイティブバイナリ）に隠蔽。
2. **抽象プロバイダインターフェース (`AIProvider`)**:
   - `GeminiProvider`、`GroqProvider`、`LocalProvider` は共通のインターフェース `transcribe(audio_path, prompts)` を実装しており、`AIWorker` はプロバイダの種類を意識せずに統一的に呼び出し可能。
3. **Rust ネイティブによる並列・安全な I/O**:
   - `PyAudioRecorder` は Rust の所有権モデルによりメモリリークや未定義動作を排除し、オーディオハードウェアから直接 WAV エンコードを行う。
