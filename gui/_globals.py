import os
import json
from server.app_paths import get_prefs_path, get_workspace_dir, get_worlds_dir

CELL_SIZE = 64
VIEWER_MODE = True

_BASE_DIR = get_workspace_dir()
_WORLDS_DIR = get_worlds_dir()


class _WorldState:
    def __init__(self):
        self.width = 10
        self.height = 10
        self.walls = set()
        self.colors = {}
        self.temperature = {}
        self.radiation = {}
        self.discovered_sensors = set()

    def add_wall(self, x, y, orientation):
        self.walls.add((int(x), int(y), str(orientation)))

    def remove_wall(self, x, y, orientation):
        self.walls.discard((int(x), int(y), str(orientation)))


class _RobotState:
    def __init__(self):
        self.x = 0
        self.y = 0
        self.direction = 'EAST'
        self.alive = True


world = _WorldState()
robot = _RobotState()


def set_viewer_mode(value: bool):
    global VIEWER_MODE
    VIEWER_MODE = value


_PREFS_PATH = get_prefs_path()

def save_prefs(dark_mode: bool):
    with open(_PREFS_PATH, 'w') as f:
        json.dump({'dark_mode': dark_mode}, f)


def load_prefs():
    try:
        with open(_PREFS_PATH, 'r') as f:
            return json.load(f)
    except Exception:
        return {'dark_mode': False}