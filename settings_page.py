"""设置页 — API Key / 刷新间隔 / 主题 / 导出"""
from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel,
                                QLineEdit, QPushButton, QComboBox, QFrame,
                                QDialog, QFormLayout, QDialogButtonBox, QMessageBox)
from PySide6.QtCore import Signal, Qt
from storage import (save_api_key, get_api_key, delete_api_key, get_setting,
                     set_setting, export_all_snapshots, get_history_dir,
                     get_presets, add_preset, update_preset, delete_preset,
                     set_active_preset, get_active_preset_key)
from theme import generate_qss


INTERVAL_OPTIONS = [
    ("5 分钟", "300"),
    ("10 分钟", "600"),
    ("15 分钟", "900"),
    ("30 分钟", "1800"),
    ("60 分钟", "3600"),
]


class PresetDialog(QDialog):
    """新增/编辑预设的对话框"""

    def __init__(self, parent=None, preset: dict = None):
        super().__init__(parent)
        self.setWindowTitle("编辑预设" if preset else "新增预设")
        self.setMinimumWidth(400)
        self.setStyleSheet(generate_qss())
        self._preset = preset

        layout = QFormLayout(self)
        self.name_input = QLineEdit()
        self.name_input.setPlaceholderText("预设名称，如「主用 Key」「R1 测试」")
        if preset:
            self.name_input.setText(preset["name"])
        layout.addRow("名称：", self.name_input)

        self.key_input = QLineEdit()
        self.key_input.setPlaceholderText("DeepSeek API Key (sk-...)")
        if preset:
            self.key_input.setPlaceholderText("留空则不修改")
        layout.addRow("API Key：", self.key_input)

        self.buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        self.buttons.accepted.connect(self._validate)
        self.buttons.rejected.connect(self.reject)
        layout.addRow(self.buttons)

    def _validate(self):
        name = self.name_input.text().strip()
        if not name:
            QMessageBox.warning(self, "提示", "预设名称不能为空")
            return
        if not self._preset:
            key = self.key_input.text().strip()
            if not key:
                QMessageBox.warning(self, "提示", "API Key 不能为空")
                return
        self.accept()

    def get_name(self) -> str:
        return self.name_input.text().strip()

    def get_key(self) -> str:
        return self.key_input.text().strip()


class SettingsPage(QWidget):
    api_key_saved = Signal()
    interval_changed = Signal(int)
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

        del_btn = QPushButton("🗑 删除 Key")
        del_btn.setObjectName("btn-secondary")
        del_btn.clicked.connect(self._delete_key)
        key_row.addWidget(del_btn)

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
        self._build_preset_section(layout)

        layout.addWidget(self._divider())
        about = QLabel("DeepSeek Monitor v1.0.0\n基于 PySide6 · 深空玻璃 9 色主题\n数据来源：DeepSeek 官方余额 API")
        about.setObjectName("about-text")
        about.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(about)
        layout.addStretch()

    def _build_preset_section(self, layout):
        layout.addWidget(QLabel("📋 API Key 预设管理"))

        hint = QLabel("💡 激活预设后，程序优先使用预设中的 Key，单 Key 模式作为兼容后备")
        hint.setObjectName("preset-hint")
        hint.setWordWrap(True)
        layout.addWidget(hint)

        select_row = QHBoxLayout()
        self.preset_combo = QComboBox()
        self.preset_combo.setMinimumWidth(200)
        select_row.addWidget(self.preset_combo)

        self.apply_preset_btn = QPushButton("✅ 应用此预设")
        self.apply_preset_btn.setObjectName("btn-primary")
        self.apply_preset_btn.clicked.connect(self._apply_preset)
        select_row.addWidget(self.apply_preset_btn)
        select_row.addStretch()
        layout.addLayout(select_row)

        btn_row = QHBoxLayout()
        add_btn = QPushButton("➕ 新建")
        add_btn.setObjectName("btn-secondary")
        add_btn.clicked.connect(self._add_preset_dialog)
        btn_row.addWidget(add_btn)

        edit_btn = QPushButton("✏️ 编辑")
        edit_btn.setObjectName("btn-secondary")
        edit_btn.clicked.connect(self._edit_preset_dialog)
        btn_row.addWidget(edit_btn)

        del_btn = QPushButton("🗑 删除")
        del_btn.setObjectName("btn-secondary")
        del_btn.clicked.connect(self._delete_preset_confirm)
        btn_row.addWidget(del_btn)

        sa_btn = QPushButton("💾 存为预设")
        sa_btn.setObjectName("btn-secondary")
        sa_btn.clicked.connect(self._save_current_as_preset)
        btn_row.addWidget(sa_btn)

        btn_row.addStretch()
        layout.addLayout(btn_row)

    def _load_presets(self):
        """刷新下拉列表"""
        self.preset_combo.clear()
        self.preset_combo.addItem("— 无（使用单 Key 模式）", "")
        for p in get_presets():
            self.preset_combo.addItem(p["name"], p["id"])
        active_id = get_setting("active_preset_id", "")
        if active_id:
            idx = self.preset_combo.findData(int(active_id))
            if idx >= 0:
                self.preset_combo.setCurrentIndex(idx)

    def _apply_preset(self):
        preset_id = self.preset_combo.currentData()
        if preset_id:
            set_active_preset(int(preset_id))
            self.api_key_saved.emit()
            QMessageBox.information(self, "切换成功",
                                    f"已切换到预设「{self.preset_combo.currentText()}」")
        else:
            set_active_preset(None)
            self.api_key_saved.emit()

    def _add_preset_dialog(self):
        dialog = PresetDialog(self)
        if dialog.exec():
            name = dialog.get_name()
            key = dialog.get_key()
            try:
                add_preset(name, key)
                self._load_presets()
            except ValueError as e:
                QMessageBox.warning(self, "添加失败", str(e))

    def _edit_preset_dialog(self):
        preset_id = self.preset_combo.currentData()
        if not preset_id:
            QMessageBox.information(self, "提示", "请先选择一个预设")
            return
        presets = get_presets()
        preset = next((p for p in presets if p["id"] == preset_id), None)
        if not preset:
            return
        dialog = PresetDialog(self, preset=preset)
        if dialog.exec():
            name = dialog.get_name()
            key = dialog.get_key()
            try:
                update_preset(preset_id, name=name, key=key if key else None)
                self._load_presets()
            except ValueError as e:
                QMessageBox.warning(self, "修改失败", str(e))

    def _delete_preset_confirm(self):
        preset_id = self.preset_combo.currentData()
        if not preset_id:
            QMessageBox.information(self, "提示", "请先选择一个预设")
            return
        name = self.preset_combo.currentText()
        reply = QMessageBox.question(
            self, "确认删除", f"确定删除预设「{name}」吗？",
            QMessageBox.Yes | QMessageBox.No
        )
        if reply == QMessageBox.Yes:
            delete_preset(preset_id)
            self._load_presets()
            self.api_key_saved.emit()

    def _save_current_as_preset(self):
        """将当前输入框的 Key 一键存为预设"""
        key = self.key_input.text().strip()
        if not key:
            QMessageBox.information(self, "提示", "请先在 API Key 输入框中输入 Key")
            return
        dialog = PresetDialog(self)
        dialog.key_input.setText(key)
        if dialog.exec():
            name = dialog.get_name()
            try:
                add_preset(name, key)
                self._load_presets()
            except ValueError as e:
                QMessageBox.warning(self, "添加失败", str(e))

    def _divider(self):
        d = QFrame()
        d.setFrameShape(QFrame.Shape.HLine)
        d.setObjectName("settings-divider")
        return d

    def _load_values(self):
        key = get_api_key()
        if key:
            self.key_input.setText(key)
        val = get_setting("refresh_interval", "600")
        for i in range(self.interval_combo.count()):
            if self.interval_combo.itemData(i) == val:
                self.interval_combo.setCurrentIndex(i)
                break
        self._load_presets()

    def _save_key(self):
        plain = self.key_input.text().strip()
        save_api_key(plain)
        self.api_key_saved.emit()

    def _delete_key(self):
        self.key_input.clear()
        delete_api_key()
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

