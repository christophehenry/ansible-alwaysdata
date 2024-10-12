import re

__version__ = "0.0.0"

try:
    with open("./galaxy.yml", "r") as stream:
        verion_re = re.compile(r"^\s*version:\s*(?P<version>[\w.]+)")
        for line in list(stream):
            match = verion_re.match(line)
            if match:
                __version__ = match.group("version")
                break
except Exception:
    pass
