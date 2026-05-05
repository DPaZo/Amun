from client import connection
from client.values import (
    Color, Direction, require_color, require_direction
)


def _send(message):
    return connection.send(message)


def _require_ok(response):
    if not response.get('ok', False):
        raise RuntimeError(response.get('error', 'Robot error'))

    return response


def move(direction, steps=1):
    direction = require_direction(direction)

    try:
        steps = int(steps)
    except Exception as e:
        raise TypeError('steps must be an integer') from e

    if steps <= 0:
        return 0

    moved = 0
    for _ in range(steps):
        result = _send({'type': 'move', 'direction': direction})
        _require_ok(result)
        moved += 1

    return moved


def walk(direction, steps=1):
    return move(direction, steps)


def paint(color=None):
    msg = {'type': 'paint'}
    color = require_color(color, optional=True)

    if color is not None:
        msg['color'] = color

    result = _send(msg)
    _require_ok(result)


def pick_color(color):
    color = require_color(color)
    result = _send({'type': 'pick_color', 'color': color})
    _require_ok(result)


def sense_color():
    result = _send({'type': 'sense_color'})
    return result.get('value', None)


def has_color():
    result = _send({'type': 'has_color'})
    return bool(result.get('value', False))


def sense_temperature():
    result = _send({'type': 'sense_temperature'})
    return float(result.get('value', 0.0))


def sense_radiation():
    result = _send({'type': 'sense_radiation'})
    return float(result.get('value', 0.0))


def has_wall(direction):
    direction = require_direction(direction)
    result = _send({'type': 'has_wall', 'direction': direction})
    return bool(result.get('value', False))


def has_border_wall(direction):
    direction = require_direction(direction)
    result = _send({'type': 'has_border_wall', 'direction': direction})
    return bool(result.get('value', False))


def reset(clear_world=False):
    result = _send({'type': 'reset', 'clear_world': bool(clear_world)})
    _require_ok(result)
    return result


def run_edit_mode():
    result = _send({'type': 'set_edit_mode', 'value': True})
    _require_ok(result)
    return result


def stop():
    result = _send({'type': 'stop'})
    _require_ok(result)
    return result