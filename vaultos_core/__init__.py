"""VaultOS core — an audit trail for AI coding agents.

Standard library only. Python 3.9+.
"""

import os

ROOT = os.path.dirname(os.path.dirname(os.path.realpath(__file__)))
FRAMEWORK = os.path.join(ROOT, "framework")


def version():
    with open(os.path.join(ROOT, "VERSION"), encoding="utf-8") as fh:
        return fh.read().strip()
