"""设置页 — API Key / 刷新间隔 / 主题 / 导出"""
from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel,
                                QLineEdit, QPushButton, QComboBox, QFrame)
from PySide6.QtCore import Signal, Qt
from storage import (save_api_key, get_api_key, get_setting, set_setting,
                     export_all_snapshots, get_history_dir)
from crypto import encrypt, decrypt
from theme import THEMES, DEFAULT_THEME

INTERVAL_OPTIONS = [
    ("5 分钟", "300"),
    ("10 分钟", "600"),
    ("15 分钟", "900"),
    ("30 分钟", "1800"),
    ("60 分钟", "3600"),
]


class SettingsPage(QWidget):
    api_key_saved = Signal()
    interval_changed = Signal(int)
    theme_changed = Signal(str)
    data_exported = Signal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._build_ui()
        self._load_values()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(20)

        layout.addWidget(QLabel("🔑 API Key"))
        self.key_input = QLineEdit()
        self.key_input.setEchoMode(QLineEdit.EchoMode.Password)
        self.key_input.setPlaceholderText("输入 DeepSeek API Key (sk-...)")
        layout.addWidget(self.key_input)

        key_row = QHBoxLayout()
        key_row.setSpacing(8)
        self.show_btn = QPushButton("👁 显示")
        self.show_btn.setObjectName("btn-secondary")
        self.show_btn.setCheckable(True)
        self.show_btn.toggled.connect(lambda checked: (
            self.key_input.setEchoMode(QLineEdit.EchoMode.Normal if checked else QLineEdit.EchoMode.Password),
            self.show_btn.setText("🙈 隐藏" if checked else "👁 显示"),
        ))
        key_row.addWidget(self.show_btn)

        save_btn = QPushButton("💾 保存 Key")
        save_btn.setObjectName("btn-primary")
        save_btn.clicked.connect(self._save_key)
        key_row.addWidget(save_btn)
        key_row.addStretch()
        layout.addLayout(key_row)

        layout.addWidget(self._divider())

        layout.addWidget(QLabel("⏱ 自动刷新间隔"))
        self.interval_combo = QComboBox()
        for label, val in INTERVAL_OPTIONS:
            self.interval_combo.addItem(label, val)
        self.interval_combo.currentIndexChanged.connect(self._on_interval_changed)
        layout.addWidget(self.interval_combo)

        layout.addWidget(self._divider())

        theme_header = QHBoxLayout()
        theme_header.addWidget(QLabel("🎨 当前主题"))
        self.theme_label = QLabel("靛蓝流光")
        theme_header.addWidget(self.theme_label)
        theme_header.addStretch()
        layout.addLayout(theme_header)

        layout.addWidget(self._divider())
        layout.addWidget(QLabel("📦 数据管理"))

        export_row = QHBoxLayout()
        export_btn = QPushButton("📋 导出历史数据")
        export_btn.setObjectName("btn-secondary")
        export_btn.clicked.connect(self._export_data)
        export_row.addWidget(export_btn)

        open_hist_btn = QPushButton("📂 打开数据文件夹")
        open_hist_btn.setObjectName("btn-secondary")
        open_hist_btn.clicked.connect(self._open_history_dir)
        export_row.addWidget(open_hist_btn)
        export_row.addStretch()
        layout.addLayout(export_row)

        layout.addWidget(self._divider())
        about = QLabel("DeepSeek Monitor v1.0.0\n基于 PySide6 · 深空玻璃 9 色主题\n数据来源：DeepSeek 官方余额 API")
        about.setStyleSheet("font-size:11px; color: #64748B;")
        about.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(about)
        layout.addStretch()

    def _divider(self):
        d = QFrame()
        d.setFrameShape(QFrame.Shape.HLine)
        d.setStyleSheet("QFrame{background: rgba(255,255,255,0.06); max-height:1px;}")
        return d

    def _load_values(self):
        encrypted = get_api_key()
        if encrypted:
            try:
                plain = decrypt(encrypted)
                self.key_input.setText(plain)
            except Exception:
                self.key_input.setText("")
                self.key_input.setPlaceholderText("解密 Key 失败，请重新输入")
        val = get_setting("refresh_interval", "600")
        for i in range(self.interval_combo.count()):
            if self.interval_combo.itemData(i) == val:
                self.interval_combo.setCurrentIndex(i)
                break

    def _save_key(self):
        plain = self.key_input.text().strip()
        if plain:
            enc = encrypt(plain)
            save_api_key(enc)
            self.api_key_saved.emit()
        else:
            save_api_key("")
            self.api_key_saved.emit()

    def _on_interval_changed(self, idx):
        val = self.interval_combo.itemData(idx)
        set_setting("refresh_interval", val)
        self.interval_changed.emit(int(val))

    def _export_data(self):
        filepath = export_all_snapshots()
        self.data_exported.emit(filepath)

    def _open_history_dir(self):
        import os
        d = get_history_dir()
        os.startfile(d)

    def update_theme_name(self, theme_name: str):
        self.theme_label.setText(THEMES.get(theme_name, {}).name or theme_name)
