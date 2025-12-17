from PyQt6.QtWidgets import (
    QDialog, QStackedWidget, QWidget, QVBoxLayout, QHBoxLayout, 
    QLabel, QPushButton, QComboBox, QLineEdit, QSpinBox, 
    QCheckBox, QMessageBox, QFormLayout, QProgressBar
)
from PyQt6.QtCore import QTimer, Qt
import sounddevice as sd
import numpy as np
import threading

from src.core.config import config_manager
from src.audio.recorder import open_input_stream_with_fallback, SAMPLE_RATE

class SetupWizardDialog(QDialog):
    from PyQt6.QtCore import pyqtSignal
    settings_applied = pyqtSignal(dict)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Setup Wizard")
        self.setMinimumSize(820, 560)

        self._audio_lock = threading.Lock()
        self._mic_level = 0.0
        self._mic_stream = None

        self.pages = QStackedWidget()
        self._build_page_welcome()
        self._build_page_provider()
        self._build_page_device()
        self._build_page_controls()
        self._build_page_finish()

        self.btn_back = QPushButton("Back")
        self.btn_next = QPushButton("Next")
        self.btn_cancel = QPushButton("Cancel")
        self.btn_back.clicked.connect(self._back)
        self.btn_next.clicked.connect(self._next)
        self.btn_cancel.clicked.connect(self.close)

        bottom = QHBoxLayout()
        bottom.addWidget(self.btn_cancel)
        bottom.addStretch(1)
        bottom.addWidget(self.btn_back)
        bottom.addWidget(self.btn_next)

        root = QVBoxLayout()
        root.addWidget(self.pages, 1)
        root.addLayout(bottom)
        self.setLayout(root)

        self._mic_timer = QTimer(self)
        self._mic_timer.setInterval(100)
        self._mic_timer.timeout.connect(self._update_mic_bar)
        
        # Load defaults
        self._load_from_current()
        self._update_nav()

    def _build_page_welcome(self):
        w = QWidget()
        layout = QVBoxLayout()
        title = QLabel("Welcome")
        title.setStyleSheet("font-size: 18px; font-weight: bold;")
        body = QLabel(
            "This wizard helps you complete initial setup.\n\n"
            "1) Configure AI provider and API key\n"
            "2) Select microphone\n"
            "3) Configure hotkey and paste options"
        )
        body.setWordWrap(True)
        layout.addWidget(title)
        layout.addWidget(body)
        layout.addStretch(1)
        w.setLayout(layout)
        self.pages.addWidget(w)

    def _build_page_provider(self):
        w = QWidget()
        form = QFormLayout()

        self.wiz_provider = QComboBox()
        self.wiz_provider.addItems(["gemini", "groq", "local"])
        self.wiz_provider.currentTextChanged.connect(self._update_provider_ui)
        
        self.wiz_gemini_model = QLineEdit()
        self.wiz_groq_key = QLineEdit()
        self.wiz_groq_key.setEchoMode(QLineEdit.EchoMode.Password)
        self.wiz_gemini_key = QLineEdit()
        self.wiz_gemini_key.setEchoMode(QLineEdit.EchoMode.Password)
        
        # Local settings for setup wizard needed? Maybe basic ones.
        self.lbl_local_note = QLabel("Local Whisper requires 'faster-whisper' installed. Model default: large-v3.")
        self.lbl_local_note.setWordWrap(True)

        form.addRow("AI Provider", self.wiz_provider)
        form.addRow("Gemini Model", self.wiz_gemini_model)
        form.addRow("Groq API Key", self.wiz_groq_key)
        form.addRow("Gemini API Key", self.wiz_gemini_key)
        form.addRow(self.lbl_local_note)

        w.setLayout(form)
        self.pages.addWidget(w)

    def _build_page_device(self):
        w = QWidget()
        layout = QVBoxLayout()
        top = QHBoxLayout()
        self.wiz_input_device = QComboBox()
        self.btn_refresh_devices = QPushButton("Refresh")
        self.btn_refresh_devices.clicked.connect(self._refresh_devices)
        top.addWidget(QLabel("Input Device"))
        top.addWidget(self.wiz_input_device, 1)
        top.addWidget(self.btn_refresh_devices)
        layout.addLayout(top)
        
        mic_row = QHBoxLayout()
        self.btn_mic_test = QPushButton("Start Mic Test")
        self.mic_bar = QProgressBar()
        self.mic_bar.setRange(0, 100)
        self.btn_mic_test.clicked.connect(self._toggle_mic_test)
        mic_row.addWidget(self.btn_mic_test)
        mic_row.addWidget(self.mic_bar)
        layout.addLayout(mic_row)
        layout.addStretch(1)
        w.setLayout(layout)
        self.pages.addWidget(w)

    def _build_page_controls(self):
        w = QWidget()
        form = QFormLayout()
        self.wiz_hold_key = QComboBox()
        for k, v in [("Left Alt", "alt_l"), ("Right Alt", "alt_r"), ("Left Ctrl", "ctrl_l"), ("Right Ctrl", "ctrl_r")]:
             self.wiz_hold_key.addItem(k, v)
             
        self.wiz_max_record_seconds = QSpinBox()
        self.wiz_max_record_seconds.setRange(5, 600)
        self.wiz_max_record_seconds.setSuffix(" s")
        
        self.wiz_auto_paste = QCheckBox("Paste automatically")
        
        form.addRow("Hold Key", self.wiz_hold_key)
        form.addRow("Max Recording", self.wiz_max_record_seconds)
        form.addRow("Auto Paste", self.wiz_auto_paste)
        w.setLayout(form)
        self.pages.addWidget(w)

    def _build_page_finish(self):
        w = QWidget()
        layout = QVBoxLayout()
        title = QLabel("Finish")
        title.setStyleSheet("font-size: 18px; font-weight: bold;")
        self.lbl_finish = QLabel("Click Finish to save settings and start using Voice In.")
        layout.addWidget(title)
        layout.addWidget(self.lbl_finish)
        layout.addStretch(1)
        w.setLayout(layout)
        self.pages.addWidget(w)

    def _load_from_current(self):
        import os
        self.wiz_provider.setCurrentText(os.getenv("AI_PROVIDER", "gemini"))
        self.wiz_gemini_model.setText(os.getenv("GEMINI_MODEL", "gemini-2.5-flash"))
        self.wiz_groq_key.setText(os.getenv("GROQ_API_KEY", ""))
        self.wiz_gemini_key.setText(os.getenv("GEMINI_API_KEY", ""))
        
        audio = config_manager.settings.get("audio", {})
        hold_key = audio.get("hold_key", "alt_l")
        idx = self.wiz_hold_key.findData(hold_key)
        if idx >= 0: self.wiz_hold_key.setCurrentIndex(idx)
        
        self.wiz_max_record_seconds.setValue(int(audio.get("max_record_seconds", 60)))
        self.wiz_auto_paste.setChecked(bool(audio.get("auto_paste", True)))
        
        self._refresh_devices()
        current_dev = audio.get("input_device")
        idx = self.wiz_input_device.findData(current_dev)
        if idx >= 0: self.wiz_input_device.setCurrentIndex(idx)
        self._update_provider_ui()

    def _update_provider_ui(self):
        prov = self.wiz_provider.currentText()
        is_gemini = (prov == "gemini")
        self.wiz_gemini_model.setEnabled(is_gemini)
        self.wiz_gemini_key.setEnabled(is_gemini)
        self.wiz_groq_key.setEnabled(prov == "groq")
        self.lbl_local_note.setVisible(prov == "local")

    def _refresh_devices(self):
        self.wiz_input_device.clear()
        self.wiz_input_device.addItem("Default", None)
        try:
            devices = sd.query_devices()
            for idx, dev in enumerate(devices):
                 if int(dev.get("max_input_channels", 0)) > 0:
                     self.wiz_input_device.addItem(f"{dev.get('name')} ({idx})", idx)
        except Exception:
            pass

    def _toggle_mic_test(self):
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
            device = self.wiz_input_device.currentData()
            self._mic_stream, _ = open_input_stream_with_fallback(device=device, channels=1, callback=callback, preferred_sr=SAMPLE_RATE)
            self._mic_stream.start()
            self.btn_mic_test.setText("Stop Mic Test")
            self._mic_timer.start()
        except Exception:
            self._mic_stream = None

    def _stop_mic_test(self):
        if self._mic_stream:
            self._mic_stream.stop()
            self._mic_stream.close()
            self._mic_stream = None
        self.btn_mic_test.setText("Start Mic Test")
        self._mic_timer.stop()
        self.mic_bar.setValue(0)

    def _update_mic_bar(self):
        with self._audio_lock: level = self._mic_level
        self.mic_bar.setValue(min(100, int(level * 300)))

    def _next(self):
        idx = self.pages.currentIndex()
        if idx == 1: # Provider
             # Simple validation
             pass
        if idx == self.pages.count() - 1:
             self._apply_all()
             self.close()
             return
        self.pages.setCurrentIndex(idx + 1)
        self._update_nav()

    def _back(self):
        idx = self.pages.currentIndex()
        if idx > 0:
             self.pages.setCurrentIndex(idx - 1)
             self._update_nav()

    def _update_nav(self):
        idx = self.pages.currentIndex()
        last = self.pages.count() - 1
        self.btn_back.setEnabled(idx > 0)
        self.btn_next.setText("Finish" if idx == last else "Next")

    def _apply_all(self):
        # Update config
        provider = self.wiz_provider.currentText()
        gemini_model = self.wiz_gemini_model.text()
        groq_key = self.wiz_groq_key.text()
        gemini_key = self.wiz_gemini_key.text()
        
        config_manager.update_env("AI_PROVIDER", provider)
        config_manager.update_env("GEMINI_MODEL", gemini_model)
        if groq_key: config_manager.update_env("GROQ_API_KEY", groq_key)
        if gemini_key: config_manager.update_env("GEMINI_API_KEY", gemini_key)
        
        new_audio = {
            "input_device": self.wiz_input_device.currentData(),
            "max_record_seconds": self.wiz_max_record_seconds.value(),
            "auto_paste": self.wiz_auto_paste.isChecked(),
            "hold_key": self.wiz_hold_key.currentData()
        }
        config_manager.update_settings({"audio": new_audio})
        self.settings_applied.emit(config_manager.settings)

    def closeEvent(self, event):
        self._stop_mic_test()
        event.accept()
