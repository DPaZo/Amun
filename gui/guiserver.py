import asyncio
import json
import re
import threading

import websockets
from PySide6.QtCore import Qt
from PySide6.QtWidgets import QListWidgetItem


class ServerMixin:
    def _natural_sort_key(self, value):
        parts = re.split(r'(\d+)', str(value))
        return [int(part) if part.isdigit() else part.lower() for part in parts]

    def _refresh_runtime_widgets_if_needed(self):
        if hasattr(self, '_refresh_runtime_widgets'):
            self._refresh_runtime_widgets()

    def _fill_world_list_widget(self, widget, files, current):
        widget.clear()

        for name in files:
            widget.addItem(QListWidgetItem(name))

        if current:
            items = widget.findItems(current, Qt.MatchExactly)
            if items:
                widget.setCurrentItem(items[0])

    def _set_enabled_if_present(self, attr_name, value):
        if hasattr(self, attr_name):
            getattr(self, attr_name).setEnabled(value)

    def _setup_server_hooks(self):
        self._server_ws = None
        self._server_loop = None
        self._program_running = False
        self._server_shutdown = threading.Event()

        async def connect_loop():
            was_connected = False

            while not self._server_shutdown.is_set():
                try:
                    async with websockets.connect('ws://localhost:8766', ping_interval=None) as ws:
                        self._server_ws = ws
                        was_connected = True
                        self._connected_signal.emit()

                        async for message in ws:
                            if self._server_shutdown.is_set():
                                break

                            try:
                                data = json.loads(message)
                            except Exception:
                                continue

                            self._server_event_signal.emit(data)
                except Exception:
                    pass
                finally:
                    self._server_ws = None

                if was_connected:
                    self._disconnected_signal.emit()
                    was_connected = False

                if self._server_shutdown.is_set():
                    break

                await asyncio.sleep(2)

        def run():
            loop = asyncio.new_event_loop()
            self._server_loop = loop
            asyncio.set_event_loop(loop)

            try:
                loop.run_until_complete(connect_loop())
            finally:
                try:
                    loop.run_until_complete(loop.shutdown_asyncgens())
                except Exception:
                    pass

                loop.close()

        threading.Thread(target=run, daemon=True).start()

    def send_to_server(self, data):
        if not hasattr(self, '_server_ws'):
            return

        ws = self._server_ws
        loop = self._server_loop

        if ws is None or loop is None or loop.is_closed():
            return

        async def _send():
            try:
                await ws.send(json.dumps(data))
            except Exception:
                pass

        try:
            asyncio.run_coroutine_threadsafe(_send(), loop)
        except Exception:
            pass

    def _shutdown_server_hooks(self):
        if hasattr(self, '_server_shutdown'):
            self._server_shutdown.set()

        if self._server_ws is not None and self._server_loop is not None:
            try:
                asyncio.run_coroutine_threadsafe(self._server_ws.close(), self._server_loop)
            except Exception:
                pass

    def _on_program_connected(self):
        if getattr(self, '_needs_initial_push', False):
            self._needs_initial_push = False
            self._push_state_to_server()

        self.update_world_list()
        self.update_scene()
        self._refresh_runtime_widgets_if_needed()

    def _on_program_disconnected(self):
        self._refresh_runtime_widgets_if_needed()
        self.update_scene()

    def _on_server_event(self, data):
        from ._globals import world, robot

        t = data.get('type')

        if t == 'snapshot':
            if getattr(self, '_needs_initial_push', False):
                return

            self.setWindowTitle('Amun')
            r = data.get('robot') or {}
            w = data.get('world') or {}
            hit_wall = data.get('hit_wall')

            try:
                if 'width' in w:
                    world.width = int(w['width'])
                if 'height' in w:
                    world.height = int(w['height'])
            except Exception:
                pass

            world.colors.clear()
            world.walls.clear()
            world.temperature.clear()
            world.radiation.clear()

            for x, y, d in (w.get('walls') or []):
                try:
                    world.walls.add((int(x), int(y), str(d)))
                except Exception:
                    pass

            for x, y, c in (w.get('colors') or []):
                try:
                    world.colors[(int(x), int(y))] = str(c)
                except Exception:
                    pass

            for x, y, v in (w.get('temperature') or []):
                try:
                    world.temperature[(int(x), int(y))] = float(v)
                except Exception:
                    pass

            for x, y, v in (w.get('radiation') or []):
                try:
                    world.radiation[(int(x), int(y))] = float(v)
                except Exception:
                    pass

            try:
                if 'x' in r:
                    robot.x = int(r['x'])
                if 'y' in r:
                    robot.y = int(r['y'])
                if 'direction' in r and r['direction']:
                    robot.direction = str(r['direction']).upper()
                if 'alive' in r:
                    robot.alive = bool(r['alive'])
            except Exception:
                pass

            if hasattr(self, 'scene'):
                self.scene.hit_wall = None

                if isinstance(hit_wall, dict):
                    try:
                        self.scene.hit_wall = (
                            int(hit_wall.get('x')),
                            int(hit_wall.get('y')),
                            str(hit_wall.get('orientation', '')),
                        )
                    except Exception:
                        self.scene.hit_wall = None

            self.update_scene()
            return

        if t == 'reset_result':
            world.discovered_sensors.clear()

            if hasattr(self, 'scene'):
                self.scene.hit_wall = None

            self.update_scene()
            return

        if t == 'world_list':
            files = sorted(data.get('files') or [], key=self._natural_sort_key)
            current = getattr(self, '_current_world', None)

            if hasattr(self, 'world_list'):
                self._fill_world_list_widget(self.world_list, files, current)

            if hasattr(self, 'edit_world_list'):
                self._fill_world_list_widget(self.edit_world_list, files, current)

            return

        if t == 'error':
            self.setWindowTitle('Amun  |  Error!')
            self.update_scene()
            return

        if t == 'program_started':
            self._program_running = True
            world.discovered_sensors.clear()

            if hasattr(self, 'scene'):
                self.scene.hit_wall = None

            if hasattr(self, 'edit_toggle'):
                self.edit_toggle.setChecked(False)
                self.edit_toggle.setEnabled(False)
                self.edit_mode = False
                self.update_ui_for_mode()

            self._set_enabled_if_present('world_list', False)
            self._set_enabled_if_present('edit_world_list', False)
            self._refresh_runtime_widgets_if_needed()
            return

        if t in ('program_finished', 'program_stopped'):
            self._program_running = False
            self.setWindowTitle('Amun')

            if hasattr(self, 'edit_toggle'):
                self.edit_toggle.setEnabled(True)
                self.edit_mode = self.edit_toggle.isChecked()
                self.update_ui_for_mode()

            self._set_enabled_if_present('world_list', True)
            self._set_enabled_if_present('edit_world_list', True)
            self._refresh_runtime_widgets_if_needed()

            self.update_scene()
            return

        if t == 'set_edit_mode':
            value = bool(data.get('value', False))

            if hasattr(self, 'edit_toggle'):
                self.edit_toggle.setChecked(value)
                self.edit_mode = value
                self.update_ui_for_mode()
                self._refresh_runtime_widgets_if_needed()
                self.update_scene()

            return