# Amun

**A visual Python learning environment powered by a virtual robot and an interactive grid world.**

Amun helps learners practice Python by connecting ordinary Python code to visible actions in a simulated world. Write a program in PyCharm, run it, and observe the robot move, paint cells, detect walls, and read environmental sensor values.

> **Source-available, noncommercial software.** Amun is distributed under the [PolyForm Noncommercial License 1.0.0](LICENSE). It is not an OSI-approved open-source project because the license restricts commercial use. Commercial use requires separate written permission from the copyright holder.

## Features

- **Robot simulation:** view the robot's position and direction in a grid world.
- **Movement and navigation:** move in four directions and query walls and world boundaries.
- **Cell painting:** paint cells using predefined colors.
- **Sensors:** read cell color, temperature, and radiation values.
- **World editing:** configure the grid, walls, cell colors, temperature, and radiation in the graphical interface.
- **Reusable scenarios:** save and load `.world` files.
- **Multilingual interface:** English, Russian, and Arabic.
- **Themes:** light and dark interface themes.
- **Python workflow:** write and run programs from PyCharm, with support for a debugging workflow.

## Core Programming Concepts

Amun provides an interactive environment for practicing fundamental programming concepts through robot tasks in a grid world.

With Amun, learners can practice:

- **Loops and iteration** — repeat robot actions and navigate grid-based environments.
- **Conditional logic (`if` / `else`)** — make decisions based on the robot's surroundings.
- **Variables and state** — store and update information while a program runs.
- **Comparisons and conditions** — check colors, walls, and sensor values to determine what the robot should do.
- **Return values** — use sensor readings and function results in program logic.
- **Nested function calls** — combine functions to build more complex behavior.
- **Recursion** — explore recursive problem-solving through suitable robot tasks.

## Requirements

Amun is designed primarily for **Windows** and use with **PyCharm**.

The Python version and platform compatibility depend on the release artifacts available on PyPI. Check the release files before choosing an interpreter: a declared minimum Python version does not guarantee that a compatible prebuilt package exists for every Python version or operating system.

- PyPI package: <https://pypi.org/project/amun-robot/>
- Source repository: <https://github.com/DPaZo/Amun>
- Releases: <https://github.com/DPaZo/Amun-releases>

## Installation

Create or open a Python project in PyCharm, select the intended Python interpreter, and open its terminal.

Install the published package:

```bash
python -m pip install amun-robot
```

If installation fails, check the available wheel files on PyPI and confirm that your selected Python version, operating system, and architecture are supported by that release.

## Quick start

Create a Python file such as `main.py`:

```python
from amun import *


def main():

    move(EAST, 3)
    paint(RED)

    move(SOUTH, 2)
    paint(BLUE)


    amun.run(main)
```

Run `main.py` from PyCharm. Amun launches its environment and executes `main()`. The robot moves east, paints a cell red, moves south, and paints another cell blue. The exact visible result depends on the current world configuration.

Use the predefined constants without quotation marks, for example `move(EAST, 3)` rather than `move("EAST", 3)`.

## Robot API

| Function | Purpose |
| --- | --- |
| `move(direction, steps=1)` | Move the robot in a direction for the requested number of steps. |
| `walk(direction, steps=1)` | Alias for `move()`. |
| `paint(color=None)` | Paint the current cell, optionally specifying a color. |
| `pick_color(color)` | Select the color used by `paint()` when no color is passed. |
| `sense_color()` | Read the current cell's color. |
| `has_color()` | Check whether the current cell has a color. |
| `sense_temperature()` | Read the current cell's temperature. |
| `sense_radiation()` | Read the current cell's radiation value. |
| `has_wall(direction)` | Check for a wall in a direction, including the world boundary. |
| `has_border_wall(direction)` | Check for an outer boundary in a direction. |
| `reset(clear_world=False)` | Reset the robot; optionally restore the baseline world. |
| `stop()` | Send Amun's stop command. This is not guaranteed to interrupt arbitrary Python execution immediately. |
| `run_edit_mode()` | Request edit mode in the graphical interface. |

### Directions

`NORTH`, `SOUTH`, `EAST`, `WEST`

### Colors

`RED`, `ORANGE`, `YELLOW`, `GREEN`, `BLUE`, `BLACK`, `PURPLE`

## Editing and saving worlds

Use the graphical interface to prepare a scenario by editing the grid, placing walls, painting cells, and setting temperature or radiation values. Save a world as a `.world` file to reuse it in another session.

## How it works

At a high level, Amun is organized into:

1. **Python client API** — exposes robot commands and constants to user programs.
2. **Simulation engine and server** — processes commands and maintains the world state.
3. **Graphical interface** — visualizes the world and provides editing tools.

The client and environment communicate locally using WebSocket connections.

## Troubleshooting

### `ModuleNotFoundError: No module named 'amun'`

Confirm that `amun-robot` is installed in the same Python environment selected in PyCharm. You can check the interpreter by running:

```bash
python -m pip show amun-robot
```

### `No matching distribution found`

Check the Python version, operating system, architecture, and available files on the [PyPI project page](https://pypi.org/project/amun-robot/).

### Invalid direction or color

Use the predefined constants, such as `EAST` and `RED`, rather than quoted strings.

## Contributing

Bug reports and suggestions are welcome. Before submitting code, please read the project license and confirm that your contribution can be shared under the same noncommercial terms. See [CONTRIBUTING.md](CONTRIBUTING.md) for contribution guidance.


## License and Commercial Use

Amun is provided under the **PolyForm Noncommercial License 1.0.0**.

You may use, modify, and redistribute Amun for permitted noncommercial purposes, subject to the full terms in [`LICENSE`](LICENSE).

**The project maintainer does not offer separate commercial licenses.** Commercial use is not permitted under the license, subject to its specific terms and exceptions. The license does not require you to publish private modifications.

Read [`LICENSE`](LICENSE) or the [official PolyForm Noncommercial License 1.0.0](https://polyformproject.org/licenses/noncommercial/1.0.0/).

Amun is source-available software, not an OSI-approved open-source project, because its license restricts commercial use.

