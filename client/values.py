from difflib import get_close_matches
from enum import Enum


class Direction(Enum):
    NORTH = 'NORTH'
    SOUTH = 'SOUTH'
    EAST = 'EAST'
    WEST = 'WEST'


class Color(Enum):
    RED = 'red'
    ORANGE = 'orange'
    YELLOW = 'yellow'
    GREEN = 'green'
    BLUE = 'blue'
    BLACK = 'black'
    PURPLE = 'purple'


NORTH, SOUTH, EAST, WEST = (
    Direction.NORTH,
    Direction.SOUTH,
    Direction.EAST,
    Direction.WEST,
)

RED, ORANGE, YELLOW, GREEN, BLUE, BLACK, PURPLE = (
    Color.RED,
    Color.ORANGE,
    Color.YELLOW,
    Color.GREEN,
    Color.BLUE,
    Color.BLACK,
    Color.PURPLE,
)

DIRECTION_ERROR = 'Direction must be NORTH, SOUTH, EAST, or WEST.'
COLOR_ERROR = 'Color must be RED, ORANGE, YELLOW, GREEN, BLUE, BLACK, or PURPLE.'


def require_direction(value):
    if isinstance(value, Direction):
        return value.value

    valid_names = tuple(Direction.__members__.keys())

    if isinstance(value, str):
        raw = value.strip()
        name = raw.upper()

        if name in Direction.__members__:
            raise TypeError(f'Use {name}, not "{value}".')

        guess = get_close_matches(name, valid_names, n=1)
        if guess:
            raise TypeError(f'Unknown direction: {value}. Use {guess[0]}.')
        raise TypeError(DIRECTION_ERROR)

    raise TypeError(DIRECTION_ERROR)


def require_color(value, optional=False):
    if value is None:
        if optional:
            return None
        raise TypeError(COLOR_ERROR)

    if isinstance(value, Color):
        return value.value

    valid_names = tuple(Color.__members__.keys())

    if isinstance(value, str):
        raw = value.strip()
        name = raw.upper()

        if name in Color.__members__:
            raise TypeError(f'Use {name}, not "{value}".')

        guess = get_close_matches(name, valid_names, n=1)
        if guess:
            raise TypeError(f'Unknown color: {value}. Use {guess[0]}.')
        raise TypeError(COLOR_ERROR)

    raise TypeError(COLOR_ERROR)