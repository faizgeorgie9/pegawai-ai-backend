import requests

msgs = requests.get("http://127.0.0.1:8090/api/groups/marketing/messages").json()
for i, m in enumerate(msgs[-8:]):
    sender = m.get("sender_label") or m.get("bot_id") or m.get("role")
    print(f"\n=== MSG #{i} ({sender}) ===")
    print(m.get("text", "")[:400])

