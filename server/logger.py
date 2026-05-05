import os
import json
import threading
from datetime import datetime
from server.app_paths import get_logs_dir

LOG_DIR = get_logs_dir()

_session_file = None
_commands_file = None
_errors_file = None
_session_id = None

_lock = threading.Lock()


def _ensure_dirs():
    for folder in ('sessions', 'commands', 'errors'):
        os.makedirs(os.path.join(LOG_DIR, folder), exist_ok=True)


def new_session():
    global _session_file, _commands_file, _errors_file, _session_id

    _ensure_dirs()

    _session_id = datetime.now().strftime('%Y%m%d_%H%M%S_%f')

    session_path = os.path.join(LOG_DIR, 'sessions', f'session_{_session_id}.jsonl')
    commands_path = os.path.join(LOG_DIR, 'commands', f'commands_{_session_id}.log')
    errors_path = os.path.join(LOG_DIR, 'errors', f'errors_{_session_id}.log')

    with _lock:
        if _session_file:
            _session_file.close()
        if _commands_file:
            _commands_file.close()
        if _errors_file:
            _errors_file.close()

        _session_file = None
        _commands_file = None
        _errors_file = None

        _session_file = open(session_path, 'w', encoding='utf-8')
        _commands_file = open(commands_path, 'w', encoding='utf-8')
        _errors_file = open(errors_path, 'w', encoding='utf-8')

    _write_session({'event': 'session_start', 'session_id': _session_id})


def _now():
    return datetime.now().strftime('%H:%M:%S.%f')[:-3]


def _write_session(entry):
    with _lock:
        if _session_file is None:
            return

        payload = dict(entry)
        payload['time'] = _now()
        _session_file.write(json.dumps(payload, ensure_ascii=False) + '\n')
        _session_file.flush()


def _write_commands(line):
    with _lock:
        if _commands_file is None:
            return

        _commands_file.write(f'[{_now()}]  {line}\n')
        _commands_file.flush()


def _write_errors(line):
    with _lock:
        if _errors_file is None:
            return

        _errors_file.write(f'[{_now()}]  {line}\n')
        _errors_file.flush()


def _pretty_value(value):
    text = str(value).strip()
    if not text:
        return text
    return text.title()


def log_move(direction, x, y):
    entry = {'event': 'move', 'direction': direction, 'x': x, 'y': y}
    _write_session(entry)
    _write_commands(f'Move ({_pretty_value(direction)}) -> ({x}, {y})')


def log_paint(x, y, color):
    entry = {'event': 'paint', 'x': x, 'y': y, 'color': color}
    _write_session(entry)
    _write_commands(f'Paint ({_pretty_value(color)}) @ ({x}, {y})')


def log_sensor(sensor, value, x, y):
    entry = {'event': 'sensor', 'sensor': sensor, 'value': value, 'x': x, 'y': y}
    _write_session(entry)
    _write_commands(f"Sense {sensor.replace('_', ' ').title()} = {value} @ ({x}, {y})")


def log_wall_check(direction, result, x, y):
    entry = {'event': 'wall_check', 'direction': direction, 'result': result, 'x': x, 'y': y}
    _write_session(entry)
    _write_commands(f'Has Wall ({_pretty_value(direction)}) = {result} @ ({x}, {y})')


def log_error(message, x=None, y=None):
    entry = {'event': 'error', 'message': message}
    if x is not None:
        entry['x'] = x
    if y is not None:
        entry['y'] = y
    _write_session(entry)
    _write_errors(message)


def log_code_error(exc_type, message, line_no=None):
    entry = {'event': 'code_error', 'exc_type': exc_type, 'message': message}
    if line_no is not None:
        entry['line_no'] = line_no
    _write_session(entry)
    _write_errors(f'{exc_type}: {message}' + (f'  (line {line_no})' if line_no else ''))


def close():
    global _session_file, _commands_file, _errors_file

    with _lock:
        for f in (_session_file, _commands_file, _errors_file):
            if f:
                try:
                    f.close()
                except Exception:
                    pass

        _session_file = None
        _commands_file = None
        _errors_file = None