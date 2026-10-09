"""CLI entry point bridge for flash_automator.cli."""
import sys
from pathlib import Path

# Ensure package directory is in sys.path for app.* resolution
_root = Path(__file__).resolve().parent
if str(_root) not in sys.path:
    sys.path.insert(0, str(_root))

from app.cli import main

if __name__ == "__main__":
    sys.exit(main())
