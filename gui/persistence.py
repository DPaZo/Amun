import os

from PySide6.QtWidgets import QColorDialog, QInputDialog, QLineEdit, QMessageBox

from .lang import tr


class PersistenceMixin:
    def _dialog_style(self):
        if getattr(self, 'is_dark_mode', False):
            return '''
                QDialog, QMessageBox, QInputDialog {
                    background: #202124;
                    color: #E8EAED;
                }
                QLabel {
                    color: #E8EAED;
                    background: transparent;
                }
                QLineEdit {
                    background: #2A2A2A;
                    color: #E8EAED;
                    border: 1px solid #5F6368;
                    border-radius: 6px;
                    padding: 6px 8px;
                }
                QPushButton {
                    background: #2A2A2A;
                    color: #E8EAED;
                    border: 1px solid #5F6368;
                    border-radius: 6px;
                    padding: 6px 12px;
                    min-width: 84px;
                }
                QPushButton:hover {
                    background: #3A3A3A;
                }
            '''

        return '''
            QDialog, QMessageBox, QInputDialog {
                background: #FFFFFF;
                color: #202124;
            }
            QLabel {
                color: #202124;
                background: transparent;
            }
            QLineEdit {
                background: #FFFFFF;
                color: #202124;
                border: 1px solid #DADCE0;
                border-radius: 6px;
                padding: 6px 8px;
            }
            QPushButton {
                background: #FFFFFF;
                color: #202124;
                border: 1px solid #DADCE0;
                border-radius: 6px;
                padding: 6px 12px;
                min-width: 84px;
            }
            QPushButton:hover {
                background: #F8F9FA;
            }
        '''

    def _prompt_world_name(self, title, label):
        dialog = QInputDialog(self)
        dialog.setWindowTitle(title)
        dialog.setLabelText(label)
        dialog.setTextEchoMode(QLineEdit.Normal)
        dialog.setOkButtonText(tr('ok'))
        dialog.setCancelButtonText(tr('cancel'))
        dialog.setStyleSheet(self._dialog_style())

        if dialog.exec() != QInputDialog.Accepted:
            return '', False

        return dialog.textValue(), True

    def _confirm_replace_world(self, name):
        box = QMessageBox(self)
        box.setWindowTitle(tr('replace_world_title'))
        box.setText(tr('replace_world_text').format(name=name))
        box.setIcon(QMessageBox.Question)
        box.setStandardButtons(QMessageBox.Yes | QMessageBox.No)
        box.setDefaultButton(QMessageBox.No)
        box.setStyleSheet(self._dialog_style())

        result = box.exec()
        return result == QMessageBox.Yes

    def _save_local_state(self, force=False):
        return

    def _load_local_state(self):
        return False

    def update_world_list(self):
        self.send_to_server({'type': 'get_world_list'})

    def load_world(self, name):
        from ._globals import world

        self._current_world = name
        world.discovered_sensors.clear()

        if hasattr(self, 'scene'):
            self.scene.hit_wall = None

        self.send_to_server({'type': 'load_world', 'name': name})

    def load_dialog(self):
        name, ok = self._prompt_world_name(
            tr('load_world_title'),
            tr('world_name_label'),
        )
        if ok and name.strip():
            self.load_world(name.strip())

    def save_world(self):
        name, ok = self._prompt_world_name(
            tr('save_world_title'),
            tr('world_name_label'),
        )
        if not ok:
            return

        name = name.strip()
        if not name:
            return

        world_path = os.path.join(self._state_dir, f'{name}.world')
        if os.path.exists(world_path):
            if not self._confirm_replace_world(name):
                return

        self._current_world = name
        self.send_to_server({'type': 'save_world', 'name': name})

    def pick_color(self):
        if not hasattr(self, 'scene'):
            return

        color = QColorDialog.getColor(self.scene.paint_color, self)
        if not color.isValid():
            return

        self.scene.paint_color = color

        if hasattr(self, 'color_preview'):
            border = '#444444' if getattr(self, 'is_dark_mode', False) else '#DADCE0'
            self.color_preview.setStyleSheet(
                f'''
                    QLabel {{
                        border: 1px solid {border};
                        border-radius: 8px;
                        background: {color.name()};
                    }}
                '''
            )