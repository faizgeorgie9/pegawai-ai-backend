import sqlite3
conn = sqlite3.connect('hermes/backend/bff.sqlite3')
r = conn.execute("SELECT input, meta FROM runs WHERE id='run_266d990d56'").fetchone()
if r:
    print("Input length:", len(r[0]))
    print("Meta:", r[1])

