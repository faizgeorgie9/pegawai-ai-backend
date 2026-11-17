import sqlite3

conn = sqlite3.connect('hermes/backend/bff.sqlite3')
rows = conn.execute("SELECT sender, bot_id, text FROM group_messages WHERE group_id='marketing' ORDER BY rowid DESC LIMIT 2").fetchall()
for r in reversed(rows):
    sender = r[0] or r[1]
    print(f"\n==================== [{sender}] ====================")
    print(r[2])

