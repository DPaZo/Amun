NORTH = 'NORTH'
SOUTH = 'SOUTH'
EAST = 'EAST'
WEST = 'WEST'

DIRECTIONS = (NORTH, SOUTH, EAST, WEST)

DELTAS = {
    NORTH: (0, -1),
    SOUTH: (0, 1),
    EAST: (1, 0),
    WEST: (-1, 0),
}


def _normalize_orientation(value):
    orientation = str(value).lower()

    if orientation in ('h', 'horizontal'):
        return 'h'
    if orientation in ('v', 'vertical'):
        return 'v'

    return None


def _normalize_direction(value):
    direction = str(value).upper()
    if direction in DIRECTIONS:
        return direction
    return EAST


class World:
    def __init__(self, width=10, height=10):
        self.width = max(1, int(width))
        self.height = max(1, int(height))
        self.walls = set()
        self.colors = {}
        self.temperature = {}
        self.radiation = {}

    def add_wall(self, x, y, orientation):
        orientation = _normalize_orientation(orientation)
        if orientation is None:
            return

        x = int(x)
        y = int(y)

        if self.in_bounds(x, y):
            self.walls.add((x, y, orientation))

    def remove_wall(self, x, y, orientation):
        orientation = _normalize_orientation(orientation)
        if orientation is None:
            return

        x = int(x)
        y = int(y)

        self.walls.discard((x, y, orientation))

        if orientation == 'h':
            self.walls.discard((x, y, 'horizontal'))
        else:
            self.walls.discard((x, y, 'vertical'))

    def has_wall_between(self, x1, y1, x2, y2):
        dx = x2 - x1
        dy = y2 - y1

        if dx == 1:
            return (x1, y1, 'v') in self.walls or (x1, y1, 'vertical') in self.walls
        if dx == -1:
            return (x2, y2, 'v') in self.walls or (x2, y2, 'vertical') in self.walls
        if dy == 1:
            return (x1, y1, 'h') in self.walls or (x1, y1, 'horizontal') in self.walls
        if dy == -1:
            return (x2, y2, 'h') in self.walls or (x2, y2, 'horizontal') in self.walls

        return False

    def in_bounds(self, x, y):
        return 0 <= x < self.width and 0 <= y < self.height

    def set_color(self, x, y, color):
        x = int(x)
        y = int(y)

        if self.in_bounds(x, y):
            self.colors[(x, y)] = str(color)

    def get_color(self, x, y):
        return self.colors.get((int(x), int(y)), None)

    def set_temperature(self, x, y, value):
        x = int(x)
        y = int(y)

        if self.in_bounds(x, y):
            self.temperature[(x, y)] = float(value)

    def get_temperature(self, x, y):
        return self.temperature.get((int(x), int(y)), 0.0)

    def set_radiation(self, x, y, value):
        x = int(x)
        y = int(y)

        if self.in_bounds(x, y):
            self.radiation[(x, y)] = float(value)

    def get_radiation(self, x, y):
        return self.radiation.get((int(x), int(y)), 0.0)

    def clear(self):
        self.walls.clear()
        self.colors.clear()
        self.temperature.clear()
        self.radiation.clear()

    def to_dict(self):
        return {
            'width': self.width,
            'height': self.height,
            'walls': [[x, y, d] for (x, y, d) in self.walls],
            'colors': [[x, y, c] for (x, y), c in self.colors.items()],
            'temperature': [[x, y, v] for (x, y), v in self.temperature.items()],
            'radiation': [[x, y, v] for (x, y), v in self.radiation.items()],
        }

    def apply_dict(self, data):
        if 'width' in data:
            self.width = max(1, int(data['width']))
        if 'height' in data:
            self.height = max(1, int(data['height']))

        self.walls.clear()
        for x, y, d in (data.get('walls') or []):
            self.add_wall(x, y, d)

        self.colors.clear()
        for x, y, c in (data.get('colors') or []):
            self.set_color(x, y, c)

        self.temperature.clear()
        for x, y, v in (data.get('temperature') or []):
            self.set_temperature(x, y, v)

        self.radiation.clear()
        for x, y, v in (data.get('radiation') or []):
            self.set_radiation(x, y, v)