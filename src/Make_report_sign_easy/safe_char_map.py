SAFE_CHAR_MAP = {
    "/": "U002F",
    "\\": "U005C",
    ":": "U003A",
    "*": "U002A",
    "?": "U003F",
    "\"": "U0022",
    "<": "U003C",
    ">": "U003E",
    "|": "U007C",
    "’": "U2019"
}
REVERSE_SAFE_CHAR_MAP = {v: k for k, v in SAFE_CHAR_MAP.items()}
