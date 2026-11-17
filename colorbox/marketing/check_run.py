import sqlite3, time
conn = sqlite3.connect('hermes/backend/bff.sqlite3')
r = conn.execute("SELECT id, bot_id, status, created_at, output_tokens FROM runs ORDER BY rowid DESC LIMIT 1").fetchone()
if r:
    print(f"Run {r[0]} ({r[1]}): {r[2]} | Elapsed: {round(time.time() - r[3], 1)}s | Tokens: {r[4]}")

