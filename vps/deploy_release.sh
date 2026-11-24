#!/usr/bin/env bash
# Deploy rilis Pegawai AI ke VPS dari /home/ubuntu/releases/<sha>.
#
# Pemakaian:  /home/ubuntu/deploy-pegawai-ai.sh <sha>
#
# Alur: backup -> sinkron backend -> dependensi -> restart + health ->
#       sinkron frontend -> buang bundle lama -> verifikasi.
# Bila health gagal setelah restart, rollback otomatis dari backup run ini.
#
# Tidak memuat rahasia. DATABASE_URL dibaca dari bff/.env saat dijalankan,
# hanya dipakai sebagai environment untuk pg_dump, dan tidak pernah dicetak.

set -euo pipefail

APP=/home/ubuntu/pegawai-ai
WEB=/var/www/pegawai-ai
REL_ROOT=/home/ubuntu/releases
BACKUP_ROOT=/home/ubuntu/backups
UNIT=pegawai-ai-bff
UV=/home/ubuntu/.local/bin/uv
HEALTH=http://127.0.0.1:8090/api/health
HOSTHDR=139.190.107.151.sslip.io
KEEP_RELEASES=3
KEEP_BACKUPS=5
LOCK=/home/ubuntu/.deploy-pegawai-ai.lock

log() { printf '[%s] %s\n' "$(date -u +%H:%M:%SZ)" "$*"; }
die() { log "GAGAL: $*"; exit 1; }

wait_health() {
    local deadline=$(( $(date +%s) + ${1:-60} ))
    while [ "$(date +%s)" -lt "$deadline" ]; do
        if curl -fsS -o /dev/null --max-time 2 "$HEALTH" 2>/dev/null; then
            return 0
        fi
        sleep 0.5
    done
    return 1
}

SHA="${1:-}"
[ -n "$SHA" ] || die "pemakaian: $0 <sha-rilis>"
REL="$REL_ROOT/$SHA"
[ -d "$REL/bff" ] || die "tidak ada $REL/bff"
[ -d "$REL/www" ] || die "tidak ada $REL/www"
[ -f "$REL/SHA" ] || die "tidak ada $REL/SHA"

# -------------------------------------------------- 0. kunci deploy (flock)
# Satu deployer pada satu waktu. Kunci dipegang sampai skrip selesai; berkas
# kunci sengaja tidak dihapus agar tidak ada balapan antar-proses.
if command -v flock >/dev/null 2>&1; then
    exec 9>>"$LOCK"
    if ! flock -n 9; then
        HOLDER=$(tail -n 1 "$LOCK" 2>/dev/null | tr -d '\r' || true)
        die "deploy lain sedang berjalan (${HOLDER:-pemegang tidak diketahui}); tunggu sampai selesai"
    fi
    printf 'pid=%s at=%s\n' "$$" "$(date -u +%Y-%m-%dT%H:%M:%SZ)" >&9
    log "0/7 kunci deploy dipegang (pid $$)"
else
    log "0/7 PERINGATAN: flock tidak ada, kunci deploy dilewati"
fi

STAMP=$(date -u +%Y%m%dT%H%M%SZ)
BK="$BACKUP_ROOT/deploy-$STAMP"
mkdir -p "$BK"
chmod 700 "$BACKUP_ROOT" "$BK"

# ---------------------------------------------------------------- 1. backup
log "1/7 backup ke $BK"
tar czf "$BK/app.tar.gz" -C /home/ubuntu \
    --exclude='pegawai-ai/bff/.venv' --exclude='__pycache__' --exclude='*.pyc' \
    --exclude='.pytest_cache' --exclude='.ruff_cache' pegawai-ai
tar czf "$BK/www.tar.gz" -C /var/www pegawai-ai
sudo -n cp -a /etc/nginx/sites-enabled/default "$BK/nginx-sites-enabled-default" 2>/dev/null || true
sudo -n cp -a /etc/systemd/system/$UNIT.service "$BK/$UNIT.service" 2>/dev/null || true
chmod 600 "$BK"/*.gz

if command -v docker >/dev/null 2>&1; then
    DBURL=$(python3 - "$APP/bff/.env" <<'PY'
import sys
for line in open(sys.argv[1], encoding="utf-8"):
    line = line.rstrip("\n")
    if line.startswith("DATABASE_URL="):
        print(line.split("=", 1)[1].strip().strip('"').strip("'"))
        break
PY
)
    if [ -n "${DBURL:-}" ]; then
        export DATABASE_URL="$DBURL"
        if docker run --rm -e DATABASE_URL postgres:18-alpine \
                sh -c 'pg_dump "$DATABASE_URL" -Fc --no-owner --no-privileges' \
                > "$BK/neon.dump" 2>"$BK/neon.dump.err"; then
            chmod 600 "$BK/neon.dump"
            log "    dump DB: $(stat -c %s "$BK/neon.dump") byte"
        else
            rm -f "$BK/neon.dump"
            log "    PERINGATAN: pg_dump gagal, lanjut tanpa dump DB (lihat neon.dump.err)"
        fi
        unset DATABASE_URL
    else
        log "    PERINGATAN: DATABASE_URL kosong, dump DB dilewati"
    fi
else
    log "    PERINGATAN: docker tidak ada, dump DB dilewati"
fi
rm -f "$BK/neon.dump.err"

# ------------------------------------------------- 2. sinkron backend (bff)
REQ_BEFORE=$(cat "$APP/bff/pyproject.toml" "$APP/bff/uv.lock" | sha256sum | cut -d' ' -f1)
BE_CHANGES=$(rsync -an --itemize-changes --delete \
    --exclude '.env' --exclude '.venv/' --exclude '__pycache__/' \
    --exclude '.pytest_cache/' --exclude '.ruff_cache/' \
    --exclude 'knowledge/marketing/' \
    "$REL/bff/" "$APP/bff/" | grep -cE '^(>f|\*deleting)' || true)
log "2/7 sinkronkan backend $REL/bff -> $APP/bff ($BE_CHANGES berkas berubah)"
rsync -a --delete \
    --exclude '.env' \
    --exclude '.venv/' \
    --exclude '__pycache__/' \
    --exclude '.pytest_cache/' \
    --exclude '.ruff_cache/' \
    --exclude 'knowledge/marketing/' \
    "$REL/bff/" "$APP/bff/"
REQ_AFTER=$(cat "$APP/bff/pyproject.toml" "$APP/bff/uv.lock" | sha256sum | cut -d' ' -f1)

# ----------------------------------------------------------- 3. dependensi
if [ "$REQ_BEFORE" != "$REQ_AFTER" ]; then
    log "3/7 pyproject/uv.lock berubah, sinkronkan venv"
    "$UV" sync --project "$APP/bff" --quiet || die "uv sync gagal"
else
    log "3/7 dependensi tidak berubah, venv dibiarkan"
fi

# ------------------------------------------------------- 4. restart + health
if [ "$BE_CHANGES" = "0" ] && [ "$REQ_BEFORE" = "$REQ_AFTER" ]; then
    log "4/7 backend tidak berubah, restart dilewati (tanpa downtime)"
    wait_health 30 || die "BFF tidak sehat padahal tidak ada perubahan"
else
log "4/7 restart $UNIT"
T0=$(date +%s%3N)
sudo -n systemctl restart "$UNIT"
if wait_health 60; then
    T1=$(date +%s%3N)
    log "    sehat setelah $(( T1 - T0 )) ms (termasuk restart)"
else
    log "    health gagal setelah 60 s -> rollback"
    sudo -n systemctl stop "$UNIT" || true
    TMP=$(mktemp -d)
    tar xzf "$BK/app.tar.gz" -C "$TMP"
    rsync -a --delete --exclude '.venv/' --exclude '.env' --exclude 'knowledge/marketing/' \
        "$TMP/pegawai-ai/bff/" "$APP/bff/"
    rm -rf "$TMP"
    tar xzf "$BK/www.tar.gz" -C /var/www
    sudo -n systemctl start "$UNIT" || true
    if wait_health 60; then
        log "    ROLLBACK SELESAI, layanan sehat dengan kode lama"
    else
        log "    ROLLBACK GAGAL, layanan tetap tidak sehat"
    fi
    exit 1
fi
fi

# ------------------------------------------------------------- 5. frontend
log "5/7 sinkronkan frontend $REL/www -> $WEB"
sudo -n rsync -rlpt "$REL/www/" "$WEB/"
sudo -n chown -R root:root "$WEB"
sudo -n find "$WEB" -type d -exec chmod 755 {} +
sudo -n find "$WEB" -type f -exec chmod 644 {} +

# ------------------------------------------------- buang bundle lama (hash)
log "6/7 buang bundle JS/CSS yang tidak dirujuk index.html"
sudo -n python3 - "$WEB" <<'PY'
import os, re, sys
web = sys.argv[1]
html = open(os.path.join(web, "index.html"), encoding="utf-8").read()
keep = set(re.findall(r"assets/[A-Za-z0-9._-]+", html))
assets = os.path.join(web, "assets")
removed = []
for name in sorted(os.listdir(assets)):
    if not re.fullmatch(r"index-[A-Za-z0-9_-]+\.(js|css)", name):
        continue
    if f"assets/{name}" not in keep:
        os.remove(os.path.join(assets, name))
        removed.append(name)
print("    dibuang:", ", ".join(removed) if removed else "(tidak ada)")
PY

# ----------------------------------------------------------- 7. verifikasi
log "7/7 verifikasi"
code_root=$(curl -sk -o /dev/null -w '%{http_code}' "https://127.0.0.1/" -H "Host: $HOSTHDR")
code_api=$(curl -sk -o /dev/null -w '%{http_code}' "https://127.0.0.1/api/health" -H "Host: $HOSTHDR")
code_bff=$(curl -sk -o /dev/null -w '%{http_code}' "https://127.0.0.1/bff/api/health" -H "Host: $HOSTHDR")
local_index=$(sha256sum "$WEB/index.html" | cut -d' ' -f1)
served_index=$(curl -sk "https://127.0.0.1/" -H "Host: $HOSTHDR" | sha256sum | cut -d' ' -f1)
asset=$(grep -oE 'assets/index-[A-Za-z0-9_-]+\.js' "$WEB/index.html" | head -1)
code_asset=$(curl -sk -o /dev/null -w '%{http_code}' "https://127.0.0.1/$asset" -H "Host: $HOSTHDR")
cc_index=$(curl -skI "https://127.0.0.1/" -H "Host: $HOSTHDR" | tr -d '\r' | awk 'tolower($1)=="cache-control:"{print $2" "$3}')
cc_asset=$(curl -skI "https://127.0.0.1/$asset" -H "Host: $HOSTHDR" | tr -d '\r' | awk 'tolower($1)=="cache-control:"{print $2" "$3}')

log "    /            = $code_root (cache-control: ${cc_index:-<none>})"
log "    /api/health  = $code_api"
log "    /bff/api/health = $code_bff"
log "    $asset = $code_asset (cache-control: ${cc_asset:-<none>})"
log "    index.html lokal = ${local_index:0:16} / dilayani = ${served_index:0:16}"

FAIL=0
[ "$code_root" = 200 ] || FAIL=1
[ "$code_api" = 200 ] || FAIL=1
[ "$code_bff" = 200 ] || FAIL=1
[ "$code_asset" = 200 ] || FAIL=1
[ "$local_index" = "$served_index" ] || FAIL=1
[ "$FAIL" = 0 ] || die "verifikasi HTTP gagal (kode di atas)"

log "cek journal 30 detik terakhir"
BAD=$(sudo -n journalctl -u "$UNIT" --since "-30 seconds" --no-pager 2>/dev/null \
      | grep -iE 'traceback|error|exception|critical' | grep -v 'INFO:' || true)
if [ -n "$BAD" ]; then
    log "    PERINGATAN: ada baris error di journal:"
    printf '%s\n' "$BAD" | tail -10
else
    log "    journal bersih"
fi

echo "$SHA" > /home/ubuntu/CURRENT_RELEASE
log "SELESAI: rilis $SHA aktif"

# ------------------------------------------------------------- housekeeping
mapfile -t old < <(ls -1dt "$REL_ROOT"/*/ 2>/dev/null | tail -n +$(( KEEP_RELEASES + 1 )))
for d in "${old[@]:-}"; do
    [ -n "${d:-}" ] || continue
    case "$d" in
        "$REL_ROOT/$SHA/") continue ;;
    esac
    log "hapus rilis lama: $d"
    rm -rf "$d"
done
mapfile -t oldb < <(ls -1dt "$BACKUP_ROOT"/deploy-*/ 2>/dev/null | tail -n +$(( KEEP_BACKUPS + 1 )))
for d in "${oldb[@]:-}"; do
    [ -n "${d:-}" ] || continue
    log "hapus backup lama: $d"
    rm -rf "$d"
done
