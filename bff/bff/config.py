import os
import shlex
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
# Read-only list of Hermes own Kanban (kanban.py adds --tenant <user id>). Override with HERMES_KANBAN_CMD, e.g. "hermes kanban list --json".
HERMES_KANBAN_CMD = shlex.split(os.environ["HERMES_KANBAN_CMD"]) if os.environ.get("HERMES_KANBAN_CMD") else [HERMES_BIN, "kanban", "list", "--json"]
