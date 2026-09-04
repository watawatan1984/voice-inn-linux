# Voice In (Linux / Cross-Platform) - シーケンス図集

**文書バージョン**: 1.0.0  
**作成日**: 2026-09-04  
**ステータス**: 正式承認版  

---

## 1. メイン処理フロー: 音声録音・AI推論・自動貼り付け (正常系)

```mermaid
sequenceDiagram
    autonumber
    actor User as ユーザー
    participant Hook as pynput Listener
    participant Overlay as AquaOverlay (Qt GUI)
    participant Rust as PyAudioRecorder (Rust)
    participant Context as context_prompt / window_detector
    participant Worker as AIWorker (QThread)
    participant Cloud as AI プロバイダ (Gemini / Groq)
    participant Hist as history.py
    participant OS as xdotool / pynput
    participant Target as 入力先アプリ (VSCode/Slack等)

    User->>Hook: Alt_L 押下
    Hook->>Overlay: on_key_press -> start_recording_signal.emit()
    Overlay->>OS: xdotool getactivewindow -> ウィンドウID記憶
    Overlay->>Overlay: 録音スタイル適用 & パルスアニメーション開始
    Overlay->>Rust: start(temp_wav_path) -> サンプルレート取得

    loop 録音中 (ユーザー発話)
        Rust->>Rust: cpal PCM ストリーム -> hound WAV 書込
    end

    User->>Hook: Alt_L 離脱
    Hook->>Overlay: on_key_release -> stop_recording_signal.emit()
    Overlay->>Rust: stop()
    Overlay->>Rust: is_silence() (Rust VAD 判定)
    Rust-->>Overlay: false (音声あり)

    Overlay->>Overlay: 処理中スタイル適用 (⏳) & パルス停止
    Overlay->>Context: get_active_window() -> カテゴリ判別 (DEV/BIZ/DOC/STD)
    Context-->>Overlay: 合成済み prompts 辞書

    Overlay->>Worker: new AIWorker(provider, wav_path, prompts)
    Overlay->>Worker: moveToThread(QThread) -> start()
    
    rect rgb(240, 248, 255)
        Note over Worker, Cloud: QThread で非同期実行 (GUI をブロックしない)
        Worker->>Cloud: transcribe(audio_path, prompts)
        Cloud-->>Worker: 整形済みテキスト
        Worker-->>Overlay: finished.emit(text)
    end

    Overlay->>Overlay: ユーザー辞書置換 (settings.Dictionary)
    Overlay->>Hist: append_history_item(text, provider)
    Overlay->>Overlay: 成功スタイル適用 (✅)
    Overlay->>Overlay: QApplication.clipboard().setText(text)

    Overlay->>OS: do_paste() (遅延タイマー後)
    OS->>OS: 修飾キー (Alt/Ctrl) 解除
    OS->>Target: xdotool windowactivate --sync {target_window}
    OS->>Target: xdotool key --clearmodifiers ctrl+v
    Target-->>User: テキストが入力完了！

    Overlay->>Overlay: threading.Thread -> 一時 WAV 物理削除
    Note over Overlay: 1000ms 後に reset_ui() (待機状態 🎤 へ復帰)
```

---

## 2. Rust ネイティブ VAD による無音自動キャンセル

キーの誤タッチや極めて短い発話（0.2秒未満）、または無音の場合に、無駄な API 課金や遅延を防止するフロー。

```mermaid
sequenceDiagram
    autonumber
    actor User as ユーザー
    participant Hook as pynput Listener
    participant Overlay as AquaOverlay
    participant Rust as PyAudioRecorder (Rust)

    User->>Hook: Alt_L 誤押下
    Hook->>Overlay: start_recording_signal
    Overlay->>Rust: start(temp_wav_path)

    User->>Hook: Alt_L 即座に離脱 (<0.2秒 または 無音)
    Hook->>Overlay: stop_recording_signal
    Overlay->>Rust: stop()
    Overlay->>Rust: is_silence(vad_energy_threshold, vad_peak_threshold, min_duration)
    Rust-->>Overlay: true (無音または最小時間未満)

    Note over Overlay: API 呼び出しを行わずに即時キャンセル
    Overlay->>Overlay: 一時 WAV ファイルを削除
    Overlay->>Overlay: reset_ui() (待機状態 🎤 へ復帰)
```

---

## 3. タスクトレイからのプロバイダ即時切替

```mermaid
sequenceDiagram
    autonumber
    actor User as ユーザー
    participant Tray as QSystemTrayIcon
    participant Menu as QMenu
    participant Config as config_manager
    participant Overlay as AquaOverlay

    User->>Tray: トレイアイコンを右クリック
    Tray->>Menu: exec() (メニュー表示)
    User->>Menu: 「Groq に切替」をクリック
    Menu->>Config: update_env("AI_PROVIDER", "groq")
    Config->>Config: .env を更新 & os.environ 反映
    Menu->>Overlay: update_style() (枠線色を Groq カラー #F55036 に更新)
    Menu->>Tray: showMessage("Voice In", "Switched to groq")
```

---

## 4. 初回セットアップウィザード & Local モデルダウンロード

初回起動時、またはメニューから起動される対話型ウィザードのフロー。

```mermaid
sequenceDiagram
    autonumber
    actor User as ユーザー
    participant Overlay as AquaOverlay
    participant Wizard as SetupWizardDialog
    participant Local as faster-whisper

    Overlay->>Wizard: open_setup_wizard()
    Wizard-->>User: 1. 言語選択 (日本語/英語/フランス語/スペイン語/韓国語)
    User->>Wizard: 「次へ」押下
    Wizard-->>User: 2. AI プロバイダ選択 (Gemini / Groq / Local)

    opt Local プロバイダを選択
        Wizard-->>User: 「モデルをダウンロード」ボタン表示
        User->>Wizard: 「モデルダウンロード」クリック
        Wizard->>Local: download_model("large-v3")
        Note over Wizard: ダウンロードプログレス表示
        Local-->>Wizard: ダウンロード完了
        Wizard-->>User: ✅ モデルダウンロード成功メッセージ
    end

    User->>Wizard: 3. マイク選択 & マイクテスト (音声レベル確認)
    User->>Wizard: 4. ホットキー & 自動貼り付け設定
    User->>Wizard: 「完了」クリック
    Wizard->>Overlay: 設定を保存 & スタイル適用
```
