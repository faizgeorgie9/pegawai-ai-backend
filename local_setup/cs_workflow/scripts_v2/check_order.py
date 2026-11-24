import urllib.request
from pathlib import Path

key = ""
for line in Path(r"C:\Users\MI\Documents\pegawai-ai-backend\bff\.env").read_text(encoding="utf-8").splitlines():
    if line.strip().startswith("BFF_API_KEY"):
        key = line.split("=", 1)[1].strip().strip('"').strip("'")

req = urllib.request.Request(
    "http://127.0.0.1:8090/api/data/orders/test/TEST-WA-20261115-CEC303",
    headers={"x-pegawai-ai-key": key},
)
print(urllib.request.urlopen(req, timeout=20).read().decode())
