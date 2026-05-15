import socket
import sys

from PySide6.QtCore import QTimer
from PySide6.QtWidgets import QApplication

import server.server as backend
from gui._globals import set_viewer_mode
from gui.main_window import MainWindow


def _is_gui_server_ready(timeout=0.5):
    import asyncio
    import websockets

    async def _probe():
        try:
            async with websockets.connect(
                'ws://localhost:8766',
                ping_interval=None,
                open_timeout=timeout,
                close_timeout=timeout,
            ):
                return True
        except Exception:
            return False

    try:
        return asyncio.run(_probe())
    except Exception:
        return False


def _ensure_backend():
    if _is_gui_server_ready(timeout=0.5):
        return False

    backend.start()
    return True


def run_app(edit_mode=False):
    set_viewer_mode(not bool(edit_mode))

    fresh_start = _ensure_backend()

    app = QApplication.instance()
    created_app = app is None

    if created_app:
        app = QApplication(sys.argv)
        app.setQuitOnLastWindowClosed(True)
        app.setStyle('Fusion')

        app._signal_timer = QTimer()
        app._signal_timer.setInterval(100)
        app._signal_timer.timeout.connect(lambda: None)
        app._signal_timer.start()

    window = MainWindow(fresh_start=fresh_start)
    window.show()
    app.processEvents()
    window.repaint()
    app.processEvents()

    if created_app:
        return app.exec()

    return window


if __name__ == '__main__':
    raise SystemExit(run_app())