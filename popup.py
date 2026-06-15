"""预览浮窗 — Frameless 弹出窗口，显示余额概览（v1.1 主题安全版）"""
from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel,
                                QPushButton, QFrame, QApplication)
from PySide6.QtCore import Qt, Signal, QPoint, QTimer
from PySide6.QtGui import QFont, QPainterPath, QRegion
from theme import generate_popup_qss
from storage import get_latest_snapshot


class PopupWindow(QWidget):
    refresh_requested = Signal()
    settings_requested = Signal()
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
        self._drag_pos = None
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
        title_label.setObjectName("popup-title")
        tb_layout.addWidget(title_label)
        tb_layout.addStretch()

        btn_refresh = QPushButton("⟳")
        btn_refresh.setObjectName("popup-refresh")
        btn_refresh.setFixedSize(28, 28)
        btn_refresh.setToolTip("刷新余额")
        btn_refresh.setCursor(Qt.PointingHandCursor)
        btn_refresh.clicked.connect(self.refresh_requested.emit)
        tb_layout.addWidget(btn_refresh)

        btn_settings = QPushButton("⚙")
        btn_settings.setObjectName("popup-settings")
        btn_settings.setFixedSize(28, 28)
        btn_settings.setToolTip("打开设置")
        btn_settings.setCursor(Qt.PointingHandCursor)
        btn_settings.clicked.connect(self.settings_requested.emit)
        tb_layout.addWidget(btn_settings)

        btn_close = QPushButton("✕")
        btn_close.setObjectName("popup-close")
        btn_close.setFixedSize(28, 28)
        btn_close.setToolTip("关闭")
        btn_close.setCursor(Qt.PointingHandCursor)
        btn_close.clicked.connect(self.hide)
        tb_layout.addWidget(btn_close)

        root.addWidget(titlebar)

        # ── 余额区域 ──
        balance_section = QFrame()
        balance_section.setObjectName("balance-section")
        bl = QVBoxLayout(balance_section)
        bl.setContentsMargins(16, 8, 16, 16)
        bl.setSpacing(8)

        header_row = QHBoxLayout()
        header_label = QLabel("💰 账户余额")
        header_label.setObjectName("balance-header")
        header_row.addWidget(header_label)
        header_row.addStretch()

        self.status_dot = QLabel()
        self.status_dot.setFixedSize(8, 8)
        self.status_dot.setObjectName("dot-gray")
        header_row.addWidget(self.status_dot)

        self.status_label = QLabel("未配置 Key")
        self.status_label.setObjectName("status-text")
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
        self.topup_amount.setObjectName("card-amount")
        ctl.addWidget(self.topup_amount)
        cards_row.addWidget(card_topup)

        card_grant = QFrame()
        card_grant.setObjectName("glass-card")
        cgl = QVBoxLayout(card_grant)
        cgl.setContentsMargins(12, 10, 12, 10)
        cgl.setSpacing(4)
        cgl.addWidget(QLabel("🎁 赠送"))
        self.granted_amount = QLabel("--.--")
        self.granted_amount.setObjectName("card-amount")
        cgl.addWidget(self.granted_amount)
        cards_row.addWidget(card_grant)

        bl.addLayout(cards_row)

        summary_row = QHBoxLayout()
        summary_label = QLabel("📊 总余额")
        summary_label.setObjectName("summary-label")
        summary_row.addWidget(summary_label)
        summary_row.addStretch()
        self.total_summary = QLabel("--.--")
        self.total_summary.setObjectName("summary-amount")
        summary_row.addWidget(self.total_summary)
        bl.addLayout(summary_row)

        root.addWidget(balance_section)

        footer = QHBoxLayout()
        footer.setContentsMargins(16, 4, 16, 8)
        self.refresh_time = QLabel("")
        self.refresh_time.setObjectName("refresh-time")
        footer.addStretch()
        footer.addWidget(self.refresh_time)
        root.addLayout(footer)

    def _apply_theme(self):
        self.setStyleSheet(generate_popup_qss())

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

        # 刷新 objectName 驱动的样式
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

    def mousePressEvent(self, event):
        """标题栏区域可拖拽"""
        if event.position().y() <= 40:  # 标题栏高度
            self._drag_pos = event.globalPosition().toPoint() - self.frameGeometry().topLeft()
        elif event.position().y() > self.height() - 40:  # 底部非交互区也可拖
            pass  # 不阻止事件传播
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        if self._drag_pos is not None:
            self.move(event.globalPosition().toPoint() - self._drag_pos)
        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event):
        self._drag_pos = None
        super().mouseReleaseEvent(event)

    def _apply_rounded_corners(self, radius: int = 12):
        """圆角裁剪"""
        path = QPainterPath()
        path.addRoundedRect(self.rect(), radius, radius)
        self.setMask(QRegion(path.toFillPolygon().toPolygon()))

    def showEvent(self, event):
        super().showEvent(event)
        self._apply_rounded_corners(12)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self._apply_rounded_corners(12)

    def focusOutEvent(self, event):
        super().focusOutEvent(event)
        QTimer.singleShot(100, self._check_hide)

    def _check_hide(self):
        if not self.isActiveWindow():
            self.hide()
            self.closed.emit()
