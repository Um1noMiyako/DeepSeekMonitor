"""预览浮窗 — Frameless 弹出窗口，显示余额概览"""
from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel,
                                QPushButton, QFrame, QApplication)
from PySide6.QtCore import Qt, Signal, QPoint, QTimer
from PySide6.QtGui import QMouseEvent
from theme import generate_popup_qss, THEMES, DEFAULT_THEME
from storage import get_latest_snapshot, get_setting

SWATCH_COLORS = [
    ("#6366F1", "indigo"), ("#10B981", "emerald"), ("#F59E0B", "amber"),
    ("#EC4899", "rose"), ("#06B6D4", "cyan"), ("#8B5CF6", "violet"),
    ("#FF0080", "neon"), ("#8888A0", "charcoal"), ("#4F46E5", "white"),
]


class ThemeSwatch(QPushButton):
    def __init__(self, color: str, theme_name: str, parent=None):
        super().__init__(parent)
        self.theme_name = theme_name
        self.setFixedSize(16, 16)
        self.setCursor(Qt.PointingHandCursor)
        self.setStyleSheet(f"""
            QPushButton {{
                background: {color};
                border-radius: 8px;
                border: 2px solid transparent;
            }}
            QPushButton:hover {{
                border-color: rgba(255,255,255,0.4);
            }}
        """)


class PopupWindow(QWidget):
    """Frameless 浮窗 — 点击外部自动关闭"""

    refresh_requested = Signal()
    settings_requested = Signal()
    theme_changed = Signal(str)
    closed = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint
            | Qt.WindowType.WindowStaysOnTopHint
            | Qt.WindowType.Tool
        )
        self.setAttribute(Qt.WidgetAttribute.WA_ShowWithoutActivating)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, False)
        self.setFixedWidth(320)

        self.setObjectName("popup-root")
        self._build_ui()
        self._apply_theme()

    def _build_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        # ── 伪标题栏 ──
        titlebar = QWidget()
        titlebar.setObjectName("popup-titlebar")
        titlebar.setFixedHeight(40)
        tb_layout = QHBoxLayout(titlebar)
        tb_layout.setContentsMargins(12, 0, 8, 0)
        tb_layout.setSpacing(8)

        title_label = QLabel("🐋 DeepSeek Monitor")
        title_label.setStyleSheet("font-weight:600; font-size:13px;")
        tb_layout.addWidget(title_label)
        tb_layout.addStretch()

        btn_refresh = QPushButton("⟳")
        btn_refresh.setFixedSize(28, 28)
        btn_refresh.setToolTip("刷新余额")
        btn_refresh.setCursor(Qt.PointingHandCursor)
        btn_refresh.clicked.connect(self.refresh_requested.emit)
        btn_refresh.setStyleSheet("QPushButton{background:transparent;border:none;font-size:16px;color:#94A3B8;} QPushButton:hover{color:#fff;}")
        tb_layout.addWidget(btn_refresh)

        btn_settings = QPushButton("⚙")
        btn_settings.setFixedSize(28, 28)
        btn_settings.setToolTip("打开设置")
        btn_settings.setCursor(Qt.PointingHandCursor)
        btn_settings.clicked.connect(self.settings_requested.emit)
        btn_settings.setStyleSheet("QPushButton{background:transparent;border:none;font-size:16px;color:#94A3B8;} QPushButton:hover{color:#fff;}")
        tb_layout.addWidget(btn_settings)

        btn_close = QPushButton("✕")
        btn_close.setFixedSize(28, 28)
        btn_close.setToolTip("关闭")
        btn_close.setCursor(Qt.PointingHandCursor)
        btn_close.clicked.connect(self.hide)
        btn_close.setStyleSheet("QPushButton{background:transparent;border:none;font-size:14px;color:#94A3B8;} QPushButton:hover{color:#EF4444;}")
        tb_layout.addWidget(btn_close)

        root.addWidget(titlebar)

        # ── 色板栏 ──
        swatch_row = QWidget()
        swatch_layout = QHBoxLayout(swatch_row)
        swatch_layout.setContentsMargins(12, 0, 12, 4)
        swatch_layout.setSpacing(6)
        swatch_layout.addStretch()
        for color, theme_name in SWATCH_COLORS:
            sw = ThemeSwatch(color, theme_name)
            sw.clicked.connect(lambda checked, tn=theme_name: self.theme_changed.emit(tn))
            swatch_layout.addWidget(sw)
        root.addWidget(swatch_row)

        # ── 余额区域 ──
        balance_section = QFrame()
        balance_section.setObjectName("balance-section")
        bl = QVBoxLayout(balance_section)
        bl.setContentsMargins(16, 8, 16, 16)
        bl.setSpacing(8)

        header_row = QHBoxLayout()
        header_label = QLabel("💰 账户余额")
        header_label.setStyleSheet("font-size:13px; font-weight:500;")
        header_row.addWidget(header_label)
        header_row.addStretch()

        self.status_dot = QLabel()
        self.status_dot.setFixedSize(8, 8)
        self.status_dot.setObjectName("dot-gray")
        header_row.addWidget(self.status_dot)

        self.status_label = QLabel("未配置 Key")
        self.status_label.setStyleSheet("font-size:12px;")
        header_row.addWidget(self.status_label)
        bl.addLayout(header_row)

        self.balance_amount = QLabel("--.--")
        self.balance_amount.setObjectName("balance-large")
        self.balance_amount.setAlignment(Qt.AlignmentFlag.AlignCenter)
        bl.addWidget(self.balance_amount)

        cards_row = QHBoxLayout()
        cards_row.setSpacing(8)

        card_topup = QFrame()
        card_topup.setObjectName("glass-card")
        ctl = QVBoxLayout(card_topup)
        ctl.setContentsMargins(12, 10, 12, 10)
        ctl.setSpacing(4)
        ctl.addWidget(QLabel("💰 充值"))
        self.topup_amount = QLabel("--.--")
        self.topup_amount.setStyleSheet("font-size:18px; font-weight:700;")
        ctl.addWidget(self.topup_amount)
        cards_row.addWidget(card_topup)

        card_grant = QFrame()
        card_grant.setObjectName("glass-card")
        cgl = QVBoxLayout(card_grant)
        cgl.setContentsMargins(12, 10, 12, 10)
        cgl.setSpacing(4)
        cgl.addWidget(QLabel("🎁 赠送"))
        self.granted_amount = QLabel("--.--")
        self.granted_amount.setStyleSheet("font-size:18px; font-weight:700;")
        cgl.addWidget(self.granted_amount)
        cards_row.addWidget(card_grant)

        bl.addLayout(cards_row)

        summary_row = QHBoxLayout()
        summary_label = QLabel("📊 总余额")
        summary_label.setStyleSheet("font-size:12px;")
        summary_row.addWidget(summary_label)
        summary_row.addStretch()
        self.total_summary = QLabel("--.--")
        self.total_summary.setStyleSheet("font-size:16px; font-weight:700;")
        summary_row.addWidget(self.total_summary)
        bl.addLayout(summary_row)

        root.addWidget(balance_section)

        footer = QHBoxLayout()
        footer.setContentsMargins(16, 4, 16, 8)
        self.refresh_time = QLabel("")
        self.refresh_time.setStyleSheet("font-size:10px; color:#64748B;")
        footer.addStretch()
        footer.addWidget(self.refresh_time)
        root.addLayout(footer)

    def _apply_theme(self):
        theme_name = get_setting("theme", DEFAULT_THEME) or DEFAULT_THEME
        qss = generate_popup_qss(theme_name)
        self.setStyleSheet(qss)

    def update_balance(self, balance_data: dict | None, status: str = "ok"):
        if status == "no_key":
            self.status_dot.setObjectName("dot-gray")
            self.status_label.setText("未配置 Key")
            self.balance_amount.setText("--.--")
            self.topup_amount.setText("--.--")
            self.granted_amount.setText("--.--")
            self.total_summary.setText("--.--")
        elif status == "error":
            self.status_dot.setObjectName("dot-red")
            self.status_label.setText("连接失败")
        elif balance_data:
            total = balance_data.get("total_balance", 0)
            granted = balance_data.get("granted_balance", 0)
            topped_up = balance_data.get("topped_up_balance", 0)
            is_avail = balance_data.get("is_available", False)
            fetched = balance_data.get("fetched_at", "")

            self.status_dot.setObjectName("dot-green" if is_avail else "dot-yellow")
            self.status_label.setText("可用" if is_avail else "余额不足")
            self.balance_amount.setText(f"¥ {total:,.2f}")
            self.topup_amount.setText(f"¥ {topped_up:,.2f}")
            self.granted_amount.setText(f"¥ {granted:,.2f}")
            self.total_summary.setText(f"¥ {total:,.2f}")
            self.refresh_time.setText(f"最后刷新：{fetched}")

        self.style().unpolish(self)
        self.style().polish(self)
        self.setStyleSheet(self.styleSheet())

    def show_at_point(self, global_pos: QPoint):
        screen = QApplication.primaryScreen()
        if screen:
            geo = screen.availableGeometry()
            x = min(global_pos.x() - 160, geo.right() - 340)
            y = global_pos.y() - self.sizeHint().height() - 10
            self.move(x, max(y, geo.top()))
        else:
            self.move(global_pos.x() - 160, global_pos.y() - 300)
        self.show()
        self.raise_()

    def focusOutEvent(self, event):
        super().focusOutEvent(event)
        QTimer.singleShot(100, self._check_hide)

    def _check_hide(self):
        if not self.isActiveWindow():
            self.hide()
            self.closed.emit()
