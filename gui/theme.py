import qtawesome as qta
from PySide6.QtGui import QBrush, QColor
from PySide6.QtWidgets import QLabel

from ._globals import save_prefs


class ThemeMixin:
    def _all_spin_buttons(self):
        return (
            self._temp_minus,
            self._temp_plus,
            self._rad_minus,
            self._rad_plus,
        )

    def _sensor_icon_buttons(self):
        return (
            (self._temp_minus, 'fa5s.minus'),
            (self._temp_plus, 'fa5s.plus'),
            (self._rad_minus, 'fa5s.minus'),
            (self._rad_plus, 'fa5s.plus'),
        )

    def get_spin_button_style(self):
        if self.is_dark_mode:
            return '''
                QPushButton {
                    background: #2A2A2A;
                    border: 1px solid #444444;
                    border-radius: 6px;
                    font-size: 18px;
                    font-weight: bold;
                    color: #FFFFFF;
                }
                QPushButton:hover { background: #3A3A3A; }
            '''

        return '''
            QPushButton {
                background: white;
                border: 1px solid #DADCE0;
                border-radius: 6px;
                font-size: 18px;
                font-weight: bold;
                color: #5F6368;
            }
            QPushButton:hover { background: #F8F9FA; }
        '''

    def _apply_action_buttons_light(self):
        if hasattr(self, '_btn_save'):
            self._btn_save.setStyleSheet('''
                QPushButton {
                    background: #4285F4;
                    color: white;
                    border: none;
                    border-radius: 6px;
                    font-size: 14px;
                    font-weight: bold;
                    padding: 0 16px;
                    text-align: center;
                }
                QPushButton:hover { background: #1967D2; }
                QPushButton:pressed { background: #174EA6; }
            ''')

        if hasattr(self, '_btn_load'):
            self._btn_load.setStyleSheet('''
                QPushButton {
                    background: white;
                    color: #202124;
                    border: 1px solid #DADCE0;
                    border-radius: 6px;
                    font-size: 14px;
                    font-weight: bold;
                    padding: 0 16px;
                    text-align: center;
                }
                QPushButton:hover {
                    background: #F8F9FA;
                    border: 1px solid #DADCE0;
                }
                QPushButton:pressed { background: #F1F3F4; }
            ''')

        if hasattr(self, 'undo_btn'):
            self.undo_btn.setStyleSheet('''
                QPushButton {
                    background: white;
                    color: #202124;
                    border: 1px solid #DADCE0;
                    border-radius: 6px;
                    font-size: 14px;
                    font-weight: bold;
                    padding: 0 16px;
                    text-align: center;
                }
                QPushButton:hover {
                    background: #F8F9FA;
                    border: 1px solid #DADCE0;
                }
                QPushButton:pressed { background: #F1F3F4; }
                QPushButton:disabled {
                    color: #9AA0A6;
                    background: #F8F9FA;
                    border: 1px solid #ECEFF1;
                }
            ''')
            self.undo_btn.setIcon(qta.icon('fa5s.undo-alt', color='#5F6368'))

        if hasattr(self, 'redo_btn'):
            self.redo_btn.setStyleSheet('''
                QPushButton {
                    background: white;
                    color: #202124;
                    border: 1px solid #DADCE0;
                    border-radius: 6px;
                    font-size: 14px;
                    font-weight: bold;
                    padding: 0 16px;
                    text-align: center;
                }
                QPushButton:hover {
                    background: #F8F9FA;
                    border: 1px solid #DADCE0;
                }
                QPushButton:pressed { background: #F1F3F4; }
                QPushButton:disabled {
                    color: #9AA0A6;
                    background: #F8F9FA;
                    border: 1px solid #ECEFF1;
                }
            ''')
            self.redo_btn.setIcon(qta.icon('fa5s.redo-alt', color='#5F6368'))

    def _apply_action_buttons_dark(self):
        if hasattr(self, '_btn_save'):
            self._btn_save.setStyleSheet('''
                QPushButton {
                    background: #4285F4;
                    color: white;
                    border: none;
                    border-radius: 6px;
                    font-size: 14px;
                    font-weight: bold;
                    padding: 0 16px;
                    text-align: center;
                }
                QPushButton:hover { background: #5A95F5; }
                QPushButton:pressed { background: #1A73E8; }
            ''')

        if hasattr(self, '_btn_load'):
            self._btn_load.setStyleSheet('''
                QPushButton {
                    background: #2A2A2A;
                    color: #E0E0E0;
                    border: 1px solid #444444;
                    border-radius: 6px;
                    font-size: 14px;
                    font-weight: bold;
                    padding: 0 16px;
                    text-align: center;
                }
                QPushButton:hover {
                    background: #333333;
                    border: 1px solid #555555;
                }
                QPushButton:pressed { background: #1E1E1E; }
            ''')

        if hasattr(self, 'undo_btn'):
            self.undo_btn.setStyleSheet('''
                QPushButton {
                    background: #2A2A2A;
                    color: #E0E0E0;
                    border: 1px solid #444444;
                    border-radius: 6px;
                    font-size: 14px;
                    font-weight: bold;
                    padding: 0 16px;
                    text-align: center;
                }
                QPushButton:hover {
                    background: #333333;
                    border: 1px solid #555555;
                }
                QPushButton:pressed { background: #1E1E1E; }
                QPushButton:disabled {
                    color: #777777;
                    background: #1E1E1E;
                    border: 1px solid #333333;
                }
            ''')
            self.undo_btn.setIcon(qta.icon('fa5s.undo-alt', color='#E0E0E0'))

        if hasattr(self, 'redo_btn'):
            self.redo_btn.setStyleSheet('''
                QPushButton {
                    background: #2A2A2A;
                    color: #E0E0E0;
                    border: 1px solid #444444;
                    border-radius: 6px;
                    font-size: 14px;
                    font-weight: bold;
                    padding: 0 16px;
                    text-align: center;
                }
                QPushButton:hover {
                    background: #333333;
                    border: 1px solid #555555;
                }
                QPushButton:pressed { background: #1E1E1E; }
                QPushButton:disabled {
                    color: #777777;
                    background: #1E1E1E;
                    border: 1px solid #333333;
                }
            ''')
            self.redo_btn.setIcon(qta.icon('fa5s.redo-alt', color='#E0E0E0'))

    def _style_live_panel_toggle(self):
        if not hasattr(self, 'live_panel_toggle_btn'):
            return

        if self.is_dark_mode:
            self.live_panel_toggle_btn.setStyleSheet('''
                QPushButton {
                    background: #2A2A2A;
                    color: #E0E0E0;
                    border: 1px solid #444444;
                    border-radius: 8px;
                    font-size: 16px;
                    font-weight: 700;
                    padding: 0px;
                }
                QPushButton:hover { background: #333333; }
                QPushButton:pressed { background: #1E1E1E; }
            ''')
        else:
            self.live_panel_toggle_btn.setStyleSheet('''
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
            ''')

    def apply_light_mode(self):
        self.is_dark_mode = False

        self.setStyleSheet('''
            QMainWindow { background: #F8F9FA; }
            QLabel { color: #202124; font-size: 14px; }
            QGroupBox {
                font-size: 14px; font-weight: 600; color: #202124;
                border: none; margin-top: 12px;
            }
            QGroupBox::title { subcontrol-origin: margin; subcontrol-position: top left; padding: 0 4px; }
        ''')

        self._header.setStyleSheet('''
            QWidget { background: white; border-bottom: 2px solid #E0E0E0; }
            QLabel { color: #202124; background: transparent; }
        ''')
        if hasattr(self, '_lbl_edit_mode'):
            self._lbl_edit_mode.setStyleSheet(
                'color: #000000; font-size: 14px; font-weight: bold; '
                'background: transparent; margin-right: 1px;'
            )

        self.left_panel.setStyleSheet('''
            QWidget { background: #F8F9FA; border-radius: 12px; }
            QLabel { color: #202124; background: transparent; font-size: 14px; }
            QGroupBox {
                color: #202124;
                border: 1px solid rgba(235, 237, 240, 0.8);
                border-radius: 8px;
                background: transparent;
            }
        ''')

        for label in self.left_panel.findChildren(QLabel):
            style = label.styleSheet()
            style = style.replace('color: #E0E0E0', 'color: #202124')
            style = style.replace('color: #9AA0A6', 'color: #5F6368')
            label.setStyleSheet(style)

        list_style = '''
            QListWidget {
                border: none;
                border-radius: 6px;
                background: white;
                padding: 4px;
                outline: none;
                font-weight: 700;
            }
            QListWidget::item {
                padding: 8px 12px;
                border-radius: 4px;
                margin: 2px 0px;
                font-weight: 900;
                color: #202124;
            }
            QListWidget::item:selected {
                background: #4285F4;
                color: white;
            }
            QListWidget::item:hover {
                background: #4285F4;
                color: white;
            }
        '''
        if hasattr(self, 'world_list'):
            self.world_list.setStyleSheet(list_style)
        if hasattr(self, 'edit_world_list'):
            self.edit_world_list.setStyleSheet(list_style)

        if hasattr(self, 'color_combo'):
            self.color_combo.setStyleSheet('''
                QComboBox {
                    border: 1px solid #DADCE0;
                    border-radius: 6px;
                    padding: 4px 12px;
                    font-size: 14px;
                    font-weight: 500;
                    color: #202124;
                    background: white;
                }
                QComboBox::drop-down {
                    border: none;
                    width: 24px;
                }
                QComboBox QAbstractItemView {
                    border: 1px solid #DADCE0;
                    background: white;
                    color: #202124;
                    selection-background-color: #4285F4;
                    selection-color: white;
                    font-size: 14px;
                }
            ''')

        for btn in self._all_spin_buttons():
            btn.setStyleSheet(self.get_spin_button_style())

        for btn, icon_name in self._sensor_icon_buttons():
            btn.setIcon(qta.icon(icon_name, color='#5F6368'))

        self.temp_button.setStyleSheet('''
            QPushButton {
                background: white; color: #202124;
                border: 1px solid #DADCE0; border-radius: 6px;
                font-size: 14px; font-weight: 500;
                text-align: left; padding-left: 12px;
            }
            QPushButton:hover { background: #F8F9FA; }
            QPushButton:checked { background: #E53935; color: white; border: 1px solid #E53935; }
        ''')
        self.rad_button.setStyleSheet('''
            QPushButton {
                background: white; color: #202124;
                border: 1px solid #DADCE0; border-radius: 6px;
                font-size: 14px; font-weight: 500;
                text-align: left; padding-left: 12px;
            }
            QPushButton:hover { background: #F8F9FA; }
            QPushButton:checked { background: #43A047; color: white; border: 1px solid #43A047; }
        ''')

        self._apply_action_buttons_light()

        light_grid_btn = '''
            QPushButton {
                background: white; border: 1px solid #DADCE0;
                border-radius: 8px; font-size: 20px; font-weight: bold;
                color: #5F6368; padding: 0px; margin: 0px;
            }
            QPushButton:hover { background: #F8F9FA; }
        '''
        for btn in (self.h_minus_btn, self.h_plus_btn, self.v_minus_btn, self.v_plus_btn):
            btn.setStyleSheet(light_grid_btn)

        light_label = '''
            font-size: 16px; font-weight: 600;
            border: 1px solid #DADCE0; border-radius: 8px;
            background: white; color: #202124; padding: 0px; margin: 0px;
        '''
        self.h_value_label.setStyleSheet(light_label)
        self.v_value_label.setStyleSheet(light_label)

        self.view.setStyleSheet('''
            QGraphicsView {
                border: 1px solid #DADCE0;
                border-radius: 8px;
                background: #E8F0FE;
            }
        ''')

        self.scene._dark = False
        self.scene.setBackgroundBrush(QBrush(QColor('#FFFFFF')))

        central = self.centralWidget()
        if central:
            central.setStyleSheet('background: #F8F9FA;')

        self._grid_outer.setStyleSheet('background: white;')
        self._scroll_area.setStyleSheet('''
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
        ''')

        self._style_live_panel_toggle()
        self.update_scene()
        self._update_lang_buttons()
        if hasattr(self, '_sync_color_preview'):
            self._sync_color_preview()
        if hasattr(self, '_update_live_panel_toggle'):
            self._update_live_panel_toggle()
        if hasattr(self, '_refresh_runtime_widgets'):
            self._refresh_runtime_widgets()
        if hasattr(self, '_refresh_undo_redo_buttons'):
            self._refresh_undo_redo_buttons()

        save_prefs(False)

    def apply_dark_mode(self):
        self.is_dark_mode = True

        self.setStyleSheet('''
            QMainWindow { background: #0F0F0F; }
            QLabel { color: #E0E0E0; font-size: 14px; background: transparent; }
            QGroupBox {
                font-size: 14px; font-weight: 600; color: #E0E0E0;
                border: 1px solid #2A2A2A; border-radius: 8px; margin-top: 12px;
            }
            QGroupBox::title { subcontrol-origin: margin; subcontrol-position: top left; padding: 0 4px; }
            QPushButton {
                background: #1E1E1E; color: #E0E0E0;
                border: 1px solid #333333; border-radius: 6px;
                font-size: 14px; padding: 0 16px;
            }
            QPushButton:hover { background: #2A2A2A; border: 1px solid #444444; }
            QPushButton:pressed { background: #333333; }
            QPushButton:checked { background: #1A3A5C; color: #90CAF9; border: 1px solid #1E88E5; }
            QSpinBox {
                background: #1E1E1E; color: #E0E0E0;
                border: 1px solid #333333; border-radius: 6px;
                font-size: 14px; font-weight: 600; padding: 6px;
            }
            QSpinBox::up-button, QSpinBox::down-button { width: 0px; }
            QListWidget {
                background: #1A1A1A; color: #E0E0E0;
                border: none; border-radius: 6px;
            }
            QListWidget::item { padding: 8px 12px; border-radius: 4px; color: #E0E0E0; }
            QListWidget::item:selected { background: #1E88E5; color: white; }
            QListWidget::item:hover { background: #2A2A2A; color: #E0E0E0; }
            QScrollArea { border: none; background: #0F0F0F; }
            QScrollBar:vertical {
                border: none; background: #1A1A1A; width: 10px; border-radius: 5px;
            }
            QScrollBar::handle:vertical { background: #333333; border-radius: 5px; min-height: 20px; }
            QScrollBar::handle:vertical:hover { background: #444444; }
            QScrollBar:horizontal {
                border: none; background: #1A1A1A; height: 10px; border-radius: 5px;
            }
            QScrollBar::handle:horizontal { background: #333333; border-radius: 5px; min-width: 20px; }
            QScrollBar::handle:horizontal:hover { background: #444444; }
            QScrollBar::add-line, QScrollBar::sub-line { border: none; background: none; }
            QSlider::groove:horizontal {
                border: none; height: 6px; background: #2A2A2A; border-radius: 3px;
            }
            QSlider::handle:horizontal {
                background: #1E88E5; border: none;
                width: 16px; height: 16px; margin: -5px 0; border-radius: 8px;
            }
            QSlider::sub-page:horizontal { background: #1E88E5; border-radius: 3px; }
        ''')

        self.scene.setBackgroundBrush(QBrush(QColor('#141414')))
        self.scene._dark = True

        self.view.setStyleSheet('''
            QGraphicsView {
                border: 1px solid #2A2A2A;
                border-radius: 8px;
                background: #141414;
            }
        ''')

        central = self.centralWidget()
        if central:
            central.setStyleSheet('background: #0F0F0F;')

        self._grid_outer.setStyleSheet('background: #0F0F0F;')
        self._scroll_area.setStyleSheet('''
            QScrollArea { border: none; background: #0F0F0F; }
            QScrollBar:vertical {
                border: none;
                background: #1A1A1A;
                width: 10px;
                border-radius: 5px;
            }
            QScrollBar::handle:vertical {
                background: #333333;
                border-radius: 5px;
                min-height: 20px;
            }
            QScrollBar::handle:vertical:hover { background: #444444; }
            QScrollBar:horizontal {
                border: none;
                background: #1A1A1A;
                height: 10px;
                border-radius: 5px;
            }
            QScrollBar::handle:horizontal {
                background: #333333;
                border-radius: 5px;
                min-width: 20px;
            }
            QScrollBar::handle:horizontal:hover { background: #444444; }
            QScrollBar::add-line, QScrollBar::sub-line {
                border: none;
                background: none;
            }
        ''')

        self._header.setStyleSheet('''
            QWidget { background: #1A1A1A; border-bottom: 2px solid #2A2A2A; }
            QLabel { color: #E0E0E0; background: transparent; }
        ''')
        if hasattr(self, '_lbl_edit_mode'):
            self._lbl_edit_mode.setStyleSheet(
                'color: #E0E0E0; font-size: 14px; font-weight: bold; '
                'background: transparent; margin-right: 1px;'
            )

        self.left_panel.setStyleSheet('''
            QWidget { background: #1A1A1A; border-radius: 12px; }
            QLabel { color: #E0E0E0; background: transparent; font-size: 14px; }
            QGroupBox { color: #E0E0E0; border: 1px solid #2A2A2A; border-radius: 8px; background: transparent; }
        ''')

        for label in self.left_panel.findChildren(QLabel):
            style = label.styleSheet()
            style = style.replace('color: #202124', 'color: #E0E0E0')
            style = style.replace('color: #5F6368', 'color: #9AA0A6')
            if 'color:' not in style:
                style += ' color: #E0E0E0;'
            label.setStyleSheet(style)

        list_style = '''
            QListWidget {
                border: none;
                border-radius: 6px;
                background: #1E1E1E;
                padding: 4px;
                outline: none;
                font-weight: 700;
            }
            QListWidget::item {
                padding: 8px 12px;
                border-radius: 4px;
                margin: 2px 0px;
                font-weight: 900;
                color: #E0E0E0;
            }
            QListWidget::item:selected {
                background: #4285F4;
                color: white;
            }
            QListWidget::item:hover {
                background: #2A2A2A;
                color: #E0E0E0;
            }
        '''
        if hasattr(self, 'world_list'):
            self.world_list.setStyleSheet(list_style)
        if hasattr(self, 'edit_world_list'):
            self.edit_world_list.setStyleSheet(list_style)

        if hasattr(self, 'color_combo'):
            self.color_combo.setStyleSheet('''
                QComboBox {
                    border: 1px solid #444444;
                    border-radius: 6px;
                    padding: 4px 12px;
                    font-size: 14px;
                    font-weight: 500;
                    color: #E0E0E0;
                    background: #2A2A2A;
                }
                QComboBox::drop-down {
                    border: none;
                    width: 24px;
                }
                QComboBox QAbstractItemView {
                    border: 1px solid #444444;
                    background: #1E1E1E;
                    color: #E0E0E0;
                    selection-background-color: #4285F4;
                    selection-color: white;
                    font-size: 14px;
                }
            ''')

        for btn in self._all_spin_buttons():
            btn.setStyleSheet(self.get_spin_button_style())

        for btn, icon_name in self._sensor_icon_buttons():
            btn.setIcon(qta.icon(icon_name, color='#E0E0E0'))

        self.temp_button.setStyleSheet('''
            QPushButton {
                background: #2A2A2A; color: #E0E0E0;
                border: 1px solid #444444; border-radius: 6px;
                font-size: 14px; font-weight: 500;
                text-align: left; padding-left: 12px;
            }
            QPushButton:hover { background: #333333; }
            QPushButton:checked { background: #E53935; color: white; border: 1px solid #E53935; }
        ''')
        self.rad_button.setStyleSheet('''
            QPushButton {
                background: #2A2A2A; color: #E0E0E0;
                border: 1px solid #444444; border-radius: 6px;
                font-size: 14px; font-weight: 500;
                text-align: left; padding-left: 12px;
            }
            QPushButton:hover { background: #333333; }
            QPushButton:checked { background: #43A047; color: white; border: 1px solid #43A047; }
        ''')

        self._apply_action_buttons_dark()

        dark_grid_btn = '''
            QPushButton {
                background: #2A2A2A; border: 1px solid #444444;
                border-radius: 8px; font-size: 20px; font-weight: bold;
                color: #E0E0E0; padding: 0px; margin: 0px;
            }
            QPushButton:hover { background: #333333; }
            QPushButton:pressed { background: #1E1E1E; }
        '''
        for btn in (self.h_minus_btn, self.h_plus_btn, self.v_minus_btn, self.v_plus_btn):
            btn.setStyleSheet(dark_grid_btn)

        dark_label = '''
            font-size: 16px; font-weight: 600;
            border: 1px solid #444444; border-radius: 8px;
            background: #2A2A2A; color: #E0E0E0; padding: 0px; margin: 0px;
        '''
        self.h_value_label.setStyleSheet(dark_label)
        self.v_value_label.setStyleSheet(dark_label)

        self._style_live_panel_toggle()
        self.update_scene()
        self._update_lang_buttons()
        if hasattr(self, '_sync_color_preview'):
            self._sync_color_preview()
        if hasattr(self, '_update_live_panel_toggle'):
            self._update_live_panel_toggle()
        if hasattr(self, '_refresh_runtime_widgets'):
            self._refresh_runtime_widgets()
        if hasattr(self, '_refresh_undo_redo_buttons'):
            self._refresh_undo_redo_buttons()

        save_prefs(True)