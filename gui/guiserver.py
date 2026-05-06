import asyncio
import json
import re
import threading

import qtawesome as qta
import websockets
from PySide6.QtCore import QSize, Qt
from PySide6.QtWidgets import QHBoxLayout, QLabel, QListWidgetItem, QPushButton, QWidget


class ServerMixin:
    def _natural_sort_key(self, value):
        parts = re.split(r'(\d+)', str(value))
        return [int(part) if part.isdigit() else part.lower() for part in parts]

    def _refresh_runtime_widgets_if_needed(self):
        if hasattr(self, '_refresh_runtime_widgets'):
            self._refresh_runtime_widgets()

    def _fill_world_list_widget(self, widget, files, current):
        widget.clear()

        is_dark = bool(getattr(self, 'is_dark_mode', False))
        inactive_fg = '#E8EAED' if is_dark else '#202124'
        hover_bg = '#3A3A3A' if is_dark else '#F1F3F4'

        for name in files:
            item = QListWidgetItem('')
            item.setData(Qt.UserRole, name)
            item.setSizeHint(QSize(0, 34))
            widget.addItem(item)

            is_current = name == current

            row = QWidget()
            row.setCursor(Qt.PointingHandCursor)
            row.setStyleSheet(
                'background: #4285F4; border-radius: 6px;'
                if is_current else
                'background: transparent; border-radius: 6px;'
            )

            layout = QHBoxLayout(row)
            layout.setContentsMargins(8, 0, 4, 0)
            layout.setSpacing(6)

            name_label = QLabel(name)
            name_label.setTextFormat(Qt.PlainText)
            name_label.setStyleSheet(
                f'''
                QLabel {{
                    background: transparent;
                    border: none;
                    color: {"white" if is_current else inactive_fg};
                    font-weight: 900;
                    padding: 0 4px 0 0;
                }}
                '''
            )
            layout.addWidget(name_label, 1)

            def _select_world(_event, n=name):
                self.request_world_switch(n)

            row.mousePressEvent = _select_world
            name_label.mousePressEvent = _select_world

            delete_button = QPushButton()
            delete_button.setCursor(Qt.PointingHandCursor)
            delete_button.setFixedSize(24, 24)
            delete_button.setIcon(qta.icon('fa5s.trash-alt', color='#E53935'))
            delete_button.setIconSize(QSize(12, 12))
            delete_button.setStyleSheet('''
                QPushButton {
                    background: transparent;
                    border: none;
                    border-radius: 12px;
                }
                QPushButton:hover {
                    background: rgba(229, 57, 53, 0.10);
                }
            ''')
            delete_button.clicked.connect(lambda _checked=False, n=name: self.delete_world(n))
            layout.addWidget(delete_button, 0, Qt.AlignRight)

            widget.setItemWidget(item, row)

        if current:
            for index in range(widget.count()):
                item = widget.item(index)
                if (item.data(Qt.UserRole) or item.text()) == current:
                    widget.setCurrentItem(item)
                    break

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
        from ._globals import robot, world

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

            if getattr(self, '_mark_next_snapshot_saved', False) or getattr(self, '_saved_snapshot', None) is None:
                self._mark_next_snapshot_saved = False
                if hasattr(self, '_remember_saved_snapshot'):
                    self._remember_saved_snapshot()

            self.update_scene()
            return

        if t == 'sense_result':
            sensor = str(data.get('sensor', '')).lower()
            current_cell = (robot.x, robot.y)

            if sensor == 'color':
                world.discovered_colors.add(current_cell)
                self.update_scene()
                return

            if sensor in ('temperature', 'radiation'):
                world.discovered_sensors.add(current_cell)
                self.update_scene()
                return

            return

        if t == 'reset_result':
            world.discovered_sensors.clear()
            world.discovered_colors.clear()

            if hasattr(self, 'scene'):
                self.scene.hit_wall = None

            self.update_scene()
            return

        if t == 'save_world_result':
            if bool(data.get('ok', False)):
                if hasattr(self, '_remember_saved_snapshot'):
                    self._remember_saved_snapshot()

                target = getattr(self, '_pending_world_switch', None)
                if target:
                    self._pending_world_switch = None
                    self.load_world(target)
                    return

            self.update_world_list()
            return

        if t == 'delete_world_result':
            files = sorted(data.get('files') or [], key=self._natural_sort_key)
            deleted_name = str(data.get('name') or '').strip()
            self._last_world_files = list(files)

            if deleted_name and getattr(self, '_pending_deleted_world', None) == deleted_name:
                next_name = getattr(self, '_pending_next_world', None)
                self._pending_deleted_world = None
                self._pending_next_world = None

                current = str(getattr(self, '_current_world', '') or '').strip()
                if current == deleted_name:
                    self._current_world = next_name or None
                    if next_name:
                        self.load_world(next_name)
                        return

            if hasattr(self, 'world_list'):
                self._fill_world_list_widget(self.world_list, files, getattr(self, '_current_world', None))

            if hasattr(self, 'edit_world_list'):
                self._fill_world_list_widget(self.edit_world_list, files, getattr(self, '_current_world', None))

            return

        if t == 'world_list':
            files = sorted(data.get('files') or [], key=self._natural_sort_key)
            self._last_world_files = list(files)
            current = getattr(self, '_current_world', None)

            if hasattr(self, 'world_list'):
                self._fill_world_list_widget(self.world_list, files, current)

            if hasattr(self, 'edit_world_list'):
                self._fill_world_list_widget(self.edit_world_list, files, current)

            return

        if t == 'error':
            if getattr(self, '_pending_world_switch', None) is not None:
                self._pending_world_switch = None
                self.update_world_list()

            if getattr(self, '_pending_deleted_world', None) is not None:
                self._pending_deleted_world = None
                self._pending_next_world = None
                self.update_world_list()

            self.setWindowTitle('Amun  |  Error!')
            self.update_scene()
            return

        if t == 'program_started':
            self._program_running = True
            world.discovered_sensors.clear()
            world.discovered_colors.clear()

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