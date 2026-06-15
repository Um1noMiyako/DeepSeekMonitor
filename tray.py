"""系统托盘 — QSystemTrayIcon + 左键弹窗 + 右键菜单"""
from PySide6.QtWidgets import QSystemTrayIcon, QMenu, QApplication
from PySide6.QtGui import QIcon, QAction
from PySide6.QtCore import Signal, QObject
from popup import PopupWindow
from main_window import MainWindow
from storage import get_presets, set_active_preset, get_setting, resolve_api_key
import os


class TrayManager(QObject):
    refresh_requested = Signal()
    quit_requested = Signal()

    def __init__(self, app: QApplication):
        super().__init__(app)
        self._app = app
        self._popup: PopupWindow | None = None
        self._main_window: MainWindow | None = None

        icon_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "resources", "icon.png")
        icon = QIcon(icon_path) if os.path.exists(icon_path) else app.style().standardIcon(
            app.style().StandardPixmap.SP_ComputerIcon)

        self._tray = QSystemTrayIcon(icon, app)
        self._tray.setToolTip("DeepSeek Monitor")
        self._tray.setVisible(True)
        self._build_menu()
        self._tray.activated.connect(self._on_activated)

    def _build_menu(self):
        menu = QMenu()
        open_action = QAction("📊 打开详情", menu)
        open_action.triggered.connect(self._show_main_window)
        menu.addAction(open_action)
        refresh_action = QAction("🔄 刷新余额", menu)
        refresh_action.triggered.connect(self.refresh_requested.emit)
        menu.addAction(refresh_action)
        menu.addSeparator()
        preset_menu = self._build_preset_submenu()
        menu.addMenu(preset_menu)
        menu.addSeparator()
        quit_action = QAction("🚪 退出", menu)
        quit_action.triggered.connect(self.quit_requested.emit)
        menu.addAction(quit_action)
        self._tray.setContextMenu(menu)

    def _build_preset_submenu(self):
        """构建切换 API Key 子菜单"""
        menu = QMenu("切换 API Key")

        presets = get_presets()
        active_id = get_setting("active_preset_id", "")

        if presets:
            for p in presets:
                action = menu.addAction(p["name"])
                action.setCheckable(True)
                action.setChecked(str(p["id"]) == active_id)
                action.setData(p["id"])
                action.triggered.connect(lambda checked, pid=p["id"], pname=p["name"]:
                    self._switch_preset(pid, pname))
            menu.addSeparator()

        no_preset_action = menu.addAction("单 Key 模式")
        no_preset_action.setCheckable(True)
        no_preset_action.setChecked(not active_id and resolve_api_key() is not None)
        no_preset_action.triggered.connect(lambda: self._switch_preset(None, "单 Key 模式"))

        return menu

    def _switch_preset(self, preset_id: int | None, name: str):
        """切换预设并触发刷新"""
        set_active_preset(preset_id)
        self.refresh_requested.emit()
        self.show_message("DeepSeek Monitor", f"已切换到「{name}」")

    def _on_activated(self, reason: QSystemTrayIcon.ActivationReason):
        if reason == QSystemTrayIcon.ActivationReason.Trigger:
            self._toggle_popup()
        elif reason == QSystemTrayIcon.ActivationReason.DoubleClick:
            self._show_main_window()

    def _toggle_popup(self):
        if self._popup and self._popup.isVisible():
            self._popup.hide()
            return
        if self._popup is None:
            self._popup = PopupWindow()
            self._popup.refresh_requested.connect(self.refresh_requested.emit)
            self._popup.settings_requested.connect(self._show_main_window_settings)
        tray_geo = self._tray.geometry()
        pos = tray_geo.center()
        pos.setY(tray_geo.top())
        self._popup.show_at_point(pos)

    def _show_main_window(self):
        if self._main_window is None:
            self._main_window = MainWindow()
            self._main_window.refresh_clicked.connect(self.refresh_requested.emit)
        self._main_window.show()
        self._main_window.raise_()
        self._main_window.activateWindow()

    def _show_main_window_settings(self):
        self._show_main_window()
        if self._main_window:
            self._main_window.tabs.setCurrentIndex(2)


    def update_popup(self, balance_data: dict | None, status: str = "ok",
                     response_time: float = 0.0):
        if self._popup and self._popup.isVisible():
            self._popup.update_balance(balance_data, status)

    def update_main_window(self, balance_data: dict | None, status: str = "ok",
                           response_time: float = 0.0):
        if self._main_window and self._main_window.isVisible():
            self._main_window.update_balance(balance_data, status, response_time)

    def show_message(self, title: str, message: str):
        self._tray.showMessage(title, message, QSystemTrayIcon.MessageIcon.Information, 3000)

    def set_icon_tooltip(self, text: str):
        self._tray.setToolTip(f"DeepSeek Monitor\n{text}")

    @property
    def popup(self) -> PopupWindow | None:
        return self._popup

    @property
    def main_window(self) -> MainWindow | None:
        return self._main_window
