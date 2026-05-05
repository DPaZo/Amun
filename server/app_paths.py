import os

_ENV_KEY = 'AMUN_WORKSPACE'


def _normalize_dir(path):
    return os.path.abspath(os.path.expanduser(str(path)))


def set_workspace_dir(path):
    if not path:
        return

    os.environ[_ENV_KEY] = _normalize_dir(path)


def get_workspace_dir():
    value = str(os.environ.get(_ENV_KEY, '')).strip()

    if value:
        base = _normalize_dir(value)
    else:
        base = _normalize_dir(os.getcwd())

    os.makedirs(base, exist_ok=True)
    return base


def get_worlds_dir():
    path = os.path.join(get_workspace_dir(), 'worlds')
    os.makedirs(path, exist_ok=True)
    return path


def get_logs_dir():
    path = os.path.join(get_workspace_dir(), 'logs')
    os.makedirs(path, exist_ok=True)
    return path


def get_lang_prefs_path():
    return os.path.join(get_worlds_dir(), '.lang')


def get_prefs_path():
    return os.path.join(get_worlds_dir(), '.prefs')


def get_last_world_path():
    return os.path.join(get_worlds_dir(), '.last_world')