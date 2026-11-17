import requests

msgs = requests.get("http://127.0.0.1:8090/api/groups/marketing/messages").json()
print(f"Total messages in marketing group: {len(msgs)}")
for m in msgs[-10:]:
    sender = m.get("sender_label") or m.get("bot_id") or m.get("role")
    txt = m.get("text", "")[:180].replace("\n", " ")
    print(f"[{sender}]: {txt}...")

