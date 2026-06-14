"""完整窗口 — 概览 / 历史 / 设置 三个 Tab"""
from PySide6.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
                                QLabel, QTabWidget, QPushButton, QTableWidget,
                                QTableWidgetItem, QHeaderView, QFrame, QMessageBox)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QIcon
from theme import generate_qss, THEMES, DEFAULT_THEME
from storage import get_recent_snapshots, get_latest_snapshot, get_setting, get_history_dir
from settings_page import SettingsPage
from popup import ThemeSwatch, SWATCH_COLORS
import os


class OverviewTab(QWidget):
    refresh_clicked = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self._build_ui()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 16, 24, 24)
        layout.setSpacing(12)

        header = QHBoxLayout()
        header.addWidget(QLabel("💰 账户余额"))
        header.addStretch()
        refresh_btn = QPushButton("🔄 手动刷新")
        refresh_btn.setObjectName("btn-secondary")
        refresh_btn.clicked.connect(self.refresh_clicked.emit)
        header.addWidget(refresh_btn)
        layout.addLayout(header)

        self.balance_amount = QLabel("--.--")
        self.balance_amount.setObjectName("balance-large")
        self.balance_amount.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.balance_amount)

        status_row = QHBoxLayout()
        status_row.addStretch()
        self.status_dot = QLabel()
        self.status_dot.setFixedSize(8, 8)
        self.status_dot.setObjectName("dot-gray")
        status_row.addWidget(self.status_dot)
        self.status_label = QLabel("未配置 Key")
        self.status_label.setStyleSheet("font-size:12px;")
        status_row.addWidget(self.status_label)
        status_row.addStretch()
        layout.addLayout(status_row)

        cards = QHBoxLayout()
        cards.setSpacing(12)
        card_topup = QFrame()
        card_topup.setObjectName("glass-card")
        ctl = QVBoxLayout(card_topup)
        ctl.setContentsMargins(16, 14, 16, 14)
        ctl.setSpacing(4)
        ctl.addWidget(QLabel("💰 充值余额"))
        self.topup_amount = QLabel("--.--")
        self.topup_amount.setStyleSheet("font-size:22px; font-weight:700;")
        ctl.addWidget(self.topup_amount)
        cards.addWidget(card_topup)

        card_grant = QFrame()
        card_grant.setObjectName("glass-card")
        cgl = QVBoxLayout(card_grant)
        cgl.setContentsMargins(16, 14, 16, 14)
        cgl.setSpacing(4)
        cgl.addWidget(QLabel("🎁 赠送余额"))
        self.granted_amount = QLabel("--.--")
        self.granted_amount.setStyleSheet("font-size:22px; font-weight:700;")
        cgl.addWidget(self.granted_amount)
        cards.addWidget(card_grant)
        layout.addLayout(cards)

        info_row = QHBoxLayout()
        info_row.addWidget(QLabel("📊 总余额"))
        self.total_label = QLabel("--.--")
        self.total_label.setStyleSheet("font-size:18px; font-weight:700;")
        info_row.addWidget(self.total_label)
        info_row.addStretch()
        self.currency_label = QLabel("")
        self.currency_label.setStyleSheet("font-size:12px;")
        info_row.addWidget(self.currency_label)
        layout.addLayout(info_row)

        extra = QHBoxLayout()
        self.response_time_label = QLabel("响应时间: -- ms")
        self.response_time_label.setObjectName("text-muted")
        extra.addWidget(self.response_time_label)
        extra.addStretch()
        self.fetched_label = QLabel("")
        self.fetched_label.setObjectName("text-muted")
        extra.addWidget(self.fetched_label)
        layout.addLayout(extra)
        layout.addStretch()

    def update_data(self, balance_data: dict | None, status: str = "ok",
                    response_time: float = 0.0):
        if status == "no_key":
            self.status_dot.setObjectName("dot-gray")
            self.status_label.setText("未配置 Key")
            self.balance_amount.setText("--.--")
            self.topup_amount.setText("--.--")
            self.granted_amount.setText("--.--")
            self.total_label.setText("--.--")
        elif status == "error":
            self.status_dot.setObjectName("dot-red")
            self.status_label.setText("连接失败")
        elif balance_data:
            total = balance_data.get("total_balance", 0)
            granted = balance_data.get("granted_balance", 0)
            topped_up = balance_data.get("topped_up_balance", 0)
            is_avail = balance_data.get("is_available", False)
            currency = balance_data.get("currency", "CNY")
            fetched = balance_data.get("fetched_at", "")

            self.status_dot.setObjectName("dot-green" if is_avail else "dot-yellow")
            self.status_label.setText("可用" if is_avail else "余额不足")
            self.balance_amount.setText(f"¥ {total:,.2f}")
            self.topup_amount.setText(f"¥ {topped_up:,.2f}")
            self.granted_amount.setText(f"¥ {granted:,.2f}")
            self.total_label.setText(f"¥ {total:,.2f}")
            self.currency_label.setText(f"货币: {currency}")
            self.fetched_label.setText(f"刷新时间: {fetched}")

        self.response_time_label.setText(f"响应时间: {response_time:.0f} ms")
        self.style().unpolish(self)
        self.style().polish(self)


class HistoryTab(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._build_ui()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 16, 24, 24)
        layout.setSpacing(12)
        layout.addWidget(QLabel("📅 余额变化记录（最近 30 天）"))

        self.table = QTableWidget()
        self.table.setColumnCount(5)
        self.table.setHorizontalHeaderLabels(["时间", "总余额", "充值", "赠金", "状态"])
        self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(4, QHeaderView.ResizeMode.ResizeToContents)
        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table.verticalHeader().setVisible(False)
        layout.addWidget(self.table)

        footer = QHBoxLayout()
        hint = QLabel("30 天前数据已自动归档至 history/ 文件夹")
        hint.setObjectName("text-muted")
        footer.addWidget(hint)
        footer.addStretch()
        open_btn = QPushButton("📂 打开文件夹")
        open_btn.setObjectName("btn-secondary")
        open_btn.clicked.connect(lambda: os.startfile(get_history_dir()))
        footer.addWidget(open_btn)
        layout.addLayout(footer)

    def load_data(self):
        snaps = get_recent_snapshots(30)
        self.table.setRowCount(len(snaps))
        for i, s in enumerate(snaps):
            self.table.setItem(i, 0, QTableWidgetItem(s["fetched_at"]))
            self.table.setItem(i, 1, QTableWidgetItem(f"¥ {s['total_balance']:,.2f}"))
            self.table.setItem(i, 2, QTableWidgetItem(f"¥ {s['topped_up_balance']:,.2f}"))
            self.table.setItem(i, 3, QTableWidgetItem(f"¥ {s['granted_balance']:,.2f}"))
            status_text = "✓ 可用" if s["is_available"] else "⚠ 不足"
            self.table.setItem(i, 4, QTableWidgetItem(status_text))


class MainWindow(QMainWindow):
    refresh_clicked = Signal()
    theme_switched = Signal(str)

    def __init__(self):
        super().__init__()
        self.setWindowTitle("DeepSeek Monitor")
        self.setMinimumSize(520, 560)
        self.resize(600, 640)

        icon_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "resources", "icon.png")
        if os.path.exists(icon_path):
            self.setWindowIcon(QIcon(icon_path))

        self._build_ui()
        self._apply_theme()

    def _build_ui(self):
        central = QWidget()
        central.setObjectName("central")
        self.setCentralWidget(central)

        layout = QVBoxLayout(central)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        titlebar = QHBoxLayout()
        titlebar.setContentsMargins(16, 8, 12, 8)
        titlebar.addWidget(QLabel("🐋 DeepSeek Monitor"))
        titlebar.addStretch()

        for color, theme_name in SWATCH_COLORS:
            sw = ThemeSwatch(color, theme_name)
            sw.clicked.connect(lambda checked, tn=theme_name: self.theme_switched.emit(tn))
            titlebar.addWidget(sw)

        layout.addLayout(titlebar)

        self.tabs = QTabWidget()
        self.tabs.setDocumentMode(True)

        self.overview = OverviewTab()
        self.overview.refresh_clicked.connect(self.refresh_clicked.emit)

        self.history = HistoryTab()

        self.settings_page = SettingsPage()
        self.settings_page.api_key_saved.connect(self.refresh_clicked.emit)
        self.settings_page.theme_changed.connect(self.theme_switched.emit)
        self.settings_page.data_exported.connect(self._on_export_done)

        self.tabs.addTab(self.overview, "概览")
        self.tabs.addTab(self.history, "历史")
        self.tabs.addTab(self.settings_page, "设置")

        layout.addWidget(self.tabs)

    def _apply_theme(self):
        theme_name = get_setting("theme", DEFAULT_THEME) or DEFAULT_THEME
        qss = generate_qss(theme_name)
        self.setStyleSheet(qss)

    def update_balance(self, balance_data: dict | None, status: str = "ok",
                       response_time: float = 0.0):
        self.overview.update_data(balance_data, status, response_time)
        if status == "ok":
            self.history.load_data()

    def showEvent(self, event):
        super().showEvent(event)
        if self.tabs.currentIndex() == 1:
            self.history.load_data()

    def _on_export_done(self, filepath):
        QMessageBox.information(self, "导出成功", f"历史数据已导出到：\n{filepath}")

    def closeEvent(self, event):
        event.ignore()
        self.hide()
