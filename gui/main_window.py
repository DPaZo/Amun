import os
import threading

from PySide6.QtCore import QFileSystemWatcher, Qt, Signal
from PySide6.QtGui import QColor, QKeySequence, QPainter, QShortcut
from PySide6.QtWidgets import (
    QApplication, QDialog, QDialogButtonBox, QGraphicsView, QGridLayout,
    QHBoxLayout, QLabel, QMainWindow, QMessageBox, QPushButton, QScrollArea,
    QTextBrowser, QVBoxLayout, QWidget,
)

import gui._globals as _g
from . import lang as _lang
from ._globals import _BASE_DIR, CELL_SIZE, load_prefs, robot, world
from .builders import BuildersMixin
from .guiserver import ServerMixin
from .lang import load_lang, tr
from .persistence import PersistenceMixin
from .theme import ThemeMixin
from .widgets import GridScene


class MainWindow(BuildersMixin, PersistenceMixin, ServerMixin, ThemeMixin, QMainWindow):
    _rebuild_signal = Signal()
    _connected_signal = Signal()
    _disconnected_signal = Signal()
    _server_event_signal = Signal(object)

    def __init__(self, fresh_start=True):
        super().__init__()
        self._rebuild_signal.connect(self._do_rebuild)
        self._connected_signal.connect(self._on_program_connected)
        self._disconnected_signal.connect(self._on_program_disconnected)
        self._server_event_signal.connect(self._on_server_event)
        self._program_connected = False

        QApplication.instance().mainwin = self

        self.setWindowTitle('Amun')
        self.resize(1120, 760)
        self.setMinimumSize(640, 480)
        self.setWindowFlags(
            Qt.Window
            | Qt.CustomizeWindowHint
            | Qt.WindowTitleHint
            | Qt.WindowMinimizeButtonHint
            | Qt.WindowStaysOnTopHint
        )

        self.paint_enabled = False
        self.wall_builder_enabled = False
        self.temp_enabled = False
        self.rad_enabled = False
        self.is_dark_mode = False
        self.edit_mode = not _g.VIEWER_MODE

        self._undo_stack = []
        self._redo_stack = []
        self._history_limit = 100
        self._history_restoring = False
        self._pending_robot_drag_snapshot = None
        self._pending_robot_drag_position = None
        self._saved_snapshot = None
        self._pending_world_switch = None
        self._mark_next_snapshot_saved = False
        self._live_panel_hidden = False
        self._pending_deleted_world = None
        self._pending_next_world = None

        self._state_dir = os.path.join(_BASE_DIR, 'worlds')
        os.makedirs(self._state_dir, exist_ok=True)

        self._needs_initial_push = fresh_start

        self.setStyleSheet(
            '''
            QMainWindow { background: #F8F9FA; }
            QLabel { color: #202124; font-size: 14px; }
            QGroupBox {
                font-size: 14px;
                font-weight: 600;
                color: #202124;
                border: none;
                margin-top: 12px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                subcontrol-position: top left;
                padding: 0 4px;
            }
            '''
        )

        central = QWidget()
        self.setCentralWidget(central)

        main_layout = QVBoxLayout(central)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        header = self.build_header()
        main_layout.addWidget(header)

        content_widget = QWidget()
        content_layout = QHBoxLayout(content_widget)
        content_layout.setContentsMargins(12, 12, 12, 12)
        content_layout.setSpacing(12)

        self.left_panel = self.build_left_panel()
        content_layout.addWidget(self.left_panel)

        self.live_panel_toggle_btn = QPushButton('◀')
        self.live_panel_toggle_btn.setFixedSize(28, 64)
        self.live_panel_toggle_btn.setCursor(Qt.PointingHandCursor)
        self.live_panel_toggle_btn.setStyleSheet(
            '''
            QPushButton {
                background: white;
                color: #5F6368;
                border: 1px solid #DADCE0;
                border-radius: 8px;
                font-size: 16px;
                font-weight: 700;
                padding: 0px;
            }
            QPushButton:hover { background: #F8F9FA; }
            QPushButton:pressed { background: #F1F3F4; }
            '''
        )
        self.live_panel_toggle_btn.clicked.connect(self.toggle_live_panel)
        content_layout.addWidget(self.live_panel_toggle_btn, 0, Qt.AlignVCenter)

        right_widget = QWidget()
        right_layout = QVBoxLayout(right_widget)
        right_layout.setContentsMargins(0, 0, 0, 0)
        right_layout.setSpacing(8)

        self.runtime_info_bar = QWidget()
        runtime_info_layout = QHBoxLayout(self.runtime_info_bar)
        runtime_info_layout.setContentsMargins(0, 0, 0, 0)
        runtime_info_layout.setSpacing(10)

        self.status_chip = QLabel('Disconnected')
        self.tool_label = QLabel('Tool: None')

        runtime_info_layout.addWidget(self.status_chip, 0, Qt.AlignLeft)
        runtime_info_layout.addWidget(self.tool_label, 1, Qt.AlignLeft)
        runtime_info_layout.addStretch()

        right_layout.addWidget(self.runtime_info_bar)

        self._grid_outer = QWidget()
        grid_outer = self._grid_outer
        grid_outer.setStyleSheet('background: white;')

        grid_outer_layout = QVBoxLayout(grid_outer)
        grid_outer_layout.setContentsMargins(0, 0, 0, 0)
        grid_outer_layout.setSpacing(0)
        grid_outer_layout.addStretch()

        h_center_container = QWidget()
        h_center_layout = QHBoxLayout(h_center_container)
        h_center_layout.setContentsMargins(0, 0, 0, 0)
        h_center_layout.addStretch()

        grid_container = QWidget()
        grid_container.setStyleSheet('background: transparent;')

        grid_layout = QGridLayout(grid_container)
        grid_layout.setContentsMargins(0, 0, 0, 0)
        grid_layout.setSpacing(4)

        self.scene = GridScene()
        self.view = QGraphicsView(self.scene)
        self.view.setRenderHints(QPainter.Antialiasing | QPainter.SmoothPixmapTransform)
        self.view.setStyleSheet(
            '''
            QGraphicsView {
                border: none;
                background: #E8F0FE;
                padding: 0px;
                margin: 0px;
            }
            '''
        )
        self.view.setFixedSize(world.width * CELL_SIZE + 2, world.height * CELL_SIZE + 2)
        self.view.setContentsMargins(0, 0, 0, 0)
        self.view.setMouseTracking(True)
        self.view.viewport().setMouseTracking(True)
        grid_layout.addWidget(self.view, 0, 0, Qt.AlignTop | Qt.AlignLeft)

        self.v_controls = self.build_v_controls()
        self.v_controls.setFixedWidth(52)
        grid_layout.addWidget(self.v_controls, 0, 1, Qt.AlignVCenter | Qt.AlignLeft)

        self.h_controls = self.build_h_controls()
        grid_layout.addWidget(self.h_controls, 1, 0, Qt.AlignTop | Qt.AlignHCenter)

        h_center_layout.addWidget(grid_container)
        h_center_layout.addStretch()

        grid_outer_layout.addWidget(h_center_container)
        grid_outer_layout.addStretch()

        self._scroll_area = QScrollArea()
        scroll_area = self._scroll_area
        scroll_area.setWidget(grid_outer)
        scroll_area.setWidgetResizable(True)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        scroll_area.setStyleSheet(
            '''
            QScrollArea { border: none; background: white; }
            QScrollBar:vertical {
                border: none;
                background: #F1F3F4;
                width: 10px;
                border-radius: 5px;
            }
            QScrollBar::handle:vertical {
                background: #DADCE0;
                border-radius: 5px;
                min-height: 20px;
            }
            QScrollBar::handle:vertical:hover { background: #BDC1C6; }
            QScrollBar:horizontal {
                border: none;
                background: #F1F3F4;
                height: 10px;
                border-radius: 5px;
            }
            QScrollBar::handle:horizontal {
                background: #DADCE0;
                border-radius: 5px;
                min-width: 20px;
            }
            QScrollBar::handle:horizontal:hover { background: #BDC1C6; }
            QScrollBar::add-line, QScrollBar::sub-line {
                border: none;
                background: none;
            }
            '''
        )

        right_layout.addWidget(scroll_area, 1)

        self._refresh_runtime_widgets()

        content_layout.addWidget(right_widget, 1)
        main_layout.addWidget(content_widget, 1)

        self._current_world = None

        _named_world_loaded = False
        last_world_file = os.path.join(_BASE_DIR, 'worlds', '.last_world')
        last = ''

        if os.path.exists(last_world_file):
            try:
                with open(last_world_file, 'r', encoding='utf-8') as f:
                    last = f.read().strip()
            except Exception:
                last = ''

        if last:
            world_path = os.path.join(_BASE_DIR, 'worlds', f'{last}.world')
            if os.path.exists(world_path):
                self._current_world = last
                _named_world_loaded = True

        self.edit_toggle.setChecked(self.edit_mode)

        load_lang()
        self._apply_lang_direction()
        self._update_lang_buttons()
        self.retranslate_ui()

        prefs = load_prefs()
        if prefs.get('dark_mode'):
            self.apply_dark_mode()

        self.update_ui_for_mode()
        self.update_scene()

        self.file_watcher = QFileSystemWatcher()
        worlds_path = os.path.join(_BASE_DIR, 'worlds')
        if os.path.exists(worlds_path):
            self.file_watcher.addPath(worlds_path)
            self.file_watcher.directoryChanged.connect(self.on_worlds_directory_changed)

        if _named_world_loaded:
            self._needs_initial_push = False

        self._setup_server_hooks()
        self.update_world_list()

        self.undo_shortcut = QShortcut(QKeySequence.Undo, self)
        self.undo_shortcut.activated.connect(self.undo_edit)

        self.redo_shortcut = QShortcut(QKeySequence.Redo, self)
        self.redo_shortcut.activated.connect(self.redo_edit)

        self.redo_shift_shortcut = QShortcut(QKeySequence('Ctrl+Shift+Z'), self)
        self.redo_shift_shortcut.activated.connect(self.redo_edit)

        self._refresh_undo_redo_buttons()

    def on_worlds_directory_changed(self):
        self.update_world_list()

    def _snapshot_signature(self, snapshot):
        if not snapshot:
            return None

        w = snapshot.get('world') or {}
        r = snapshot.get('robot') or {}

        return {
            'world': {
                'width': int(w.get('width', 0)),
                'height': int(w.get('height', 0)),
                'walls': sorted(
                    (int(x), int(y), str(d))
                    for x, y, d in (w.get('walls') or [])
                ),
                'colors': sorted(
                    (int(x), int(y), self._normalize_color_value(c))
                    for x, y, c in (w.get('colors') or [])
                ),
                'temperature': sorted(
                    (int(x), int(y), float(v))
                    for x, y, v in (w.get('temperature') or [])
                ),
                'radiation': sorted(
                    (int(x), int(y), float(v))
                    for x, y, v in (w.get('radiation') or [])
                ),
            },
            'robot': {
                'x': int(r.get('x', 0)),
                'y': int(r.get('y', 0)),
                'direction': str(r.get('direction', 'EAST')).upper(),
                'alive': bool(r.get('alive', True)),
            },
        }

    def _remember_saved_snapshot(self):
        self._saved_snapshot = self._make_snapshot()

    def _has_unsaved_world_changes(self):
        if not self.edit_mode:
            return False

        if self._saved_snapshot is None:
            return False

        return self._snapshot_signature(self._make_snapshot()) != self._snapshot_signature(self._saved_snapshot)

    def _confirm_world_switch_with_unsaved_edits(self):
        box = QMessageBox(self)
        box.setWindowTitle(tr('unsaved_changes_title'))
        box.setText(tr('unsaved_changes_text').format(name=self._current_world or ''))
        box.setIcon(QMessageBox.Warning)
        box.setStyleSheet(self._dialog_style())

        save_button = box.addButton(tr('save'), QMessageBox.AcceptRole)
        dont_save_button = box.addButton(tr('dont_save'), QMessageBox.DestructiveRole)
        cancel_button = box.addButton(tr('cancel'), QMessageBox.RejectRole)
        box.setDefaultButton(save_button)

        box.exec()
        clicked = box.clickedButton()

        if clicked == save_button:
            return 'save'
        if clicked == dont_save_button:
            return 'dont_save'
        if clicked == cancel_button:
            return 'cancel'
        return 'cancel'

    def _confirm_leave_edit_mode_with_unsaved_edits(self):
        box = QMessageBox(self)
        box.setWindowTitle(tr('unsaved_changes_title'))
        box.setText(tr('leave_edit_mode_unsaved_text'))
        box.setIcon(QMessageBox.Warning)
        box.setStyleSheet(self._dialog_style())

        save_button = box.addButton(tr('save'), QMessageBox.AcceptRole)
        dont_save_button = box.addButton(tr('dont_save'), QMessageBox.DestructiveRole)
        cancel_button = box.addButton(tr('cancel'), QMessageBox.RejectRole)
        box.setDefaultButton(save_button)

        box.exec()
        clicked = box.clickedButton()

        if clicked == save_button:
            return 'save'
        if clicked == dont_save_button:
            return 'dont_save'
        if clicked == cancel_button:
            return 'cancel'
        return 'cancel'

    def request_world_switch(self, name):
        name = str(name).strip()
        current = str(getattr(self, '_current_world', '') or '').strip()

        if not name:
            self.update_world_list()
            return

        if name == current:
            self.update_world_list()
            return

        if not self.edit_mode or not self._has_unsaved_world_changes():
            self._pending_world_switch = None
            self.load_world(name)
            return

        action = self._confirm_world_switch_with_unsaved_edits()

        if action == 'cancel':
            self.update_world_list()
            return

        if action == 'dont_save':
            self._pending_world_switch = None
            self.load_world(name)
            return

        self._pending_world_switch = name
        started = self.save_world()

        if not started:
            self._pending_world_switch = None
            self.update_world_list()

    def toggle_edit_mode(self):
        was_edit_mode = self.edit_mode
        next_edit_mode = self.edit_toggle.isChecked()

        if was_edit_mode and not next_edit_mode and self._has_unsaved_world_changes():
            action = self._confirm_leave_edit_mode_with_unsaved_edits()

            if action == 'cancel':
                self.edit_toggle.setChecked(True)
                self.edit_mode = True
                self.update_ui_for_mode()
                self.update_scene()
                return

            if action == 'save':
                if not self.save_world():
                    self.edit_toggle.setChecked(True)
                    self.edit_mode = True
                    self.update_ui_for_mode()
                    self.update_scene()
                    return

        self.edit_mode = next_edit_mode
        self.update_ui_for_mode()

        if self.edit_mode and not was_edit_mode:
            current = getattr(self, '_current_world', None)
            if current:
                self.load_world(current)
                return

        self.update_scene()

    def update_ui_for_mode(self):
        self.edit_actions.setVisible(self.edit_mode)
        self.edit_controls_rest.setVisible(self.edit_mode)

        if hasattr(self, 'world_group'):
            self.world_group.setVisible(not self.edit_mode)

        if hasattr(self, 'edit_world_selection_section'):
            self.edit_world_selection_section.setVisible(self.edit_mode)

        self.h_minus_btn.setVisible(self.edit_mode)
        self.h_plus_btn.setVisible(self.edit_mode)
        self.v_minus_btn.setVisible(self.edit_mode)
        self.v_plus_btn.setVisible(self.edit_mode)

        if self.edit_mode:
            self._live_panel_hidden = False
            if hasattr(self, 'left_panel'):
                self.left_panel.setVisible(True)

        self._update_live_panel_toggle()

        if hasattr(self, 'left_panel'):
            self.left_panel.updateGeometry()

        self._refresh_runtime_widgets()
        self._refresh_undo_redo_buttons()

    def _update_live_panel_toggle(self):
        if not hasattr(self, 'live_panel_toggle_btn'):
            return

        live_mode = not self.edit_mode
        panel_hidden = live_mode and self._live_panel_hidden

        self.live_panel_toggle_btn.setVisible(live_mode)

        if hasattr(self, 'left_panel'):
            self.left_panel.setVisible(not panel_hidden)

        self.live_panel_toggle_btn.setText('▶' if panel_hidden else '◀')

    def toggle_live_panel(self):
        if self.edit_mode:
            self._live_panel_hidden = False
        else:
            self._live_panel_hidden = not self._live_panel_hidden

        self._update_live_panel_toggle()

    def toggle_paint(self, checked=None):
        if hasattr(self, 'paint_toggle'):
            self.paint_enabled = self.paint_toggle.isChecked()
        else:
            self.paint_enabled = bool(checked)

        if self.paint_enabled:
            if hasattr(self, 'temp_button'):
                self.temp_button.setChecked(False)
            if hasattr(self, 'rad_button'):
                self.rad_button.setChecked(False)
            self.temp_enabled = False
            self.rad_enabled = False

        self._refresh_runtime_widgets()

    def toggle_temp_sensor(self, checked):
        self.temp_enabled = checked
        if checked:
            if hasattr(self, 'rad_button'):
                self.rad_button.setChecked(False)
            self.rad_enabled = False

            if hasattr(self, 'paint_toggle'):
                self.paint_toggle.setChecked(False)
            self.paint_enabled = False

        self._refresh_runtime_widgets()

    def toggle_rad_sensor(self, checked):
        self.rad_enabled = checked
        if checked:
            if hasattr(self, 'temp_button'):
                self.temp_button.setChecked(False)
            self.temp_enabled = False

            if hasattr(self, 'paint_toggle'):
                self.paint_toggle.setChecked(False)
            self.paint_enabled = False

        self._refresh_runtime_widgets()

    def toggle_wall_builder(self):
        self.wall_builder_enabled = self.wall_toggle.isChecked()
        self._refresh_runtime_widgets()

    def _normalize_color_value(self, value):
        return value.name() if hasattr(value, 'name') else str(value)

    def _remove_border_walls(self):
        world.walls = {
            (int(x), int(y), str(d))
            for x, y, d in world.walls
            if not (
                    (str(d) in ('v', 'vertical') and int(x) >= world.width - 1)
                    or (str(d) in ('h', 'horizontal') and int(y) >= world.height - 1)
            )
        }

    def _prune_world_state_to_bounds(self):
        world.walls = {
            (int(x), int(y), str(d))
            for x, y, d in world.walls
            if 0 <= int(x) < world.width
               and 0 <= int(y) < world.height
               and not (
                    (str(d) in ('v', 'vertical') and int(x) >= world.width - 1)
                    or (str(d) in ('h', 'horizontal') and int(y) >= world.height - 1)
            )
        }
        world.colors = {
            (int(x), int(y)): self._normalize_color_value(c)
            for (x, y), c in world.colors.items()
            if 0 <= int(x) < world.width and 0 <= int(y) < world.height
        }
        world.temperature = {
            (int(x), int(y)): float(v)
            for (x, y), v in world.temperature.items()
            if 0 <= int(x) < world.width and 0 <= int(y) < world.height
        }
        world.radiation = {
            (int(x), int(y)): float(v)
            for (x, y), v in world.radiation.items()
            if 0 <= int(x) < world.width and 0 <= int(y) < world.height
        }
        world.discovered_sensors = {
            (int(x), int(y))
            for x, y in world.discovered_sensors
            if 0 <= int(x) < world.width and 0 <= int(y) < world.height
        }
        world.discovered_colors = {
            (int(x), int(y))
            for x, y in world.discovered_colors
            if 0 <= int(x) < world.width and 0 <= int(y) < world.height
        }

    def adjust_grid_dimension(self, dim, delta):
        changed = False

        self._remove_border_walls()

        if dim == 'h':
            old_width = world.width
            new_width = max(1, min(30, world.width + delta))
            if old_width != new_width:
                if robot.x >= new_width:
                    robot.x = new_width - 1
                world.width = new_width
                changed = True
        else:
            old_height = world.height
            new_height = max(1, min(30, world.height + delta))
            if old_height != new_height:
                if robot.y >= new_height:
                    robot.y = new_height - 1
                world.height = new_height
                changed = True

        if not changed:
            return

        self._prune_world_state_to_bounds()
        self.update_scene()
        self._save_local_state()
        self._push_state_to_server()

    def _do_rebuild(self):
        self.scene.rebuild()
        self.view.viewport().update()

    def update_scene(self):
        if threading.current_thread() is not threading.main_thread():
            self._rebuild_signal.emit()
            return

        try:
            self.scene.rebuild()
            self.view.viewport().update()

            self.h_value_label.setText(f'{world.width}')
            self.v_value_label.setText(f'{world.height}')

            self.view.setFixedSize(world.width * CELL_SIZE + 2, world.height * CELL_SIZE + 2)
            self.h_controls.setFixedWidth(max(world.width * CELL_SIZE, 152))
            self.h_controls.updateGeometry()

        except Exception as e:
            print(f'Error updating scene: {e}')

    def _make_snapshot(self):
        return {
            'world': {
                'width': world.width,
                'height': world.height,
                'walls': [[x, y, d] for (x, y, d) in world.walls],
                'colors': [
                    [x, y, c.name() if hasattr(c, 'name') else str(c)]
                    for (x, y), c in world.colors.items()
                ],
                'temperature': [[x, y, v] for (x, y), v in world.temperature.items()],
                'radiation': [[x, y, v] for (x, y), v in world.radiation.items()],
            },
            'robot': {
                'x': robot.x,
                'y': robot.y,
                'direction': robot.direction,
                'alive': robot.alive,
            },
        }

    def _make_history_snapshot(self):
        return {
            'world': {
                'walls': sorted(
                    [int(x), int(y), str(d)]
                    for x, y, d in world.walls
                    if 0 <= int(x) < world.width and 0 <= int(y) < world.height
                ),
                'colors': sorted(
                    [int(x), int(y), self._normalize_color_value(c)]
                    for (x, y), c in world.colors.items()
                    if 0 <= int(x) < world.width and 0 <= int(y) < world.height
                ),
                'temperature': sorted(
                    [int(x), int(y), float(v)]
                    for (x, y), v in world.temperature.items()
                    if 0 <= int(x) < world.width and 0 <= int(y) < world.height
                ),
                'radiation': sorted(
                    [int(x), int(y), float(v)]
                    for (x, y), v in world.radiation.items()
                    if 0 <= int(x) < world.width and 0 <= int(y) < world.height
                ),
            }
        }

    def _history_snapshot_signature(self, snapshot):
        if not snapshot:
            return None

        w = snapshot.get('world') or {}
        return {
            'world': {
                'walls': sorted(
                    (int(x), int(y), str(d))
                    for x, y, d in (w.get('walls') or [])
                    if 0 <= int(x) < world.width and 0 <= int(y) < world.height
                ),
                'colors': sorted(
                    (int(x), int(y), self._normalize_color_value(c))
                    for x, y, c in (w.get('colors') or [])
                    if 0 <= int(x) < world.width and 0 <= int(y) < world.height
                ),
                'temperature': sorted(
                    (int(x), int(y), float(v))
                    for x, y, v in (w.get('temperature') or [])
                    if 0 <= int(x) < world.width and 0 <= int(y) < world.height
                ),
                'radiation': sorted(
                    (int(x), int(y), float(v))
                    for x, y, v in (w.get('radiation') or [])
                    if 0 <= int(x) < world.width and 0 <= int(y) < world.height
                ),
            }
        }

    def _restore_history_snapshot(self, snapshot):
        if not snapshot:
            return

        self._history_restoring = True
        try:
            w = snapshot.get('world') or {}

            world.walls = {
                (int(x), int(y), str(d))
                for x, y, d in (w.get('walls') or [])
                if 0 <= int(x) < world.width and 0 <= int(y) < world.height
            }
            world.colors = {
                (int(x), int(y)): self._normalize_color_value(c)
                for x, y, c in (w.get('colors') or [])
                if 0 <= int(x) < world.width and 0 <= int(y) < world.height
            }
            world.temperature = {
                (int(x), int(y)): float(v)
                for x, y, v in (w.get('temperature') or [])
                if 0 <= int(x) < world.width and 0 <= int(y) < world.height
            }
            world.radiation = {
                (int(x), int(y)): float(v)
                for x, y, v in (w.get('radiation') or [])
                if 0 <= int(x) < world.width and 0 <= int(y) < world.height
            }

            self._prune_world_state_to_bounds()
        finally:
            self._history_restoring = False

        self.update_scene()
        self._save_local_state()
        self._push_state_to_server()
        self._refresh_runtime_widgets()
        self._refresh_undo_redo_buttons()

    def _push_undo_snapshot(self, snapshot=None):
        if self._history_restoring or not self.edit_mode:
            return

        if snapshot is None:
            snapshot = self._make_history_snapshot()

        signature = self._history_snapshot_signature(snapshot)
        if self._undo_stack:
            previous = self._history_snapshot_signature(self._undo_stack[-1])
            if signature == previous:
                return

        self._undo_stack.append(snapshot)
        if len(self._undo_stack) > self._history_limit:
            self._undo_stack = self._undo_stack[-self._history_limit:]

        self._redo_stack.clear()
        self._refresh_undo_redo_buttons()

    def _refresh_undo_redo_buttons(self):
        can_edit_history = self.edit_mode and not getattr(self, '_program_running', False)

        if hasattr(self, 'undo_btn'):
            self.undo_btn.setEnabled(can_edit_history and bool(self._undo_stack))
        if hasattr(self, 'redo_btn'):
            self.redo_btn.setEnabled(can_edit_history and bool(self._redo_stack))

    def _begin_robot_drag_history(self):
        self._pending_robot_drag_position = (robot.x, robot.y)

    def _end_robot_drag_history(self):
        start_pos = self._pending_robot_drag_position
        self._pending_robot_drag_snapshot = None
        self._pending_robot_drag_position = None

        if start_pos is None:
            return

        if start_pos == (robot.x, robot.y):
            return

        self._save_local_state()
        self._push_state_to_server()
        self._refresh_undo_redo_buttons()

    def undo_edit(self):
        if not self.edit_mode or getattr(self, '_program_running', False):
            return
        if not self._undo_stack:
            return

        self._redo_stack.append(self._make_history_snapshot())
        if len(self._redo_stack) > self._history_limit:
            self._redo_stack = self._redo_stack[-self._history_limit:]

        snapshot = self._undo_stack.pop()
        self._restore_history_snapshot(snapshot)

    def redo_edit(self):
        if not self.edit_mode or getattr(self, '_program_running', False):
            return
        if not self._redo_stack:
            return

        self._undo_stack.append(self._make_history_snapshot())
        if len(self._undo_stack) > self._history_limit:
            self._undo_stack = self._undo_stack[-self._history_limit:]

        snapshot = self._redo_stack.pop()
        self._restore_history_snapshot(snapshot)

    def _tool_summary(self):
        if not self.edit_mode and getattr(self, '_program_running', False):
            return tr('tool_running')

        active = []
        if self.paint_enabled:
            active.append(tr('tool_paint'))
        if self.wall_builder_enabled:
            active.append(tr('tool_wall'))
        if self.temp_enabled:
            active.append(tr('tool_temperature'))
        if self.rad_enabled:
            active.append(tr('tool_radiation'))

        if not active:
            return tr('tool_none')

        return tr('tool_prefix') + ' + '.join(active)

    def _status_summary(self):
        if getattr(self, '_program_running', False):
            return tr('status_running'), 'running'
        if getattr(self, '_server_ws', None) is None:
            return tr('status_disconnected'), 'disconnected'
        if self.edit_mode:
            return tr('status_editing'), 'editing'
        return tr('status_connected'), 'connected'

    def _refresh_runtime_widgets(self):
        if not hasattr(self, 'status_chip') or not hasattr(self, 'tool_label'):
            return

        status_text, status_kind = self._status_summary()
        self.status_chip.setText(status_text)
        self.tool_label.setText(self._tool_summary())

        if self.is_dark_mode:
            chip_styles = {
                'editing': ('#1A3A5C', '#1E88E5', '#90CAF9'),
                'running': ('#1F3324', '#2E7D32', '#A5D6A7'),
                'connected': ('#2A2A2A', '#444444', '#E0E0E0'),
                'disconnected': ('#3A1F1F', '#8B2E2E', '#FFB3B3'),
            }
            tool_style = '''
                QLabel {
                    color: #E0E0E0;
                    background: transparent;
                    font-size: 13px;
                    font-weight: 600;
                    padding: 6px 8px;
                }
            '''
        else:
            chip_styles = {
                'editing': ('#E8F0FE', '#D2E3FC', '#1967D2'),
                'running': ('#E6F4EA', '#CEEAD6', '#188038'),
                'connected': ('#F1F3F4', '#DADCE0', '#3C4043'),
                'disconnected': ('#FCE8E6', '#FAD2CF', '#D93025'),
            }
            tool_style = '''
                QLabel {
                    color: #3C4043;
                    background: transparent;
                    font-size: 13px;
                    font-weight: 600;
                    padding: 6px 8px;
                }
            '''

        bg, border, fg = chip_styles[status_kind]
        self.status_chip.setStyleSheet(
            f'''
            QLabel {{
                background: {bg};
                color: {fg};
                border: 1px solid {border};
                border-radius: 12px;
                font-size: 13px;
                font-weight: 700;
                padding: 6px 12px;
            }}
            '''
        )
        self.tool_label.setStyleSheet(tool_style)

    def show_about_dialog(self):
        dialog = QDialog(self)
        dialog.setWindowTitle(tr('about_title'))
        dialog.setModal(True)
        dialog.resize(760, 560)
        dialog.setMinimumSize(560, 420)

        if self.is_dark_mode:
            dialog.setStyleSheet(
                '''
                QDialog {
                    background: #202124;
                    color: #E8EAED;
                }
                QTextBrowser {
                    background: #202124;
                    color: #E8EAED;
                    border: none;
                    padding: 8px;
                    font-size: 14px;
                }
                QScrollBar:vertical {
                    border: none;
                    background: transparent;
                    width: 10px;
                    margin: 4px 0 4px 0;
                }
                QScrollBar::handle:vertical {
                    background: #4A4A4A;
                    border-radius: 5px;
                    min-height: 40px;
                }
                QScrollBar::handle:vertical:hover {
                    background: #5A5A5A;
                }
                QScrollBar::add-line:vertical,
                QScrollBar::sub-line:vertical {
                    height: 0px;
                    background: none;
                    border: none;
                }
                QScrollBar::add-page:vertical,
                QScrollBar::sub-page:vertical {
                    background: transparent;
                }
                QPushButton {
                    background: #2A2A2A;
                    color: #E8EAED;
                    border: 1px solid #5F6368;
                    border-radius: 6px;
                    padding: 6px 16px;
                    min-width: 84px;
                }
                QPushButton:hover {
                    background: #3A3A3A;
                }
                '''
            )
        else:
            dialog.setStyleSheet(
                '''
                QDialog {
                    background: #FFFFFF;
                    color: #202124;
                }
                QTextBrowser {
                    background: #FFFFFF;
                    color: #202124;
                    border: none;
                    padding: 8px;
                    font-size: 14px;
                }
                QScrollBar:vertical {
                    border: none;
                    background: transparent;
                    width: 10px;
                    margin: 4px 0 4px 0;
                }
                QScrollBar::handle:vertical {
                    background: #C2C6CC;
                    border-radius: 5px;
                    min-height: 40px;
                }
                QScrollBar::handle:vertical:hover {
                    background: #AEB4BC;
                }
                QScrollBar::add-line:vertical,
                QScrollBar::sub-line:vertical {
                    height: 0px;
                    background: none;
                    border: none;
                }
                QScrollBar::add-page:vertical,
                QScrollBar::sub-page:vertical {
                    background: transparent;
                }
                QPushButton {
                    background: #FFFFFF;
                    color: #202124;
                    border: 1px solid #DADCE0;
                    border-radius: 6px;
                    padding: 6px 16px;
                    min-width: 84px;
                }
                QPushButton:hover {
                    background: #F8F9FA;
                }
                '''
            )

        layout = QVBoxLayout(dialog)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(12)

        text = QTextBrowser(dialog)
        text.setReadOnly(True)
        text.setOpenExternalLinks(False)
        text.setPlainText(tr('about_text'))
        layout.addWidget(text, 1)

        buttons = QDialogButtonBox(QDialogButtonBox.Ok, parent=dialog)
        buttons.accepted.connect(dialog.accept)
        layout.addWidget(buttons)

        dialog.exec()

    def switch_lang(self, lang):
        _lang.set_lang(lang)
        _lang.save_lang()
        self._apply_lang_direction()
        self._update_lang_buttons()
        self.retranslate_ui()

    def _on_lang_combo_changed(self, _index):
        if not hasattr(self, 'lang_combo'):
            return

        lang = self.lang_combo.currentData()
        if lang:
            self.switch_lang(str(lang))

    def _apply_lang_direction(self):
        direction = Qt.RightToLeft if _lang.LANG == 'AR' else Qt.LeftToRight
        self.setLayoutDirection(direction)

        if hasattr(self, 'left_panel'):
            self.left_panel.setLayoutDirection(direction)
        if hasattr(self, 'runtime_info_bar'):
            self.runtime_info_bar.setLayoutDirection(direction)
        if hasattr(self, '_grid_outer'):
            self._grid_outer.setLayoutDirection(Qt.LeftToRight)
        if hasattr(self, 'temp_button'):
            self.temp_button.setLayoutDirection(direction)
        if hasattr(self, 'rad_button'):
            self.rad_button.setLayoutDirection(direction)

    def _update_lang_buttons(self):
        if hasattr(self, 'lang_label'):
            fg = '#E0E0E0' if self.is_dark_mode else '#5F6368'
            self.lang_label.setText(tr('language'))
            self.lang_label.setStyleSheet(f'''
                font-size: 13px;
                font-weight: 700;
                color: {fg};
                background: transparent;
            ''')

        if hasattr(self, 'lang_combo'):
            if self.is_dark_mode:
                self.lang_combo.setStyleSheet(
                    '''
                    QComboBox {
                        background: rgba(66, 133, 244, 0.16);
                        color: #E8F0FE;
                        border: 2px solid #4285F4;
                        border-radius: 8px;
                        padding: 4px 10px;
                        font-size: 12px;
                        font-weight: 800;
                    }
                    QComboBox:hover {
                        background: rgba(66, 133, 244, 0.22);
                    }
                    QComboBox::drop-down {
                        border: none;
                        width: 22px;
                    }
                    QComboBox QAbstractItemView {
                        border: 1px solid #4285F4;
                        background: #1E1E1E;
                        color: #E0E0E0;
                        selection-background-color: #4285F4;
                        selection-color: white;
                        font-size: 12px;
                        font-weight: 700;
                    }
                    '''
                )
            else:
                self.lang_combo.setStyleSheet(
                    '''
                    QComboBox {
                        background: #E8F0FE;
                        color: #1967D2;
                        border: 2px solid #4285F4;
                        border-radius: 8px;
                        padding: 4px 10px;
                        font-size: 12px;
                        font-weight: 800;
                    }
                    QComboBox:hover {
                        background: #DCE8FD;
                    }
                    QComboBox::drop-down {
                        border: none;
                        width: 22px;
                    }
                    QComboBox QAbstractItemView {
                        border: 1px solid #4285F4;
                        background: white;
                        color: #202124;
                        selection-background-color: #4285F4;
                        selection-color: white;
                        font-size: 12px;
                        font-weight: 700;
                    }
                    '''
                )

            index = self.lang_combo.findData(_lang.LANG)
            if index >= 0 and self.lang_combo.currentIndex() != index:
                self.lang_combo.blockSignals(True)
                self.lang_combo.setCurrentIndex(index)
                self.lang_combo.blockSignals(False)

    def retranslate_ui(self):
        if hasattr(self, '_lbl_edit_mode'):
            self._lbl_edit_mode.setText(tr('edit_mode'))
        if hasattr(self, '_logo_label'):
            self._logo_label.setToolTip(tr('about_title'))
        if hasattr(self, '_title_label'):
            self._title_label.setToolTip(tr('about_title'))

        self._update_lang_buttons()

        if hasattr(self, '_lbl_actions'):
            self._lbl_actions.setText(tr('actions'))
        if hasattr(self, '_btn_save'):
            self._btn_save.setText('💾  ' + tr('save'))
        if hasattr(self, '_btn_load'):
            self._btn_load.setText('📁  ' + tr('load'))
        if hasattr(self, 'undo_btn'):
            self.undo_btn.setText(tr('undo'))
        if hasattr(self, 'redo_btn'):
            self.redo_btn.setText(tr('redo'))

        if hasattr(self, '_lbl_paint_tools'):
            self._lbl_paint_tools.setText(tr('paint_tools'))
        if hasattr(self, '_lbl_paint_action'):
            self._lbl_paint_action.setText(tr('paint'))
        if hasattr(self, '_lbl_selected_color'):
            self._lbl_selected_color.setText(tr('selected_color'))
        if hasattr(self, '_lbl_preset_colors'):
            self._lbl_preset_colors.setText(tr('preset_colors'))
        if hasattr(self, '_lbl_wall_builder'):
            self._lbl_wall_builder.setText(tr('wall_builder'))
        if hasattr(self, '_lbl_sensors'):
            self._lbl_sensors.setText(tr('sensors'))
        if hasattr(self, 'temp_button'):
            self.temp_button.setText('🌡 ' + tr('temperature'))
        if hasattr(self, 'rad_button'):
            self.rad_button.setText('☢ ' + tr('radiation'))

        if hasattr(self, '_lbl_world_selection'):
            self._lbl_world_selection.setText(tr('world_selection'))
        if hasattr(self, '_lbl_edit_world_selection'):
            self._lbl_edit_world_selection.setText(tr('world_selection'))

        if hasattr(self, 'color_combo'):
            self._rebuild_color_combo()

        self._refresh_runtime_widgets()

    def get_selected_color_name(self):
        if not hasattr(self, 'color_combo'):
            return 'green'

        value = self.color_combo.currentData(Qt.UserRole)
        return str(value or 'green')

    def get_selected_color_hex(self):
        if not hasattr(self, 'color_combo'):
            return '#43A047'

        value = self.color_combo.currentData(Qt.UserRole + 1)
        return str(value or '#43A047')

    def _rebuild_color_combo(self):
        if not hasattr(self, 'color_combo'):
            return

        current_name = self.get_selected_color_name() if self.color_combo.count() else 'red'

        presets = [
            ('red', '#E53935', tr('color_red')),
            ('orange', '#FB8C00', tr('color_orange')),
            ('yellow', '#FDD835', tr('color_yellow')),
            ('green', '#43A047', tr('color_green')),
            ('blue', '#1E88E5', tr('color_blue')),
            ('purple', '#8E24AA', tr('color_purple')),
            ('black', '#212121', tr('color_black')),
        ]

        self.color_combo.blockSignals(True)
        self.color_combo.clear()

        for name, hex_color, label in presets:
            self.color_combo.addItem(label)
            idx = self.color_combo.count() - 1
            self.color_combo.setItemData(idx, name, Qt.UserRole)
            self.color_combo.setItemData(idx, hex_color, Qt.UserRole + 1)
            self.color_combo.setItemData(idx, QColor(hex_color), Qt.DecorationRole)

        index = self.color_combo.findData(current_name, Qt.UserRole)
        if index < 0:
            index = 0

        self.color_combo.setCurrentIndex(index)
        self.color_combo.blockSignals(False)

        self._sync_color_preview()

    def _sync_color_preview(self):
        color_name = self.get_selected_color_name()
        hex_color = self.get_selected_color_hex()

        if hasattr(self, 'scene'):
            self.scene.paint_color = QColor(hex_color)

        if hasattr(self, 'color_name_label'):
            fg = '#E0E0E0' if self.is_dark_mode else '#202124'
            self.color_name_label.setText(tr(f'color_{color_name}'))
            self.color_name_label.setStyleSheet(
                f'''
                font-size: 15px;
                font-weight: 700;
                color: {fg};
                background: transparent;
                font-family: 'Segoe UI', Arial, sans-serif;
                '''
            )

        if hasattr(self, 'color_preview'):
            border = '#444444' if self.is_dark_mode else '#DADCE0'
            self.color_preview.setStyleSheet(
                f'''
                QLabel {{
                    border: 1px solid {border};
                    border-radius: 8px;
                    background: {hex_color};
                }}
                '''
            )

    def _on_color_combo_changed(self, _value=None):
        self._sync_color_preview()

    def _push_state_to_server(self):
        snap = self._make_snapshot()
        self.send_to_server({'type': 'client_snapshot', 'snapshot': snap})

    def closeEvent(self, event):
        if getattr(self, '_program_running', False):
            event.ignore()
            return

        try:
            self._shutdown_server_hooks()
        except Exception:
            pass

        event.accept()
        super().closeEvent(event)