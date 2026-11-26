#!/usr/bin/env python3
"""board_params.py SERIAL [--power auto|fitted|none]: bring-up parameters of a board.

Serial characters 5 and 6 give the geometry, which sets the config family, the
--board name, the ROC count and whether a power distribution board is fitted.

    $ board_params.py 320XLF4CQH00443
    initLD-Full-3b LD-Full 3 POWER=

POWER= means a power board is fitted; a wrong flag leaves the module unpowered.

    --power fitted|none   override the table (HB and HL/HR rows are guesses)
    --describe            one line: "LD Full, 3 ROCs, power board"
    --shell               eval-able assignments, for run_slots.sh
    --table               the whole table as JSON, for the web form

Exit 2 on a malformed serial or unknown type code.
"""
import json
import re
import sys

# type code -> config family, --board, ROC count, power board fitted, max bias V.
# power_measured False = row not yet seen on a bench; MMTS_bench.hv.max_volts can cap maxv.
TABLE = {
    "LF": {"name": "LD Full",   "family": "initLD-Full-3b",         "board": "LD-Full",   "nrocs": 3, "power": True,  "power_measured": True, "maxv": 600},
    "L5": {"name": "LD Five",   "family": "initLD-Five-3b",         "board": "LD-Five",   "nrocs": 3, "power": False, "power_measured": True, "maxv": 600},
    "LL": {"name": "LD Left",   "family": "initLD-Left-3b",         "board": "LD-Semi",   "nrocs": 2, "power": False, "power_measured": True, "maxv": 600},
    "LR": {"name": "LD Right",  "family": "initLD-Left-3b",         "board": "LD-Semi",   "nrocs": 2, "power": False, "power_measured": True, "maxv": 600},
    "LB": {"name": "LD Bottom", "family": "initLD-Bottom-3b",       "board": "LD-Semi",   "nrocs": 2, "power": False, "power_measured": True, "maxv": 600},
    "LT": {"name": "LD Top",    "family": "initLD-Bottom-3b",       "board": "LD-Semi",   "nrocs": 2, "power": False, "power_measured": True, "maxv": 600},
    "HF": {"name": "HD Full",   "family": "initHD-Full-trophyV3",   "board": "HD-Full",   "nrocs": 6, "power": True,  "power_measured": True, "maxv": 800},
    "HT": {"name": "HD Top",    "family": "initHD-Top-trophyV3",    "board": "HD-Top",    "nrocs": 3, "power": False, "power_measured": True, "maxv": 800},
    "HB": {"name": "HD Bottom", "family": "initHD-Bottom-trophyV3", "board": "HD-Bottom", "nrocs": 4, "power": False, "power_measured": False, "maxv": 800},
    "HL": {"name": "HD Semi",   "family": "initHD-Semi-trophyV3",   "board": "HD-Semi",   "nrocs": 2, "power": False, "power_measured": False, "maxv": 800},
    "HR": {"name": "HD Semi",   "family": "initHD-Semi-trophyV3",   "board": "HD-Semi",   "nrocs": 2, "power": False, "power_measured": False, "maxv": 800},
}

SERIAL_RE = re.compile(r"^320[A-Z0-9]{12}$")


def normalise(serial):
    """Uppercase, dashless, 15 characters; None when not a module serial.

    Downstream scripts read characters 5 and 6 positionally, so dashes must go.
    """
    s = re.sub(r"[^A-Za-z0-9]", "", serial or "").upper()
    return s if SERIAL_RE.match(s) else None


def params(serial, power_override="auto"):
    """(serial, row, power_fitted) for a serial, or raise ValueError."""
    s = normalise(serial)
    if not s:
        raise ValueError("not a module serial: %r (want 320X<TT>..., 15 characters)" % serial)
    code = s[4:6]
    if code not in TABLE:
        raise ValueError("unknown board type code %r in %s -- known codes: %s"
                         % (code, s, " ".join(sorted(TABLE))))
    row = TABLE[code]
    power = row["power"]
    if power_override == "fitted":
        power = True
    elif power_override == "none":
        power = False
    elif power_override != "auto":
        raise ValueError("--power takes auto, fitted or none, got %r" % power_override)
    return s, row, power


def describe(row, power):
    return "%s, %d ROCs, %s" % (row["name"], row["nrocs"],
                                "power board" if power else "external power")


def main(argv):
    if "--table" in argv:
        print(json.dumps(TABLE, indent=2, sort_keys=True))
        return 0

    args = [a for a in argv if not a.startswith("--")]
    power_override = "auto"
    if "--power" in argv:
        i = argv.index("--power")
        if i + 1 >= len(argv):
            sys.stderr.write("--power needs a value: auto, fitted or none\n")
            return 2
        power_override = argv[i + 1]
        args = [a for a in args if a != power_override]
    if len(args) != 1:
        sys.stderr.write(__doc__)
        return 2

    try:
        serial, row, power = params(args[0], power_override)
    except ValueError as e:
        sys.stderr.write("%s\n" % e)
        return 2

    if "--describe" in argv:
        print(describe(row, power))
        return 0

    if "--shell" in argv:
        for k, v in (("SERIAL", serial), ("FAMILY", row["family"]),
                     ("BOARD", row["board"]), ("NROCS", row["nrocs"]),
                     ("POWERFLAG", "POWER=" if power else ""),
                     ("MAXV", row["maxv"]),
                     ("DESC", describe(row, power))):
            print("%s='%s'" % (k, str(v).replace("'", "")))
        return 0

    # "POWER=" is an env assignment with an empty value; a partial prints no fourth field.
    print(" ".join(str(x) for x in (row["family"], row["board"], row["nrocs"])
                   ) + (" POWER=" if power else ""))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
