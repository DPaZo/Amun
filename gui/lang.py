import json
import os

from server.app_paths import get_lang_prefs_path

_LANG_PREFS_PATH = get_lang_prefs_path()

_DEFAULT_LANG = 'EN'
LANG = _DEFAULT_LANG

STRINGS = {
    'EN': {
        'edit_mode': 'Edit Mode',
        'robot_controls': 'Robot Controls',
        'waiting': 'Waiting for robot program',
        'color': 'Color',
        'actions': 'Actions',
        'save': 'Save Configuration',
        'load': 'Load Configuration',
        'undo': 'Undo',
        'redo': 'Redo',
        'paint_tools': 'Paint Tools',
        'paint': 'Paint',
        'selected_color': 'Selected Color:',
        'preset_colors': 'Palette',
        'color_red': 'Red',
        'color_orange': 'Orange',
        'color_yellow': 'Yellow',
        'color_green': 'Green',
        'color_blue': 'Blue',
        'color_purple': 'Purple',
        'color_black': 'Black',
        'wall_builder': 'Wall Builder',
        'world_selection': 'World Selection',
        'sensors': 'Environmental Sensors',
        'robot_settings': 'Robot Settings',
        'visuals': 'Visuals Display',
        'connected': 'Connected',
        'temperature': 'Temperature',
        'radiation': 'Radiation',
        'status_editing': 'Editing',
        'status_running': 'Running',
        'status_connected': 'Connected',
        'status_disconnected': 'Disconnected',
        'tool_none': 'Tool: None',
        'tool_running': 'Tool: Running',
        'tool_prefix': 'Tool: ',
        'tool_paint': 'Paint',
        'tool_wall': 'Wall',
        'tool_temperature': 'Temperature',
        'tool_radiation': 'Radiation',
        'language': 'Language',
        'load_world_title': 'Load World',
        'save_world_title': 'Save World',
        'world_name_label': 'World name:',
        'replace_world_title': 'Replace World',
        'replace_world_text': 'World "{name}" already exists.\n\nDo you want to replace it?',
        'ok': 'OK',
        'cancel': 'Cancel',
        'about_title': 'About Amun',
        'about_text': (
            'Amun is an educational robot simulator built with Python and PySide6.\n\n'
            'Amun supports learning programming through interactive robot tasks in a grid world.\n\n'
            'With Amun, you can:\n'
            '- Write and run robot programs\n'
            '- Move the robot in a grid world\n'
            '- Paint cells\n'
            '- Read color, temperature, and radiation\n'
            '- Check walls and border walls\n'
            '- Reset the robot to its start state\n'
            '- Stop a running robot program\n\n'
            'Core Programming Concepts You Can Practice:\n'
            '- Loops and Iteration\n'
            '- Conditional Logic (if/else)\n'
            '- Variables and State\n'
            '- Comparisons and Conditions\n'
            '- Return Values\n'
            '- Nested Function Calls\n'
            '- Recursion\n\n'
            'Author:\n'
            'Мохамед Ахмед Асем Сайед\n\n'
            'Supervisor:\n'
            'доцент, к.т.н., доцент кафедры Литовкин Д.В.'
        ),
    },
    'RU': {
        'edit_mode': 'Режим редактирования',
        'robot_controls': 'Управление роботом',
        'waiting': 'Ожидание программы робота',
        'color': 'Цвет',
        'actions': 'Действия',
        'save': 'Сохранить конфигурацию',
        'load': 'Загрузить конфигурацию',
        'undo': 'Отменить',
        'redo': 'Повторить',
        'paint_tools': 'Инструменты рисования',
        'paint': 'Рисовать',
        'selected_color': 'Выбранный цвет:',
        'preset_colors': 'Палитра',
        'color_red': 'Красный',
        'color_orange': 'Оранжевый',
        'color_yellow': 'Жёлтый',
        'color_green': 'Зелёный',
        'color_blue': 'Синий',
        'color_purple': 'Фиолетовый',
        'color_black': 'Чёрный',
        'wall_builder': 'Построитель стен',
        'world_selection': 'Выбор мира',
        'sensors': 'Датчики среды',
        'robot_settings': 'Настройки робота',
        'visuals': 'Отображение',
        'connected': 'Подключено',
        'temperature': 'Температура',
        'radiation': 'Радиация',
        'status_editing': 'Редактирование',
        'status_running': 'Выполнение',
        'status_connected': 'Подключено',
        'status_disconnected': 'Отключено',
        'tool_none': 'Инструмент: нет',
        'tool_running': 'Инструмент: выполнение',
        'tool_prefix': 'Инструмент: ',
        'tool_paint': 'Рисование',
        'tool_wall': 'Стены',
        'tool_temperature': 'Температура',
        'tool_radiation': 'Радиация',
        'language': 'Язык',
        'load_world_title': 'Загрузить мир',
        'save_world_title': 'Сохранить мир',
        'world_name_label': 'Имя мира:',
        'replace_world_title': 'Заменить мир',
        'replace_world_text': 'Мир "{name}" уже существует.\n\nХотите заменить его?',
        'ok': 'OK',
        'cancel': 'Отмена',
        'about_title': 'О программе Amun',
        'about_text': (
            'Amun — обучающий симулятор робота, созданный на Python и PySide6.\n\n'
            'Amun помогает изучать программирование с помощью интерактивных задач для робота в клеточном мире.\n\n'
            'С помощью Amun можно:\n'
            '- Писать и запускать программы робота\n'
            '- Перемещать робота по клеточному миру\n'
            '- Раскрашивать клетки\n'
            '- Считывать цвет, температуру и радиацию\n'
            '- Проверять стены и граничные стены\n'
            '- Возвращать робота в начальное состояние\n'
            '- Останавливать выполняющуюся программу робота\n\n'
            'Основные концепции программирования, которые можно изучать:\n'
            '- Циклы и итерации\n'
            '- Условная логика (if/else)\n'
            '- Переменные и состояние\n'
            '- Сравнения и условия\n'
            '- Возвращаемые значения\n'
            '- Вложенные вызовы функций\n'
            '- Рекурсия\n\n'
            'Автор:\n'
            'Мохамед Ахмед Асем Сайед\n\n'
            'Руководитель:\n'
            'доцент, к.т.н., доцент кафедры Литовкин Д.В.'
        ),
    },
    'AR': {
        'edit_mode': 'وضع التحرير',
        'robot_controls': 'عناصر تحكم الروبوت',
        'waiting': 'بانتظار برنامج الروبوت',
        'color': 'اللون',
        'actions': 'الإجراءات',
        'save': 'حفظ الإعداد',
        'load': 'تحميل الإعداد',
        'undo': 'تراجع',
        'redo': 'إعادة',
        'paint_tools': 'أدوات التلوين',
        'paint': 'تلوين',
        'selected_color': 'اللون المحدد:',
        'preset_colors': 'لوحة الألوان',
        'color_red': 'أحمر',
        'color_orange': 'برتقالي',
        'color_yellow': 'أصفر',
        'color_green': 'أخضر',
        'color_blue': 'أزرق',
        'color_purple': 'بنفسجي',
        'color_black': 'أسود',
        'wall_builder': 'بناء الجدران',
        'world_selection': 'اختيار العالم',
        'sensors': 'مستشعرات البيئة',
        'robot_settings': 'إعدادات الروبوت',
        'visuals': 'العرض',
        'connected': 'متصل',
        'temperature': 'درجة الحرارة',
        'radiation': 'الإشعاع',
        'status_editing': 'تحرير',
        'status_running': 'تشغيل',
        'status_connected': 'متصل',
        'status_disconnected': 'غير متصل',
        'tool_none': 'الأداة: لا شيء',
        'tool_running': 'الأداة: تشغيل',
        'tool_prefix': 'الأداة: ',
        'tool_paint': 'تلوين',
        'tool_wall': 'جدار',
        'tool_temperature': 'حرارة',
        'tool_radiation': 'إشعاع',
        'language': 'اللغة',
        'load_world_title': 'تحميل العالم',
        'save_world_title': 'حفظ العالم',
        'world_name_label': 'اسم العالم:',
        'replace_world_title': 'استبدال العالم',
        'replace_world_text': 'العالم "{name}" موجود بالفعل.\n\nهل تريد استبداله؟',
        'ok': 'موافق',
        'cancel': 'إلغاء',
        'about_title': 'حول Amun',
        'about_text': (
            'Amun هو محاكي روبوت تعليمي مبني باستخدام Python وPySide6.\n\n'
            'يساعد Amun على تعلم البرمجة من خلال مهام تفاعلية للروبوت داخل عالم شبكي.\n\n'
            'باستخدام Amun يمكنك:\n'
            '- كتابة وتشغيل برامج الروبوت\n'
            '- تحريك الروبوت داخل عالم شبكي\n'
            '- تلوين الخلايا\n'
            '- قراءة اللون ودرجة الحرارة والإشعاع\n'
            '- فحص الجدران وحدود العالم\n'
            '- إعادة الروبوت إلى حالته الابتدائية\n'
            '- إيقاف برنامج روبوت قيد التشغيل\n\n'
            'المفاهيم الأساسية في البرمجة التي يمكنك التدرّب عليها:\n'
            '- الحلقات والتكرار\n'
            '- المنطق الشرطي (if/else)\n'
            '- المتغيرات والحالة\n'
            '- المقارنات والشروط\n'
            '- القيم المعادة\n'
            '- الاستدعاءات المتداخلة للدوال\n'
            '- الاستدعاء الذاتي\n\n'
            'المؤلف:\n'
            'Мохамед Ахмед Асем Сайед\n\n'
            'المشرف:\n'
            'доцент, к.т.н., доцент кафедры Литовкин Д.В.'
        ),
    },
}


def tr(key: str) -> str:
    return STRINGS.get(LANG, STRINGS[_DEFAULT_LANG]).get(key, key)


def set_lang(lang: str):
    global LANG
    value = str(lang).upper()
    LANG = value if value in STRINGS else _DEFAULT_LANG


def save_lang():
    try:
        os.makedirs(os.path.dirname(_LANG_PREFS_PATH), exist_ok=True)
        with open(_LANG_PREFS_PATH, 'w', encoding='utf-8') as f:
            json.dump({'lang': LANG}, f, ensure_ascii=False)
    except Exception:
        pass


def load_lang():
    try:
        with open(_LANG_PREFS_PATH, 'r', encoding='utf-8') as f:
            data = json.load(f)
        set_lang(data.get('lang', _DEFAULT_LANG))
    except Exception:
        pass