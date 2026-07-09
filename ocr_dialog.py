"""
ocr_dialog.py - Dialog hien thi ket qua OCR voi nut Copy.
"""
from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QTextEdit, QPushButton, QLabel,
    QApplication,
)
from PyQt5.QtCore import Qt


DIALOG_QSS = """
QDialog {
    background: #262a33;
}
QLabel {
    color: #9aa0ac;
    font-size: 12px;
}
QTextEdit {
    background: #1c1f26;
    color: #e8eaf0;
    border: 1px solid #3a3f4b;
    border-radius: 8px;
    padding: 10px;
    font-family: monospace;
    font-size: 13px;
}
QPushButton {
    background: #33394a;
    color: #e8eaf0;
    border: 1px solid #3a3f4b;
    border-radius: 8px;
    padding: 8px 18px;
    font-size: 13px;
}
QPushButton:hover {
    background: #3d6bff;
    border-color: #3d6bff;
}
QPushButton:pressed {
    background: #2f56cc;
}
"""


class OcrResultDialog(QDialog):
    def __init__(self, text, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Extract Text")
        self.setMinimumSize(480, 320)
        self.setStyleSheet(DIALOG_QSS)

        layout = QVBoxLayout(self)
        layout.setSpacing(12)
        layout.setContentsMargins(16, 16, 16, 16)

        hint = QLabel("Ket qua OCR — chon va sua truoc khi copy neu can:")
        layout.addWidget(hint)

        self.text_edit = QTextEdit()
        self.text_edit.setPlainText(text)
        self.text_edit.setReadOnly(False)
        layout.addWidget(self.text_edit, stretch=1)

        btn_row = QHBoxLayout()
        btn_row.addStretch()

        copy_btn = QPushButton("Copy")
        copy_btn.setDefault(True)
        copy_btn.clicked.connect(self._copy)
        btn_row.addWidget(copy_btn)

        close_btn = QPushButton("Dong")
        close_btn.clicked.connect(self.accept)
        btn_row.addWidget(close_btn)

        layout.addLayout(btn_row)

    def _copy(self):
        QApplication.clipboard().setText(self.text_edit.toPlainText())
