"""PostToolUse(Edit|Write) hook entrypoint; logic lives in core hookcheck."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))

from scicodewiki.hookcheck import main  # noqa: E402

if __name__ == "__main__":
    sys.exit(main())
