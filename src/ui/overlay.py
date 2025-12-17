import sys
import os
import shutil
import subprocess
import threading
import traceback
import logging
from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QLabel, QApplication, QSystemTrayIcon, QMenu
)
from PyQt6.QtCore import Qt, pyqtSignal, QTimer, QThread, QObject
from PyQt6.QtGui import QAction
from pynput import keyboard

from src.core.config import config_manager
from src.core.i18n import t
from src.core.history import append_history_item
from src.audio.recorder import AudioRecorder
from src.audio.vad import SimpleVAD
from src.ai.worker import AIWorker
from src.ui.widgets import make_tray_icon_for_state
from src.ui.settings import SettingsDialog
from src.ui.history import HistoryDialog
from src.ui.setup import SetupWizardDialog

class AquaOverlay(QMainWindow):
    start_recording_signal = pyqtSignal()
    stop_recording_signal = pyqtSignal()

    def __init__(self):
        super().__init__()
        self.recorder = AudioRecorder()
        self.vad = SimpleVAD()
        
        self._tray = None
        self._last_text = ""
        self._last_error = ""
        self._paste_target_window = None
        self._history_dialog = None
        self._settings_dialog = None
        self._setup_dialog = None
        
        self._ai_thread = None
        self._ai_worker = None
        self._is_processing = False
        self._status = "idle"
        
        self.initUI()
        self.initKeyboard()
        self.keyboard_controller = keyboard.Controller()
        
        self.start_recording_signal.connect(self.start_recording)
        self.stop_recording_signal.connect(self.stop_recording)
        
        # Poll for auto-stop form recorder if needed, but recorder has callback slot now.
        # But callback is in audio thread. We need to handle it. 
        # Actually I didn't connect recorder callback to signal in previous recorder code.
        # I added `on_auto_stop`.
        
    def initUI(self):
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.WindowStaysOnTopHint | Qt.WindowType.ToolTip | Qt.WindowType.WindowDoesNotAcceptFocus)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        
        screen = QApplication.primaryScreen().availableGeometry()
        size = 60
        self.setGeometry(screen.width() - size - 20, screen.height() - size - 50, size, size)
        
        pos = config_manager.settings.get("ui", {}).get("overlay_pos")
        if pos and len(pos) == 2:
            self.move(pos[0], pos[1])
            
        self.widget = QWidget()
        self.update_style()
        
        layout = QVBoxLayout()
        self.label = QLabel("🎤")
        self.label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.label)
        layout.setContentsMargins(0,0,0,0)
        self.widget.setLayout(layout)
        self.setCentralWidget(self.widget)
        self.setWindowOpacity(0.8)
        self.setToolTip(t("tooltip_hold_key"))

        # Dragging logic... (omitted for brevity, can implement if needed or copy from original)
        self._dragging = False
        self._drag_offset = None
    
    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self._dragging = True
            self._drag_offset = event.globalPosition().toPoint() - self.frameGeometry().topLeft()
            event.accept()

    def mouseMoveEvent(self, event):
        if self._dragging and self._drag_offset:
            self.move(event.globalPosition().toPoint() - self._drag_offset)
            event.accept()

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self._dragging = False
            # Save pos
            pos = [self.x(), self.y()]
            config_manager.update_settings({"ui": {"overlay_pos": pos}})
            event.accept()

    def contextMenuEvent(self, event):
        menu = QMenu(self)
        menu.addAction(t("ctx_setup"), self.open_setup_wizard)
        menu.addAction(t("ctx_settings"), self.open_settings)
        menu.addAction(t("ctx_history"), self.show_history)
        menu.addSeparator()
        menu.addAction(t("ctx_quit"), QApplication.quit)
        menu.exec(event.globalPos())

    def update_style(self):
        provider = os.getenv("AI_PROVIDER", "gemini")
        color = "#4285F4" if provider == "gemini" else "#f55036" if provider == "groq" else "#888888" # Local gray?
        
        self.widget.setStyleSheet(f"""
            QWidget {{
                background-color: rgba(50, 50, 50, 200);
                border-radius: 30px;
                border: 2px solid {color};
            }}
            QLabel {{
                color: white;
                font-weight: bold;
                font-size: 24px;
            }}
        """)
        
        # Apply audio settings to VAD/Recorder if needed
        min_dur = float(config_manager.settings.get("audio", {}).get("min_duration", 0.2))
        if hasattr(self, 'vad'):
            self.vad.min_duration = min_dur
        
    def set_tray(self, tray):
        self._tray = tray
        self._set_status("idle")

    def _set_status(self, status):
        self._status = status
        if self._tray:
            self._tray.setIcon(make_tray_icon_for_state(status))

    def initKeyboard(self):
        self.listener = keyboard.Listener(on_press=self.on_key_press, on_release=self.on_key_release)
        self.listener.start()

    def on_key_press(self, key):
        # check hold key
        target = config_manager.settings.get("audio", {}).get("hold_key", "alt_l")
        k_map = {"alt_l": keyboard.Key.alt_l, "alt_r": keyboard.Key.alt_r, "ctrl_l": keyboard.Key.ctrl_l, "ctrl_r": keyboard.Key.ctrl_r}
        if key == k_map.get(target, keyboard.Key.alt_l):
            # Get active window for pasting
            if not self._paste_target_window:
                 try:
                     if shutil.which("xdotool"):
                         r = subprocess.run(["xdotool", "getactivewindow"], stdout=subprocess.PIPE, text=True)
                         if r.returncode == 0: self._paste_target_window = r.stdout.strip()
                 except: pass
            self.start_recording_signal.emit()

    def on_key_release(self, key):
        target = config_manager.settings.get("audio", {}).get("hold_key", "alt_l")
        k_map = {"alt_l": keyboard.Key.alt_l, "alt_r": keyboard.Key.alt_r, "ctrl_l": keyboard.Key.ctrl_l, "ctrl_r": keyboard.Key.ctrl_r}
        if key == k_map.get(target, keyboard.Key.alt_l):
            self.stop_recording_signal.emit()

    def start_recording(self):
        if self.recorder.is_recording or self._is_processing: return
        self._set_status("recording")
        self.label.setText("🎙️")
        self.widget.setStyleSheet("""
            QWidget { background-color: rgba(220, 20, 60, 230); border-radius: 30px; border: 2px solid #ff9999; }
        """)
        max_sec = config_manager.settings.get("audio", {}).get("max_record_seconds", 60)
        
        def on_auto_stop():
            # Signal emitter from background thread
            self.stop_recording_signal.emit()
            
        try:
            self.recorder.start(max_seconds=max_sec, on_auto_stop=on_auto_stop)
        except Exception as e:
            self._set_status("error")
            self.label.setText("❌")
            print(f"Rec Error: {e}")
            if self._tray:
                self._tray.showMessage(t("app_name"), f"Recording Failed: {e}", QSystemTrayIcon.MessageIcon.Critical, 2000)
            self.reset_ui_delayed()

    def stop_recording(self):
        if not self.recorder.is_recording: return
        wav_path = self.recorder.stop()
        
        stats = self.recorder.get_stats()
        if self.vad.is_silence(stats):
             try: os.remove(wav_path)
             except: pass
             self.reset_ui()
             return

        self._set_status("processing")
        self.label.setText("⏳")
        self.widget.setStyleSheet("""
             QWidget { background-color: rgba(255, 193, 7, 230); border-radius: 30px; border: 2px solid #ffeabe; }
        """)
        self._is_processing = True
        
        provider = os.getenv("AI_PROVIDER", "gemini")
        prompts = config_manager.settings.get("prompts", {})
        
        self._ai_thread = QThread()
        self._ai_worker = AIWorker(provider, wav_path, prompts)
        self._ai_worker.moveToThread(self._ai_thread)
        self._ai_thread.started.connect(self._ai_worker.run)
        self._ai_worker.finished.connect(self.on_ai_finished)
        self._ai_worker.error.connect(self.on_ai_error)
        self._ai_worker.finished.connect(self._ai_thread.quit)
        self._ai_worker.error.connect(self._ai_thread.quit)
        self._ai_worker.finished.connect(lambda: threading.Thread(target=lambda: self.cleanup_wav(wav_path)).start())
        self._ai_thread.start()

    def cleanup_wav(self, path):
        if path and os.path.exists(path):
            try: os.remove(path)
            except: pass

    def on_ai_finished(self, text):
        dic = config_manager.settings.get("dictionary", {})
        for k, v in dic.items():
            text = text.replace(k, v)
        self._last_text = text
        append_history_item(text=text, provider=os.getenv("AI_PROVIDER"))
        
        if text:
             QApplication.clipboard().setText(text)
             if config_manager.settings.get("audio", {}).get("auto_paste", True):
                 self.do_paste()
        
        self.label.setText("✅")
        self._set_status("success")
        self.reset_ui_delayed()

    def do_paste(self):
        # Simplified paste logic
        delay = config_manager.settings.get("audio", {}).get("paste_delay_ms", 200)
        def _job():
            try:
                # Release modifiers
                for k in [keyboard.Key.alt_l, keyboard.Key.ctrl_l]:
                    try: self.keyboard_controller.release(k)
                    except: pass
                
                print(f"DEBUG: do_paste - TargetWindow: {self._paste_target_window}, Xdotool: {shutil.which('xdotool')}")
                cb_text = QApplication.clipboard().text()
                print(f"DEBUG: Clipboard content before paste: '{cb_text}'")
                
                if shutil.which("xdotool") and self._paste_target_window:
                     # Check if we really need to activate (avoid redundant focus events that might reset cursor)
                     active_now = subprocess.run(["xdotool", "getactivewindow"], capture_output=True, text=True).stdout.strip()
                     if active_now != self._paste_target_window:
                         print(f"DEBUG: Activating window (Current: {active_now} != Target: {self._paste_target_window})")
                         r1 = subprocess.run(["xdotool", "windowactivate", "--sync", self._paste_target_window], capture_output=True, text=True)
                         print(f"DEBUG: activate ret={r1.returncode}, err={r1.stderr}")
                     else:
                         print("DEBUG: Window already active, skipping activate")
                         
                     # Force a small sleep to ensure modifiers are clear and focus is stable
                     # time.sleep(0.1) -> handled by QTimer delay usually, but maybe helpful?
                     
                     r2 = subprocess.run(["xdotool", "key", "--clearmodifiers", "ctrl+v"], capture_output=True, text=True)
                     print(f"DEBUG: key ret={r2.returncode}, err={r2.stderr}")
                else:
                     print("DEBUG: Fallback to pynput paste")
                     with self.keyboard_controller.pressed(keyboard.Key.ctrl):
                         self.keyboard_controller.press('v')
                         self.keyboard_controller.release('v')
            except Exception as e:
                print(f"Paste failed: {e}")
                
        QTimer.singleShot(delay, _job)

    def on_ai_error(self, err):
        self.label.setText("❌")
        self._set_status("error")
        print(f"AI Error: {err}")
        self.reset_ui_delayed()

    def reset_ui(self):
        self._is_processing = False
        self.update_style()
        self.label.setText("🎤")
        self._set_status("idle")
        self.setWindowOpacity(0.8)

    def reset_ui_delayed(self):
        QTimer.singleShot(1000, self.reset_ui)

    def open_settings(self):
        if not self._settings_dialog:
             self._settings_dialog = SettingsDialog(self)
             self._settings_dialog.settings_applied.connect(lambda s: self.update_style()) # Refresh style on save
        self._settings_dialog.show()

    def show_history(self):
        if not self._history_dialog:
             self._history_dialog = HistoryDialog(self)
        self._history_dialog.reload()
        self._history_dialog.show()

    def open_setup_wizard(self):
        if not self._setup_dialog:
             self._setup_dialog = SetupWizardDialog(self)
        self._setup_dialog.show()
    
    def closeEvent(self, event):
        self.listener.stop()
        event.accept()
