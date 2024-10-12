from yaml import load

try:
    from yaml import CLoader as Loader
except ImportError:
    from yaml import Loader

try:
    with open("./galaxy.yml", "r") as stream:
        data = load(stream, Loader=Loader)
        __version__ = data["version"]
except Exception:
    __version__ = "unknown"
