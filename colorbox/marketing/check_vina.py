import sqlite3
conn = sqlite3.connect('hermes/backend/bff.sqlite3')
rows = conn.execute("SELECT bot_id, author, text FROM group_messages WHERE group_id='marketing' ORDER BY rowid DESC LIMIT 15").fetchall()
for r in reversed(rows):
    sender = r[0] or r[1] or ""
    txt = (r[2] or "")[:60].replace("\n", " ")
    print(f"[{sender}]: {txt}")
    if "Vina" in f"{sender}: {r[2]}":
        print("  ^^ Contains 'Vina'!")
