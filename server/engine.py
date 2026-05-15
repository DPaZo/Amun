import time

from server import logger, message_list
from server.world import DELTAS

_world = None
_robot = None
_baseline_world = None
_baseline_robot = None
_last_hit_wall = None


def init(world, robot):
    global _world, _robot

    _world = world
    _robot = robot
    set_baseline_from_current()


def get_world():
    return _world


def get_robot():
    return _robot


def get_last_hit_wall():
    if _last_hit_wall is None:
        return None

    return dict(_last_hit_wall)


def clear_last_hit_wall():
    global _last_hit_wall
    _last_hit_wall = None


def _set_last_hit_wall(x, y, orientation):
    global _last_hit_wall

    _last_hit_wall = {
        'x': int(x),
        'y': int(y),
        'orientation': str(orientation),
    }


def _collision_wall_for_direction(x, y, direction):
    if direction == 'EAST':
        return x, y, 'v'
    if direction == 'WEST':
        return x - 1, y, 'v'
    if direction == 'SOUTH':
        return x, y, 'h'
    return x, y - 1, 'h'


def _move_fail(direction, reason):
    _robot.alive = False

    wx, wy, wd = _collision_wall_for_direction(_robot.x, _robot.y, direction)
    _set_last_hit_wall(wx, wy, wd)

    msg = f'{reason} while moving {direction.title()} from ({_robot.x}, {_robot.y})'
    logger.log_error(msg, _robot.x, _robot.y)
    print(f'[error] {msg}')
    message_list.add({'type': 'error', 'message': msg})

    return {
        'type': 'move_result',
        'ok': False,
        'error': msg,
        'robot': _robot.to_dict(),
        'hit_wall': get_last_hit_wall(),
    }


def _require_runtime():
    if _world is None or _robot is None:
        return {'type': 'error', 'message': 'Runtime not initialized'}
    return None


def _parse_direction(data):
    direction = str(data.get('direction', '')).upper()
    if direction not in DELTAS:
        return None
    return direction


def _normalize_color_value(color):
    return str(color).strip().lower()


def _sleep_for_robot_speed():
    try:
        delay = float(getattr(_robot, 'speed', 0))
    except (TypeError, ValueError):
        delay = 0.0

    if delay > 0:
        time.sleep(delay)


def set_baseline_from_current():
    global _baseline_world, _baseline_robot

    if _world is None or _robot is None:
        return

    _baseline_world = _world.to_dict(include_runtime=False)
    _baseline_robot = {
        'x': _robot.start_x,
        'y': _robot.start_y,
        'direction': _robot.start_direction,
        'alive': True,
        'speed': _robot.speed,
    }


def restore_baseline():
    if _baseline_world is None or _baseline_robot is None:
        _robot.reset()
        return

    _world.apply_dict(_baseline_world)
    _robot.apply_dict(_baseline_robot)
    _robot.start_x = int(_baseline_robot['x'])
    _robot.start_y = int(_baseline_robot['y'])
    _robot.start_direction = str(_baseline_robot['direction']).upper()
    _robot.alive = True


def handle_command(data):
    if not isinstance(data, dict):
        return {'type': 'error', 'message': 'Command payload must be an object'}

    runtime_error = _require_runtime()
    if runtime_error is not None:
        return runtime_error

    cmd = str(data.get('type', '')).lower()

    if cmd == 'move':
        return _cmd_move(data)
    if cmd == 'paint':
        return _cmd_paint(data)
    if cmd == 'pick_color':
        return _cmd_pick_color(data)
    if cmd == 'sense_color':
        return _cmd_sense_color()
    if cmd == 'has_color':
        return _cmd_has_color()
    if cmd == 'sense_temperature':
        return _cmd_sense_temperature()
    if cmd == 'sense_radiation':
        return _cmd_sense_radiation()
    if cmd == 'has_wall':
        return _cmd_has_wall(data)
    if cmd == 'has_border_wall':
        return _cmd_has_border_wall(data)
    if cmd == 'reset':
        return _cmd_reset(data)
    if cmd == 'snapshot_request':
        return _cmd_snapshot()
    if cmd == 'stop':
        return _cmd_stop()

    return {'type': 'error', 'message': f'Unknown command: {cmd}'}


def _cmd_move(data):
    direction = _parse_direction(data)
    if direction is None:
        raw_direction = str(data.get('direction', '')).upper()
        return {'type': 'error', 'message': f'Unknown direction: {raw_direction}'}

    _robot.direction = direction
    dx, dy = DELTAS[direction]
    nx, ny = _robot.x + dx, _robot.y + dy

    if not _world.in_bounds(nx, ny):
        return _move_fail(direction, 'Out of bounds')

    if _world.has_wall_between(_robot.x, _robot.y, nx, ny):
        return _move_fail(direction, 'Wall hit')

    clear_last_hit_wall()
    _robot.x = nx
    _robot.y = ny

    logger.log_move(direction, _robot.x, _robot.y)
    message_list.add({'type': 'move', 'direction': direction, 'x': _robot.x, 'y': _robot.y})
    print(f'[robot] Move ({direction.title()}) -> ({_robot.x}, {_robot.y})')

    _sleep_for_robot_speed()

    return {
        'type': 'move_result',
        'ok': True,
        'x': _robot.x,
        'y': _robot.y,
        'robot': _robot.to_dict(),
    }


def _cmd_paint(data):
    color = data.get('color', None)

    if color is None:
        if _robot.paint_color is not None:
            color = _robot.paint_color
        else:
            return {'type': 'error', 'message': 'No color set — use pick_color() first or pass a color to paint()'}

    color = _normalize_color_value(color)
    if not color:
        return {'type': 'error', 'message': 'Color must not be empty'}

    _world.set_color(_robot.x, _robot.y, color, runtime=True)

    logger.log_paint(_robot.x, _robot.y, color)
    message_list.add({'type': 'paint', 'x': _robot.x, 'y': _robot.y, 'color': color})
    print(f'[robot] Paint ({color.title()}) @ ({_robot.x}, {_robot.y})')

    return {
        'type': 'paint_result',
        'ok': True,
        'x': _robot.x,
        'y': _robot.y,
        'color': color,
    }


def _cmd_pick_color(data):
    color = _normalize_color_value(data.get('color', ''))
    if not color:
        return {'type': 'error', 'message': 'Color must not be empty'}

    _robot.paint_color = color
    return {'type': 'pick_color_result', 'ok': True, 'color': color}


def _cmd_sense_color():
    color = _world.get_color(_robot.x, _robot.y)
    logger.log_sensor('color', color, _robot.x, _robot.y)
    print(f'[robot] Sense Color = {str(color).title() if color is not None else None} @ ({_robot.x}, {_robot.y})')
    message_list.add({'type': 'sensor', 'sensor': 'color', 'value': color, 'x': _robot.x, 'y': _robot.y})
    return {'type': 'sense_result', 'sensor': 'color', 'value': color}


def _cmd_has_color():
    result = _world.has_color(_robot.x, _robot.y)
    return {'type': 'bool_result', 'command': 'has_color', 'value': result}


def _cmd_sense_temperature():
    val = _world.get_temperature(_robot.x, _robot.y)
    logger.log_sensor('temperature', val, _robot.x, _robot.y)
    print(f'[robot] Sense Temperature = {val} @ ({_robot.x}, {_robot.y})')
    message_list.add({'type': 'sensor', 'sensor': 'temperature', 'value': val, 'x': _robot.x, 'y': _robot.y})
    return {'type': 'sense_result', 'sensor': 'temperature', 'value': val}


def _cmd_sense_radiation():
    val = _world.get_radiation(_robot.x, _robot.y)
    logger.log_sensor('radiation', val, _robot.x, _robot.y)
    print(f'[robot] Sense Radiation = {val} @ ({_robot.x}, {_robot.y})')
    message_list.add({'type': 'sensor', 'sensor': 'radiation', 'value': val, 'x': _robot.x, 'y': _robot.y})
    return {'type': 'sense_result', 'sensor': 'radiation', 'value': val}


def _cmd_has_wall(data):
    direction = _parse_direction(data)
    if direction is None:
        raw_direction = str(data.get('direction', '')).upper()
        return {'type': 'error', 'message': f'Unknown direction: {raw_direction}'}

    result = _robot.check_wall(direction)
    logger.log_wall_check(direction, result, _robot.x, _robot.y)
    print(f'[robot] Has Wall ({direction.title()}) = {result} @ ({_robot.x}, {_robot.y})')
    message_list.add({'type': 'wall_check', 'direction': direction, 'result': result, 'x': _robot.x, 'y': _robot.y})
    return {'type': 'bool_result', 'command': 'has_wall', 'value': result}


def _cmd_has_border_wall(data):
    direction = _parse_direction(data)
    if direction is None:
        raw_direction = str(data.get('direction', '')).upper()
        return {'type': 'error', 'message': f'Unknown direction: {raw_direction}'}

    result = _robot.check_border_wall(direction)
    return {'type': 'bool_result', 'command': 'has_border_wall', 'value': result}


def _cmd_reset(data):
    if bool(data.get('clear_world', False)):
        restore_baseline()
    else:
        _robot.reset()

    clear_last_hit_wall()
    message_list.clear()
    return {
        'type': 'reset_result',
        'ok': True,
        'robot': _robot.to_dict(),
        'world': _world.to_dict(include_runtime=True),
    }


def _cmd_snapshot():
    return {
        'type': 'snapshot',
        'ts': time.time(),
        'robot': _robot.to_dict(),
        'world': _world.to_dict(include_runtime=True),
        'hit_wall': get_last_hit_wall(),
    }


def _cmd_stop():
    print('[server] program finished')
    message_list.add({'type': 'stop'})
    return {'type': 'stop_result', 'ok': True}