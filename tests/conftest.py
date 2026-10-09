"""Session setup shared by every test file."""
import os

# Scripts under test print emoji. Run the Python processes they spawn in UTF-8 mode, as
# scripts/release.py does, so captured output doesn't fail on a Windows code page.
os.environ.setdefault("PYTHONUTF8", "1")
