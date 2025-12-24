from PyQt6.QtWidgets import (
    QDialog, QStackedWidget, QWidget, QVBoxLayout, QHBoxLayout, 
    QLabel, QPushButton, QComboBox, QLineEdit, QSpinBox, 
    QCheckBox, QMessageBox, QFormLayout, QProgressBar
)
from PyQt6.QtCore import QTimer, Qt, QThread, pyqtSignal
from PyQt6.QtGui import QIcon
import sounddevice as sd
import numpy as np
import threading

from src.core.config import config_manager
# from src.audio.recorder import open_input_stream_with_fallback, SAMPLE_RATE
from src.core.const import SAMPLE_RATE

class SetupWizardDialog(QDialog):
    from PyQt6.QtCore import pyqtSignal
    settings_applied = pyqtSignal(dict)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Voice In - Setup Wizard")
        self.setMinimumSize(900, 600)
        self.setStyleSheet("""
            QDialog {
                background-color: #f5f5f5;
            }
            QLabel {
                color: #333;
            }
            QPushButton {
                background-color: #4285F4;
                color: white;
                border: none;
                padding: 8px 16px;
                border-radius: 4px;
                font-weight: bold;
                min-width: 80px;
            }
            QPushButton:hover {
                background-color: #357ae8;
            }
            QPushButton:pressed {
                background-color: #2d6fc7;
            }
            QPushButton:disabled {
                background-color: #cccccc;
                color: #666666;
            }
            QLineEdit, QComboBox, QSpinBox {
                padding: 6px;
                border: 2px solid #ddd;
                border-radius: 4px;
                background-color: white;
                font-size: 13px;
            }
            QLineEdit:focus, QComboBox:focus, QSpinBox:focus {
                border: 2px solid #4285F4;
            }
            QLineEdit:disabled {
                background-color: #f5f5f5;
                color: #999;
            }
            QLineEdit[readOnly="true"] {
                background-color: #f5f5f5;
                color: #999;
            }
            QComboBox::drop-down {
                border: none;
            }
            QProgressBar {
                border: 2px solid #ddd;
                border-radius: 4px;
                text-align: center;
                background-color: #f0f0f0;
            }
            QProgressBar::chunk {
                background-color: #4285F4;
                border-radius: 2px;
            }
        """)

        self._audio_lock = threading.Lock()
        self._mic_level = 0.0
        self._mic_stream = None

        self.pages = QStackedWidget()
        self._build_page_welcome()
        self._build_page_provider()
        self._build_page_device()
        self._build_page_controls()
        self._build_page_finish()

        self.btn_back = QPushButton("← Back")
        self.btn_next = QPushButton("Next →")
        self.btn_cancel = QPushButton("Cancel")
        self.btn_cancel.setStyleSheet("""
            QPushButton {
                background-color: #f44336;
            }
            QPushButton:hover {
                background-color: #d32f2f;
            }
        """)
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
        layout.setSpacing(20)
        layout.setContentsMargins(40, 40, 40, 40)
        
        title = QLabel("🎤 Welcome to Voice In")
        title.setStyleSheet("font-size: 24px; font-weight: bold; color: #4285F4; margin-bottom: 10px;")
        
        subtitle = QLabel("AI-powered Voice Dictation Tool")
        subtitle.setStyleSheet("font-size: 14px; color: #666; margin-bottom: 30px;")
        
        body = QLabel(
            "This wizard will guide you through the initial setup:\n\n"
            "✨ Configure AI provider and API key\n"
            "🎙️ Select your microphone\n"
            "⌨️ Configure hotkey and paste options"
        )
        body.setWordWrap(True)
        body.setStyleSheet("font-size: 14px; color: #333; line-height: 1.6; padding: 20px; background-color: white; border-radius: 8px;")
        
        layout.addWidget(title)
        layout.addWidget(subtitle)
        layout.addWidget(body)
        layout.addStretch(1)
        w.setLayout(layout)
        self.pages.addWidget(w)

    def _build_page_provider(self):
        w = QWidget()
        layout = QVBoxLayout()
        layout.setSpacing(20)
        layout.setContentsMargins(40, 40, 40, 40)
        
        title = QLabel("🤖 AI Provider Configuration")
        title.setStyleSheet("font-size: 20px; font-weight: bold; color: #4285F4; margin-bottom: 20px;")
        layout.addWidget(title)
        
        form = QFormLayout()
        form.setSpacing(15)
        form.setLabelAlignment(Qt.AlignmentFlag.AlignRight)

        self.wiz_provider = QComboBox()
        self.wiz_provider.addItems(["gemini", "groq", "local"])
        self.wiz_provider.currentTextChanged.connect(self._update_provider_ui)
        self.wiz_provider.setStyleSheet("min-width: 200px;")
        
        self.wiz_gemini_model = QLineEdit()
        self.wiz_gemini_model.setPlaceholderText("e.g., gemini-2.5-flash")
        
        # API Key fields with show/hide toggle
        # Start with normal mode to ensure input works, then switch to password mode
        self.wiz_groq_key = QLineEdit()
        self.wiz_groq_key.setPlaceholderText("Enter your Groq API key")
        self.wiz_groq_key.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        self.wiz_groq_key.setReadOnly(False)
        self.wiz_groq_key.setEnabled(True)
        # Set password mode after widget is fully initialized
        QTimer.singleShot(0, lambda: self.wiz_groq_key.setEchoMode(QLineEdit.EchoMode.Password))
        
        self.btn_show_groq = QPushButton("👁️")
        self.btn_show_groq.setCheckable(True)
        self.btn_show_groq.setMaximumWidth(40)
        self.btn_show_groq.setFocusPolicy(Qt.FocusPolicy.NoFocus)  # Don't steal focus
        self.btn_show_groq.clicked.connect(lambda: self._toggle_password_visibility(self.wiz_groq_key, self.btn_show_groq))
        
        groq_row = QHBoxLayout()
        groq_row.setSpacing(5)
        groq_row.addWidget(self.wiz_groq_key)
        groq_row.addWidget(self.btn_show_groq)
        groq_widget = QWidget()
        groq_widget.setLayout(groq_row)
        
        self.wiz_gemini_key = QLineEdit()
        self.wiz_gemini_key.setPlaceholderText("Enter your Gemini API key")
        self.wiz_gemini_key.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        self.wiz_gemini_key.setReadOnly(False)
        self.wiz_gemini_key.setEnabled(True)
        # Set password mode after widget is fully initialized
        QTimer.singleShot(0, lambda: self.wiz_gemini_key.setEchoMode(QLineEdit.EchoMode.Password))
        
        self.btn_show_gemini = QPushButton("👁️")
        self.btn_show_gemini.setCheckable(True)
        self.btn_show_gemini.setMaximumWidth(40)
        self.btn_show_gemini.setFocusPolicy(Qt.FocusPolicy.NoFocus)  # Don't steal focus
        self.btn_show_gemini.clicked.connect(lambda: self._toggle_password_visibility(self.wiz_gemini_key, self.btn_show_gemini))
        
        gemini_row = QHBoxLayout()
        gemini_row.setSpacing(5)
        gemini_row.addWidget(self.wiz_gemini_key)
        gemini_row.addWidget(self.btn_show_gemini)
        gemini_widget = QWidget()
        gemini_widget.setLayout(gemini_row)
        
        # Local settings for setup wizard needed? Maybe basic ones.
        self.lbl_local_note = QLabel("ℹ️ Local Whisper requires 'faster-whisper' installed. Model default: large-v3.")
        self.lbl_local_note.setWordWrap(True)
        self.lbl_local_note.setStyleSheet("padding: 12px; background-color: #e3f2fd; border-radius: 4px; color: #1976d2;")
        
        # Model download button for local provider
        self.btn_download_model = QPushButton("⬇️ Download Model")
        self.btn_download_model.setStyleSheet("""
            QPushButton {
                background-color: #4CAF50;
                padding: 10px 20px;
                font-size: 14px;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
            QPushButton:disabled {
                background-color: #cccccc;
            }
        """)
        self.btn_download_model.clicked.connect(self._download_local_model)
        
        self.lbl_download_status = QLabel("")
        self.lbl_download_status.setWordWrap(True)
        self.lbl_download_status.setStyleSheet("padding: 8px; color: #666;")
        
        self.progress_download = QProgressBar()
        self.progress_download.setRange(0, 0)  # Indeterminate progress
        self.progress_download.setVisible(False)

        form.addRow("AI Provider:", self.wiz_provider)
        form.addRow("Gemini Model:", self.wiz_gemini_model)
        form.addRow("Groq API Key:", groq_widget)
        form.addRow("Gemini API Key:", gemini_widget)
        form.addRow("", self.lbl_local_note)
        
        # Local model download section
        local_download_layout = QVBoxLayout()
        local_download_layout.addWidget(self.btn_download_model)
        local_download_layout.addWidget(self.progress_download)
        local_download_layout.addWidget(self.lbl_download_status)
        local_download_widget = QWidget()
        local_download_widget.setLayout(local_download_layout)
        form.addRow("", local_download_widget)

        layout.addLayout(form)
        layout.addStretch(1)
        w.setLayout(layout)
        self.pages.addWidget(w)
    
    def _toggle_password_visibility(self, line_edit, button):
        """Toggle password visibility for API key fields"""
        if button.isChecked():
            line_edit.setEchoMode(QLineEdit.EchoMode.Normal)
            button.setText("🙈")
        else:
            line_edit.setEchoMode(QLineEdit.EchoMode.Password)
            button.setText("👁️")

    def _build_page_device(self):
        w = QWidget()
        layout = QVBoxLayout()
        layout.setSpacing(20)
        layout.setContentsMargins(40, 40, 40, 40)
        
        title = QLabel("🎙️ Microphone Configuration")
        title.setStyleSheet("font-size: 20px; font-weight: bold; color: #4285F4; margin-bottom: 20px;")
        layout.addWidget(title)
        
        device_label = QLabel("Input Device:")
        device_label.setStyleSheet("font-weight: bold; font-size: 13px;")
        layout.addWidget(device_label)
        
        top = QHBoxLayout()
        top.setSpacing(10)
        self.wiz_input_device = QComboBox()
        self.btn_refresh_devices = QPushButton("🔄 Refresh")
        self.btn_refresh_devices.clicked.connect(self._refresh_devices)
        top.addWidget(self.wiz_input_device, 1)
        top.addWidget(self.btn_refresh_devices)
        layout.addLayout(top)
        
        layout.addSpacing(30)
        
        test_label = QLabel("Microphone Test:")
        test_label.setStyleSheet("font-weight: bold; font-size: 13px; margin-top: 10px;")
        layout.addWidget(test_label)
        
        mic_row = QHBoxLayout()
        mic_row.setSpacing(10)
        self.btn_mic_test = QPushButton("▶️ Start Mic Test")
        self.mic_bar = QProgressBar()
        self.mic_bar.setRange(0, 100)
        self.mic_bar.setStyleSheet("""
            QProgressBar {
                height: 25px;
                border: 2px solid #ddd;
                border-radius: 4px;
                text-align: center;
                background-color: #f0f0f0;
            }
            QProgressBar::chunk {
                background-color: #4285F4;
                border-radius: 2px;
            }
        """)
        self.btn_mic_test.clicked.connect(self._toggle_mic_test)
        mic_row.addWidget(self.btn_mic_test)
        mic_row.addWidget(self.mic_bar, 1)
        layout.addLayout(mic_row)
        
        layout.addStretch(1)
        w.setLayout(layout)
        self.pages.addWidget(w)

    def _build_page_controls(self):
        w = QWidget()
        layout = QVBoxLayout()
        layout.setSpacing(20)
        layout.setContentsMargins(40, 40, 40, 40)
        
        title = QLabel("⌨️ Control Settings")
        title.setStyleSheet("font-size: 20px; font-weight: bold; color: #4285F4; margin-bottom: 20px;")
        layout.addWidget(title)
        
        form = QFormLayout()
        form.setSpacing(15)
        form.setLabelAlignment(Qt.AlignmentFlag.AlignRight)
        
        self.wiz_hold_key = QComboBox()
        for k, v in [("Left Alt", "alt_l"), ("Right Alt", "alt_r"), ("Left Ctrl", "ctrl_l"), ("Right Ctrl", "ctrl_r")]:
             self.wiz_hold_key.addItem(k, v)
             
        self.wiz_max_record_seconds = QSpinBox()
        self.wiz_max_record_seconds.setRange(5, 600)
        self.wiz_max_record_seconds.setSuffix(" s")
        
        self.wiz_auto_paste = QCheckBox("Automatically paste transcribed text")
        self.wiz_auto_paste.setStyleSheet("padding: 5px;")
        
        form.addRow("Hold Key:", self.wiz_hold_key)
        form.addRow("Max Recording Time:", self.wiz_max_record_seconds)
        form.addRow("", self.wiz_auto_paste)
        
        layout.addLayout(form)
        layout.addStretch(1)
        w.setLayout(layout)
        self.pages.addWidget(w)

    def _build_page_finish(self):
        w = QWidget()
        layout = QVBoxLayout()
        layout.setSpacing(20)
        layout.setContentsMargins(40, 40, 40, 40)
        
        title = QLabel("✅ Setup Complete!")
        title.setStyleSheet("font-size: 24px; font-weight: bold; color: #4285F4; margin-bottom: 20px;")
        
        self.lbl_finish = QLabel(
            "All settings have been configured.\n\n"
            "Click 'Finish' to save your settings and start using Voice In.\n\n"
            "You can change these settings anytime from the system tray menu."
        )
        self.lbl_finish.setWordWrap(True)
        self.lbl_finish.setStyleSheet("font-size: 14px; color: #333; line-height: 1.6; padding: 20px; background-color: white; border-radius: 8px;")
        
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
        is_groq = (prov == "groq")
        is_local = (prov == "local")
        
        # Enable/disable fields based on provider
        self.wiz_gemini_model.setEnabled(is_gemini)
        self.wiz_gemini_key.setEnabled(is_gemini)
        self.wiz_gemini_key.setReadOnly(not is_gemini)
        
        self.wiz_groq_key.setEnabled(is_groq)
        self.wiz_groq_key.setReadOnly(not is_groq)
        
        self.lbl_local_note.setVisible(is_local)
        self.btn_download_model.setVisible(is_local)
        self.lbl_download_status.setVisible(is_local)
        
        # Ensure enabled fields can receive focus
        if is_gemini:
            self.wiz_gemini_key.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        if is_groq:
            self.wiz_groq_key.setFocusPolicy(Qt.FocusPolicy.StrongFocus)

    def _refresh_devices(self):
        self.wiz_input_device.clear()
        self.wiz_input_device.addItem("Default", None)
        try:
            import rust_core
            devices = rust_core.get_input_devices()
            for name, idx in devices:
                self.wiz_input_device.addItem(f"{name} ({idx})", idx)
        except Exception as e:
             # Fallback
            try:
                import sounddevice as sd
                devices = sd.query_devices()
                for idx, dev in enumerate(devices):
                     if int(dev.get("max_input_channels", 0)) > 0:
                         self.wiz_input_device.addItem(f"{dev.get('name')} (sd:{idx})", idx)
            except:
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
            self._mic_stream = sd.InputStream(
                device=device,
                channels=1,
                samplerate=SAMPLE_RATE,
                callback=callback
            )
            self._mic_stream.start()
            self.btn_mic_test.setText("Stop Mic Test")
            self._mic_timer.start()
        except Exception as e:
            print(f"Mic Test Error: {e}")
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

    def _download_local_model(self):
        """Download Whisper model for local provider"""
        try:
            from faster_whisper import WhisperModel
        except ImportError:
            QMessageBox.warning(
                self,
                "Missing Dependency",
                "faster-whisper is not installed.\n\n"
                "Please install it with:\n"
                "pip install faster-whisper"
            )
            return
        
        self.btn_download_model.setEnabled(False)
        self.progress_download.setVisible(True)
        self.lbl_download_status.setText("Downloading model... This may take several minutes.")
        
        # Get model settings
        local_settings = config_manager.settings.get("local", {})
        model_size = local_settings.get("model_size", "large-v3")
        device = local_settings.get("device", "cuda")
        compute_type = local_settings.get("compute_type", "float16")
        
        # Download in background thread
        self._download_thread = ModelDownloadThread(model_size, device, compute_type)
        self._download_thread.finished.connect(self._on_model_download_finished)
        self._download_thread.error.connect(self._on_model_download_error)
        self._download_thread.start()
    
    def _on_model_download_finished(self, success):
        self.progress_download.setVisible(False)
        self.btn_download_model.setEnabled(True)
        if success:
            self.lbl_download_status.setText("✅ Model downloaded successfully!")
            self.lbl_download_status.setStyleSheet("padding: 8px; color: #4CAF50; font-weight: bold;")
        else:
            self.lbl_download_status.setText("❌ Model download failed. Please check the logs.")
            self.lbl_download_status.setStyleSheet("padding: 8px; color: #f44336;")
    
    def _on_model_download_error(self, error_msg):
        self.progress_download.setVisible(False)
        self.btn_download_model.setEnabled(True)
        self.lbl_download_status.setText(f"❌ Error: {error_msg}")
        self.lbl_download_status.setStyleSheet("padding: 8px; color: #f44336;")
        QMessageBox.critical(self, "Download Error", f"Failed to download model:\n{error_msg}")
    
    def closeEvent(self, event):
        self._stop_mic_test()
        if hasattr(self, '_download_thread') and self._download_thread.isRunning():
            self._download_thread.terminate()
            self._download_thread.wait()
        event.accept()


class ModelDownloadThread(QThread):
    """Background thread for downloading Whisper model"""
    finished = pyqtSignal(bool)
    error = pyqtSignal(str)
    
    def __init__(self, model_size, device, compute_type):
        super().__init__()
        self.model_size = model_size
        self.device = device
        self.compute_type = compute_type
    
    def run(self):
        try:
            from faster_whisper import WhisperModel
            import logging
            
            logging.info(f"Downloading Whisper model: {self.model_size} on {self.device} ({self.compute_type})")
            # This will automatically download the model if not present
            model = WhisperModel(self.model_size, device=self.device, compute_type=self.compute_type)
            logging.info("Model downloaded successfully")
            self.finished.emit(True)
        except Exception as e:
            import traceback
            error_msg = str(e)
            logging.error(f"Model download error: {traceback.format_exc()}")
            self.error.emit(error_msg)
