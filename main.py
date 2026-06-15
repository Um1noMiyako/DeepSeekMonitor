"""DeepSeek Monitor -- 入口 + 单例保护"""
import sys
from PySide6.QtWidgets import QApplication
from PySide6.QtNetwork import QLocalSocket, QLocalServer
from PySide6.QtCore import QCoreApplication
from app import MonitorApp


def is_already_running() -> bool:
    socket = QLocalSocket()
    socket.connectToServer("DeepSeekMonitor")
    if socket.waitForConnected(500):
        socket.close()
        return True
    return False


def main():
    QCoreApplication.setApplicationName("DeepSeekMonitor")
    QCoreApplication.setOrganizationName("DeepSeekMonitor")

    if is_already_running():
        print("DeepSeek Monitor 已在运行")
        sys.exit(0)

    app = QApplication(sys.argv)
    app.setQuitOnLastWindowClosed(False)

    server = QLocalServer(app)
    server.listen("DeepSeekMonitor")

    from theme import generate_qss
    app.setStyleSheet(generate_qss())

    monitor = MonitorApp(app)
    monitor.start()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
