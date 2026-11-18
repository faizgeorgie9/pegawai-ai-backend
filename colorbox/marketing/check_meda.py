import sqlite3
conn = sqlite3.connect('hermes/backend/bff.sqlite3')
r = conn.execute("SELECT output_tokens, error, meta FROM runs WHERE bot_id='meda' ORDER BY rowid DESC LIMIT 1").fetchone()
print(r)

