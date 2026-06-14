"""后台刷新线程 — QThread 定时拉取余额"""
from PySide6.QtCore import QThread, Signal
from api import fetch_balance, Balance, BalanceError
from storage import get_api_key as db_get_api_key, insert_snapshot, get_setting
from crypto import decrypt


class RefreshWorker(QThread):
    """后台定时刷新线程"""

    balance_ready = Signal(object)   # Balance 对象
    error_occurred = Signal(str)     # 错误消息
    no_key = Signal()                # 无 Key 信号

    def __init__(self, parent=None):
        super().__init__(parent)
        self._running = True
        self._fail_count = 0

    def run(self):
        """首次立即执行，之后按间隔循环"""
        import time

        # 首次立即刷新
        self._refresh()
        if not self._running:
            return

        interval = self._get_interval_seconds()

        while self._running:
            for _ in range(interval):
                if not self._running:
                    return
                time.sleep(1)
            self._refresh()

    def _refresh(self):
        """执行一次刷新"""
        encrypted = db_get_api_key()
        if not encrypted:
            self.no_key.emit()
            return

        api_key = decrypt(encrypted)
        result = fetch_balance(api_key)

        if isinstance(result, Balance):
            self._fail_count = 0
            for info in result.balance_infos:
                try:
                    insert_snapshot(
                        total=float(info.total_balance),
                        granted=float(info.granted_balance),
                        topped_up=float(info.topped_up_balance),
                        is_available=result.is_available,
                        currency=info.currency,
                    )
                except (ValueError, TypeError):
                    pass
            self.balance_ready.emit(result)
        else:
            self._fail_count += 1
            self.error_occurred.emit(result.message)

    def _get_interval_seconds(self) -> int:
        try:
            val = get_setting("refresh_interval", "600")
            return max(60, int(val))
        except (ValueError, TypeError):
            return 600

    def stop(self):
        self._running = False
        self.wait(3000)
