import urllib.request
import json
import time

api_key = "oc_sk_927379dbbd11_HAmLjjZQNY2eABc9nZO2xw9fP3nFAoOi"
url = "https://opencode.ai/zen/v1/chat/completions"

payload = {
    "model": "deepseek-v4.1-flash",
    "messages": [{"role": "user", "content": "Halo, jawab dalam 1 kata."}],
    "max_tokens": 50,
}

t0 = time.time()
print("Sending test request to OpenCode Zen...")
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
        body = resp.read().decode("utf-8")
        print(f"Success in {time.time()-t0:.2f}s:")
        print(body[:200])
except Exception as e:
    print(f"Failed in {time.time()-t0:.2f}s: {e}")

