import asyncio
import concurrent.futures
import json
import os
import sys
import threading
import time

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import websockets

from server import engine, logger, message_list
from server.app_paths import get_worlds_dir
from server.server_robot import Robot
from server.world import World

HOST = 'localhost'
ROBOT_PORT = 8765
GUI_PORT = 8766

STATE_DIR = get_worlds_dir()

_loop = None
_server_thread = None
_robot_server = None
_gui_server = None
_gui_clients = set()
_shutdown_event = threading.Event()
_state_lock = threading.Lock()
_connection_lock = threading.Lock()
_active_connection = False
connection_error = 'This server is already in use by another client'


def _normalize_world_name(name):
    value = str(name).strip()

    if not value:
        return ''

    if value in {'.', '..'}:
        return ''

    if '/' in value or '\\' in value:
        return ''

    return value


def _write_last_world_name(name):
    name = _normalize_world_name(name)
    if not name:
        raise ValueError('Invalid world name')

    os.makedirs(STATE_DIR, exist_ok=True)

    last_path = os.path.join(STATE_DIR, '.last_world')
    with open(last_path, 'w', encoding='utf-8') as f:
        f.write(name)


def _load_world_file():
    last_file = os.path.join(STATE_DIR, '.last_world')
    if not os.path.exists(last_file):
        return

    try:
        with open(last_file, 'r', encoding='utf-8') as f:
            name = _normalize_world_name(f.read().strip())

        if not name:
            return

        world_file = os.path.join(STATE_DIR, f'{name}.world')
        if not os.path.exists(world_file):
            return

        _load_world_file_by_path(world_file)
    except (OSError, UnicodeError, ValueError) as e:
        print(f'[server] world load error: {e}')


def _save_world_file(name):
    name = _normalize_world_name(name)
    if not name:
        raise ValueError('Invalid world name')

    os.makedirs(STATE_DIR, exist_ok=True)
    filename = os.path.join(STATE_DIR, f'{name}.world')

    w = engine.get_world()
    r = engine.get_robot()

    with open(filename, 'w', encoding='utf-8') as f:
        f.write(f'{w.width}x{w.height}\n')
        if w.walls:
            f.write('WALLS: ' + ' '.join(f'{x},{y},{d}' for x, y, d in w.walls) + '\n')
        if w.colors:
            f.write('COLORS: ' + ' '.join(f'{x},{y},{c}' for (x, y), c in w.colors.items()) + '\n')
        if w.temperature:
            f.write('TEMP: ' + ' '.join(f'{x},{y},{v}' for (x, y), v in w.temperature.items()) + '\n')
        if w.radiation:
            f.write('RAD: ' + ' '.join(f'{x},{y},{v}' for (x, y), v in w.radiation.items()) + '\n')
        f.write(f'ROBOT: {r.x},{r.y},{r.direction}\n')

    _write_last_world_name(name)
    print(f'[server] saved world: {name}')


def _load_named_world(name):
    name = _normalize_world_name(name)
    if not name:
        raise ValueError('Invalid world name')

    world_file = os.path.join(STATE_DIR, f'{name}.world')
    if not os.path.exists(world_file):
        raise FileNotFoundError(f'World not found: {name}')

    _load_world_file_by_path(world_file)
    _write_last_world_name(name)
    print(f'[server] loaded world: {name}')


def _delete_named_world(name):
    name = _normalize_world_name(name)
    if not name:
        raise ValueError('Invalid world name')

    world_file = os.path.join(STATE_DIR, f'{name}.world')
    if not os.path.exists(world_file):
        raise FileNotFoundError(f'World not found: {name}')

    os.remove(world_file)

    last_path = os.path.join(STATE_DIR, '.last_world')
    try:
        if os.path.exists(last_path):
            with open(last_path, 'r', encoding='utf-8') as f:
                last_name = _normalize_world_name(f.read().strip())

            if last_name == name:
                files = _get_world_list()
                if files:
                    _write_last_world_name(files[0])
                else:
                    os.remove(last_path)
    except OSError:
        pass

    print(f'[server] deleted world: {name}')


def _load_world_file_by_path(path):
    w = engine.get_world()
    r = engine.get_robot()

    w.walls.clear()
    w.colors.clear()
    w.temperature.clear()
    w.radiation.clear()

    with open(path, 'r', encoding='utf-8') as f:
        lines = [line.strip() for line in f.readlines() if line.strip()]

    if lines and 'x' in lines[0]:
        sz = lines[0].split('x')
        w.width = int(sz[0])
        w.height = int(sz[1])
        lines = lines[1:]

    for line in lines:
        if line.startswith('WALLS:'):
            for spec in line.replace('WALLS:', '').strip().split():
                try:
                    x, y, d = spec.split(',')
                    w.walls.add((int(x), int(y), d))
                except (ValueError, IndexError):
                    pass

        elif line.startswith('COLORS:'):
            for spec in line.replace('COLORS:', '').strip().split():
                try:
                    parts = spec.split(',')
                    w.colors[(int(parts[0]), int(parts[1]))] = str(parts[2])
                except (ValueError, IndexError):
                    pass

        elif line.startswith('TEMP:'):
            for spec in line.replace('TEMP:', '').strip().split():
                try:
                    x, y, v = spec.split(',')
                    w.temperature[(int(x), int(y))] = float(v)
                except (ValueError, IndexError):
                    pass

        elif line.startswith('RAD:'):
            for spec in line.replace('RAD:', '').strip().split():
                try:
                    x, y, v = spec.split(',')
                    w.radiation[(int(x), int(y))] = float(v)
                except (ValueError, IndexError):
                    pass

        elif line.startswith('ROBOT:'):
            try:
                parts = line.replace('ROBOT:', '').strip().split(',')
                r.x = int(parts[0])
                r.y = int(parts[1])
                r.direction = str(parts[2]).upper()
                r.alive = True
            except (ValueError, IndexError):
                pass

    r.start_x = r.x
    r.start_y = r.y
    r.start_direction = r.direction
    engine.set_baseline_from_current()


def _get_world_list():
    try:
        return sorted(
            [f.replace('.world', '') for f in os.listdir(STATE_DIR) if f.endswith('.world')]
        )
    except OSError:
        return []


def _init_world():
    world = World(10, 10)
    robot = Robot(world, 0, 0, 'EAST')
    engine.init(world, robot)
    _load_world_file()


def _make_snapshot():
    robot = engine.get_robot()
    world = engine.get_world()

    if robot is None or world is None:
        return {
            'type': 'snapshot',
            'ts': time.time(),
            'robot': {},
            'world': {},
            'hit_wall': None,
        }

    return {
        'type': 'snapshot',
        'ts': time.time(),
        'robot': robot.to_dict(),
        'world': world.to_dict(),
        'hit_wall': engine.get_last_hit_wall(),
    }


def _acquire_connection():
    global _active_connection

    with _connection_lock:
        if _active_connection:
            return False
        _active_connection = True
        return True


def _release_connection():
    global _active_connection

    with _connection_lock:
        _active_connection = False


def broadcast_to_gui(event):
    if _loop is None:
        return

    asyncio.run_coroutine_threadsafe(
        _broadcast_all(json.dumps(event)),
        _loop,
    )


async def _broadcast_all(message):
    dead = set()

    for ws in list(_gui_clients):
        try:
            await ws.send(message)
        except websockets.ConnectionClosed:
            dead.add(ws)
        except OSError:
            dead.add(ws)

    _gui_clients.difference_update(dead)


async def _robot_handler(websocket):
    if not _acquire_connection():
        await websocket.send(json.dumps({'type': 'error', 'message': connection_error}))
        await websocket.close()
        return

    print('[server] program started')
    broadcast_to_gui({'type': 'program_started'})

    try:
        async for raw in websocket:
            try:
                data = json.loads(raw)
            except json.JSONDecodeError:
                await websocket.send(json.dumps({'type': 'error', 'message': 'Invalid JSON'}))
                continue

            if data.get('type') == 'set_edit_mode':
                broadcast_to_gui({'type': 'set_edit_mode', 'value': bool(data.get('value', False))})
                await websocket.send(json.dumps({'type': 'set_edit_mode_result', 'ok': True}))
                continue

            with _state_lock:
                response = engine.handle_command(data)

            await websocket.send(json.dumps(response))

            t = response.get('type', '')

            if t == 'reset_result':
                broadcast_to_gui({'type': 'reset_result'})

            if t == 'sense_result':
                broadcast_to_gui(response)

            if t in ('move_result', 'paint_result', 'sense_result', 'bool_result', 'reset_result'):
                broadcast_to_gui(_make_snapshot())

            if t == 'stop_result':
                broadcast_to_gui({'type': 'program_stopped'})

            if t == 'error':
                broadcast_to_gui(response)

    except websockets.ConnectionClosed:
        pass
    except OSError as e:
        print(f'[server] robot handler error: {e}')
    finally:
        _release_connection()
        print('[server] program finished')
        broadcast_to_gui({'type': 'program_finished'})


async def _gui_handler(websocket):
    _gui_clients.add(websocket)
    print('[server] GUI client connected')

    await websocket.send(json.dumps(_make_snapshot()))

    try:
        async for raw in websocket:
            try:
                data = json.loads(raw)
            except json.JSONDecodeError:
                continue

            t = data.get('type', '')

            if t == 'client_snapshot':
                try:
                    snap = data.get('snapshot') or {}
                    with _state_lock:
                        engine.get_world().apply_dict(snap.get('world') or {})
                        r = engine.get_robot()
                        r.apply_dict(snap.get('robot') or {})
                        r.start_x = r.x
                        r.start_y = r.y
                        r.start_direction = r.direction
                        engine.set_baseline_from_current()
                        engine.clear_last_hit_wall()
                    broadcast_to_gui(_make_snapshot())
                except (TypeError, ValueError, AttributeError):
                    pass

            elif t == 'save_world':
                name = _normalize_world_name(data.get('name') or '')
                if not name:
                    await websocket.send(json.dumps({'type': 'error', 'message': 'Invalid world name'}))
                    continue

                try:
                    with _state_lock:
                        _save_world_file(name)
                    await websocket.send(json.dumps({'type': 'save_world_result', 'ok': True, 'name': name}))
                    broadcast_to_gui({'type': 'world_list', 'files': _get_world_list()})
                except (OSError, ValueError) as e:
                    await websocket.send(json.dumps({'type': 'error', 'message': str(e)}))

            elif t == 'load_world':
                name = _normalize_world_name(data.get('name') or '')
                if not name:
                    await websocket.send(json.dumps({'type': 'error', 'message': 'Invalid world name'}))
                    continue

                try:
                    with _state_lock:
                        _load_named_world(name)
                        engine.clear_last_hit_wall()
                    broadcast_to_gui(_make_snapshot())
                except (OSError, ValueError) as e:
                    await websocket.send(json.dumps({'type': 'error', 'message': str(e)}))

            elif t == 'get_world_list':
                files = _get_world_list()
                await websocket.send(json.dumps({'type': 'world_list', 'files': files}))

            elif t == 'delete_world':
                name = _normalize_world_name(data.get('name') or '')
                if not name:
                    await websocket.send(json.dumps({'type': 'error', 'message': 'Invalid world name'}))
                    continue

                try:
                    with _state_lock:
                        _delete_named_world(name)
                        files = _get_world_list()
                    await websocket.send(json.dumps({
                        'type': 'delete_world_result',
                        'ok': True,
                        'name': name,
                        'files': files,
                    }))
                    broadcast_to_gui({'type': 'world_list', 'files': files})
                except (OSError, ValueError) as e:
                    await websocket.send(json.dumps({'type': 'error', 'message': str(e)}))

            elif t == 'set_edit_mode':
                broadcast_to_gui({'type': 'set_edit_mode', 'value': bool(data.get('value', False))})

    except websockets.ConnectionClosed:
        pass
    except OSError as e:
        print(f'[server] GUI handler error: {e}')
    finally:
        _gui_clients.discard(websocket)
        print('[server] GUI client disconnected')


async def _run():
    global _robot_server, _gui_server

    try:
        _robot_server = await websockets.serve(
            _robot_handler,
            HOST,
            ROBOT_PORT,
            ping_interval=None,
        )
        _gui_server = await websockets.serve(
            _gui_handler,
            HOST,
            GUI_PORT,
            ping_interval=None,
        )
    except OSError:
        raise RuntimeError('Port already in use — another instance is running')

    print(f'[server] robot port {ROBOT_PORT}  |  GUI port {GUI_PORT}')

    await asyncio.gather(
        _robot_server.wait_closed(),
        _gui_server.wait_closed(),
    )


def start():
    global _loop, _server_thread

    if _loop and _server_thread and _server_thread.is_alive():
        return

    _shutdown_event.clear()
    _init_world()
    logger.new_session()
    message_list.clear()

    _loop = asyncio.new_event_loop()
    _server_thread = threading.Thread(target=_loop.run_forever, daemon=True)
    _server_thread.start()

    future = asyncio.run_coroutine_threadsafe(_run(), _loop)
    time.sleep(0.2)

    try:
        future.result(timeout=0.2)
    except concurrent.futures.TimeoutError:
        print('[server] started')
        return
    except Exception:
        if _loop:
            _loop.call_soon_threadsafe(_loop.stop)
        if _server_thread and _server_thread.is_alive():
            _server_thread.join(timeout=1)
        _loop = None
        _server_thread = None
        raise

    print('[server] started')


def stop():
    global _loop, _server_thread, _robot_server, _gui_server, _active_connection

    _shutdown_event.set()
    logger.close()

    if _robot_server and _loop:
        _loop.call_soon_threadsafe(_robot_server.close)

    if _gui_server and _loop:
        _loop.call_soon_threadsafe(_gui_server.close)

    if _loop:
        close_futures = []
        for ws in list(_gui_clients):
            close_futures.append(asyncio.run_coroutine_threadsafe(ws.close(), _loop))

        for future in close_futures:
            try:
                future.result(timeout=0.5)
            except Exception:
                pass

        _loop.call_soon_threadsafe(_loop.stop)

    if _server_thread and _server_thread.is_alive():
        _server_thread.join(timeout=1)

    with _connection_lock:
        _active_connection = False

    _gui_clients.clear()
    _robot_server = None
    _gui_server = None
    _loop = None
    _server_thread = None


def wait_forever():
    _shutdown_event.wait()


if __name__ == '__main__':
    start()
    wait_forever()