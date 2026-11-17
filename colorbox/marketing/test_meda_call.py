import sqlite3
import json
import urllib.request
import time

conn = sqlite3.connect('hermes/backend/bff.sqlite3')
r = conn.execute("SELECT id, input, meta FROM runs WHERE id='run_266d990d56'").fetchone()

print("Run ID:", r[0])
user_input = r[1]
print("Input snippet:", user_input[:200])

api_key = "oc_sk_927379dbbd11_HAmLjjZQNY2eABc9nZO2xw9fP3nFAoOi"
url = "https://opencode.ai/zen/v1/chat/completions"

# Let's test a non-streaming or streaming call with small max_tokens
payload = {
    "model": "deepseek-v4.1-flash",
    "messages": [
        {"role": "user", "content": user_input[:1000]}
    ],
    "max_tokens": 2048,
    "stream": False,
    "reasoning_effort": "low"
}

print("\nTesting call to OpenCode Zen...")
t0 = time.time()
try:
    req = urllib.request.Request(
        url,
        data=json.dumps(payload).encode("utf-8"),
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {api_key}",
            "User-Agent": "PegawaiAI/2.0",
        },
    )
    with urllib.request.urlopen(req, timeout=30) as resp:
        res = json.loads(resp.read().decode("utf-8"))
        print(f"Response in {time.time()-t0:.2f}s:")
        print("Keys:", res.keys())
        print("Choices:", res.get("choices"))
except Exception as e:
    print(f"Error in {time.time()-t0:.2f}s: {e}")
