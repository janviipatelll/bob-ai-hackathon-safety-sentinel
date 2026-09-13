"""conftest.py — ensure src/ is on sys.path for all tests."""
import sys
import pathlib

# Add src/ to sys.path so that `import signal_detector` etc. work regardless
# of the directory from which pytest is invoked.
_src = pathlib.Path(__file__).parent.parent.resolve()
if str(_src) not in sys.path:
    sys.path.insert(0, str(_src))
