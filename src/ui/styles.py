"""
UI Style Sheets and Theme Definitions
Provides reusable Qt Style Sheets (QSS) for consistent design across dialogs.
"""

COMMON_DIALOG_STYLESHEET = """
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
"""

DANGER_BUTTON_STYLE = """
    QPushButton {
        background-color: #f44336;
        color: white;
        border: none;
        padding: 8px 16px;
        border-radius: 4px;
        font-weight: bold;
        min-width: 80px;
    }
    QPushButton:hover {
        background-color: #d32f2f;
    }
    QPushButton:pressed {
        background-color: #b71c1c;
    }
"""

SUCCESS_BUTTON_STYLE = """
    QPushButton {
        background-color: #4CAF50;
        color: white;
        border: none;
        padding: 8px 16px;
        border-radius: 4px;
        font-weight: bold;
        min-width: 80px;
    }
    QPushButton:hover {
        background-color: #43A047;
    }
    QPushButton:pressed {
        background-color: #388E3C;
    }
"""
