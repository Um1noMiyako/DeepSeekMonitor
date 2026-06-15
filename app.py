"""App 生命周期管理 — 连接 worker、tray、存储"""
from PySide6.QtCore import QObject
from tray import TrayManager
from worker import RefreshWorker
from storage import init_db, get_latest_snapshot, resolve_api_key, get_active_preset_name


class MonitorApp(QObject):
    def __init__(self, app):
        super().__init__()
        self._app = app
        self._worker = None
        self._tray = None

    def start(self):
        init_db()
        self._tray = TrayManager(self._app)
        self._tray.refresh_requested.connect(self._refresh_now)
        self._tray.quit_requested.connect(self._quit)

        preset_name = get_active_preset_name()
        if preset_name:
            self._tray.set_icon_tooltip(f"预设：{preset_name}\n正在获取余额...")
            self._tray.show_message("DeepSeek Monitor", f"已载入预设「{preset_name}」")
        elif resolve_api_key():
            self._tray.set_icon_tooltip("单 Key 模式\n正在获取余额...")
        else:
            self._tray.show_message("DeepSeek Monitor", "请右键托盘菜单打开详情 → 设置页配置 API Key")
            self._tray.set_icon_tooltip("未配置 API Key")

        snap = get_latest_snapshot()
        self._refresh_ui_from_snapshot(snap)

        self._worker = RefreshWorker()
        self._worker.balance_ready.connect(self._on_balance_ready)
        self._worker.error_occurred.connect(self._on_error)
        self._worker.no_key.connect(lambda: self._refresh_ui_from_snapshot(None, "no_key"))
        self._worker.start()

    def _refresh_now(self):
        if self._worker:
            import threading
            t = threading.Thread(target=self._worker._refresh, daemon=True)
            t.start()

    def _on_balance_ready(self, balance):
        snap = get_latest_snapshot()
        status = "ok" if snap else "no_key"
        rt = balance.response_time_ms
        self._tray.update_popup(snap, status, rt)
        self._tray.update_main_window(snap, status, rt)
        preset_name = get_active_preset_name()
        if snap:
            tip = f"¥{snap['total_balance']:,.2f}"
            if preset_name:
                tip = f"预设：{preset_name}\n余额 {tip}"
            self._tray.set_icon_tooltip(tip)
        else:
            self._tray.set_icon_tooltip(f"预设：{preset_name}" if preset_name else "已连接")

    def _on_error(self, message: str):
        snap = get_latest_snapshot()
        self._tray.update_popup(snap, "error")
        self._tray.update_main_window(snap, "error")
        preset_name = get_active_preset_name()
        prefix = f"「{preset_name}」" if preset_name else ""
        self._tray.set_icon_tooltip(f"{prefix}{message}" if prefix else message)

    def _refresh_ui_from_snapshot(self, snap: dict | None, status: str = "ok"):
        if snap is None:
            status = "no_key" if not resolve_api_key() else "ok"
        self._tray.update_popup(snap, status)
        self._tray.update_main_window(snap, status)

    def _quit(self):
        if self._worker:
            self._worker.stop()
        self._app.quit()
