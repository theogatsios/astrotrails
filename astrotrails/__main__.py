# SPDX-License-Identifier: GPL-3.0-or-later
"""Allow `python -m astrotrails` to invoke the CLI."""

from .cli import main

if __name__ == "__main__":
    raise SystemExit(main())
