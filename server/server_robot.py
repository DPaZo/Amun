from server.world import DELTAS, EAST, NORTH, SOUTH, WEST


def _normalize_direction(value):
    direction = str(value).upper()
    if direction in DELTAS:
        return direction
    return EAST


class Robot:
    def __init__(self, world, x=0, y=0, direction=EAST):
        self.world = world
        self.x = int(x)
        self.y = int(y)
        self.direction = _normalize_direction(direction)
        self.alive = True
        self.paint_color = None
        self.speed = 0.4

        self.start_x = self.x
        self.start_y = self.y
        self.start_direction = self.direction

    def reset(self):
        self.x = self.start_x
        self.y = self.start_y
        self.direction = _normalize_direction(self.start_direction)
        self.alive = True

    def check_wall(self, direction):
        direction = str(direction).upper()
        if direction not in DELTAS:
            return False

        dx, dy = DELTAS[direction]
        nx, ny = self.x + dx, self.y + dy

        if not self.world.in_bounds(nx, ny):
            return True

        return self.world.has_wall_between(self.x, self.y, nx, ny)

    def check_border_wall(self, direction):
        direction = str(direction).upper()

        if direction == NORTH:
            return self.y == 0
        if direction == SOUTH:
            return self.y == self.world.height - 1
        if direction == EAST:
            return self.x == self.world.width - 1
        if direction == WEST:
            return self.x == 0

        return False

    def to_dict(self):
        return {
            'x': self.x,
            'y': self.y,
            'direction': self.direction,
            'alive': self.alive,
            'speed': self.speed,
        }

    def apply_dict(self, data):
        if 'x' in data:
            self.x = int(data['x'])
        if 'y' in data:
            self.y = int(data['y'])
        if data.get('direction'):
            self.direction = _normalize_direction(data['direction'])
        if 'alive' in data:
            self.alive = bool(data['alive'])
        if 'speed' in data:
            self.speed = max(0.0, float(data['speed']))