import time
import requests
import json

BASE_URL = "http://127.0.0.1:8090"
GROUP_ID = "marketing"

PROMPT = "Tolong buatkan carousel untuk outfit kuliah santai, promosikan kemeja chambray dan celana barrel denim"

print(f"=== TESTING 5-AGENT GROUP CHAT CASCADE ===")
print(f"User Prompt: {PROMPT}\n")

# Pre-populate seen IDs with previous messages
seen_ids = set()
try:
    init_r = requests.get(f"{BASE_URL}/api/groups/{GROUP_ID}/messages")
    if init_r.status_code == 200:
        for m in init_r.json():
            if m.get("id"):
                seen_ids.add(m["id"])
except Exception as e:
    pass

# 1. Post user message
res = requests.post(f"{BASE_URL}/api/groups/{GROUP_ID}/messages", json={"text": PROMPT})
print(f"Post Response: {res.status_code}")
if res.status_code not in (200, 202):
    print(f"Error: {res.text}")
    exit(1)
start_time = time.time()
max_wait = 360  # 6 minutes max

print("\nMonitoring group chat cascade in real-time...")
bots_seen = []

while time.time() - start_time < max_wait:
    try:
        r = requests.get(f"{BASE_URL}/api/groups/{GROUP_ID}/messages")
        if r.status_code == 200:
            msgs = r.json()
            for m in msgs:
                mid = m.get("id")
                if mid and mid not in seen_ids:
                    seen_ids.add(mid)
                    role = m.get("role")
                    sender = m.get("sender_label") or m.get("bot_id") or role
                    text = m.get("text", "")
                    if role == "bot":
                        bot_id = m.get("bot_id")
                        bots_seen.append(bot_id)
                        print(f"\n[AGENT: {sender} (@{bot_id})] posted:", flush=True)
                        preview = text[:250].replace("\n", " ")
                        print(f"  Preview: {preview}...", flush=True)
                        if "Preview Visual Carousel" in text or "slide_1_cover_hero.png" in text:
                            print(f"  >>> Visual Carousel Assets detected in response! <<<", flush=True)
                    elif role == "user":
                        print(f"\n[USER]: {text}", flush=True)
        
        # Check if cascade is complete: Vina has spoken, then Bimo signed off
        if "vina" in bots_seen and "bimo" in bots_seen[bots_seen.index("vina")+1:]:
            print("\n>>> All 5 agents completed their cascade, Bimo provided final sign-off! <<<", flush=True)
            break
    except Exception as e:
        print(f"Polling error: {e}", flush=True)

    time.sleep(3)

print("\n=== SUMMARY OF AGENTS PARTICIPATION ===")
print("Sequence of bot responses:", bots_seen)

# Check files generated
import os
out_dir = "hermes/colorbox/marketing/output/carousel_latest"
if os.path.exists(out_dir):
    files = os.listdir(out_dir)
    print(f"\nFiles in {out_dir}:")
    for f in files:
        fpath = os.path.join(out_dir, f)
        print(f"  - {f} ({os.path.getsize(fpath):,} bytes)")
else:
    print(f"\nWarning: Output dir {out_dir} not found!")

print("\n=== TEST COMPLETED ===")
