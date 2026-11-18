import sqlite3
conn = sqlite3.connect('hermes/backend/bff.sqlite3')
rows = conn.execute("SELECT text FROM group_messages WHERE bot_id='bram' ORDER BY id DESC LIMIT 1").fetchall()
if rows:
    print("=== END OF BRAM MESSAGE ===")
    print(rows[0][0][-600:])
else:
    print("No messages from bram")
