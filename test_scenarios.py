import urllib.request
import json
import time
import sys

BASE_URL = "http://127.0.0.1:8090"

def send_msg(text):
    url = f"{BASE_URL}/api/groups/marketing/messages"
    req = urllib.request.Request(
        url,
        data=json.dumps({"text": text, "mode": "queue"}).encode("utf-8"),
        headers={"Content-Type": "application/json"}
    )
    with urllib.request.urlopen(req) as resp:
        return json.loads(resp.read().decode("utf-8"))

def get_msgs(limit=50):
    url = f"{BASE_URL}/api/groups/marketing/messages?limit={limit}"
    with urllib.request.urlopen(url) as resp:
        return json.loads(resp.read().decode("utf-8"))

def run_test_scenario(scenario_name, prompt, timeout=120):
    print(f"\n=======================================================")
    print(f"RUNNING: {scenario_name}")
    print(f"PROMPT : '{prompt}'")
    print(f"=======================================================")
    
    before_msgs = get_msgs(100)
    init_count = len(before_msgs)
    
    send_msg(prompt)
    print("User message sent. Waiting for agent pipeline to execute...")
    
    start_t = time.time()
    last_count = init_count
    stable_count = 0
    
    while time.time() - start_t < timeout:
        time.sleep(5)
        curr_msgs = get_msgs(50)
        curr_count = len(curr_msgs)
        new_msgs = curr_msgs[init_count:]
        senders = [m.get("bot_id") or m.get("role") for m in new_msgs]
        print(f"[{int(time.time() - start_t)}s] Senders sequence: {senders}")
        
        # If we have at least 3 agent responses and cre-01 has spoken at the end, discussion is complete
        if len(new_msgs) >= 3 and senders[-1] == "cre-01":
            print("Detected loop completion (returned to CRE-01)!")
            time.sleep(3)
            return get_msgs(50)[init_count:]
            
        if curr_count == last_count and len(new_msgs) >= 3:
            stable_count += 1
            if stable_count >= 3:
                print("Discussion stable.")
                return new_msgs
        else:
            stable_count = 0
            last_count = curr_count
            
    return get_msgs(50)[init_count:]

if __name__ == "__main__":
    test_type = sys.argv[1] if len(sys.argv) > 1 else "all"
    
    if test_type in ("carousel", "all"):
        res_a = run_test_scenario(
            "Scenario A: Carousel Only",
            "buat carousel saja untuk produk double-pocket-flared-denim-grey"
        )
        senders_a = [m.get("bot_id") or m.get("role") for m in res_a]
        print("\n--> Sequence Scenario A:", " -> ".join(senders_a))
        assert "cre-04" not in senders_a, "FAIL: cre-04 was called in carousel only!"
        assert "cre-03" in senders_a, "FAIL: cre-03 was not called in carousel only!"
        print(">>> SUCCESS: Scenario A passed (CRE-04 successfully skipped)!")
        
    if test_type in ("video", "all"):
        time.sleep(5)
        res_b = run_test_scenario(
            "Scenario B: Video Only",
            "buat video reels doang untuk produk double-pocket-flared-denim-grey"
        )
        senders_b = [m.get("bot_id") or m.get("role") for m in res_b]
        print("\n--> Sequence Scenario B:", " -> ".join(senders_b))
        assert "cre-03" not in senders_b, "FAIL: cre-03 was called in video only!"
        assert "cre-04" in senders_b, "FAIL: cre-04 was not called in video only!"
        print(">>> SUCCESS: Scenario B passed (CRE-03 successfully skipped)!")
        
    if test_type in ("both", "all"):
        time.sleep(5)
        res_c = run_test_scenario(
            "Scenario C: Content / Both",
            "buat konten promosi untuk produk double-pocket-flared-denim-grey"
        )
        senders_c = [m.get("bot_id") or m.get("role") for m in res_c]
        print("\n--> Sequence Scenario C:", " -> ".join(senders_c))
        assert "cre-03" in senders_c, "FAIL: cre-03 was not called in both!"
        assert "cre-04" in senders_c, "FAIL: cre-04 was not called in both!"
        print(">>> SUCCESS: Scenario C passed (Both CRE-03 and CRE-04 called)!")
