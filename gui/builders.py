import qtawesome as qta
from PySide6.QtCore import QSize, Qt
from PySide6.QtWidgets import (
    QComboBox, QGridLayout, QGroupBox, QHBoxLayout, QLabel,
    QListWidget, QPushButton, QScrollArea, QSizePolicy, QSpinBox,
    QVBoxLayout, QWidget,
)

import gui._globals as _g
from ._globals import CELL_SIZE, world
from .lang import tr
from .widgets import ModernButton, ToggleSwitch

FONT_STACK = "'Segoe UI', Arial, sans-serif"
TRANSPARENT_STYLE = 'background: transparent;'


def _style(css):
    return css.replace('{FONT_STACK}', FONT_STACK)


HISTORY_BUTTON_STYLE = _style('''
    QPushButton {
        background: white;
        color: #202124;
        border: 1px solid #DADCE0;
        border-radius: 6px;
        font-size: 14px;
        font-weight: bold;
        font-family: {FONT_STACK};
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

SENSOR_STEP_BUTTON_STYLE = '''
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

SENSOR_SPIN_STYLE = '''
    QSpinBox {
        font-size: 14px;
        font-weight: 600;
        color: #202124;
        padding: 6px;
        background: white;
        border: 1px solid #DADCE0;
        border-radius: 6px;
    }
    QSpinBox::up-button, QSpinBox::down-button { width: 0px; }
'''


class NoWheelComboBox(QComboBox):
    def wheelEvent(self, event):
        event.ignore()


class BuildersMixin:
    def build_header(self):
        header = QWidget()
        self._header = header
        header.setFixedHeight(70)
        header.setStyleSheet('''
            QWidget {
                background: white;
                border-bottom: 2px solid #E0E0E0;
            }
        ''')

        layout = QHBoxLayout(header)
        layout.setContentsMargins(24, 0, 24, 0)
        layout.setSpacing(10)

        left_container = QWidget()
        left_container.setStyleSheet(TRANSPARENT_STYLE)

        left_layout = QHBoxLayout(left_container)
        left_layout.setContentsMargins(0, 0, 0, 0)
        left_layout.setSpacing(0)

        self._logo_label = QLabel('🤖')
        self._logo_label.setCursor(Qt.PointingHandCursor)
        self._logo_label.setToolTip(tr('about_title'))
        self._logo_label.setStyleSheet('font-size: 22px; background: transparent;')
        self._logo_label.mousePressEvent = lambda _event: self.show_about_dialog()
        left_layout.addWidget(self._logo_label)

        self._title_label = QLabel('Amun')
        self._title_label.setCursor(Qt.PointingHandCursor)
        self._title_label.setToolTip(tr('about_title'))
        self._title_label.setStyleSheet('''
            font-size: 18px;
            font-weight: 800;
            color: #4285F4;
            background: transparent;
        ''')
        self._title_label.mousePressEvent = lambda _event: self.show_about_dialog()
        left_layout.addWidget(self._title_label)

        layout.addWidget(left_container)
        layout.addStretch()

        self._lbl_edit_mode = QLabel(tr('edit_mode'))
        self._lbl_edit_mode.setStyleSheet(
            'color: #000000; font-size: 14px; font-weight: bold; '
            'background: transparent; margin-right: 1px;'
        )
        layout.addWidget(self._lbl_edit_mode)

        self.edit_toggle = ToggleSwitch()
        self.edit_toggle.on_toggle = self.toggle_edit_mode
        self.edit_toggle.setChecked(not _g.VIEWER_MODE)
        self.edit_toggle.layout().setContentsMargins(0, 0, 0, 0)
        self.edit_toggle.layout().setSpacing(0)
        layout.addWidget(self.edit_toggle)

        self._lbl_edit_mode.setVisible(True)
        self.edit_toggle.setVisible(True)

        lang_container = QWidget()
        lang_container.setStyleSheet(TRANSPARENT_STYLE)

        lang_layout = QHBoxLayout(lang_container)
        lang_layout.setContentsMargins(0, 0, 0, 0)
        lang_layout.setSpacing(4)

        self.lang_label = QLabel(tr('language'))
        self.lang_label.setStyleSheet('''
            font-size: 13px;
            font-weight: 700;
            color: #5F6368;
            background: transparent;
        ''')
        lang_layout.addWidget(self.lang_label)

        self.lang_combo = QComboBox()
        self.lang_combo.setFixedSize(92, 34)
        self.lang_combo.setCursor(Qt.PointingHandCursor)
        self.lang_combo.addItem('EN', 'EN')
        self.lang_combo.addItem('RU', 'RU')
        self.lang_combo.addItem('AR', 'AR')
        self.lang_combo.currentIndexChanged.connect(self._on_lang_combo_changed)
        lang_layout.addWidget(self.lang_combo)

        self._update_lang_buttons()

        self.light_btn = QPushButton()
        self.light_btn.setFixedSize(36, 36)
        self.light_btn.setCursor(Qt.PointingHandCursor)
        self.light_btn.setIcon(qta.icon('fa5s.sun', color='#FBC02D'))
        self.light_btn.setIconSize(QSize(18, 18))
        self.light_btn.clicked.connect(self.apply_light_mode)
        self.light_btn.setStyleSheet('''
            QPushButton {
                background: transparent;
                border: 2px solid #FBC02D;
                border-radius: 18px;
            }
            QPushButton:hover { background: rgba(251, 192, 45, 0.1); }
            QPushButton:pressed { background: rgba(251, 192, 45, 0.2); }
        ''')
        lang_layout.addWidget(self.light_btn)

        self.dark_btn = QPushButton()
        self.dark_btn.setFixedSize(36, 36)
        self.dark_btn.setCursor(Qt.PointingHandCursor)
        self.dark_btn.setIcon(qta.icon('fa5s.moon', color='#607D8B'))
        self.dark_btn.setIconSize(QSize(18, 18))
        self.dark_btn.clicked.connect(self.apply_dark_mode)
        self.dark_btn.setStyleSheet('''
            QPushButton {
                background: transparent;
                border: 2px solid #607D8B;
                border-radius: 18px;
            }
            QPushButton:hover { background: rgba(96, 125, 139, 0.1); }
            QPushButton:pressed { background: rgba(96, 125, 139, 0.2); }
        ''')
        lang_layout.addWidget(self.dark_btn)

        layout.addWidget(lang_container)

        return header

    def _build_grid_icon_container(self):
        grid_icon_widget = QWidget()
        grid_icon_widget.setFixedSize(24, 24)

        grid_icon_layout = QGridLayout(grid_icon_widget)
        grid_icon_layout.setContentsMargins(0, 0, 0, 0)
        grid_icon_layout.setSpacing(1)

        for row in range(2):
            for col in range(2):
                square = QWidget()
                square.setFixedSize(10, 10)
                square.setStyleSheet('''
                    background: transparent;
                    border: 2px solid #4285F4;
                    border-radius: 1px;
                ''')
                grid_icon_layout.addWidget(square, row, col)

        icon_container = QWidget()
        icon_layout = QHBoxLayout(icon_container)
        icon_layout.setContentsMargins(0, 0, 0, 0)
        icon_layout.addStretch()
        icon_layout.addWidget(grid_icon_widget)
        icon_layout.addStretch()

        return icon_container

    def build_left_panel(self):
        panel = QWidget()
        panel.setFixedWidth(320)
        panel.setStyleSheet('''
            QWidget {
                background: #F8F9FA;
                border-radius: 12px;
            }
        ''')

        main_layout = QVBoxLayout(panel)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        content_container = QWidget()
        content_container.setStyleSheet(TRANSPARENT_STYLE)

        layout = QVBoxLayout(content_container)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(8)

        self.edit_actions = self.build_edit_actions_section()
        layout.addWidget(self.edit_actions)

        self.edit_controls_rest = self.build_edit_controls_rest()
        layout.addWidget(self.edit_controls_rest)

        self.world_group = QGroupBox()
        self.world_group.setStyleSheet('''
            QGroupBox {
                border: 1px solid rgba(235, 237, 240, 0.8);
                border-radius: 8px;
                padding: 0px;
                background: transparent;
            }
        ''')

        world_layout = QVBoxLayout(self.world_group)
        world_layout.setSpacing(12)
        world_layout.setContentsMargins(12, 12, 12, 12)

        world_layout.addWidget(self._build_grid_icon_container())

        self._lbl_world_selection = QLabel(tr('world_selection'))
        self._lbl_world_selection.setStyleSheet('''
            font-size: 16px;
            font-weight: 700;
            color: #202124;
            background: transparent;
        ''')
        self._lbl_world_selection.setAlignment(Qt.AlignCenter)
        world_layout.addWidget(self._lbl_world_selection)

        self.world_list = QListWidget()
        self.world_list.setMinimumHeight(320)
        self.world_list.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.world_list.setStyleSheet('''
            QListWidget {
                border: none;
                border-radius: 6px;
                background: white;
                padding: 4px;
                outline: none;
                font-weight: 700;
            }
            QListWidget::item {
                padding: 0px;
                border: none;
                margin: 2px 0px;
                background: transparent;
                color: #202124;
            }
            QListWidget::item:selected {
                background: transparent;
                color: #202124;
            }
            QListWidget::item:hover {
                background: transparent;
                color: #202124;
            }
        ''')
        self.world_list.itemClicked.connect(
            lambda it: self.request_world_switch(it.data(Qt.UserRole) or it.text())
        )
        world_layout.addWidget(self.world_list)

        layout.addWidget(self.world_group, 1)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        scroll.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        scroll.setStyleSheet('''
            QScrollArea {
                border: none;
                background: transparent;
            }
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
            QScrollBar::handle:vertical:hover {
                background: #BDC1C6;
            }
            QScrollBar::add-line:vertical,
            QScrollBar::sub-line:vertical {
                border: none;
                background: none;
                height: 0px;
            }
        ''')
        scroll.setWidget(content_container)

        main_layout.addWidget(scroll)

        return panel

    def build_world_selection_section(self):
        world_section = QGroupBox()
        world_section.setStyleSheet(_style('''
            QGroupBox {
                border: 1px solid rgba(235, 237, 240, 0.8);
                border-radius: 8px;
                padding: 0px;
                background: transparent;
                font-family: {FONT_STACK};
            }
        '''))

        world_layout = QVBoxLayout(world_section)
        world_layout.setSpacing(12)
        world_layout.setContentsMargins(12, 12, 12, 12)

        world_layout.addWidget(self._build_grid_icon_container())

        self._lbl_edit_world_selection = QLabel(tr('world_selection'))
        self._lbl_edit_world_selection.setStyleSheet(_style('''
            font-size: 16px;
            font-weight: 700;
            color: #202124;
            background: transparent;
            font-family: {FONT_STACK};
        '''))
        self._lbl_edit_world_selection.setAlignment(Qt.AlignCenter)
        world_layout.addWidget(self._lbl_edit_world_selection)

        self.edit_world_list = QListWidget()
        self.edit_world_list.setMinimumHeight(240)
        self.edit_world_list.setMaximumHeight(300)
        self.edit_world_list.setStyleSheet(_style('''
            QListWidget {
                border: none;
                border-radius: 6px;
                background: white;
                padding: 4px;
                outline: none;
                font-weight: 700;
            }
            QListWidget::item {
                padding: 0px;
                border: none;
                margin: 2px 0px;
                background: transparent;
                font-family: {FONT_STACK};
                font-weight: 900;
                color: #202124;
            }
            QListWidget::item:selected {
                background: transparent;
                color: #202124;
                font-weight: 900;
            }
            QListWidget::item:hover {
                background: transparent;
                color: #202124;
                font-weight: 900;
            }
            QListWidget::item:hover:!selected {
                background: transparent;
                color: #202124;
                font-weight: 900;
            }
            QListWidget::item:focus {
                outline: none;
            }
        '''))
        self.edit_world_list.itemClicked.connect(
            lambda it: self.request_world_switch(it.data(Qt.UserRole) or it.text())
        )
        world_layout.addWidget(self.edit_world_list)

        return world_section

    def build_edit_actions_section(self):
        group = QGroupBox()
        self.edit_actions_section = group
        group.setStyleSheet(_style('''
            QGroupBox {
                border: 1px solid rgba(235, 237, 240, 0.8);
                border-radius: 8px;
                padding: 0px;
                background: transparent;
                font-family: {FONT_STACK};
            }
        '''))

        layout = QVBoxLayout(group)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(8)

        self._lbl_actions = QLabel(tr('actions'))
        self._lbl_actions.setStyleSheet(_style('''
            font-size: 16px;
            font-weight: bold;
            color: #202124;
            background: transparent;
            font-family: {FONT_STACK};
            padding-left: 0px;
            margin: 0px;
        '''))
        self._lbl_actions.setAlignment(Qt.AlignLeft)
        layout.addWidget(self._lbl_actions)

        self._btn_save = QPushButton()
        self._btn_save.setMinimumHeight(34)
        self._btn_save.setCursor(Qt.PointingHandCursor)
        self._btn_save.setText('💾  ' + tr('save'))
        self._btn_save.setStyleSheet(_style('''
            QPushButton {
                background: #4285F4;
                color: white;
                border: none;
                border-radius: 6px;
                font-size: 14px;
                font-weight: bold;
                font-family: {FONT_STACK};
                padding: 0 16px;
                text-align: center;
            }
            QPushButton:hover { background: #1967D2; }
            QPushButton:pressed { background: #174EA6; }
        '''))
        self._btn_save.clicked.connect(self.save_world)
        layout.addWidget(self._btn_save)

        self._btn_load = QPushButton()
        self._btn_load.setMinimumHeight(34)
        self._btn_load.setCursor(Qt.PointingHandCursor)
        self._btn_load.setText('📁  ' + tr('load'))
        self._btn_load.setStyleSheet(_style('''
            QPushButton {
                background: white;
                color: #202124;
                border: 1px solid #DADCE0;
                border-radius: 6px;
                font-size: 14px;
                font-weight: bold;
                font-family: {FONT_STACK};
                padding: 0 16px;
                text-align: center;
            }
            QPushButton:hover {
                background: #F8F9FA;
                border: 1px solid #DADCE0;
            }
            QPushButton:pressed { background: #F1F3F4; }
        '''))
        self._btn_load.clicked.connect(self.load_dialog)
        layout.addWidget(self._btn_load)

        history_row = QWidget()
        history_row.setStyleSheet(TRANSPARENT_STYLE)

        history_layout = QHBoxLayout(history_row)
        history_layout.setContentsMargins(0, 0, 0, 0)
        history_layout.setSpacing(8)

        self.undo_btn = QPushButton(tr('undo'))
        self.undo_btn.setMinimumHeight(34)
        self.undo_btn.setCursor(Qt.PointingHandCursor)
        self.undo_btn.setIcon(qta.icon('fa5s.undo-alt', color='#5F6368'))
        self.undo_btn.setIconSize(QSize(14, 14))
        self.undo_btn.setStyleSheet(HISTORY_BUTTON_STYLE)
        self.undo_btn.clicked.connect(self.undo_edit)
        history_layout.addWidget(self.undo_btn)

        self.redo_btn = QPushButton(tr('redo'))
        self.redo_btn.setMinimumHeight(34)
        self.redo_btn.setCursor(Qt.PointingHandCursor)
        self.redo_btn.setIcon(qta.icon('fa5s.redo-alt', color='#5F6368'))
        self.redo_btn.setIconSize(QSize(14, 14))
        self.redo_btn.setStyleSheet(HISTORY_BUTTON_STYLE)
        self.redo_btn.clicked.connect(self.redo_edit)
        history_layout.addWidget(self.redo_btn)

        layout.addWidget(history_row)

        return group

    def build_edit_controls_rest(self):
        container = QWidget()
        container.setStyleSheet(TRANSPARENT_STYLE)

        layout = QVBoxLayout(container)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(4)

        paint_section = QGroupBox()
        paint_section.setStyleSheet(_style('''
            QGroupBox {
                border: 1px solid rgba(235, 237, 240, 0.8);
                border-radius: 8px;
                padding: 0px;
                margin: 0px;
                background: transparent;
                font-family: {FONT_STACK};
            }
        '''))
        paint_section.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Minimum)

        paint_layout = QVBoxLayout(paint_section)
        paint_layout.setContentsMargins(16, 12, 16, 12)
        paint_layout.setSpacing(4)

        self._lbl_paint_tools = QLabel(tr('paint_tools'))
        self._lbl_paint_tools.setStyleSheet(_style('''
            font-size: 16px;
            font-weight: bold;
            color: #202124;
            background: transparent;
            font-family: {FONT_STACK};
            padding-left: 0px;
            margin: 0px;
        '''))
        self._lbl_paint_tools.setAlignment(Qt.AlignLeft)
        paint_layout.addWidget(self._lbl_paint_tools)

        paint_row = QWidget()
        paint_row.setStyleSheet(TRANSPARENT_STYLE)

        paint_row_layout = QHBoxLayout(paint_row)
        paint_row_layout.setContentsMargins(0, 0, 0, 0)
        paint_row_layout.setSpacing(12)

        self._lbl_paint_action = QLabel(tr('paint'))
        self._lbl_paint_action.setStyleSheet(_style('''
            font-size: 16px;
            font-weight: bold;
            color: #202124;
            background: transparent;
            font-family: {FONT_STACK};
        '''))
        paint_row_layout.addWidget(self._lbl_paint_action)
        paint_row_layout.addStretch()

        self.paint_toggle = ToggleSwitch('')
        self.paint_toggle.on_toggle = self.toggle_paint
        paint_row_layout.addWidget(self.paint_toggle)

        paint_layout.addWidget(paint_row)

        self._lbl_selected_color = QLabel(tr('selected_color'))
        self._lbl_selected_color.setStyleSheet(_style('''
            font-size: 13px;
            font-weight: 700;
            color: #5F6368;
            background: transparent;
            font-family: {FONT_STACK};
            margin-top: 6px;
        '''))
        paint_layout.addWidget(self._lbl_selected_color)

        preview_row = QWidget()
        preview_row.setStyleSheet(TRANSPARENT_STYLE)

        preview_layout = QHBoxLayout(preview_row)
        preview_layout.setContentsMargins(0, 0, 0, 0)
        preview_layout.setSpacing(12)

        self.color_preview = QLabel()
        self.color_preview.setFixedSize(36, 36)
        self.color_preview.setStyleSheet('''
            QLabel {
                border: 1px solid #DADCE0;
                border-radius: 10px;
                background: #E53935;
            }
        ''')
        preview_layout.addWidget(self.color_preview, 0, Qt.AlignVCenter)

        self.color_name_label = QLabel()
        self.color_name_label.setStyleSheet(_style('''
            font-size: 15px;
            font-weight: 700;
            color: #202124;
            background: transparent;
            font-family: {FONT_STACK};
        '''))
        preview_layout.addWidget(self.color_name_label, 0, Qt.AlignVCenter)
        preview_layout.addStretch()

        paint_layout.addWidget(preview_row)

        self._lbl_preset_colors = QLabel(tr('preset_colors'))
        self._lbl_preset_colors.setStyleSheet(_style('''
            font-size: 13px;
            font-weight: 700;
            color: #5F6368;
            background: transparent;
            font-family: {FONT_STACK};
            margin-top: 4px;
        '''))
        paint_layout.addWidget(self._lbl_preset_colors)

        self.color_combo = NoWheelComboBox()
        self.color_combo.setCursor(Qt.PointingHandCursor)
        self.color_combo.setFixedHeight(36)
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
        self.color_combo.currentIndexChanged.connect(self._on_color_combo_changed)
        self._rebuild_color_combo()
        paint_layout.addWidget(self.color_combo)

        layout.addWidget(paint_section)

        wall_builder_section = QGroupBox()
        wall_builder_section.setStyleSheet(_style('''
            QGroupBox {
                border: 1px solid rgba(235, 237, 240, 0.8);
                border-radius: 8px;
                padding: 0px;
                background: transparent;
                font-family: {FONT_STACK};
            }
        '''))

        wall_builder_layout = QVBoxLayout(wall_builder_section)
        wall_builder_layout.setContentsMargins(12, 12, 12, 12)
        wall_builder_layout.setSpacing(8)

        row = QHBoxLayout()
        row.setContentsMargins(0, 0, 0, 0)
        row.setSpacing(12)

        self._lbl_wall_builder = QLabel(tr('wall_builder'))
        self._lbl_wall_builder.setStyleSheet(_style('''
            font-size: 16px;
            font-weight: bold;
            color: #202124;
            background: transparent;
            font-family: {FONT_STACK};
        '''))
        row.addWidget(self._lbl_wall_builder)
        row.addStretch()

        self.wall_toggle = ToggleSwitch('')
        self.wall_toggle.on_toggle = self.toggle_wall_builder
        row.addWidget(self.wall_toggle)

        wall_builder_layout.addLayout(row)
        layout.addWidget(wall_builder_section)

        sensors_section = QGroupBox()
        sensors_section.setStyleSheet(_style('''
            QGroupBox {
                border: 1px solid rgba(235, 237, 240, 0.8);
                border-radius: 8px;
                padding: 0px;
                background: transparent;
                font-family: {FONT_STACK};
            }
        '''))

        sensors_layout = QVBoxLayout(sensors_section)
        sensors_layout.setContentsMargins(12, 12, 12, 12)
        sensors_layout.setSpacing(12)

        self._lbl_sensors = QLabel(tr('sensors'))
        self._lbl_sensors.setStyleSheet(_style('''
            font-size: 16px;
            font-weight: bold;
            color: #202124;
            background: transparent;
            font-family: {FONT_STACK};
        '''))
        self._lbl_sensors.setAlignment(Qt.AlignLeft)
        sensors_layout.addWidget(self._lbl_sensors)

        temp_row = QWidget()
        temp_row.setLayoutDirection(Qt.LeftToRight)

        temp_row_layout = QHBoxLayout(temp_row)
        temp_row_layout.setContentsMargins(0, 0, 0, 0)
        temp_row_layout.setSpacing(6)

        self.temp_button = QPushButton('🌡 ' + tr('temperature'))
        self.temp_button.setObjectName('sensor_btn')
        self.temp_button.setCheckable(True)
        self.temp_button.setFixedHeight(40)
        self.temp_button.setCursor(Qt.PointingHandCursor)
        self.temp_button.setStyleSheet('''
            QPushButton {
                background: white;
                color: #202124;
                border: 1px solid #DADCE0;
                border-radius: 6px;
                font-size: 14px;
                font-weight: 600;
                text-align: left;
                padding: 0 12px;
            }
            QPushButton:hover { background: #F8F9FA; }
            QPushButton:checked {
                background: #E53935;
                color: white;
                border: 1px solid #E53935;
            }
        ''')
        self.temp_button.toggled.connect(self.toggle_temp_sensor)
        temp_row_layout.addWidget(self.temp_button, 1)

        temp_minus = QPushButton()
        temp_minus.setIcon(qta.icon('fa5s.minus', color='#5F6368'))
        temp_minus.setIconSize(QSize(12, 12))
        self._temp_minus = temp_minus
        temp_minus.setObjectName('spin_btn')
        temp_minus.setFixedSize(32, 32)
        temp_minus.setCursor(Qt.PointingHandCursor)
        temp_minus.setStyleSheet(SENSOR_STEP_BUTTON_STYLE)
        temp_row_layout.addWidget(temp_minus)

        self.temp_spin = QSpinBox()
        self.temp_spin.setRange(-50, 100)
        self.temp_spin.setValue(0)
        self.temp_spin.setFixedSize(50, 32)
        self.temp_spin.setAlignment(Qt.AlignCenter)
        self.temp_spin.setStyleSheet(SENSOR_SPIN_STYLE)
        temp_row_layout.addWidget(self.temp_spin)

        temp_plus = QPushButton()
        temp_plus.setIcon(qta.icon('fa5s.plus', color='#5F6368'))
        temp_plus.setIconSize(QSize(12, 12))
        self._temp_plus = temp_plus
        temp_plus.setObjectName('spin_btn')
        temp_plus.setFixedSize(32, 32)
        temp_plus.setCursor(Qt.PointingHandCursor)
        temp_plus.setStyleSheet(SENSOR_STEP_BUTTON_STYLE)
        temp_row_layout.addWidget(temp_plus)

        temp_minus.clicked.connect(lambda: self.temp_spin.setValue(self.temp_spin.value() - 1))
        temp_plus.clicked.connect(lambda: self.temp_spin.setValue(self.temp_spin.value() + 1))
        sensors_layout.addWidget(temp_row)

        rad_row = QWidget()
        rad_row.setLayoutDirection(Qt.LeftToRight)

        rad_row_layout = QHBoxLayout(rad_row)
        rad_row_layout.setContentsMargins(0, 0, 0, 0)
        rad_row_layout.setSpacing(6)

        self.rad_button = QPushButton('☢ ' + tr('radiation'))
        self.rad_button.setObjectName('sensor_btn')
        self.rad_button.setCheckable(True)
        self.rad_button.setFixedHeight(40)
        self.rad_button.setCursor(Qt.PointingHandCursor)
        self.rad_button.setStyleSheet('''
            QPushButton {
                background: white;
                color: #202124;
                border: 1px solid #DADCE0;
                border-radius: 6px;
                font-size: 14px;
                font-weight: 600;
                text-align: left;
                padding: 0 12px;
            }
            QPushButton:hover { background: #F8F9FA; }
            QPushButton:checked {
                background: #43A047;
                color: white;
                border: 1px solid #43A047;
            }
        ''')
        self.rad_button.toggled.connect(self.toggle_rad_sensor)
        rad_row_layout.addWidget(self.rad_button, 1)

        rad_minus = QPushButton()
        rad_minus.setIcon(qta.icon('fa5s.minus', color='#5F6368'))
        rad_minus.setIconSize(QSize(12, 12))
        self._rad_minus = rad_minus
        rad_minus.setObjectName('spin_btn')
        rad_minus.setFixedSize(32, 32)
        rad_minus.setCursor(Qt.PointingHandCursor)
        rad_minus.setStyleSheet(SENSOR_STEP_BUTTON_STYLE)
        rad_row_layout.addWidget(rad_minus)

        self.rad_spin = QSpinBox()
        self.rad_spin.setRange(0, 100)
        self.rad_spin.setValue(0)
        self.rad_spin.setFixedSize(50, 32)
        self.rad_spin.setAlignment(Qt.AlignCenter)
        self.rad_spin.setStyleSheet(SENSOR_SPIN_STYLE)
        rad_row_layout.addWidget(self.rad_spin)

        rad_plus = QPushButton()
        rad_plus.setIcon(qta.icon('fa5s.plus', color='#5F6368'))
        rad_plus.setIconSize(QSize(12, 12))
        self._rad_plus = rad_plus
        rad_plus.setObjectName('spin_btn')
        rad_plus.setFixedSize(32, 32)
        rad_plus.setCursor(Qt.PointingHandCursor)
        rad_plus.setStyleSheet(SENSOR_STEP_BUTTON_STYLE)
        rad_row_layout.addWidget(rad_plus)

        rad_minus.clicked.connect(lambda: self.rad_spin.setValue(self.rad_spin.value() - 1))
        rad_plus.clicked.connect(lambda: self.rad_spin.setValue(self.rad_spin.value() + 1))
        sensors_layout.addWidget(rad_row)

        self.edit_sensors_section = sensors_section
        layout.addWidget(self.edit_sensors_section)

        self.edit_world_selection_section = self.build_world_selection_section()
        layout.addWidget(self.edit_world_selection_section)

        return container

    def build_h_controls(self):
        h_controls = QWidget()
        h_controls.setFixedWidth(max(world.width * CELL_SIZE, 152))
        h_controls.setStyleSheet(TRANSPARENT_STYLE)

        layout = QHBoxLayout(h_controls)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(8)

        layout.addStretch()

        self.h_minus_btn = QPushButton('−')
        self.h_minus_btn.setFixedSize(40, 40)
        self.h_minus_btn.setStyleSheet('''
            QPushButton {
                background: white;
                border: 1px solid #DADCE0;
                border-radius: 8px;
                font-size: 20px;
                font-weight: bold;
                color: #5F6368;
                padding: 0px;
                margin: 0px;
            }
            QPushButton:hover { background: #F8F9FA; }
        ''')
        self.h_minus_btn.clicked.connect(lambda: self.adjust_grid_dimension('h', -1))
        layout.addWidget(self.h_minus_btn)

        self.h_value_label = QLabel(f'{world.width}')
        self.h_value_label.setFixedSize(40, 40)
        self.h_value_label.setStyleSheet('''
            font-size: 16px;
            font-weight: 600;
            border: 1px solid #DADCE0;
            border-radius: 8px;
            background: white;
            padding: 0px;
            margin: 0px;
        ''')
        self.h_value_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.h_value_label)

        self.h_plus_btn = QPushButton('+')
        self.h_plus_btn.setFixedSize(40, 40)
        self.h_plus_btn.setStyleSheet('''
            QPushButton {
                background: white;
                border: 1px solid #DADCE0;
                border-radius: 8px;
                font-size: 20px;
                font-weight: bold;
                color: #5F6368;
                padding: 0px;
                padding-bottom: 2px;
                margin: 0px;
            }
            QPushButton:hover { background: #F8F9FA; }
        ''')
        self.h_plus_btn.clicked.connect(lambda: self.adjust_grid_dimension('h', 1))
        layout.addWidget(self.h_plus_btn)

        layout.addStretch()

        return h_controls

    def build_v_controls(self):
        v_controls = QWidget()
        v_controls.setStyleSheet(TRANSPARENT_STYLE)

        layout = QVBoxLayout(v_controls)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(8)

        self.v_plus_btn = ModernButton('+')
        self.v_plus_btn.setFixedSize(40, 40)
        self.v_plus_btn.setStyleSheet('''
            QPushButton {
                background: white;
                border: 1px solid #DADCE0;
                border-radius: 8px;
                font-size: 20px;
                font-weight: bold;
                color: #5F6368;
            }
            QPushButton:hover { background: #F8F9FA; }
        ''')
        self.v_plus_btn.clicked.connect(lambda: self.adjust_grid_dimension('v', 1))
        layout.addWidget(self.v_plus_btn)

        self.v_value_label = QLabel(f'{world.height}')
        self.v_value_label.setFixedSize(40, 40)
        self.v_value_label.setStyleSheet('''
            font-size: 16px;
            font-weight: 600;
            border: 1px solid #DADCE0;
            background: white;
            border-radius: 8px;
        ''')
        self.v_value_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.v_value_label)

        self.v_minus_btn = ModernButton('−')
        self.v_minus_btn.setFixedSize(40, 40)
        self.v_minus_btn.setStyleSheet('''
            QPushButton {
                background: white;
                border: 1px solid #DADCE0;
                border-radius: 8px;
                font-size: 20px;
                font-weight: bold;
                color: #5F6368;
            }
            QPushButton:hover { background: #F8F9FA; }
        ''')
        self.v_minus_btn.clicked.connect(lambda: self.adjust_grid_dimension('v', -1))
        layout.addWidget(self.v_minus_btn)

        return v_controls