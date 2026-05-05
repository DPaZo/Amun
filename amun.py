import os
import signal
import socket
import sys
import threading
from difflib import get_close_matches

from PySide6.QtCore import QTimer
from PySide6.QtWidgets import QApplication

from client import connection as _connection
from client import robot as _robot
from client.values import (
    BLACK, BLUE, Color, Direction, EAST, GREEN, NORTH,
    ORANGE, PURPLE, RED, SOUTH, WEST, YELLOW,
)
from server.app_paths import set_workspace_dir

NAMED_COLORS = ['red', 'orange', 'yellow', 'green', 'blue', 'purple', 'black']


class Amun:
    def __init__(self):
        self._app = None
        self._window = None

        self.Direction = Direction
        self.Color = Color

        self.NORTH = NORTH
        self.SOUTH = SOUTH
        self.EAST = EAST
        self.WEST = WEST

        self.RED = RED
        self.ORANGE = ORANGE
        self.YELLOW = YELLOW
        self.GREEN = GREEN
        self.BLUE = BLUE
        self.BLACK = BLACK
        self.PURPLE = PURPLE

    def _public_bindings(self):
        return {
            'Direction': Direction,
            'Color': Color,
            'NORTH': NORTH,
            'SOUTH': SOUTH,
            'EAST': EAST,
            'WEST': WEST,
            'RED': RED,
            'ORANGE': ORANGE,
            'YELLOW': YELLOW,
            'GREEN': GREEN,
            'BLUE': BLUE,
            'BLACK': BLACK,
            'PURPLE': PURPLE,
            'move': self.move,
            'walk': self.walk,
            'paint': self.paint,
            'pick_color': self.pick_color,
            'sense_color': self.sense_color,
            'has_color': self.has_color,
            'sense_temperature': self.sense_temperature,
            'sense_radiation': self.sense_radiation,
            'has_wall': self.has_wall,
            'has_border_wall': self.has_border_wall,
            'reset': self.reset,
            'stop': self.stop,
            'run_edit_mode': self.run_edit_mode,
        }

    def _public_name_suggestion(self, name):
        choices = [
            'NORTH', 'SOUTH', 'EAST', 'WEST',
            'RED', 'ORANGE', 'YELLOW', 'GREEN', 'BLUE', 'BLACK', 'PURPLE',
            'Direction', 'Color',
            'move', 'walk', 'paint', 'pick_color',
            'sense_color', 'has_color',
            'sense_temperature', 'sense_radiation',
            'has_wall', 'has_border_wall',
            'reset', 'stop', 'run_edit_mode',
            'amun',
        ]
        matches = get_close_matches(str(name), choices, n=1, cutoff=0.6)
        return matches[0] if matches else None

    def _format_program_error(self, exc):
        if isinstance(exc, NameError):
            name = getattr(exc, 'name', None)
            if not name:
                text = str(exc)
                parts = text.split("'")
                if len(parts) >= 2:
                    name = parts[1]

            if name:
                suggestion = self._public_name_suggestion(name)
                if suggestion:
                    return f'Unknown name: {name}. Did you mean {suggestion}?'
                return f'Unknown name: {name}.'

            return str(exc)

        if isinstance(exc, (TypeError, RuntimeError)):
            return str(exc)

        return f'{type(exc).__name__}: {exc}'

    def _prepare_workspace(self, program_func):
        namespace = getattr(program_func, '__globals__', {}) or {}
        module_file = namespace.get('__file__')

        if module_file:
            workspace = os.path.abspath(os.path.dirname(module_file))
        else:
            workspace = os.path.abspath(os.getcwd())

        set_workspace_dir(workspace)
        return workspace

    def _setup(self, program_func):
        if not callable(program_func):
            raise TypeError('program_func must be callable')

        namespace = getattr(program_func, '__globals__', None)
        if namespace is None:
            raise TypeError('program_func must be a normal Python function')

        bindings = self._public_bindings()
        missing = object()
        previous = {}

        for name, value in bindings.items():
            previous[name] = namespace.get(name, missing)
            namespace[name] = value

        return namespace, previous, tuple(bindings.keys()), missing

    def _restore_bindings(self, namespace, previous, names, missing):
        for name in names:
            if previous[name] is missing:
                if name in namespace:
                    del namespace[name]
            else:
                namespace[name] = previous[name]

    def _ensure_backend(self):
        import server.server as backend

        try:
            with socket.create_connection(('localhost', 8766), timeout=0.2):
                return False
        except OSError:
            backend.start()
            return True

    def _ensure_app(self, fresh_start):
        from gui.main_window import MainWindow

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

            signal.signal(signal.SIGINT, self._handle_interrupt)
            signal.signal(signal.SIGTERM, self._handle_interrupt)

        self._app = app
        self._window = MainWindow(fresh_start=fresh_start)
        self._window.show()

        return created_app

    def _shutdown_runtime(self):
        try:
            _connection.close()
        except Exception:
            pass

    def _handle_interrupt(self, *_args):
        try:
            if self._window is not None:
                self._window.close()
        except Exception:
            pass

        self._shutdown_runtime()

        app = QApplication.instance()
        if app is not None:
            app.quit()

    def _run_program(self, program_func, namespace, previous, names, missing):
        try:
            return program_func()
        except Exception as exc:
            print(f'[program error] {self._format_program_error(exc)}')
        finally:
            try:
                self.stop()
            except Exception:
                pass

            self._restore_bindings(namespace, previous, names, missing)

    def run(self, program_func):
        namespace, previous, names, missing = self._setup(program_func)
        self._prepare_workspace(program_func)

        try:
            fresh_start = self._ensure_backend()
            created_app = self._ensure_app(fresh_start)
        except Exception:
            self._restore_bindings(namespace, previous, names, missing)
            raise

        delay_ms = 2000 if fresh_start else 200

        QTimer.singleShot(
            delay_ms,
            lambda: threading.Thread(
                target=self._run_program,
                args=(program_func, namespace, previous, names, missing),
                daemon=True,
            ).start(),
        )

        if created_app:
            try:
                return self._app.exec()
            finally:
                self._shutdown_runtime()

        return None

    def move(self, direction, steps=1):
        return _robot.move(direction, steps)

    def walk(self, direction, steps=1):
        return _robot.walk(direction, steps)

    def paint(self, color=None):
        return _robot.paint(color)

    def pick_color(self, color):
        return _robot.pick_color(color)

    def sense_color(self):
        return _robot.sense_color()

    def has_color(self):
        return _robot.has_color()

    def sense_temperature(self):
        return _robot.sense_temperature()

    def sense_radiation(self):
        return _robot.sense_radiation()

    def has_wall(self, direction):
        return _robot.has_wall(direction)

    def has_border_wall(self, direction):
        return _robot.has_border_wall(direction)

    def reset(self, clear_world=False):
        return _robot.reset(clear_world)

    def stop(self):
        return _robot.stop()

    def run_edit_mode(self):
        return _robot.run_edit_mode()


amun = Amun()

__all__ = ['Amun', 'amun']