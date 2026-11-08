"""A small simulated smart building for Labs 24, 25 and 26: sensors you can read and switches you can turn on.

Everything is kept in memory, so nothing real can break. The labs give these functions to a language model as TOOLS.
The functions are plain Python: read them, change them, add your own.
"""
import copy
import inspect
import time

START = {
    "kitchen": {"temperature": 27.5, "humidity": 62.0, "light": False, "fan": False},
    "lab":     {"temperature": 24.0, "humidity": 45.0, "light": True,  "fan": False},
    "garage":  {"temperature": 29.0, "humidity": 70.0, "light": False, "fan": False},
}
START_DOORS = {"front": "locked", "garage": "locked"}

STATE = copy.deepcopy(START)       # the rooms: temperature, humidity, light and fan
DOORS = dict(START_DOORS)          # the doors: "locked" or "open"
LOG = []                           # every action that changed something: (time, tool, arguments, result)
FAN_COOLING = 3.0                  # degrees that a fan takes away


def reset():
    """Put the building back to the start."""
    STATE.clear()
    STATE.update(copy.deepcopy(START))
    DOORS.clear()
    DOORS.update(START_DOORS)
    LOG.clear()


def _room(room):
    if room not in STATE:
        raise ValueError(f"unknown room '{room}'. The rooms are: {', '.join(STATE)}")
    return STATE[room]


def list_rooms() -> list:
    """List the names of all rooms that have sensors."""
    return list(STATE)


def get_temperature(room: str) -> float:
    """Read the temperature of a room in degrees Celsius."""
    r = _room(room)
    return round(r["temperature"] - (FAN_COOLING if r["fan"] else 0.0), 1)


def get_humidity(room: str) -> float:
    """Read the relative humidity of a room in percent."""
    return _room(room)["humidity"]


def set_light(room: str, on: bool) -> str:
    """Switch the light of a room on (true) or off (false)."""
    _room(room)["light"] = bool(on)
    result = f"light in {room} is now {'on' if on else 'off'}"
    LOG.append((time.time(), "set_light", {"room": room, "on": on}, result))
    return result


def set_fan(room: str, on: bool) -> str:
    """Switch the fan of a room on (true) or off (false). A fan makes the room cooler."""
    _room(room)["fan"] = bool(on)
    result = f"fan in {room} is now {'on' if on else 'off'}"
    LOG.append((time.time(), "set_fan", {"room": room, "on": on}, result))
    return result


def open_door(name: str) -> str:
    """Unlock and open a door. The doors are: front, garage."""
    if name not in DOORS:
        raise ValueError(f"unknown door '{name}'. The doors are: {', '.join(DOORS)}")
    DOORS[name] = "open"
    result = f"the {name} door is now open"
    LOG.append((time.time(), "open_door", {"name": name}, result))
    return result


FUNCTIONS = {f.__name__: f for f in (list_rooms, get_temperature, get_humidity, set_light, set_fan, open_door)}
CONSEQUENTIAL = {"set_fan", "open_door"}      # actions that change the real world: a person must approve them in Lab 26

_TYPES = {str: "string", int: "integer", float: "number", bool: "boolean", list: "array"}


def schema(func):
    """Make the tool description for the language model from a Python function (its name, its first docstring line and its typed arguments)."""
    parameters, required = {}, []
    for name, p in inspect.signature(func).parameters.items():
        parameters[name] = {"type": _TYPES.get(p.annotation, "string")}
        required.append(name)
    return {"type": "function", "function": {
        "name": func.__name__,
        "description": inspect.getdoc(func).split("\n")[0],
        "parameters": {"type": "object", "properties": parameters, "required": required}}}


def all_schemas(names=None):
    """The tool descriptions of the functions in `names` (default: all of them)."""
    return [schema(FUNCTIONS[n]) for n in (names or FUNCTIONS)]
