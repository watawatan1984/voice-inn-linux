from PyQt6.QtWidgets import (
    QDialog, QWidget, QVBoxLayout, QHBoxLayout, QFormLayout, 
    QTabWidget, QLabel, QComboBox, QLineEdit, QDoubleSpinBox, 
    QSpinBox, QCheckBox, QPushButton, QMessageBox, QTableWidget,
    QTableWidgetItem, QPlainTextEdit, QProgressBar
)
from PyQt6.QtCore import Qt, QTimer
import threading
import numpy as np
import sounddevice as sd

from src.core.config import config_manager
from src.core.i18n import t
from src.ai.worker import AIWorker

# Reuse audio logic for tests if possible or keep simple inside dialog
from src.audio.recorder import open_input_stream_with_fallback, SAMPLE_RATE

class SettingsDialog(QDialog):
    # settings_applied signal? 
    # Actually using config_manager, maybe we don't need signal if main loop watches config?
    # But usually applying settings needs immediate effect on Overlay.
    # We can emit a signal or just rely on main checking config.
    # The original implementation had a signal.
    # Let's keep it simple: saving updates config_manager. Main window can connect to a signal if I add one to ConfigManager?
    # Or I can just emit a custom signal from dialog.
    from PyQt6.QtCore import pyqtSignal
    settings_applied = pyqtSignal(dict)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle(t("settings_title"))
        self.setMinimumSize(820, 640)

        self._general_form = None
        self._general_label_rows = {}
        self._local_form = None
        
        self._audio_lock = threading.Lock()
        self._mic_level = 0.0
        self._mic_stream = None
        self._test_rec_stream = None
        self._test_recorded_chunks = []
        self._test_is_recording = False
        self._test_recording_fs = SAMPLE_RATE
        self._ai_worker = None
        # Thread management for test AI worker?
        # Using QThread locally for tests.
        from PyQt6.QtCore import QThread
        self._ai_thread = None

        self.tabs = QTabWidget()
        self._build_general_tab()
        self._build_prompts_tab()
        self._build_local_tab()
        self._build_dictionary_tab()
        self._build_tests_tab()

        self.btn_save_apply = QPushButton(t("settings_save_apply"))
        self.btn_close = QPushButton(t("settings_close"))
        self.btn_save_apply.clicked.connect(self.on_save_apply)
        self.btn_close.clicked.connect(self.close)

        bottom = QHBoxLayout()
        bottom.addStretch(1)
        bottom.addWidget(self.btn_save_apply)
        bottom.addWidget(self.btn_close)

        root = QVBoxLayout()
        root.addWidget(self.tabs)
        root.addLayout(bottom)
        self.setLayout(root)
        
        self._mic_timer = QTimer(self)
        self._mic_timer.setInterval(100)
        self._mic_timer.timeout.connect(self._update_mic_bar)

        self._load_from_current()

    def _build_general_tab(self):
        w = QWidget()
        form = QFormLayout()
        self._general_form = form
        
        self.cmb_provider = QComboBox()
        self.cmb_provider.addItems(["gemini", "groq", "local"])
        
        self.txt_gemini_model = QLineEdit()
        self.txt_groq_key = QLineEdit()
        self.txt_groq_key.setEchoMode(QLineEdit.EchoMode.Password)
        self.txt_gemini_key = QLineEdit()
        self.txt_gemini_key.setEchoMode(QLineEdit.EchoMode.Password)
        
        self.cmb_input_device = QComboBox()
        self.btn_refresh_input_devices = QPushButton(t("btn_refresh"))
        self.btn_refresh_input_devices.clicked.connect(self.on_refresh_input_devices)
        
        device_row = QHBoxLayout()
        device_row.addWidget(self.cmb_input_device, 1)
        device_row.addWidget(self.btn_refresh_input_devices)
        
        self.spn_input_gain_db = QDoubleSpinBox()
        self.spn_input_gain_db.setRange(-30.0, 30.0)
        self.spn_input_gain_db.setSuffix(" dB")
        
        self.spn_max_record_seconds = QSpinBox()
        self.spn_max_record_seconds.setRange(5, 600)
        self.spn_max_record_seconds.setSuffix(" s")
        
        self.spn_min_duration = QDoubleSpinBox()
        self.spn_min_duration.setRange(0.2, 5.0)
        self.spn_min_duration.setSingleStep(0.1)
        self.spn_min_duration.setSuffix(" s")
        
        self.chk_auto_paste = QCheckBox(t("label_auto_paste"))
        self.spn_paste_delay_ms = QSpinBox()
        self.spn_paste_delay_ms.setRange(0, 1000)
        self.spn_paste_delay_ms.setSuffix(" ms")
        
        self.cmb_hold_key = QComboBox()
        for k, v in [("Left Alt", "alt_l"), ("Right Alt", "alt_r"), ("Left Ctrl", "ctrl_l"), ("Right Ctrl", "ctrl_r")]:
            self.cmb_hold_key.addItem(k, v)
            
        self.cmb_language = QComboBox()
        for k, v in [("日本語", "ja"), ("English", "en"), ("Français", "fr"), ("Español", "es"), ("한국어", "ko")]:
            self.cmb_language.addItem(k, v)
        
        form.addRow(t("label_ai_provider"), self.cmb_provider)
        form.addRow(t("label_gemini_model"), self.txt_gemini_model)
        form.addRow(t("label_groq_key"), self.txt_groq_key)
        form.addRow(t("label_gemini_key"), self.txt_gemini_key)
        form.addRow(t("label_input_device"), device_row)
        form.addRow(t("label_input_gain"), self.spn_input_gain_db)
        form.addRow(t("label_hold_key"), self.cmb_hold_key)
        form.addRow(t("label_max_recording"), self.spn_max_record_seconds)
        form.addRow(t("label_min_duration"), self.spn_min_duration)
        form.addRow(t("label_auto_paste"), self.chk_auto_paste)
        form.addRow(t("label_paste_delay"), self.spn_paste_delay_ms)
        form.addRow(t("label_language"), self.cmb_language)
        
        w.setLayout(form)
        self.tabs.addTab(w, t("tab_general"))

    def _build_prompts_tab(self):
        w = QWidget()
        layout = QVBoxLayout()
        self.txt_groq_whisper_prompt = QPlainTextEdit()
        self.txt_groq_refine_prompt = QPlainTextEdit()
        self.txt_gemini_prompt = QPlainTextEdit()
        
        layout.addWidget(QLabel("Groq Whisper Prompt"))
        layout.addWidget(self.txt_groq_whisper_prompt)
        layout.addWidget(QLabel("Groq Refine System Prompt"))
        layout.addWidget(self.txt_groq_refine_prompt)
        layout.addWidget(QLabel("Gemini Transcribe Prompt"))
        layout.addWidget(self.txt_gemini_prompt)
        w.setLayout(layout)
        self.tabs.addTab(w, t("tab_prompts"))

    def _build_local_tab(self):
        w = QWidget()
        form = QFormLayout()
        self._local_form = form
        
        self.cmb_local_size = QComboBox()
        # faster-whisper models
        for m in ["tiny", "base", "small", "medium", "large-v3", "large-v2"]:
            self.cmb_local_size.addItem(m)
            
        self.cmb_local_device = QComboBox()
        self.cmb_local_device.addItems(["cuda", "cpu", "auto"])
        
        self.cmb_local_compute = QComboBox()
        self.cmb_local_compute.addItems(["float16", "int8_float16", "int8"])
        
        form.addRow(t("label_local_model_size"), self.cmb_local_size)
        form.addRow(t("label_local_device"), self.cmb_local_device)
        form.addRow(t("label_local_compute_type"), self.cmb_local_compute)
        
        w.setLayout(form)
        self.tabs.addTab(w, "Local Whisper")

    def _build_dictionary_tab(self):
        w = QWidget()
        layout = QVBoxLayout()
        self.tbl_dict = QTableWidget(0, 2)
        self.tbl_dict.setHorizontalHeaderLabels([t("dict_from"), t("dict_to")])
        self.tbl_dict.horizontalHeader().setStretchLastSection(True)
        
        btn_row = QHBoxLayout()
        self.btn_dict_add = QPushButton(t("dict_add"))
        self.btn_dict_remove = QPushButton(t("dict_remove"))
        self.btn_dict_add.clicked.connect(self.on_dict_add)
        self.btn_dict_remove.clicked.connect(self.on_dict_remove)
        btn_row.addWidget(self.btn_dict_add)
        btn_row.addWidget(self.btn_dict_remove)
        btn_row.addStretch(1)
        
        layout.addWidget(self.tbl_dict)
        layout.addLayout(btn_row)
        w.setLayout(layout)
        self.tabs.addTab(w, t("tab_dictionary"))

    def _build_tests_tab(self):
        w = QWidget()
        layout = QVBoxLayout()
        
        layout.addWidget(QLabel(t("tests_mic_title")))
        mic_row = QHBoxLayout()
        self.btn_mic_test = QPushButton(t("tests_mic_start"))
        self.mic_bar = QProgressBar()
        self.mic_bar.setRange(0, 100)
        self.btn_mic_test.clicked.connect(self.on_toggle_mic_test)
        mic_row.addWidget(self.btn_mic_test)
        mic_row.addWidget(self.mic_bar)
        layout.addLayout(mic_row)
        
        layout.addWidget(QLabel(t("tests_accuracy_title")))
        rec_row = QHBoxLayout()
        self.btn_test_record = QPushButton(t("tests_rec_start"))
        self.btn_test_stop = QPushButton(t("tests_stop"))
        self.btn_test_transcribe = QPushButton(t("tests_transcribe"))
        self.btn_test_stop.setEnabled(False)
        self.btn_test_transcribe.setEnabled(False)
        self.btn_test_record.clicked.connect(self.on_test_start_recording)
        self.btn_test_stop.clicked.connect(self.on_test_stop_recording)
        self.btn_test_transcribe.clicked.connect(self.on_test_transcribe)
        rec_row.addWidget(self.btn_test_record)
        rec_row.addWidget(self.btn_test_stop)
        rec_row.addWidget(self.btn_test_transcribe)
        layout.addLayout(rec_row)
        
        self.txt_test_result = QPlainTextEdit()
        self.txt_test_result.setPlaceholderText(t("tests_result_ph"))
        layout.addWidget(self.txt_test_result)
        
        w.setLayout(layout)
        self.tabs.addTab(w, t("tab_tests"))

    def _load_from_current(self):
        settings = config_manager.settings
        
        # Audio
        audio = settings.get("audio", {})
        self.spn_input_gain_db.setValue(float(audio.get("input_gain_db", 0.0)))
        self.spn_max_record_seconds.setValue(int(audio.get("max_record_seconds", 60)))
        self.spn_min_duration.setValue(float(audio.get("min_duration", 0.2)))
        self.chk_auto_paste.setChecked(bool(audio.get("auto_paste", True)))
        self.spn_paste_delay_ms.setValue(int(audio.get("paste_delay_ms", 60)))
        
        # Keys & Provider
        self.cmb_provider.setCurrentText(config_manager.settings.get("ai_provider") or "gemini") # It's actually stored in .env usually, but ConfigManager loads it to settings?
        # Re-check config implementation. ConfigManager loads .env but doesn't explicitly put AI_PROVIDER in settings dict unless we do it.
        # But `load_settings` merges `settings.json`.
        # `os.environ` has the provider logic in main.py.
        # Let's fix ConfigManager usage. `update_env` sets `os.environ`.
        # So we should read from `os.environ` or `config_manager.settings`.
        import os
        self.cmb_provider.setCurrentText(os.getenv("AI_PROVIDER", "gemini"))
        self.txt_gemini_model.setText(os.getenv("GEMINI_MODEL", "gemini-2.5-flash"))
        self.txt_groq_key.setText(os.getenv("GROQ_API_KEY", ""))
        self.txt_gemini_key.setText(os.getenv("GEMINI_API_KEY", ""))

        hold_key = audio.get("hold_key", "alt_l")
        idx = self.cmb_hold_key.findData(hold_key)
        if idx >= 0: self.cmb_hold_key.setCurrentIndex(idx)
        
        ui = settings.get("ui", {})
        idx = self.cmb_language.findData(ui.get("language", "ja"))
        if idx >= 0: self.cmb_language.setCurrentIndex(idx)

        # Prompts
        p = settings.get("prompts", {})
        self.txt_groq_whisper_prompt.setPlainText(p.get("groq_whisper_prompt", ""))
        self.txt_groq_refine_prompt.setPlainText(p.get("groq_refine_system_prompt", ""))
        self.txt_gemini_prompt.setPlainText(p.get("gemini_transcribe_prompt", ""))
        
        # Dictionary
        self.tbl_dict.setRowCount(0)
        for k, v in settings.get("dictionary", {}).items():
            row = self.tbl_dict.rowCount()
            self.tbl_dict.insertRow(row)
            self.tbl_dict.setItem(row, 0, QTableWidgetItem(k))
            self.tbl_dict.setItem(row, 1, QTableWidgetItem(v))
            
        # Local
        loc = settings.get("local", {})
        self.cmb_local_size.setCurrentText(loc.get("model_size", "large-v3"))
        self.cmb_local_device.setCurrentText(loc.get("device", "cuda"))
        self.cmb_local_compute.setCurrentText(loc.get("compute_type", "float16"))
        
        self.on_refresh_input_devices()
        current_dev = audio.get("input_device")
        idx = self.cmb_input_device.findData(current_dev)
        if idx >= 0: self.cmb_input_device.setCurrentIndex(idx)

    def on_refresh_input_devices(self):
        self.cmb_input_device.clear()
        self.cmb_input_device.addItem("Default", None)
        try:
            import rust_core
            devices = rust_core.get_input_devices()
            # devices is list of (name, index)
            for name, idx in devices:
                self.cmb_input_device.addItem(f"{name} ({idx})", idx)
        except Exception as e:
            # Fallback to sounddevice if rust fails or logic differs
            try:
                import sounddevice as sd
                devices = sd.query_devices()
                for idx, dev in enumerate(devices):
                    if int(dev.get("max_input_channels", 0)) > 0:
                        self.cmb_input_device.addItem(f"{dev.get('name')} (sd:{idx})", idx)
            except:
                pass

    def on_dict_add(self):
        row = self.tbl_dict.rowCount()
        self.tbl_dict.insertRow(row)
        self.tbl_dict.setItem(row, 0, QTableWidgetItem(""))
        self.tbl_dict.setItem(row, 1, QTableWidgetItem(""))
        
    def on_dict_remove(self):
        row = self.tbl_dict.currentRow()
        if row >= 0: self.tbl_dict.removeRow(row)

    def on_save_apply(self):
        # Gather data
        provider = self.cmb_provider.currentText()
        gemini_model = self.txt_gemini_model.text()
        groq_key = self.txt_groq_key.text()
        gemini_key = self.txt_gemini_key.text()
        
        config_manager.update_env("AI_PROVIDER", provider)
        config_manager.update_env("GEMINI_MODEL", gemini_model)
        if groq_key: config_manager.update_env("GROQ_API_KEY", groq_key)
        if gemini_key: config_manager.update_env("GEMINI_API_KEY", gemini_key)
        
        dic = {}
        for row in range(self.tbl_dict.rowCount()):
            k = self.tbl_dict.item(row, 0).text().strip()
            v = self.tbl_dict.item(row, 1).text().strip()
            if k: dic[k] = v
            
        new_settings = {
            "audio": {
                "input_gain_db": self.spn_input_gain_db.value(),
                "max_record_seconds": self.spn_max_record_seconds.value(),
                "min_duration": self.spn_min_duration.value(),
                "auto_paste": self.chk_auto_paste.isChecked(),
                "paste_delay_ms": self.spn_paste_delay_ms.value(),
                # keep legacy or hidden values
                "hold_key": self.cmb_hold_key.currentData(),
                "input_device": self.cmb_input_device.currentData(),
            },
            "ui": {
                "language": self.cmb_language.currentData()
            },
            "prompts": {
                "groq_whisper_prompt": self.txt_groq_whisper_prompt.toPlainText(),
                "groq_refine_system_prompt": self.txt_groq_refine_prompt.toPlainText(),
                "gemini_transcribe_prompt": self.txt_gemini_prompt.toPlainText()
            },
            "dictionary": dic,
            "local": {
                "model_size": self.cmb_local_size.currentText(),
                "device": self.cmb_local_device.currentText(),
                "compute_type": self.cmb_local_compute.currentText()
            }
        }
        
        config_manager.update_settings(new_settings)
        self.settings_applied.emit(config_manager.settings)
        QMessageBox.information(self, t("saved_title"), t("saved_message"))

    # Test logic stubs (mic test, recording test)
    # Similar to main.py but using local methods
    def on_toggle_mic_test(self):
        if self._mic_stream:
            self._stop_mic_test()
        else:
            self._start_mic_test()

    def _start_mic_test(self):
        def callback(indata, frames, time_info, status):
             level = float(np.sqrt(np.mean(np.square(indata)))) if frames else 0.0
             with self._audio_lock:
                 self._mic_level = level
        try:
            device = self.cmb_input_device.currentData()
            self._mic_stream, _ = open_input_stream_with_fallback(device=device, channels=1, callback=callback, preferred_sr=SAMPLE_RATE)
            self._mic_stream.start()
            self.btn_mic_test.setText(t("tests_mic_stop"))
            self._mic_timer.start()
        except Exception:
            self._mic_stream = None

    def _stop_mic_test(self):
        if self._mic_stream:
            self._mic_stream.stop()
            self._mic_stream.close()
            self._mic_stream = None
        self.btn_mic_test.setText(t("tests_mic_start"))
        self._mic_timer.stop()
        self.mic_bar.setValue(0)

    def _update_mic_bar(self):
        with self._audio_lock:
            level = self._mic_level
        self.mic_bar.setValue(min(100, int(level * 300)))

    def on_test_start_recording(self):
        self._test_recorded_chunks = []
        self._test_is_recording = True
        
        def callback(indata, frames, time_info, status):
             if self._test_is_recording:
                 self._test_recorded_chunks.append(indata.copy())
        
        try:
            device = self.cmb_input_device.currentData()
            self._test_rec_stream, sr = open_input_stream_with_fallback(device=device, channels=1, callback=callback, preferred_sr=SAMPLE_RATE)
            self._test_recording_fs = int(sr)
            self._test_rec_stream.start()
            self.btn_test_record.setEnabled(False)
            self.btn_test_stop.setEnabled(True)
        except Exception:
            pass

    def on_test_stop_recording(self):
        self._test_is_recording = False
        if self._test_rec_stream:
            self._test_rec_stream.stop()
            self._test_rec_stream.close()
            self._test_rec_stream = None
        self.btn_test_record.setEnabled(True)
        self.btn_test_stop.setEnabled(False)
        self.btn_test_transcribe.setEnabled(True)

    # ... (previous methods)

    def on_test_transcribe(self):
        if not self._test_recorded_chunks: return
        import wave
        import tempfile
        from PyQt6.QtCore import QThread
        
        full_audio = np.concatenate(self._test_recorded_chunks, axis=0)
        # normalize
        mx = np.max(np.abs(full_audio))
        if mx > 0: full_audio = full_audio / mx
        
        # Cleanup previous temp file if exists? 
        # In this scope we create a new one. cleanup logic should be in worker or here after done.
        
        tmp = tempfile.NamedTemporaryFile(suffix=".wav", delete=False)
        self._test_temp_path = tmp.name # Keep reference
        with wave.open(tmp.name, "wb") as w:
            w.setnchannels(1)
            w.setsampwidth(2)
            w.setframerate(self._test_recording_fs)
            w.writeframes((full_audio * 32767).astype(np.int16).tobytes())
            
        provider = self.cmb_provider.currentText()
        prompts = config_manager.settings.get("prompts", {})
        
        self.txt_test_result.setPlainText(t("tests_transcribing"))
        self.btn_test_transcribe.setEnabled(False)
        
        self._ai_thread = QThread()
        self._ai_worker = AIWorker(provider, tmp.name, prompts)
        self._ai_worker.moveToThread(self._ai_thread)
        self._ai_thread.started.connect(self._ai_worker.run)
        self._ai_worker.finished.connect(self._on_test_finished)
        self._ai_worker.error.connect(self._on_test_error)
        # Cleanup thread
        self._ai_worker.finished.connect(self._ai_thread.quit)
        self._ai_worker.error.connect(self._ai_thread.quit)
        self._ai_worker.finished.connect(self._ai_worker.deleteLater)
        self._ai_thread.finished.connect(self._ai_thread.deleteLater)
        # Cleanup temp file
        self._ai_worker.finished.connect(lambda: self._cleanup_test_file())
        self._ai_worker.error.connect(lambda: self._cleanup_test_file())
        
        self._ai_thread.start()
        
    def _cleanup_test_file(self):
        if hasattr(self, '_test_temp_path') and self._test_temp_path and os.path.exists(self._test_temp_path):
            try:
                os.remove(self._test_temp_path)
            except Exception:
                pass
            self._test_temp_path = None
        self.btn_test_transcribe.setEnabled(True)

    def _on_test_finished(self, text):
        self.txt_test_result.setPlainText(text)
        
    def _on_test_error(self, err):
        self.txt_test_result.setPlainText(f"Error: {err}")

    def closeEvent(self, event):
        self._stop_mic_test()
        self.on_test_stop_recording()
        self._cleanup_test_file() # Ensure cleanup on close
        event.accept()

