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

# Connections (Google Drive, Gmail): OAuth client credentials live only here, never in code. See docs/sprint4/setup-koneksi.md.
GOOGLE_CLIENT_ID = os.environ.get("GOOGLE_CLIENT_ID", "").strip()
GOOGLE_CLIENT_SECRET = os.environ.get("GOOGLE_CLIENT_SECRET", "").strip()
# Origin the browser uses to open the app (the Vite proxy / reverse proxy serves the BFF under /bff). Redirect URIs are built from it.
PUBLIC_BASE_URL = os.environ.get("PUBLIC_BASE_URL", "http://localhost:5173").strip().rstrip("/")
# Fernet key that encrypts stored tokens. Without it no token is ever stored.
CONNECTIONS_KEY = os.environ.get("CONNECTIONS_KEY", "").strip()
