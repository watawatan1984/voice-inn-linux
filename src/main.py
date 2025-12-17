import sys
import os
import signal
import logging
import traceback
from PyQt6.QtWidgets import QApplication, QSystemTrayIcon, QMenu
from PyQt6.QtGui import QIcon, QAction
from PyQt6.QtCore import QTimer

from src.core.config import config_manager, get_state_dir
from src.core.i18n import t
from src.ui.overlay import AquaOverlay
from src.ui.widgets import make_tray_icon_for_state
from src.ui.setup import SetupWizardDialog

def setup_logging():
    log_dir = get_state_dir()
    os.makedirs(log_dir, exist_ok=True)
    log_file = os.path.join(log_dir, "app.log")
    
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(message)s",
        handlers=[
            logging.StreamHandler(sys.stdout),
            logging.FileHandler(log_file, encoding='utf-8')
        ]
    )
    
    def handle_exception(exc_type, exc_value, exc_traceback):
        if issubclass(exc_type, KeyboardInterrupt):
            sys.__excepthook__(exc_type, exc_value, exc_traceback)
            return
        logging.error("Uncaught exception", exc_info=(exc_type, exc_value, exc_traceback))

    sys.excepthook = handle_exception

def check_first_run(overlay):
    # If no providers configured, simple heuristic or check specific flag
    # But checking if API keys are missing is good enough
    has_gemini = bool(os.getenv("GEMINI_API_KEY"))
    has_groq = bool(os.getenv("GROQ_API_KEY"))
    if not has_gemini and not has_groq:
        overlay.open_setup_wizard()

def main():
    setup_logging()
    app = QApplication(sys.argv)
    app.setQuitOnLastWindowClosed(False)

    overlay = AquaOverlay()
    overlay.show()

    # System Tray
    tray = QSystemTrayIcon(app)
    tray.setIcon(make_tray_icon_for_state("idle"))
    
    menu = QMenu()
    
    # helper to update menu
    def update_menu():
        menu.clear()
        
        provider = os.getenv("AI_PROVIDER", "gemini")
        status_label = menu.addAction(t("tray_current", provider=provider))
        status_label.setEnabled(False)
        menu.addSeparator()
        
        a_gemini = menu.addAction(t("tray_switch_gemini"))
        a_gemini.triggered.connect(lambda: set_provider("gemini"))
        
        a_groq = menu.addAction(t("tray_switch_groq"))
        a_groq.triggered.connect(lambda: set_provider("groq"))
        
        a_local = menu.addAction(t("tray_switch_local"))
        a_local.triggered.connect(lambda: set_provider("local"))
        
        menu.addSeparator()
        menu.addAction(t("tray_setup"), overlay.open_setup_wizard)
        menu.addAction(t("tray_settings"), overlay.open_settings)
        menu.addAction(t("tray_history"), overlay.show_history)
        menu.addSeparator()
        menu.addAction(t("tray_show_hide"), lambda: overlay.setVisible(not overlay.isVisible()))
        menu.addAction(t("tray_quit"), app.quit)

    def set_provider(name):
        config_manager.update_env("AI_PROVIDER", name)
        overlay.update_style()
        update_menu()
        tray.showMessage("Voice In", f"Switched to {name}")

    update_menu()
    tray.setContextMenu(menu)
    tray.show()
    
    overlay.set_tray(tray)

    signal.signal(signal.SIGINT, signal.SIG_DFL)
    
    QTimer.singleShot(1000, lambda: check_first_run(overlay))

    sys.exit(app.exec())

if __name__ == "__main__":
    main()
