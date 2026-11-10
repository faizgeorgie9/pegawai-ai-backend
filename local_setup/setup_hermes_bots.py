"""
Setup Hermes profiles for the 5 builtin bots: rian, diana, budi, siti, hendra
Configures API_SERVER_KEY, model (deepseek-v4.1-flash via opencode-zen), SOUL.md, and hardening.
"""
import os
import secrets
from pathlib import Path
from ruamel.yaml import YAML

HERMES_HOME = Path(os.environ.get("LOCALAPPDATA", str(Path.home()))) / "hermes"
PROFILES_DIR = HERMES_HOME / "profiles"

BOTS = {
    "rian": {
        "name": "Rian",
        "role": "Copywriting Specialist",
        "team": "marketing",
        "persona": (
            "Kamu Rian, Copywriting Specialist di tim marketing AI Top Trends untuk Colorbox (PT Delamibrands Kharisma Busana).\n"
            "Tugasmu menulis copy/caption promosi yang segar, santai, menggunakan formula AIDA, dan cocok untuk Gen-Z di Instagram/TikTok.\n"
            "Gunakan bahasa Indonesia kasual yang sopan dan menarik."
        )
    },
    "diana": {
        "name": "Diana",
        "role": "Creative Director & QC Auditor",
        "team": "marketing",
        "persona": (
            "Kamu Diana, Creative Director & QC Auditor di tim marketing AI Top Trends untuk Colorbox.\n"
            "Tugasmu mengevaluasi naskah/copy dari Rian dengan kritis, memberikan skor mutu 1-10, serta poin perbaikan yang jelas dan tajam."
        )
    },
    "budi": {
        "name": "Budi",
        "role": "Visual Designer & Art Director",
        "team": "marketing",
        "persona": (
            "Kamu Budi, Visual Designer & Art Director di tim marketing AI Top Trends untuk Colorbox.\n"
            "Tugasmu merancang konsep visual, palet warna tren fashion remaja, dan menyusun prompt generator gambar (rasio 1:1, gaya streetwear/chic)."
        )
    },
    "siti": {
        "name": "Siti",
        "role": "Frontline Support Specialist",
        "team": "customer_support",
        "persona": (
            "Kamu Siti, Frontline Support Specialist di tim customer service AI Top Trends untuk Colorbox.\n"
            "Tugasmu membalas keluhan/pertanyaan pelanggan dengan sangat empatik, ramah, dan solutif sesuai SOP penukaran barang 7 hari (SOP-CBX-RET-01)."
        )
    },
    "hendra": {
        "name": "Hendra",
        "role": "CS Team Lead & Quality Auditor",
        "team": "customer_support",
        "persona": (
            "Kamu Hendra, CS Team Lead & Quality Auditor di tim customer service AI Top Trends untuk Colorbox.\n"
            "Tugasmu mengaudit draf balasan CS dari Siti, memastikan kepatuhan SOP kebijakan retur, dan memberikan keputusan eskalasi keluhan pelanggan."
        )
    }
}

HOUSE_SOUL_TEMPLATE = """# {name} — {role}, AI Top Trends

Kamu {name}, {role} di tim {team} AI Top Trends (perusahaan sintetis untuk proyek Pegawai AI).

## Kepribadian dan peran dari pengguna
{persona}

## Aturan bersama
- Sebut perusahaan "AI Top Trends", tanpa "PT".
- Balasan singkat dan langsung ke inti; di luar naskah panjang, usahakan di bawah 60 kata.
- Di grup, kalau tidak ada yang perlu kamu tambahkan, balas hanya [SILENT], tanpa kata lain.
- Paling banyak 2 putaran revisi, lalu rangkum dalam 3 poin dan serahkan ke @user.
- Jangan mengarang fakta, angka, atau fitur yang tidak disebut di permintaan. Bila ragu, tanya satu baris.
- Naskah selalu draf; jangan bilang sudah dipublikasikan atau disetujui.
"""

def update_env(env_path: Path, key: str, value: str):
    lines = env_path.read_bytes().splitlines(keepends=True) if env_path.exists() else []
    target = f"{key}=".encode()
    new_line = f"{key}={value}".encode()
    for i, ln in enumerate(lines):
        if ln.startswith(target):
            lines[i] = new_line + ln[len(ln.rstrip(b"\r\n")):]
            break
    else:
        if lines and not lines[-1].endswith(b"\n"):
            lines[-1] += b"\r\n"
        lines.append(new_line + b"\r\n")
    env_path.write_bytes(b"".join(lines))

def update_config_model(cfg_path: Path, is_root: bool = False, key: str = ""):
    yaml = YAML()
    yaml.preserve_quotes = True
    if not cfg_path.exists():
        return
    data = yaml.load(cfg_path.read_text(encoding="utf-8")) or {}
    if not isinstance(data.get("model"), dict):
        data["model"] = {}
    data["model"]["default"] = "deepseek-v4.1-flash"
    data["model"]["provider"] = "opencode"
    
    if is_root:
        if not isinstance(data.get("platforms"), dict):
            data["platforms"] = {}
        data["platforms"]["api_server"] = {
            "enabled": True,
            "extra": {
                "host": "127.0.0.1",
                "port": 8642,
                "key": key
            }
        }
    
    with cfg_path.open("w", encoding="utf-8") as f:
        yaml.dump(data, f)

def main():
    # Read opencode key from local_setup/backend_template/.env
    backend_env_path = Path(__file__).resolve().parent / "backend_template" / ".env"
    opencode_key = ""
    deepseek_key = ""
    if backend_env_path.exists():
        for line in backend_env_path.read_text(encoding="utf-8").splitlines():
            if line.startswith("OPENCODE_ZEN_API_KEY="):
                opencode_key = line.split("=", 1)[1].strip()
            elif line.startswith("DEEPSEEK_API_KEY="):
                deepseek_key = line.split("=", 1)[1].strip()

    # 1. Update default profile env with API_SERVER_KEY
    default_env = HERMES_HOME / ".env"
    default_key = secrets.token_urlsafe(32)
    update_env(default_env, "API_SERVER_KEY", default_key)
    update_env(default_env, "API_SERVER_PORT", "8642")
    update_env(default_env, "API_SERVER_HOST", "127.0.0.1")
    if opencode_key:
        update_env(default_env, "OPENCODE_ZEN_API_KEY", opencode_key)
    if deepseek_key:
        update_env(default_env, "DEEPSEEK_API_KEY", deepseek_key)
    update_config_model(HERMES_HOME / "config.yaml", is_root=True, key=default_key)
    print(f"Default profile API_SERVER_KEY set in {default_env}")

    # 2. Update each bot profile
    for slug, info in BOTS.items():
        pdir = PROFILES_DIR / slug
        pdir.mkdir(parents=True, exist_ok=True)

        # .env
        env_path = pdir / ".env"
        bot_key = secrets.token_urlsafe(32)
        update_env(env_path, "API_SERVER_KEY", bot_key)
        update_env(env_path, "API_SERVER_PORT", "8642")
        update_env(env_path, "API_SERVER_HOST", "127.0.0.1")
        if opencode_key:
            update_env(env_path, "OPENCODE_ZEN_API_KEY", opencode_key)
        if deepseek_key:
            update_env(env_path, "DEEPSEEK_API_KEY", deepseek_key)

        # SOUL.md
        soul_text = HOUSE_SOUL_TEMPLATE.format(
            name=info["name"],
            role=info["role"],
            team=info["team"],
            persona=info["persona"]
        )
        (pdir / "SOUL.md").write_text(soul_text, encoding="utf-8")

        # config.yaml
        cfg_path = pdir / "config.yaml"
        update_config_model(cfg_path)
        print(f"Bot {slug}: .env, SOUL.md, config.yaml updated.")

if __name__ == "__main__":
    main()
