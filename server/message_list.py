import threading

_lock = threading.Lock()
_entries = []


def add(entry):
    with _lock:
        _entries.append(dict(entry))


def get_all():
    with _lock:
        return list(_entries)


def get_last(n=1):
    with _lock:
        return list(_entries[-n:])


def clear():
    with _lock:
        _entries.clear()


def count():
    with _lock:
        return len(_entries)
