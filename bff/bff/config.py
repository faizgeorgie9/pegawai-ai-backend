import os
import shutil
from pathlib import Path

from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parent.parent  # bff/
load_dotenv(ROOT / ".env")

DATABASE_URL = os.environ.get("DATABASE_URL", "")
BFF_API_KEY = os.environ.get("BFF_API_KEY", "")
HERMES_API_URL = os.environ.get("HERMES_API_URL", "http://127.0.0.1:8642").rstrip("/")
HERMES_HOME = Path(os.environ.get("HERMES_HOME") or (Path(os.environ.get("LOCALAPPDATA", str(Path.home()))) / "hermes"))
HERMES_BIN = os.environ.get("HERMES_BIN") or shutil.which("hermes") or "hermes"
# Persona files for the five template bots (repo: bots/souls).
SOULS_DIR = Path(os.environ.get("SOULS_DIR") or ROOT.parent.parent / "bots" / "souls")
