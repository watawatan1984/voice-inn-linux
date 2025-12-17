from PyQt6.QtWidgets import (
    QDialog, QLabel, QVBoxLayout, QHBoxLayout, 
    QTableWidget, QTableWidgetItem, QPlainTextEdit, 
    QLineEdit, QPushButton, QApplication, QWidget
)
from PyQt6.QtCore import Qt

from src.core.i18n import t
from src.core.history import load_history_file, HISTORY_MAX_ITEMS

class HistoryDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle(t("history_title"))
        self.setMinimumSize(860, 520)

        self._items = []
        self._filtered = []

        self.txt_search = QLineEdit()
        self.txt_search.setPlaceholderText(t("history_search_ph"))
        self.txt_search.textChanged.connect(self._apply_filter)

        self.tbl = QTableWidget(0, 4)
        self.tbl.setHorizontalHeaderLabels([
            t("history_col_time"),
            t("history_col_provider"),
            t("history_col_type"),
            t("history_col_preview"),
        ])
        self.tbl.horizontalHeader().setStretchLastSection(True)
        self.tbl.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.tbl.setSelectionMode(QTableWidget.SelectionMode.SingleSelection)
        self.tbl.itemSelectionChanged.connect(self._on_select)

        self.txt_detail = QPlainTextEdit()
        self.txt_detail.setReadOnly(True)

        self.btn_copy = QPushButton(t("history_copy"))
        self.btn_close = QPushButton(t("history_close"))
        self.btn_copy.clicked.connect(self._copy_selected)
        self.btn_close.clicked.connect(self.close)

        top = QHBoxLayout()
        top.addWidget(QLabel(t("history_search")))
        top.addWidget(self.txt_search, 1)

        buttons = QHBoxLayout()
        buttons.addStretch(1)
        buttons.addWidget(self.btn_copy)
        buttons.addWidget(self.btn_close)

        root = QVBoxLayout()
        root.addLayout(top)
        root.addWidget(self.tbl, 2)
        root.addWidget(self.txt_detail, 3)
        root.addLayout(buttons)
        self.setLayout(root)

        self.reload()

    def reload(self):
        try:
            self._items = load_history_file()
            if not isinstance(self._items, list):
                self._items = []
        except Exception:
            self._items = []
        self._apply_filter()

    def _apply_filter(self):
        q = (self.txt_search.text() or "").strip().lower()
        if not q:
            self._filtered = list(self._items)
        else:
            filtered = []
            for it in self._items:
                if not isinstance(it, dict):
                    continue
                text = str(it.get("text") or "")
                err = str(it.get("error") or "")
                prov = str(it.get("provider") or "")
                created = str(it.get("created_at") or "")
                hay = (created + "\n" + prov + "\n" + text + "\n" + err).lower()
                if q in hay:
                    filtered.append(it)
            self._filtered = filtered
        self._render_table()

    def _render_table(self):
        self.tbl.setRowCount(0)
        for it in self._filtered[:HISTORY_MAX_ITEMS]:
            created = str(it.get("created_at") or "")
            provider = str(it.get("provider") or "")
            text = str(it.get("text") or "")
            err = it.get("error")
            kind = "Text" if text.strip() else "Error"
            preview_src = text if text.strip() else str(err or "")
            preview = preview_src.strip().replace("\n", " ")
            if len(preview) > 80:
                preview = preview[:77] + "..."

            row = self.tbl.rowCount()
            self.tbl.insertRow(row)
            self.tbl.setItem(row, 0, QTableWidgetItem(created))
            self.tbl.setItem(row, 1, QTableWidgetItem(provider))
            self.tbl.setItem(row, 2, QTableWidgetItem(kind))
            self.tbl.setItem(row, 3, QTableWidgetItem(preview))

        if self.tbl.rowCount() > 0:
            self.tbl.selectRow(0)
        else:
            self.txt_detail.setPlainText(t("history_no_history"))

    def _selected_item(self):
        row = self.tbl.currentRow()
        if row < 0:
            return None
        if row >= len(self._filtered):
            return None
        it = self._filtered[row]
        return it if isinstance(it, dict) else None

    def _on_select(self):
        it = self._selected_item()
        if not it:
            self.txt_detail.setPlainText("")
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
        self.txt_detail.setPlainText(header + body)

    def _copy_selected(self):
        it = self._selected_item()
        if not it:
            return
        text = str(it.get("text") or "").strip()
        if not text:
            text = str(it.get("error") or "").strip()
        if not text:
            return
        try:
            QApplication.clipboard().setText(text)
        except Exception:
            pass
