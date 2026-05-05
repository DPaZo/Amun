import asyncio
import json
import threading

import websockets

HOST = 'localhost'
PORT = 8765
MAX_RETRIES = 10
RETRY_DELAY = 0.5

_loop = None
_ws = None
_thread = None
_connected = False


def _start_event_loop():
    global _loop, _thread

    _loop = asyncio.new_event_loop()
    _thread = threading.Thread(target=_loop.run_forever, daemon=True)
    _thread.start()


async def _connect():
    global _ws, _connected

    uri = f'ws://{HOST}:{PORT}'
    last_err = None

    for attempt in range(1, MAX_RETRIES + 1):
        try:
            _ws = await websockets.connect(
                uri,
                ping_interval=None,
                open_timeout=5,
            )
            _connected = True
            print('[client] connected to server')
            return
        except Exception as e:
            last_err = e
            print(f'[client] waiting for server (attempt {attempt}/{MAX_RETRIES})...')
            await asyncio.sleep(RETRY_DELAY)

    raise RuntimeError(f'[client] could not connect to server after {MAX_RETRIES} attempts: {last_err}')


def connect():
    if _loop is None:
        _start_event_loop()
    future = asyncio.run_coroutine_threadsafe(_connect(), _loop)
    future.result(timeout=15)


async def _send_and_receive(message):
    raw = json.dumps(message)
    await _ws.send(raw)
    response_raw = await _ws.recv()
    return json.loads(response_raw)


def send(message):
    global _connected
    if not _connected:
        connect()

    if _ws is None:
        raise RuntimeError('[client] not connected to server')

    if getattr(_ws, 'closed', False):
        raise RuntimeError('[client] connection is closed')

    future = asyncio.run_coroutine_threadsafe(
        _send_and_receive(message),
        _loop,
    )
    try:
        return future.result(timeout=10)
    except Exception as e:
        _connected = False
        raise RuntimeError(f'[client] communication error: {e}')


def close():
    global _ws, _connected
    _connected = False
    if _ws and _loop:
        asyncio.run_coroutine_threadsafe(_ws.close(), _loop)
        _ws = None