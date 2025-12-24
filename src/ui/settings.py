from PyQt6.QtWidgets import (
    QDialog, QWidget, QVBoxLayout, QHBoxLayout, QFormLayout, 
    QTabWidget, QLabel, QComboBox, QLineEdit, QDoubleSpinBox, 
    QSpinBox, QCheckBox, QPushButton, QMessageBox, QTableWidget,
    QTableWidgetItem, QPlainTextEdit, QProgressBar, QSplitter,
    QSizePolicy, QScrollArea
)
from PyQt6.QtCore import Qt, QTimer
import threading
import numpy as np
import sounddevice as sd
import os

from src.core.config import config_manager
from src.core.i18n import t
from src.ai.worker import AIWorker
from src.core.history import load_history_file, HISTORY_MAX_ITEMS
from src.core.const import SAMPLE_RATE

class SettingsDialog(QDialog):
    from PyQt6.QtCore import pyqtSignal
    settings_applied = pyqtSignal(dict)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle(t("settings_title"))
        self.setMinimumSize(1000, 700)
        
        # Apply modern styling similar to setup wizard
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
            QLineEdit, QComboBox, QSpinBox, QDoubleSpinBox {
                padding: 6px;
                border: 2px solid #ddd;
                border-radius: 4px;
                background-color: white;
                font-size: 13px;
            }
            QLineEdit:focus, QComboBox:focus, QSpinBox:focus, QDoubleSpinBox:focus {
                border: 2px solid #4285F4;
            }
            QSpinBox::up-button, QDoubleSpinBox::up-button {
                subcontrol-origin: border;
                subcontrol-position: top right;
                width: 22px;
                border-left: 1px solid #ddd;
                border-top-right-radius: 4px;
                background-color: #4CAF50;
            }
            QSpinBox::up-button:hover, QDoubleSpinBox::up-button:hover {
                background-color: #45a049;
            }
            QSpinBox::up-button:pressed, QDoubleSpinBox::up-button:pressed {
                background-color: #3d8b40;
            }
            QSpinBox::up-arrow, QDoubleSpinBox::up-arrow {
                image: none;
                border-left: 5px solid transparent;
                border-right: 5px solid transparent;
                border-bottom: 7px solid white;
                width: 0px;
                height: 0px;
                margin: 2px;
            }
            QSpinBox::down-button, QDoubleSpinBox::down-button {
                subcontrol-origin: border;
                subcontrol-position: bottom right;
                width: 22px;
                border-left: 1px solid #ddd;
                border-bottom-right-radius: 4px;
                background-color: #f44336;
            }
            QSpinBox::down-button:hover, QDoubleSpinBox::down-button:hover {
                background-color: #da190b;
            }
            QSpinBox::down-button:pressed, QDoubleSpinBox::down-button:pressed {
                background-color: #c62828;
            }
            QSpinBox::down-arrow, QDoubleSpinBox::down-arrow {
                image: none;
                border-left: 5px solid transparent;
                border-right: 5px solid transparent;
                border-top: 7px solid white;
                width: 0px;
                height: 0px;
                margin: 2px;
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
            QTabWidget::pane {
                border: 1px solid #ddd;
                background-color: white;
                border-radius: 4px;
            }
            QTabBar::tab {
                background-color: #e0e0e0;
                color: #333;
                padding: 8px 16px;
                margin-right: 2px;
                border-top-left-radius: 4px;
                border-top-right-radius: 4px;
            }
            QTabBar::tab:selected {
                background-color: white;
                color: #4285F4;
                font-weight: bold;
            }
            QTableWidget {
                border: 1px solid #ddd;
                border-radius: 4px;
                background-color: white;
            }
            QPlainTextEdit {
                border: 2px solid #ddd;
                border-radius: 4px;
                background-color: white;
                padding: 4px;
            }
            QPlainTextEdit:focus {
                border: 2px solid #4285F4;
            }
        """)

        self._general_form = None
        self._local_form = None
        
        self._audio_lock = threading.Lock()
        self._mic_level = 0.0
        self._mic_stream = None
        self._test_rec_stream = None
        self._test_recorded_chunks = []
        self._test_is_recording = False
        self._test_recording_fs = SAMPLE_RATE
        self._ai_worker = None
        from PyQt6.QtCore import QThread
        self._ai_thread = None

        self.tabs = QTabWidget()
        self._build_general_tab()
        self._build_prompts_tab()
        self._build_dictionary_tab()
        self._build_history_tab()

        self.btn_save_apply = QPushButton(t("settings_save_apply"))
        self.btn_close = QPushButton(t("settings_close"))
        self.btn_save_apply.clicked.connect(self.on_save_apply)
        self.btn_close.clicked.connect(self.close)

        bottom = QHBoxLayout()
        bottom.addStretch(1)
        bottom.addWidget(self.btn_save_apply)
        bottom.addWidget(self.btn_close)

        root = QVBoxLayout()
        root.setSpacing(10)
        root.setContentsMargins(10, 10, 10, 10)
        root.addWidget(self.tabs)
        root.addLayout(bottom)
        self.setLayout(root)
        
        self._mic_timer = QTimer(self)
        self._mic_timer.setInterval(100)
        self._mic_timer.timeout.connect(self._update_mic_bar)

        self._load_from_current()

    def _build_general_tab(self):
        # Create scroll area for the general tab
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        
        w = QWidget()
        layout = QVBoxLayout()
        layout.setSpacing(20)
        layout.setContentsMargins(30, 30, 30, 30)
        
        # AI Provider Section
        provider_title = QLabel("🤖 AI Provider & Model")
        provider_title.setStyleSheet("font-size: 18px; font-weight: bold; color: #4285F4; margin-bottom: 10px;")
        layout.addWidget(provider_title)
        
        form = QFormLayout()
        form.setSpacing(15)
        form.setLabelAlignment(Qt.AlignmentFlag.AlignRight)
        
        self.cmb_provider = QComboBox()
        self.cmb_provider.addItems(["gemini", "groq", "local"])
        self.cmb_provider.currentTextChanged.connect(self._update_provider_ui)
        self.cmb_provider.setStyleSheet("min-width: 200px;")
        
        # Gemini settings
        self.txt_gemini_model = QLineEdit()
        self.txt_gemini_model.setPlaceholderText("e.g., gemini-2.5-flash")
        
        self.txt_gemini_key = QLineEdit()
        self.txt_gemini_key.setPlaceholderText("Enter your Gemini API key")
        self.txt_gemini_key.setEchoMode(QLineEdit.EchoMode.Password)
        
        self.btn_show_gemini = QPushButton("👁️")
        self.btn_show_gemini.setCheckable(True)
        self.btn_show_gemini.setMaximumWidth(40)
        self.btn_show_gemini.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.btn_show_gemini.clicked.connect(lambda: self._toggle_password_visibility(self.txt_gemini_key, self.btn_show_gemini))
        
        gemini_key_row = QHBoxLayout()
        gemini_key_row.setSpacing(5)
        gemini_key_row.addWidget(self.txt_gemini_key)
        gemini_key_row.addWidget(self.btn_show_gemini)
        gemini_key_widget = QWidget()
        gemini_key_widget.setLayout(gemini_key_row)
        
        # Groq settings
        self.txt_groq_key = QLineEdit()
        self.txt_groq_key.setPlaceholderText("Enter your Groq API key")
        self.txt_groq_key.setEchoMode(QLineEdit.EchoMode.Password)
        
        self.btn_show_groq = QPushButton("👁️")
        self.btn_show_groq.setCheckable(True)
        self.btn_show_groq.setMaximumWidth(40)
        self.btn_show_groq.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.btn_show_groq.clicked.connect(lambda: self._toggle_password_visibility(self.txt_groq_key, self.btn_show_groq))
        
        groq_key_row = QHBoxLayout()
        groq_key_row.setSpacing(5)
        groq_key_row.addWidget(self.txt_groq_key)
        groq_key_row.addWidget(self.btn_show_groq)
        groq_key_widget = QWidget()
        groq_key_widget.setLayout(groq_key_row)
        
        # Local Whisper settings (unified with provider selection)
        self.lbl_local_note = QLabel("ℹ️ Local Whisper requires 'faster-whisper' installed.")
        self.lbl_local_note.setWordWrap(True)
        self.lbl_local_note.setStyleSheet("padding: 12px; background-color: #e3f2fd; border-radius: 4px; color: #1976d2;")
        
        self.cmb_local_size = QComboBox()
        for m in ["tiny", "base", "small", "medium", "large-v3", "large-v2"]:
            self.cmb_local_size.addItem(m)
            
        self.cmb_local_device = QComboBox()
        self.cmb_local_device.addItems(["cuda", "cpu", "auto"])
        
        self.cmb_local_compute = QComboBox()
        self.cmb_local_compute.addItems(["float16", "int8_float16", "int8"])
        
        form.addRow("AI Provider:", self.cmb_provider)
        form.addRow("Gemini Model:", self.txt_gemini_model)
        form.addRow("Gemini API Key:", gemini_key_widget)
        form.addRow("Groq API Key:", groq_key_widget)
        
        layout.addLayout(form)
        
        # Local settings section - separate container that can be shown/hidden
        self.local_settings_container = QWidget()
        local_settings_layout = QVBoxLayout()
        local_settings_layout.setContentsMargins(0, 10, 0, 0)
        local_settings_layout.setSpacing(10)
        
        # Add note label directly (not in form layout)
        local_settings_layout.addWidget(self.lbl_local_note)
        
        # Local settings form
        local_form = QFormLayout()
        local_form.setSpacing(15)
        local_form.setLabelAlignment(Qt.AlignmentFlag.AlignRight)
        local_form.addRow("Local Model Size:", self.cmb_local_size)
        local_form.addRow("Local Device:", self.cmb_local_device)
        local_form.addRow("Local Compute Type:", self.cmb_local_compute)
        
        local_settings_layout.addLayout(local_form)
        self.local_settings_container.setLayout(local_settings_layout)
        # Set size policy to prevent collapsing
        self.local_settings_container.setSizePolicy(
            QSizePolicy.Policy.Expanding, 
            QSizePolicy.Policy.Minimum
        )
        self.local_settings_container.setVisible(False)  # Initially hidden
        layout.addWidget(self.local_settings_container)
        
        layout.addSpacing(20)
        
        # Audio Device Section
        audio_title = QLabel("🎙️ Audio Device")
        audio_title.setStyleSheet("font-size: 18px; font-weight: bold; color: #4285F4; margin-top: 20px; margin-bottom: 10px;")
        layout.addWidget(audio_title)
        
        audio_form = QFormLayout()
        audio_form.setSpacing(15)
        audio_form.setLabelAlignment(Qt.AlignmentFlag.AlignRight)
        
        self.cmb_input_device = QComboBox()
        self.btn_refresh_input_devices = QPushButton("🔄 " + t("btn_refresh"))
        self.btn_refresh_input_devices.clicked.connect(self.on_refresh_input_devices)
        
        device_row = QHBoxLayout()
        device_row.setSpacing(10)
        device_row.addWidget(self.cmb_input_device, 1)
        device_row.addWidget(self.btn_refresh_input_devices)
        device_widget = QWidget()
        device_widget.setLayout(device_row)
        
        self.spn_input_gain_db = QDoubleSpinBox()
        self.spn_input_gain_db.setRange(-30.0, 30.0)
        self.spn_input_gain_db.setSuffix(" dB")
        self.spn_input_gain_db.setToolTip("上矢印: 増加 / 下矢印: 減少")
        
        # Microphone test integrated with device selection
        test_label = QLabel("Microphone Test:")
        test_label.setStyleSheet("font-weight: bold; font-size: 13px; margin-top: 10px;")
        
        mic_test_row = QHBoxLayout()
        mic_test_row.setSpacing(10)
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
        self.btn_mic_test.clicked.connect(self.on_toggle_mic_test)
        mic_test_row.addWidget(self.btn_mic_test)
        mic_test_row.addWidget(self.mic_bar, 1)
        mic_test_widget = QWidget()
        mic_test_widget.setLayout(mic_test_row)
        
        audio_form.addRow("Input Device:", device_widget)
        audio_form.addRow("Input Gain:", self.spn_input_gain_db)
        audio_form.addRow("", test_label)
        audio_form.addRow("", mic_test_widget)
        
        layout.addLayout(audio_form)
        layout.addSpacing(20)
        
        # Control Settings Section
        control_title = QLabel("⌨️ Control Settings")
        control_title.setStyleSheet("font-size: 18px; font-weight: bold; color: #4285F4; margin-top: 20px; margin-bottom: 10px;")
        layout.addWidget(control_title)
        
        control_form = QFormLayout()
        control_form.setSpacing(15)
        control_form.setLabelAlignment(Qt.AlignmentFlag.AlignRight)
        
        self.cmb_hold_key = QComboBox()
        for k, v in [("Left Alt", "alt_l"), ("Right Alt", "alt_r"), ("Left Ctrl", "ctrl_l"), ("Right Ctrl", "ctrl_r")]:
            self.cmb_hold_key.addItem(k, v)
        
        self.spn_max_record_seconds = QSpinBox()
        self.spn_max_record_seconds.setRange(5, 600)
        self.spn_max_record_seconds.setSuffix(" s")
        self.spn_max_record_seconds.setToolTip("上矢印: 増加 / 下矢印: 減少")
        
        self.spn_min_duration = QDoubleSpinBox()
        self.spn_min_duration.setRange(0.2, 5.0)
        self.spn_min_duration.setSingleStep(0.1)
        self.spn_min_duration.setSuffix(" s")
        self.spn_min_duration.setToolTip("上矢印: 増加 / 下矢印: 減少")
        
        self.chk_auto_paste = QCheckBox(t("label_auto_paste"))
        self.chk_auto_paste.setStyleSheet("padding: 5px;")
        
        self.spn_paste_delay_ms = QSpinBox()
        self.spn_paste_delay_ms.setRange(0, 1000)
        self.spn_paste_delay_ms.setSuffix(" ms")
        self.spn_paste_delay_ms.setToolTip("上矢印: 増加 / 下矢印: 減少")
        
        self.cmb_language = QComboBox()
        for k, v in [("日本語", "ja"), ("English", "en"), ("Français", "fr"), ("Español", "es"), ("한국어", "ko")]:
            self.cmb_language.addItem(k, v)
        
        control_form.addRow(t("label_hold_key"), self.cmb_hold_key)
        control_form.addRow(t("label_max_recording"), self.spn_max_record_seconds)
        control_form.addRow(t("label_min_duration"), self.spn_min_duration)
        control_form.addRow(t("label_auto_paste"), self.chk_auto_paste)
        control_form.addRow(t("label_paste_delay"), self.spn_paste_delay_ms)
        control_form.addRow(t("label_language"), self.cmb_language)
        
        layout.addLayout(control_form)
        layout.addStretch(1)
        
        w.setLayout(layout)
        scroll.setWidget(w)
        self.tabs.addTab(scroll, t("tab_general"))

    def _toggle_password_visibility(self, line_edit, button):
        """Toggle password visibility for API key fields"""
        if button.isChecked():
            line_edit.setEchoMode(QLineEdit.EchoMode.Normal)
            button.setText("🙈")
        else:
            line_edit.setEchoMode(QLineEdit.EchoMode.Password)
            button.setText("👁️")

    def _update_provider_ui(self):
        """Update UI based on selected provider"""
        prov = self.cmb_provider.currentText()
        is_gemini = (prov == "gemini")
        is_groq = (prov == "groq")
        is_local = (prov == "local")
        
        # Enable/disable fields based on provider
        self.txt_gemini_model.setEnabled(is_gemini)
        self.txt_gemini_key.setEnabled(is_gemini)
        self.txt_gemini_key.setReadOnly(not is_gemini)
        
        self.txt_groq_key.setEnabled(is_groq)
        self.txt_groq_key.setReadOnly(not is_groq)
        
        # Show/hide local settings container based on provider
        if hasattr(self, 'local_settings_container'):
            self.local_settings_container.setVisible(is_local)
            # Force layout update
            if self.local_settings_container.parent():
                self.local_settings_container.parent().updateGeometry()

    def _build_prompts_tab(self):
        w = QWidget()
        layout = QVBoxLayout()
        layout.setSpacing(15)
        layout.setContentsMargins(30, 30, 30, 30)
        
        title = QLabel("📝 Prompts")
        title.setStyleSheet("font-size: 18px; font-weight: bold; color: #4285F4; margin-bottom: 10px;")
        layout.addWidget(title)
        
        self.txt_groq_whisper_prompt = QPlainTextEdit()
        self.txt_groq_whisper_prompt.setPlaceholderText("Groq Whisper Prompt (e.g., context hints for speech recognition)")
        
        self.txt_groq_refine_prompt = QPlainTextEdit()
        self.txt_groq_refine_prompt.setPlaceholderText("Groq Refine System Prompt (e.g., post-processing rules)")
        
        self.txt_gemini_prompt = QPlainTextEdit()
        self.txt_gemini_prompt.setPlaceholderText("Gemini Transcribe Prompt (e.g., transcription style instructions)")
        
        layout.addWidget(QLabel("Groq Whisper Prompt:"))
        layout.addWidget(self.txt_groq_whisper_prompt, 1)
        layout.addWidget(QLabel("Groq Refine System Prompt:"))
        layout.addWidget(self.txt_groq_refine_prompt, 1)
        layout.addWidget(QLabel("Gemini Transcribe Prompt:"))
        layout.addWidget(self.txt_gemini_prompt, 1)
        
        w.setLayout(layout)
        self.tabs.addTab(w, t("tab_prompts"))

    def _build_dictionary_tab(self):
        w = QWidget()
        layout = QVBoxLayout()
        layout.setSpacing(15)
        layout.setContentsMargins(30, 30, 30, 30)
        
        title = QLabel("📖 Dictionary")
        title.setStyleSheet("font-size: 18px; font-weight: bold; color: #4285F4; margin-bottom: 10px;")
        layout.addWidget(title)
        
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
        
        layout.addWidget(self.tbl_dict, 1)
        layout.addLayout(btn_row)
        w.setLayout(layout)
        self.tabs.addTab(w, t("tab_dictionary"))

    def _build_history_tab(self):
        """Build history tab similar to HistoryDialog"""
        w = QWidget()
        layout = QVBoxLayout()
        layout.setSpacing(15)
        layout.setContentsMargins(30, 30, 30, 30)
        
        title = QLabel("📜 History")
        title.setStyleSheet("font-size: 18px; font-weight: bold; color: #4285F4; margin-bottom: 10px;")
        layout.addWidget(title)
        
        self.txt_history_search = QLineEdit()
        self.txt_history_search.setPlaceholderText(t("history_search_ph"))
        self.txt_history_search.textChanged.connect(self._apply_history_filter)
        
        self.tbl_history = QTableWidget(0, 4)
        self.tbl_history.setHorizontalHeaderLabels([
            t("history_col_time"),
            t("history_col_provider"),
            t("history_col_type"),
            t("history_col_preview"),
        ])
        self.tbl_history.horizontalHeader().setStretchLastSection(True)
        self.tbl_history.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.tbl_history.setSelectionMode(QTableWidget.SelectionMode.SingleSelection)
        self.tbl_history.itemSelectionChanged.connect(self._on_history_select)
        
        self.txt_history_detail = QPlainTextEdit()
        self.txt_history_detail.setReadOnly(True)
        
        self.btn_history_copy = QPushButton(t("history_copy"))
        self.btn_history_copy.clicked.connect(self._copy_history_selected)
        
        top = QHBoxLayout()
        top.addWidget(QLabel(t("history_search")))
        top.addWidget(self.txt_history_search, 1)
        
        buttons = QHBoxLayout()
        buttons.addStretch(1)
        buttons.addWidget(self.btn_history_copy)
        
        layout.addLayout(top)
        layout.addWidget(self.tbl_history, 2)
        layout.addWidget(self.txt_history_detail, 3)
        layout.addLayout(buttons)
        
        w.setLayout(layout)
        self.tabs.addTab(w, t("history_title"))
        
        # Load history
        self._history_items = []
        self._history_filtered = []
        self._reload_history()

    def _reload_history(self):
        """Reload history from file"""
        try:
            self._history_items = load_history_file()
            if not isinstance(self._history_items, list):
                self._history_items = []
        except Exception:
            self._history_items = []
        self._apply_history_filter()

    def _apply_history_filter(self):
        """Apply search filter to history"""
        q = (self.txt_history_search.text() or "").strip().lower()
        if not q:
            self._history_filtered = list(self._history_items)
        else:
            filtered = []
            for it in self._history_items:
                if not isinstance(it, dict):
                    continue
                text = str(it.get("text") or "")
                err = str(it.get("error") or "")
                prov = str(it.get("provider") or "")
                created = str(it.get("created_at") or "")
                hay = (created + "\n" + prov + "\n" + text + "\n" + err).lower()
                if q in hay:
                    filtered.append(it)
            self._history_filtered = filtered
        self._render_history_table()

    def _render_history_table(self):
        """Render history table"""
        self.tbl_history.setRowCount(0)
        for it in self._history_filtered[:HISTORY_MAX_ITEMS]:
            created = str(it.get("created_at") or "")
            provider = str(it.get("provider") or "")
            text = str(it.get("text") or "")
            err = it.get("error")
            kind = "Text" if text.strip() else "Error"
            preview_src = text if text.strip() else str(err or "")
            preview = preview_src.strip().replace("\n", " ")
            if len(preview) > 80:
                preview = preview[:77] + "..."

            row = self.tbl_history.rowCount()
            self.tbl_history.insertRow(row)
            self.tbl_history.setItem(row, 0, QTableWidgetItem(created))
            self.tbl_history.setItem(row, 1, QTableWidgetItem(provider))
            self.tbl_history.setItem(row, 2, QTableWidgetItem(kind))
            self.tbl_history.setItem(row, 3, QTableWidgetItem(preview))

        if self.tbl_history.rowCount() > 0:
            self.tbl_history.selectRow(0)
        else:
            self.txt_history_detail.setPlainText(t("history_no_history"))

    def _on_history_select(self):
        """Handle history item selection"""
        row = self.tbl_history.currentRow()
        if row < 0 or row >= len(self._history_filtered):
            self.txt_history_detail.setPlainText("")
            return
        
        it = self._history_filtered[row]
        if not isinstance(it, dict):
            return

        created = str(it.get("created_at") or "")
        provider = str(it.get("provider") or "")
        text = str(it.get("text") or "")
        err = it.get("error")

        if text.strip():
            body = text
        else:
            body = "Error:\n" + str(err or "")

        header = f"{created}  [{provider}]\n\n"
        self.txt_history_detail.setPlainText(header + body)

    def _copy_history_selected(self):
        """Copy selected history item to clipboard"""
        row = self.tbl_history.currentRow()
        if row < 0 or row >= len(self._history_filtered):
            return
        
        it = self._history_filtered[row]
        if not isinstance(it, dict):
            return
        
        text = str(it.get("text") or "").strip()
        if not text:
            text = str(it.get("error") or "").strip()
        if not text:
            return
        
        try:
            from PyQt6.QtWidgets import QApplication
            QApplication.clipboard().setText(text)
        except Exception:
            pass

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
        
        # Update provider UI after loading - this ensures correct visibility
        self._update_provider_ui()
        
        # Force layout update to prevent collapsed sections
        self.tabs.currentWidget().updateGeometry()

    def on_refresh_input_devices(self):
        self.cmb_input_device.clear()
        self.cmb_input_device.addItem("Default", None)
        try:
            import rust_core
            devices = rust_core.get_input_devices()
            for name, idx in devices:
                self.cmb_input_device.addItem(f"{name} ({idx})", idx)
        except Exception as e:
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
        
        # Reload history after save
        self._reload_history()

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
            self._mic_stream = sd.InputStream(
                device=device,
                channels=1,
                samplerate=SAMPLE_RATE,
                callback=callback
            )
            self._mic_stream.start()
            self.btn_mic_test.setText("⏹️ Stop Mic Test")
            self._mic_timer.start()
        except Exception as e:
            print(f"Mic Test Error: {e}")
            QMessageBox.warning(self, "Mic Test Error", f"Failed to start microphone test:\n{e}")
            self._mic_stream = None

    def _stop_mic_test(self):
        if self._mic_stream:
            self._mic_stream.stop()
            self._mic_stream.close()
            self._mic_stream = None
        self.btn_mic_test.setText("▶️ Start Mic Test")
        self._mic_timer.stop()
        self.mic_bar.setValue(0)

    def _update_mic_bar(self):
        with self._audio_lock:
            level = self._mic_level
        self.mic_bar.setValue(min(100, int(level * 300)))

    def closeEvent(self, event):
        self._stop_mic_test()
        event.accept()
