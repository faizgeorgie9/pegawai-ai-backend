import requests
import datetime

msgs = requests.get("http://127.0.0.1:8090/api/groups/marketing/messages").json()
for m in msgs[-10:]:
    dt = datetime.datetime.fromtimestamp(m.get("created_at", 0)).strftime("%H:%M:%S")
    sender = m.get("sender_label") or m.get("bot_id") or m.get("role")
    txt = m.get("text", "")[:120].replace("\n", " ")
    print(f"[{dt}] [{sender}]: {txt}")

