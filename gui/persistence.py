import os

from PySide6.QtGui import QColor
from PySide6.QtWidgets import (
    QColorDialog, QFileDialog, QInputDialog, QLineEdit, QMessageBox, QPushButton
)

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

    def _prompt_world_name(self, title, label, value=''):
        dialog = QInputDialog(self)
        dialog.setWindowTitle(title)
        dialog.setLabelText(label)
        dialog.setTextEchoMode(QLineEdit.Normal)
        dialog.setTextValue(str(value or ''))
        dialog.setOkButtonText(tr('ok'))
        dialog.setCancelButtonText(tr('cancel'))
        dialog.setStyleSheet(self._dialog_style())

        line_edit = dialog.findChild(QLineEdit)
        if line_edit is not None:
            line_edit.returnPressed.connect(dialog.accept)

        ok_button = dialog.findChild(QPushButton)
        if ok_button is not None:
            ok_button.setDefault(True)
            ok_button.setAutoDefault(True)

        if dialog.exec() != QInputDialog.Accepted:
            return '', False

        return dialog.textValue(), True

    def _confirm_replace_world(self, name):
        box = QMessageBox(self)
        box.setWindowTitle(tr('replace_world_title'))
        box.setText(tr('replace_world_text').format(name=name))
        box.setIcon(QMessageBox.Question)
        box.setStandardButtons(QMessageBox.Yes | QMessageBox.No)
        box.setDefaultButton(QMessageBox.Yes)
        box.setStyleSheet(self._dialog_style())

        result = box.exec()
        return result == QMessageBox.Yes

    def _confirm_delete_world(self, name):
        box = QMessageBox(self)
        box.setWindowTitle(tr('delete_world_title'))
        box.setText(tr('delete_world_text').format(name=name))
        box.setIcon(QMessageBox.Warning)
        box.setStandardButtons(QMessageBox.Yes | QMessageBox.No)
        box.setDefaultButton(QMessageBox.Yes)
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

        name = str(name).strip()
        if not name:
            return False

        self._current_world = name
        world.discovered_sensors.clear()
        world.discovered_colors.clear()

        if hasattr(self, 'scene'):
            self.scene.hit_wall = None

        self._mark_next_snapshot_saved = True
        self.send_to_server({'type': 'load_world', 'name': name})
        return True

    def load_dialog(self):
        dialog = QFileDialog(self, tr('load_world_title'), self._state_dir, 'World Files (*.world)')
        dialog.setFileMode(QFileDialog.ExistingFile)
        dialog.setViewMode(QFileDialog.Detail)
        dialog.setOption(QFileDialog.DontUseNativeDialog, True)
        dialog.setStyleSheet(self._dialog_style())

        line_edit = dialog.findChild(QLineEdit)
        if line_edit is not None:
            line_edit.returnPressed.connect(dialog.accept)

        for button in dialog.findChildren(QPushButton):
            text = button.text().replace('&', '').strip().lower()
            if text in {'open', 'load', 'ok'}:
                button.setDefault(True)
                button.setAutoDefault(True)
                break

        if dialog.exec() != QFileDialog.Accepted:
            return False

        files = dialog.selectedFiles()
        if not files:
            return False

        path = files[0]
        name = os.path.splitext(os.path.basename(path))[0].strip()
        if not name:
            return False

        self.request_world_switch(name)
        return True

    def save_world(self):
        name, ok = self._prompt_world_name(
            tr('save_world_title'),
            tr('world_name_label'),
            self._current_world or '',
        )
        if not ok:
            return False

        name = name.strip()
        if not name:
            return False

        world_path = os.path.join(self._state_dir, f'{name}.world')
        if os.path.exists(world_path):
            if not self._confirm_replace_world(name):
                return False

        self._current_world = name
        self.send_to_server({'type': 'save_world', 'name': name})
        return True

    def delete_world(self, name):
        name = str(name).strip()
        if not name:
            return False

        if not self._confirm_delete_world(name):
            return False

        files = list(getattr(self, '_last_world_files', []))
        next_name = None

        if name in files:
            index = files.index(name)

            if len(files) > 1:
                if index < len(files) - 1:
                    next_name = files[index + 1]
                else:
                    next_name = files[index - 1]

        self._pending_deleted_world = name
        self._pending_next_world = next_name

        self.send_to_server({'type': 'delete_world', 'name': name})
        return True

    def pick_color(self):
        if not hasattr(self, 'scene'):
            return False

        current = getattr(self.scene, 'paint_color', QColor('#43A047'))
        color = QColorDialog.getColor(current, self, tr('color'))

        if not color.isValid():
            return False

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

        return True