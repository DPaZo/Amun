# amun.py
import os
import signal
import sys
import threading
from difflib import get_close_matches

from client import connection as _connection
from client import robot as _robot
from client.values import (
    BLACK,
    BLUE,
    Color,
    Direction,
    EAST,
    GREEN,
    NORTH,
    ORANGE,
    PURPLE,
    RED,
    SOUTH,
    WEST,
    YELLOW,
)
from server.app_paths import set_workspace_dir


def _is_debug_mode():
    if sys.gettrace() is not None:
        return True

    try:
        import pydevd

        get_debugger = getattr(pydevd, "get_global_debugger", None)
        if callable(get_debugger) and get_debugger() is not None:
            return True
    except Exception:
        pass

    return False


class Amun:
    def __init__(self):
        self._app = None
        self._window = None
        self._backend_started = False
        self._shutting_down = False
        self._gui_process = None
        self._debug_gui_connected = False

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
            "Direction": Direction,
            "Color": Color,
            "NORTH": NORTH,
            "SOUTH": SOUTH,
            "EAST": EAST,
            "WEST": WEST,
            "RED": RED,
            "ORANGE": ORANGE,
            "YELLOW": YELLOW,
            "GREEN": GREEN,
            "BLUE": BLUE,
            "BLACK": BLACK,
            "PURPLE": PURPLE,
            "move": self.move,
            "walk": self.walk,
            "paint": self.paint,
            "pick_color": self.pick_color,
            "sense_color": self.sense_color,
            "has_color": self.has_color,
            "sense_temperature": self.sense_temperature,
            "sense_radiation": self.sense_radiation,
            "has_wall": self.has_wall,
            "has_border_wall": self.has_border_wall,
            "reset": self.reset,
            "stop": self.stop,
            "run_edit_mode": self.run_edit_mode,
        }

    def install(self, namespace):
        if not isinstance(namespace, dict):
            raise TypeError("namespace must be a dict, usually globals()")

        for name, value in self._public_bindings().items():
            namespace[name] = value

        return namespace

    def _public_name_suggestion(self, name):
        choices = [
            "NORTH",
            "SOUTH",
            "EAST",
            "WEST",
            "RED",
            "ORANGE",
            "YELLOW",
            "GREEN",
            "BLUE",
            "BLACK",
            "PURPLE",
            "Direction",
            "Color",
            "move",
            "walk",
            "paint",
            "pick_color",
            "sense_color",
            "has_color",
            "sense_temperature",
            "sense_radiation",
            "has_wall",
            "has_border_wall",
            "reset",
            "stop",
            "run_edit_mode",
            "amun",
        ]
        matches = get_close_matches(str(name), choices, n=1, cutoff=0.6)
        return matches[0] if matches else None

    def _format_program_error(self, exc):
        if isinstance(exc, NameError):
            name = getattr(exc, "name", None)

            if not name:
                text = str(exc)
                parts = text.split("'")
                if len(parts) >= 2:
                    name = parts[1]

            if name:
                suggestion = self._public_name_suggestion(name)
                if suggestion:
                    return f"Unknown name: {name}. Did you mean {suggestion}?"
                return f"Unknown name: {name}."

            return str(exc)

        if isinstance(exc, (TypeError, RuntimeError)):
            return str(exc)

        return f"{type(exc).__name__}: {exc}"

    def _prepare_workspace(self, program_func):
        namespace = getattr(program_func, "__globals__", {}) or {}
        module_file = namespace.get("__file__")

        if module_file:
            workspace = os.path.abspath(os.path.dirname(module_file))
        else:
            workspace = os.path.abspath(os.getcwd())

        set_workspace_dir(workspace)
        return workspace

    def _setup(self, program_func):
        if not callable(program_func):
            raise TypeError("program_func must be callable")

        namespace = getattr(program_func, "__globals__", None)
        if namespace is None:
            raise TypeError("program_func must be a normal Python function")

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
                namespace.pop(name, None)
            else:
                namespace[name] = previous[name]

    def _launch_gui_subprocess(self):
        import subprocess

        gui_script = os.path.join(os.path.dirname(os.path.abspath(__file__)), "gui.py")
        self._gui_process = subprocess.Popen([sys.executable, gui_script])

    def _is_gui_server_ready(self, timeout=0.5):
        import asyncio
        import websockets

        async def _probe():
            try:
                async with websockets.connect(
                    "ws://localhost:8766",
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

    def _wait_for_server(self, timeout=10.0):
        import time

        deadline = time.time() + timeout
        while time.time() < deadline:
            if self._is_gui_server_ready(timeout=0.5):
                return
            time.sleep(0.1)

        raise RuntimeError("[amun] timed out waiting for GUI to start")

    def _get_runtime_status(self, timeout=0.5):
        import asyncio
        import json
        import websockets

        async def _probe():
            try:
                async with websockets.connect(
                        "ws://localhost:8766",
                        ping_interval=None,
                        open_timeout=timeout,
                        close_timeout=timeout,
                ) as ws:
                    await ws.send(json.dumps({"type": "get_runtime_status"}))
                    deadline = asyncio.get_event_loop().time() + timeout
                    while True:
                        remaining = deadline - asyncio.get_event_loop().time()
                        if remaining <= 0:
                            break
                        raw = await asyncio.wait_for(ws.recv(), timeout=remaining)
                        data = json.loads(raw)
                        if isinstance(data, dict) and data.get("type") == "runtime_status":
                            return data
            except Exception:
                return None

            return None

        try:
            return asyncio.run(_probe())
        except Exception:
            return None

    def _wait_for_gui_client(self, timeout=10.0):
        import time

        self._debug_gui_connected = False
        deadline = time.time() + timeout
        while time.time() < deadline:
            status = self._get_runtime_status(timeout=0.5) or {}
            if int(status.get("gui_app_clients", 0)) > 0:
                self._debug_gui_connected = True
                return
            time.sleep(0.1)

        raise RuntimeError("[amun] timed out waiting for GUI client to connect")

    def _sync_debug_gui(self, delay=0.05):
        if not _is_debug_mode():
            return

        if not getattr(self, "_debug_gui_connected", False):
            return

        try:
            import time
            time.sleep(delay)
        except Exception:
            pass

    def _ensure_backend(self):
        import server.server as backend

        if self._is_gui_server_ready(timeout=0.5):
            self._backend_started = False
            return False

        backend.start()
        self._backend_started = True
        return True

    def _install_signal_handlers(self):
        signal.signal(signal.SIGINT, self._handle_interrupt)
        signal.signal(signal.SIGTERM, self._handle_interrupt)

    def _ensure_app(self, fresh_start):
        from PySide6.QtCore import QTimer
        from PySide6.QtWidgets import QApplication
        from gui.main_window import MainWindow

        app = QApplication.instance()
        created_app = app is None

        if created_app:
            app = QApplication(sys.argv)
            app.setQuitOnLastWindowClosed(True)
            app.setStyle("Fusion")

            app._signal_timer = QTimer()
            app._signal_timer.setInterval(100)
            app._signal_timer.timeout.connect(lambda: None)
            app._signal_timer.start()

        self._app = app
        self._window = MainWindow(fresh_start=fresh_start)
        self._window.show()
        return created_app

    def _shutdown_runtime(self):
        if self._shutting_down:
            return

        self._shutting_down = True

        try:
            _robot.stop()
        except Exception:
            pass

        try:
            _connection.close()
        except Exception:
            pass

        if self._backend_started:
            try:
                import server.server as backend

                backend.stop()
            except Exception:
                pass
            finally:
                self._backend_started = False

    def _handle_interrupt(self, *_args):
        try:
            _connection.close()
        except Exception:
            pass

        if self._backend_started:
            try:
                import server.server as backend

                backend.stop()
            except Exception:
                pass
            finally:
                self._backend_started = False

        if self._gui_process is not None:
            try:
                self._gui_process.terminate()
                self._gui_process.wait(timeout=2)
            except Exception:
                try:
                    self._gui_process.kill()
                except Exception:
                    pass
            finally:
                self._gui_process = None

        try:
            if self._window is not None:
                self._window.close()
        except Exception:
            pass

        try:
            from PySide6.QtWidgets import QApplication

            app = QApplication.instance()
            if app is not None:
                app.quit()
        except Exception:
            pass

        os._exit(0)

    def _build_debug_shadow_function(self, program_func, namespace):
        import ast
        import inspect
        import textwrap
        from collections import OrderedDict

        try:
            source_lines, start_line = inspect.getsourcelines(program_func)
        except (OSError, IOError, TypeError):
            return None

        source = textwrap.dedent("".join(source_lines))

        try:
            tree = ast.parse(source)
        except SyntaxError:
            return None

        func_node = None
        for node in tree.body:
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and node.name == program_func.__name__:
                func_node = node
                break

        if func_node is None:
            return None

        func_node.decorator_list = []

        existing_names = {
            *(arg.arg for arg in func_node.args.posonlyargs),
            *(arg.arg for arg in func_node.args.args),
            *(arg.arg for arg in func_node.args.kwonlyargs),
        }
        if func_node.args.vararg is not None:
            existing_names.add(func_node.args.vararg.arg)
        if func_node.args.kwarg is not None:
            existing_names.add(func_node.args.kwarg.arg)

        debug_bindings = OrderedDict()
        for name in program_func.__code__.co_names:
            if not str(name).isidentifier():
                continue
            if name in existing_names:
                continue
            if name in namespace:
                debug_bindings[name] = namespace[name]

        for name in debug_bindings:
            func_node.args.args.append(ast.arg(arg=name))
            func_node.args.defaults.append(
                ast.Subscript(
                    value=ast.Name(id="__amun_debug_bindings", ctx=ast.Load()),
                    slice=ast.Constant(value=name),
                    ctx=ast.Load(),
                )
            )

        ast.increment_lineno(tree, start_line - 1)
        ast.fix_missing_locations(tree)

        sentinel = object()
        original_func = namespace.get(program_func.__name__, sentinel)
        original_bindings = namespace.get("__amun_debug_bindings", sentinel)

        namespace["__amun_debug_bindings"] = dict(debug_bindings)

        try:
            exec(compile(tree, program_func.__code__.co_filename, "exec"), namespace, namespace)
            shadow = namespace.get(program_func.__name__)
        except Exception:
            shadow = None
        finally:
            if original_bindings is sentinel:
                namespace.pop("__amun_debug_bindings", None)
            else:
                namespace["__amun_debug_bindings"] = original_bindings

            if original_func is sentinel:
                namespace.pop(program_func.__name__, None)
            else:
                namespace[program_func.__name__] = original_func

        return shadow if callable(shadow) else None

    def _run_program(self, program_func, namespace, previous, names, missing):
        try:
            return program_func()
        except Exception as exc:
            print(f"[program error] {self._format_program_error(exc)}")
        finally:
            try:
                self.stop()
            except Exception:
                pass

            self._restore_bindings(namespace, previous, names, missing)

    def run(self, program_func):
        namespace, previous, names, missing = self._setup(program_func)
        self._prepare_workspace(program_func)
        self._install_signal_handlers()

        if _is_debug_mode():
            try:
                if not self._is_gui_server_ready(timeout=0.5):
                    self._launch_gui_subprocess()
                    self._wait_for_server()

                self._wait_for_gui_client()

                shadow = self._build_debug_shadow_function(program_func, namespace)
                target = shadow if shadow is not None else program_func

                self._sync_debug_gui(delay=0.3)
                print("[amun] debug mode")
                return self._run_program(target, namespace, previous, names, missing)
            finally:
                self._shutting_down = False

        try:
            fresh_start = self._ensure_backend()
            created_app = self._ensure_app(fresh_start)
        except Exception:
            self._restore_bindings(namespace, previous, names, missing)
            raise

        from PySide6.QtCore import QTimer

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
                self._shutting_down = False

        self._shutting_down = False
        return None

    def move(self, direction, steps=1):
        result = _robot.move(direction, steps)
        self._sync_debug_gui()
        return result

    def walk(self, direction, steps=1):
        result = _robot.walk(direction, steps)
        self._sync_debug_gui()
        return result

    def paint(self, color=None):
        result = _robot.paint(color)
        self._sync_debug_gui()
        return result

    def pick_color(self, color):
        result = _robot.pick_color(color)
        self._sync_debug_gui()
        return result

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
        result = _robot.reset(clear_world)
        self._sync_debug_gui()
        return result

    def stop(self):
        return _robot.stop()

    def run_edit_mode(self):
        return _robot.run_edit_mode()


amun = Amun()


def move(direction, steps=1):
    return amun.move(direction, steps)


def walk(direction, steps=1):
    return amun.walk(direction, steps)


def paint(color=None):
    return amun.paint(color)


def pick_color(color):
    return amun.pick_color(color)


def sense_color():
    return amun.sense_color()


def has_color():
    return amun.has_color()


def sense_temperature():
    return amun.sense_temperature()


def sense_radiation():
    return amun.sense_radiation()


def has_wall(direction):
    return amun.has_wall(direction)


def has_border_wall(direction):
    return amun.has_border_wall(direction)


def reset(clear_world=False):
    return amun.reset(clear_world)


def stop():
    return amun.stop()


def run_edit_mode():
    return amun.run_edit_mode()


__all__ = [
    "amun",
    "move",
    "walk",
    "paint",
    "pick_color",
    "sense_color",
    "has_color",
    "sense_temperature",
    "sense_radiation",
    "has_wall",
    "has_border_wall",
    "reset",
    "stop",
    "run_edit_mode",
    "Direction",
    "Color",
    "NORTH",
    "SOUTH",
    "EAST",
    "WEST",
    "RED",
    "ORANGE",
    "YELLOW",
    "GREEN",
    "BLUE",
    "BLACK",
    "PURPLE",
]