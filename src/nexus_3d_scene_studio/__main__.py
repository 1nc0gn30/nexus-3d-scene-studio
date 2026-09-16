"""Package main entrypoint for `python -m nexus_3d_scene_studio`."""

from __future__ import annotations

import sys
from .cli import main

if __name__ == "__main__":
    sys.exit(main())
