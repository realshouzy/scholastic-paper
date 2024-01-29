"""Example Nr. 2."""

from __future__ import annotations

# pylint: skip-file


# bare-except
try:
    exit()
except:
    print("Catching any exception")  # even SystemExit

# empty-except-body
try:
    raise Exception
except Exception:
    pass  # or ...
