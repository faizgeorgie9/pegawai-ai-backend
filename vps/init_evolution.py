import urllib.request
import json
import ssl

EVOLUTION_API_URL = "http://127.0.0.1:8080"
EVOLUTION_API_KEY = "pegawai_ai_evolution_secret_key_2026"
INSTANCE_NAME = "colorbox"
WEBHOOK_URL = "https://139.190.107.151.sslip.io/bff/api/whatsapp/webhook"

headers = {
    "apikey": EVOLUTION_API_KEY,
    "Content-Type": "application/json"
}

def post(path, data):
    url = f"{EVOLUTION_API_URL}{path}"
    req = urllib.request.Request(url, data=json.dumps(data).encode("utf-8"), headers=headers, method="POST")
    try:
        with urllib.request.urlopen(req) as resp:
            return resp.status, json.loads(resp.read().decode())
    except urllib.error.HTTPError as e:
        return e.code, e.read().decode()

def get(path):
    url = f"{EVOLUTION_API_URL}{path}"
    req = urllib.request.Request(url, headers=headers)
    try:
        with urllib.request.urlopen(req) as resp:
            return resp.status, json.loads(resp.read().decode())
    except urllib.error.HTTPError as e:
        return e.code, e.read().decode()

print("1. Creating Evolution instance:", INSTANCE_NAME)
status, res = post("/instance/create", {
    "instanceName": INSTANCE_NAME,
    "token": f"token_{INSTANCE_NAME}",
    "qrcode": True,
    "integration": "WHATSAPP-BAILEYS"
})
print("Create Status:", status)
print(res)

print("\n2. Setting Webhook for instance...")
status, res = post(f"/webhook/set/{INSTANCE_NAME}", {
    "webhook": {
        "enabled": True,
        "url": WEBHOOK_URL,
        "byEvents": False,
        "base64": False,
        "events": [
            "MESSAGES_UPSERT",
            "CONNECTION_UPDATE"
        ]
    }
})
print("Webhook Status:", status)
print(res)

print("\n3. Fetching QR Code connection...")
status, res = get(f"/instance/connect/{INSTANCE_NAME}")
print("Connect Status:", status)
if isinstance(res, dict) and res.get("base64"):
    print("QR Code Base64 generated successfully (Length:", len(res["base64"]), ")")
    print("Pairing Code / Code:", res.get("pairingCode") or res.get("code", "")[:40])
else:
    print(res)
