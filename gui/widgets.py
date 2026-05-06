from PySide6.QtCore import Qt
from PySide6.QtGui import QBrush, QColor, QFont, QPainter, QPen
from PySide6.QtWidgets import (
    QApplication, QGraphicsEllipseItem, QGraphicsRectItem,
    QGraphicsScene, QHBoxLayout, QLabel, QPushButton, QWidget,
)

from ._globals import CELL_SIZE, robot, world

SENSOR_TEXT_FONT = QFont('Segoe UI', 10)


def _main_window():
    app = QApplication.instance()
    return getattr(app, 'mainwin', None) if app else None


class RobotItem(QGraphicsEllipseItem):
    def __init__(self):
        super().__init__(-20, -20, 40, 40)
        self.setZValue(100)
        self.setCursor(Qt.PointingHandCursor)

    def paint(self, p, option, widget=None):
        p.setRenderHint(QPainter.Antialiasing, False)

        s = 2

        def draw(col, row, color, w=1, h=1):
            p.fillRect(-20 + col * s, -20 + row * s, s * w, s * h, QColor(color))

        if robot.alive:
            palette = {
                'outline': '#4E5663',
                'side': '#6D7582',
                'body': '#8D96A4',
                'light': '#BAC3CF',
                'face': '#D9E0E8',
                'gold': '#C9A34A',
                'eye_ring': '#F3C37C',
                'eye_core': '#DB7B1D',
                'grille': '#5B6370',
                'antenna': '#7A625C',
                'antenna_tip': '#E4A11F',
                'foot': '#59616D',
            }
        else:
            palette = {
                'outline': '#701F1F',
                'side': '#8E3333',
                'body': '#B34747',
                'light': '#D96A6A',
                'face': '#E18A8A',
                'gold': '#F0A36B',
                'eye_ring': '#FFC38F',
                'eye_core': '#FFE1C5',
                'grille': '#7C2626',
                'antenna': '#8A4545',
                'antenna_tip': '#FF8A65',
                'foot': '#672A2A',
            }

        draw(9, 0, palette['antenna_tip'], 2, 2)
        draw(9, 2, palette['antenna'], 2, 2)
        draw(9, 4, palette['antenna'], 2, 1)

        draw(1, 7, palette['side'], 2, 4)
        draw(17, 7, palette['side'], 2, 4)

        draw(6, 4, palette['outline'], 8, 1)
        draw(4, 5, palette['outline'], 12, 1)
        for row in range(6, 14):
            draw(3, row, palette['outline'], 14, 1)
        draw(4, 14, palette['outline'], 12, 1)
        draw(6, 15, palette['outline'], 8, 1)

        draw(7, 5, palette['body'], 6, 1)
        draw(5, 6, palette['light'], 10, 1)
        for row in range(7, 13):
            draw(4, row, palette['body'], 12, 1)
        draw(5, 13, palette['body'], 10, 1)
        draw(7, 14, palette['body'], 6, 1)

        draw(4, 7, palette['side'], 1, 6)
        draw(15, 7, palette['side'], 1, 6)
        draw(5, 7, palette['face'], 10, 5)
        draw(6, 7, palette['light'], 4, 1)
        draw(9, 6, palette['gold'], 2, 1)
        draw(9, 7, palette['gold'], 2, 1)

        draw(6, 8, palette['eye_ring'], 3, 3)
        draw(11, 8, palette['eye_ring'], 3, 3)
        draw(7, 9, palette['eye_core'], 1, 1)
        draw(12, 9, palette['eye_core'], 1, 1)

        draw(7, 12, palette['grille'], 6, 1)
        draw(7, 12, palette['grille'], 1, 2)
        draw(9, 12, palette['grille'], 1, 2)
        draw(11, 12, palette['grille'], 1, 2)
        draw(12, 12, palette['grille'], 1, 2)

        draw(6, 16, palette['side'], 3, 2)
        draw(11, 16, palette['side'], 3, 2)
        draw(5, 18, palette['foot'], 4, 1)
        draw(11, 18, palette['foot'], 4, 1)

        if robot.direction == 'NORTH':
            draw(9, 5, palette['antenna_tip'], 2, 1)
        elif robot.direction == 'SOUTH':
            draw(9, 15, palette['antenna_tip'], 2, 1)
        elif robot.direction == 'EAST':
            draw(14, 9, palette['antenna_tip'], 1, 2)
        elif robot.direction == 'WEST':
            draw(5, 9, palette['antenna_tip'], 1, 2)

    def mousePressEvent(self, event):
        gw = _main_window()
        if gw and gw.edit_mode and hasattr(gw, '_begin_robot_drag_history'):
            gw._begin_robot_drag_history()
        event.accept()

    def mouseMoveEvent(self, event):
        gw = _main_window()
        if gw and gw.edit_mode:
            p = event.scenePos()
            x = int(p.x() // CELL_SIZE)
            y = int(p.y() // CELL_SIZE)
            if 0 <= x < world.width and 0 <= y < world.height:
                robot.x, robot.y = x, y
                robot.alive = True
                gw.scene.rebuild()
        event.accept()

    def mouseReleaseEvent(self, event):
        gw = _main_window()
        if gw and gw.edit_mode:
            if hasattr(gw, '_end_robot_drag_history'):
                gw._end_robot_drag_history()
            else:
                gw._save_local_state()
                gw._push_state_to_server()
        event.accept()


class GridScene(QGraphicsScene):
    def __init__(self):
        super().__init__()
        self.paint_color = QColor('#4CAF50')
        self.robot_item = RobotItem()
        self.hover_cell = None
        self.selected_cell = None
        self.hover_wall = None
        self.hit_wall = None
        self._dark = False
        self.rebuild()

    def _cell_in_bounds(self, cell):
        if cell is None:
            return False

        x, y = cell
        return 0 <= x < world.width and 0 <= y < world.height

    def _cell_from_scene_pos(self, p):
        x = int(p.x() // CELL_SIZE)
        y = int(p.y() // CELL_SIZE)
        if 0 <= x < world.width and 0 <= y < world.height:
            return x, y
        return None

    def _wall_from_scene_pos(self, p):
        cell = self._cell_from_scene_pos(p)
        if cell is None:
            return None

        x, y = cell
        px = p.x() % CELL_SIZE
        py = p.y() % CELL_SIZE

        wall_x, wall_y, wall_dir = None, None, None

        if px < 15:
            wall_x, wall_y, wall_dir = x - 1, y, 'v'
        elif px > CELL_SIZE - 15:
            wall_x, wall_y, wall_dir = x, y, 'v'
        elif py < 15:
            wall_x, wall_y, wall_dir = x, y - 1, 'h'
        elif py > CELL_SIZE - 15:
            wall_x, wall_y, wall_dir = x, y, 'h'

        if wall_x is None:
            return None

        if not (0 <= wall_x < world.width and 0 <= wall_y < world.height):
            return None

        if wall_dir == 'v' and wall_x >= world.width - 1:
            return None

        if wall_dir == 'h' and wall_y >= world.height - 1:
            return None

        return wall_x, wall_y, wall_dir

    def _add_wall_line(self, x, y, d, pen):
        if d in ['h', 'horizontal']:
            self.addLine(
                x * CELL_SIZE,
                (y + 1) * CELL_SIZE,
                (x + 1) * CELL_SIZE,
                (y + 1) * CELL_SIZE,
                pen,
            )
        else:
            self.addLine(
                (x + 1) * CELL_SIZE,
                y * CELL_SIZE,
                (x + 1) * CELL_SIZE,
                (y + 1) * CELL_SIZE,
                pen,
            )

    def _add_crash_marker(self, x, y, d, dark):
        if d in ['h', 'horizontal']:
            cx = x * CELL_SIZE + CELL_SIZE / 2
            cy = (y + 1) * CELL_SIZE
        else:
            cx = (x + 1) * CELL_SIZE
            cy = y * CELL_SIZE + CELL_SIZE / 2

        glow_color = QColor('#FF8A80' if dark else '#F28B82')
        glow_color.setAlpha(110 if dark else 90)
        glow_pen = QPen(glow_color, 8, Qt.SolidLine, Qt.RoundCap)

        x_color = QColor('#FF5252' if dark else '#D93025')
        x_pen = QPen(x_color, 4, Qt.SolidLine, Qt.RoundCap)

        size = 10

        self.addLine(cx - size, cy - size, cx + size, cy + size, glow_pen)
        self.addLine(cx - size, cy + size, cx + size, cy - size, glow_pen)

        self.addLine(cx - size, cy - size, cx + size, cy + size, x_pen)
        self.addLine(cx - size, cy + size, cx + size, cy - size, x_pen)

    def _add_preview_wall(self, x, y, d, dark):
        glow_color = QColor('#FFD54F' if dark else '#FFB300')
        glow_color.setAlpha(90 if dark else 70)
        glow_pen = QPen(glow_color, 10, Qt.SolidLine, Qt.RoundCap)
        self._add_wall_line(x, y, d, glow_pen)

        line_color = QColor('#FFF176' if dark else '#FB8C00')
        line_pen = QPen(line_color, 4, Qt.DashLine, Qt.RoundCap)
        self._add_wall_line(x, y, d, line_pen)

        dot_brush = QBrush(QColor('#FFF176' if dark else '#FB8C00'))
        dot_pen = QPen(QColor('#5F4300' if dark else '#C66900'), 1)
        r = 4

        if d in ['h', 'horizontal']:
            y0 = (y + 1) * CELL_SIZE
            x1 = x * CELL_SIZE
            x2 = (x + 1) * CELL_SIZE
            self.addEllipse(x1 - r, y0 - r, r * 2, r * 2, dot_pen, dot_brush)
            self.addEllipse(x2 - r, y0 - r, r * 2, r * 2, dot_pen, dot_brush)
        else:
            x0 = (x + 1) * CELL_SIZE
            y1 = y * CELL_SIZE
            y2 = (y + 1) * CELL_SIZE
            self.addEllipse(x0 - r, y1 - r, r * 2, r * 2, dot_pen, dot_brush)
            self.addEllipse(x0 - r, y2 - r, r * 2, r * 2, dot_pen, dot_brush)

    def _add_sensor_text(self, x, y, text, color, y_offset):
        item = self.addText(text, SENSOR_TEXT_FONT)
        item.setDefaultTextColor(QColor(color))
        item.setPos(x * CELL_SIZE + 4, y * CELL_SIZE + y_offset)

    def _push_undo_if_available(self, gw):
        if hasattr(gw, '_push_undo_snapshot'):
            gw._push_undo_snapshot()

    def _commit_edit_change(self, gw):
        self.rebuild()
        gw._save_local_state()
        gw._push_state_to_server()

    def rebuild(self):
        gw = _main_window()

        items_to_remove = [item for item in self.items() if item != self.robot_item]
        for item in items_to_remove:
            self.removeItem(item)

        if self.robot_item not in self.items():
            self.addItem(self.robot_item)

        sw = world.width * CELL_SIZE
        sh = world.height * CELL_SIZE
        self.setSceneRect(0, 0, sw, sh)

        dark = getattr(self, '_dark', False)
        bg_color = '#141414' if dark else '#FFFFFF'
        grid_color = '#2A2A2A' if dark else '#E0E0E0'
        self.setBackgroundBrush(QBrush(QColor(bg_color)))

        pen = QPen(QColor(grid_color), 1)
        border_pen = QPen(QColor('#555555') if dark else QColor('#222222'), 3)

        for i in range(world.width + 1):
            x = i * CELL_SIZE
            current_pen = border_pen if i == 0 or i == world.width else pen
            self.addLine(x, 0, x, sh, current_pen)

        for j in range(world.height + 1):
            y = j * CELL_SIZE
            current_pen = border_pen if j == 0 or j == world.height else pen
            self.addLine(0, y, sw, y, current_pen)

        show_all_colors = bool(gw and gw.edit_mode)
        discovered_colors = getattr(world, 'discovered_colors', set())

        for (cx, cy), color in world.colors.items():
            if not show_all_colors and (cx, cy) not in discovered_colors:
                continue

            rect = QGraphicsRectItem(cx * CELL_SIZE, cy * CELL_SIZE, CELL_SIZE, CELL_SIZE)
            color_val = QColor(color) if isinstance(color, str) else color
            rect.setBrush(QBrush(color_val))
            rect.setOpacity(0.4)
            rect.setPen(Qt.NoPen)
            self.addItem(rect)

        if self._cell_in_bounds(self.selected_cell):
            sx, sy = self.selected_cell
            selected_rect = QGraphicsRectItem(
                sx * CELL_SIZE + 2,
                sy * CELL_SIZE + 2,
                CELL_SIZE - 4,
                CELL_SIZE - 4,
            )
            selected_fill = QColor('#4285F4' if not dark else '#90CAF9')
            selected_fill.setAlpha(45 if not dark else 35)
            selected_pen = QPen(QColor('#4285F4' if not dark else '#90CAF9'), 3)
            selected_rect.setBrush(QBrush(selected_fill))
            selected_rect.setPen(selected_pen)
            selected_rect.setZValue(2)
            self.addItem(selected_rect)

        if self._cell_in_bounds(self.hover_cell) and self.hover_cell != self.selected_cell:
            hx, hy = self.hover_cell
            hover_rect = QGraphicsRectItem(
                hx * CELL_SIZE + 4,
                hy * CELL_SIZE + 4,
                CELL_SIZE - 8,
                CELL_SIZE - 8,
            )
            hover_fill = QColor('#1E88E5' if not dark else '#B3E5FC')
            hover_fill.setAlpha(25 if not dark else 20)
            hover_pen = QPen(QColor('#1E88E5' if not dark else '#B3E5FC'), 2, Qt.DashLine)
            hover_rect.setBrush(QBrush(hover_fill))
            hover_rect.setPen(hover_pen)
            hover_rect.setZValue(1.5)
            self.addItem(hover_rect)

        wall_pen = QPen(
            QColor('#AAAAAA') if dark else QColor('#000000'),
            4,
            Qt.SolidLine,
            Qt.FlatCap,
        )
        for x, y, d in world.walls:
            self._add_wall_line(x, y, d, wall_pen)

        if self.hit_wall is not None:
            hx, hy, hd = self.hit_wall
            hit_pen = QPen(
                QColor('#FF6F61') if dark else QColor('#D93025'),
                6,
                Qt.SolidLine,
                Qt.RoundCap,
            )
            self._add_wall_line(hx, hy, hd, hit_pen)
            self._add_crash_marker(hx, hy, hd, dark)

        if gw and gw.edit_mode and gw.wall_builder_enabled and self.hover_wall is not None:
            wx, wy, wd = self.hover_wall
            self._add_preview_wall(wx, wy, wd, dark)

        if gw and gw.edit_mode:
            for (cx, cy), temp in world.temperature.items():
                if temp != 0:
                    self._add_sensor_text(cx, cy, f'🌡{temp}', '#E53935', CELL_SIZE - 24)

            for (cx, cy), rad in world.radiation.items():
                if rad != 0:
                    self._add_sensor_text(cx, cy, f'☢{rad}', '#43A047', 4)
        elif gw:
            for cell in getattr(world, 'discovered_sensors', set()):
                temp = world.temperature.get(cell, 0)
                rad = world.radiation.get(cell, 0)

                if temp != 0:
                    self._add_sensor_text(
                        cell[0],
                        cell[1],
                        f'🌡{temp}',
                        '#E53935',
                        CELL_SIZE - 24,
                    )

                if rad != 0:
                    self._add_sensor_text(
                        cell[0],
                        cell[1],
                        f'☢{rad}',
                        '#43A047',
                        4,
                    )

        self.robot_item.setPos(
            robot.x * CELL_SIZE + CELL_SIZE // 2,
            robot.y * CELL_SIZE + CELL_SIZE // 2,
        )
        self.robot_item.update()

    def mouseMoveEvent(self, e):
        gw = _main_window()

        new_hover_cell = None
        new_hover_wall = None

        if gw and gw.edit_mode:
            p = e.scenePos()
            new_hover_cell = self._cell_from_scene_pos(p)
            if gw.wall_builder_enabled:
                new_hover_wall = self._wall_from_scene_pos(p)

        if new_hover_cell != self.hover_cell or new_hover_wall != self.hover_wall:
            self.hover_cell = new_hover_cell
            self.hover_wall = new_hover_wall
            self.rebuild()

        super().mouseMoveEvent(e)

    def mousePressEvent(self, e):
        gw = _main_window()
        if gw is None:
            super().mousePressEvent(e)
            return

        clicked = self.items(e.scenePos())
        if any(isinstance(item, RobotItem) for item in clicked):
            super().mousePressEvent(e)
            return

        p = e.scenePos()
        x = int(p.x() // CELL_SIZE)
        y = int(p.y() // CELL_SIZE)

        if not (0 <= x < world.width and 0 <= y < world.height):
            super().mousePressEvent(e)
            return

        if gw.edit_mode:
            self.selected_cell = (x, y)
            self.hover_cell = (x, y)

        if gw.edit_mode and gw.wall_builder_enabled:
            wall_info = self._wall_from_scene_pos(p)
            if wall_info is not None:
                self._push_undo_if_available(gw)

                wall_x, wall_y, wall_dir = wall_info
                if (wall_x, wall_y, wall_dir) in world.walls:
                    world.remove_wall(wall_x, wall_y, wall_dir)
                else:
                    world.add_wall(wall_x, wall_y, wall_dir)

                self._commit_edit_change(gw)
                return

        if gw.edit_mode and gw.temp_enabled:
            key = (x, y)
            old_value = world.temperature.get(key)
            new_value = gw.temp_spin.value()

            if new_value == 0:
                if old_value is None:
                    self.rebuild()
                    return
            elif old_value == new_value:
                self.rebuild()
                return

            self._push_undo_if_available(gw)

            if new_value == 0:
                world.temperature.pop(key, None)
            else:
                world.temperature[key] = new_value

            world.discovered_sensors.discard(key)

            self._commit_edit_change(gw)
            return

        if gw.edit_mode and gw.rad_enabled:
            key = (x, y)
            old_value = world.radiation.get(key)
            new_value = gw.rad_spin.value()

            if new_value == 0:
                if old_value is None:
                    self.rebuild()
                    return
            elif old_value == new_value:
                self.rebuild()
                return

            self._push_undo_if_available(gw)

            if new_value == 0:
                world.radiation.pop(key, None)
            else:
                world.radiation[key] = new_value

            world.discovered_sensors.discard(key)

            self._commit_edit_change(gw)
            return

        if gw.edit_mode and gw.paint_enabled:
            self._push_undo_if_available(gw)

            key = (x, y)
            if key in world.colors:
                del world.colors[key]
            else:
                color_name = (
                    gw.get_selected_color_name()
                    if hasattr(gw, 'get_selected_color_name')
                    else 'green'
                )
                world.colors[key] = color_name

            world.discovered_colors.discard(key)

            self._commit_edit_change(gw)
            return

        if gw.edit_mode:
            self.rebuild()

        super().mousePressEvent(e)


class ModernButton(QPushButton):
    def __init__(self, text, primary=False):
        super().__init__(text)
        self.primary = primary
        self.setFixedHeight(36)
        self.setCursor(Qt.PointingHandCursor)
        self.update_style()

    def update_style(self):
        if self.primary:
            self.setStyleSheet('''
                QPushButton {
                    background: #4285F4;
                    color: white;
                    border: none;
                    border-radius: 6px;
                    font-size: 14px;
                    font-weight: 500;
                    padding: 0 16px;
                }
                QPushButton:hover { background: #1967D2; }
                QPushButton:pressed { background: #174EA6; }
            ''')
        else:
            self.setStyleSheet('''
                QPushButton {
                    background: white;
                    color: #202124;
                    border: 1px solid #DADCE0;
                    border-radius: 6px;
                    font-size: 14px;
                    padding: 0 16px;
                }
                QPushButton:hover {
                    background: #F8F9FA;
                    border: 1px solid #DADCE0;
                }
                QPushButton:pressed { background: #F1F3F4; }
            ''')


class ToggleSwitch(QWidget):
    def __init__(self, text='', parent=None):
        super().__init__(parent)
        self.setStyleSheet('border: none; background: transparent;')
        self.checked = False

        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(8)

        self.label = QLabel(text)
        self.label.setStyleSheet('color: #5F6368; font-size: 13px;')
        layout.addWidget(self.label)

        self.switch_container = QWidget()
        self.switch_container.setFixedSize(44, 24)
        self.switch_container.setCursor(Qt.PointingHandCursor)
        self.switch_container.setStyleSheet('border: none; background: transparent;')

        self.switch_bg = QWidget(self.switch_container)
        self.switch_bg.setGeometry(0, 0, 44, 24)
        self.switch_bg.setStyleSheet('''
            background: #DADCE0;
            border-radius: 12px;
            border: none;
        ''')

        self.switch_circle = QWidget(self.switch_container)
        self.switch_circle.setGeometry(3, 3, 18, 18)
        self.switch_circle.setStyleSheet('''
            background: white;
            border-radius: 9px;
            border: none;
        ''')

        self.switch_container.mousePressEvent = lambda e: self.toggle()

        layout.addWidget(self.switch_container)
        self.update_style()

    def toggle(self):
        self.checked = not self.checked
        self.update_style()
        cb = getattr(self, 'on_toggle', None)
        if callable(cb):
            cb()

    def setChecked(self, checked):
        self.checked = checked
        self.update_style()

    def isChecked(self):
        return self.checked

    def update_style(self):
        if self.checked:
            self.switch_bg.setStyleSheet('''
                background: #4285F4;
                border-radius: 12px;
            ''')
            self.switch_circle.setGeometry(23, 3, 18, 18)
        else:
            self.switch_bg.setStyleSheet('''
                background: #DADCE0;
                border-radius: 12px;
            ''')
            self.switch_circle.setGeometry(3, 3, 18, 18)