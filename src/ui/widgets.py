from PyQt6.QtGui import QIcon, QPixmap, QPainter, QFont, QColor
from PyQt6.QtCore import Qt

def make_tray_icon_for_state(state: str):
    s = (state or "idle").strip().lower()
    fill = QColor("#2ecc71")
    if s == "recording":
        fill = QColor("#dc143c")
    elif s == "processing":
        fill = QColor("#ffc107")
    elif s == "error":
        fill = QColor("#b00020")
    elif s == "success":
        fill = QColor("#2ecc71")
    elif s == "idle_blue":
        fill = QColor("#4285F4")

    pixmap = QPixmap(64, 64)
    pixmap.fill(Qt.GlobalColor.transparent)
    painter = QPainter(pixmap)
    painter.setRenderHint(QPainter.RenderHint.Antialiasing)
    painter.setPen(Qt.GlobalColor.transparent)
    painter.setBrush(fill)
    painter.drawEllipse(4, 4, 56, 56)
    painter.setPen(Qt.GlobalColor.white)
    font = QFont()
    font.setPointSize(28)
    font.setBold(True)
    painter.setFont(font)
    painter.drawText(pixmap.rect(), Qt.AlignmentFlag.AlignCenter, "🎤")
    painter.end()
    return QIcon(pixmap)
