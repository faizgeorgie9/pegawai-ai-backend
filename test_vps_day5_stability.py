import json
import urllib.request
import paramiko

BASE_URL = "https://139.190.107.151.sslip.io"
BFF_KEY = "mh6IG_kqNfpu4YJe1Gi8FzM1tzejRPSbWfDSRNFriCI"
VPS_HOST = "139.190.107.151"
VPS_USER = "ubuntu"
VPS_PASS = "@Baruk516"

results = {}

def log_test(name, success, details):
    status_str = "PASS" if success else "FAIL"
    print(f"[{status_str}] {name}")
    results[name] = {"success": success, "details": details}

def main():
    print("=====================================================")
    print("🔬 SPRINT 4 DAY 5: VPS LIVE REGRESSION & STABILITY")
    print(f"Target: {BASE_URL}")
    print("=====================================================")

    # 1. Frontend Root
    try:
        resp = urllib.request.urlopen(f"{BASE_URL}/", timeout=15)
        html = resp.read().decode('utf-8')
        ok = (resp.status == 200 and "<!doctype html>" in html.lower())
        log_test("1. Frontend SPA Root (HTTPS)", ok, f"HTTP {resp.status}, length: {len(html)}")
    except Exception as e:
        log_test("1. Frontend SPA Root (HTTPS)", False, str(e))

    # 2. Healthcheck
    try:
        req = urllib.request.Request(f"{BASE_URL}/bff/api/health")
        with urllib.request.urlopen(req, timeout=15) as resp:
            data = json.loads(resp.read().decode('utf-8'))
            ok = (data.get("ok") is True and data.get("db") is True and data.get("hermes") is True)
            log_test("2. Backend Healthcheck (/bff/api/health)", ok, data)
    except Exception as e:
        log_test("2. Backend Healthcheck (/bff/api/health)", False, str(e))

    # 3. WhatsApp Gateway Status
    try:
        req = urllib.request.Request(f"{BASE_URL}/bff/api/whatsapp/status", headers={"X-Pegawai-AI-Key": BFF_KEY})
        with urllib.request.urlopen(req, timeout=15) as resp:
            data = json.loads(resp.read().decode('utf-8'))
            ok = (data.get("status") == "ready" and data.get("primary_agent", {}).get("id") == "siti")
            log_test("3. WhatsApp Gateway Status (/bff/api/whatsapp/status)", ok, {
                "status": data.get("status"),
                "webhook_url": data.get("webhook_url"),
                "primary": data.get("primary_agent", {}).get("name"),
                "escalation": data.get("escalation_agent", {}).get("name"),
                "processed": data.get("total_messages_processed")
            })
    except Exception as e:
        log_test("3. WhatsApp Gateway Status (/bff/api/whatsapp/status)", False, str(e))

    # 4. Meta Webhook Handshake Verification (GET)
    try:
        challenge = "day5_e2e_challenge_9988"
        url_v = f"{BASE_URL}/bff/api/whatsapp/webhook?hub.mode=subscribe&hub.verify_token=pegawai_ai_wa_verify_secret&hub.challenge={challenge}"
        resp = urllib.request.urlopen(url_v, timeout=15)
        text = resp.read().decode('utf-8')
        ok = (resp.status == 200 and text == challenge)
        log_test("4. Meta Webhook Verification Handshake (GET)", ok, f"HTTP {resp.status}, Echo: {text}")
    except Exception as e:
        log_test("4. Meta Webhook Verification Handshake (GET)", False, str(e))

    # 5. WhatsApp Inbound Meta Format -> Frontline Siti
    try:
        url_wh = f"{BASE_URL}/bff/api/whatsapp/webhook"
        meta_payload = {
            "object": "whatsapp_business_account",
            "entry": [{
                "id": "1002938475",
                "changes": [{
                    "value": {
                        "messaging_product": "whatsapp",
                        "contacts": [{"wa_id": "6281122334455", "profile": {"name": "Maya Indah"}}],
                        "messages": [{
                            "from": "6281122334455",
                            "id": "wamid.HBgLMDYyODExMjIzMzQ0NTU=",
                            "timestamp": "1731910000",
                            "type": "text",
                            "text": {"body": "Halo Colorbox, apakah oversized blazer warna dusty olive masih ada?"}
                        }]
                    },
                    "field": "messages"
                }]
            }]
        }
        req_wh = urllib.request.Request(url_wh, data=json.dumps(meta_payload).encode('utf-8'), headers={"Content-Type": "application/json"}, method="POST")
        with urllib.request.urlopen(req_wh, timeout=15) as resp:
            data = json.loads(resp.read().decode('utf-8'))
            msg = data.get("messages", [{}])[0]
            ok = (msg.get("routed_bot") == "siti" and msg.get("status") == "replied")
            log_test("5. WhatsApp Inbound Webhook -> Siti (POST)", ok, {
                "routed_bot": msg.get("routed_bot"),
                "intent": msg.get("intent"),
                "priority": msg.get("priority"),
                "reply_snippet": msg.get("reply", "")[:80] + "..."
            })
    except Exception as e:
        log_test("5. WhatsApp Inbound Webhook -> Siti (POST)", False, str(e))

    # 6. WhatsApp Simulation Escalation -> Hendra (P1)
    try:
        url_sim = f"{BASE_URL}/bff/api/whatsapp/simulate"
        esc_payload = {
            "sender": "6281987654321",
            "customer_name": "Rian Kusuma",
            "message": "Barang pesanan saya yang sampai jahitannya sobek parah dan kotor! Saya minta ganti rugi atau refund!"
        }
        req_sim = urllib.request.Request(url_sim, data=json.dumps(esc_payload).encode('utf-8'), headers={"Content-Type": "application/json", "X-Pegawai-AI-Key": BFF_KEY}, method="POST")
        with urllib.request.urlopen(req_sim, timeout=15) as resp:
            data = json.loads(resp.read().decode('utf-8'))
            ok = (data.get("routed_bot") == "hendra" and data.get("priority") == "P1" and data.get("status") == "escalated")
            log_test("6. WhatsApp Simulation Escalation -> Hendra P1 (POST)", ok, {
                "routed_bot": data.get("routed_bot"),
                "priority": data.get("priority"),
                "status": data.get("status"),
                "reply_snippet": data.get("reply", "")[:80] + "..."
            })
    except Exception as e:
        log_test("6. WhatsApp Simulation Escalation -> Hendra P1 (POST)", False, str(e))

    # 7. Unified Third-Party Tools Integrations Overview
    try:
        url_tools = f"{BASE_URL}/bff/api/tools/integrations"
        req_tools = urllib.request.Request(url_tools, headers={"X-Pegawai-AI-Key": BFF_KEY})
        with urllib.request.urlopen(req_tools, timeout=15) as resp:
            data = json.loads(resp.read().decode('utf-8'))
            tools = data.get("tools", [])
            gdrive = next((t for t in tools if t["id"] == "gdrive"), None)
            ok = (len(tools) == 4 and gdrive and gdrive.get("redirect_uri", "").startswith("https://"))
            log_test("7. Unified Tools Overview (/bff/api/tools/integrations)", ok, {
                "tools_count": len(tools),
                "gdrive_redirect": gdrive.get("redirect_uri") if gdrive else None,
                "whatsapp_webhook": next((t for t in tools if t["id"] == "whatsapp"), {}).get("webhook_url")
            })
    except Exception as e:
        log_test("7. Unified Tools Overview (/bff/api/tools/integrations)", False, str(e))

    # 8. Hermes Connectors Catalog (54 Apps)
    try:
        url_cat = f"{BASE_URL}/bff/api/apps/catalog"
        req_cat = urllib.request.Request(url_cat, headers={"X-Pegawai-AI-Key": BFF_KEY})
        with urllib.request.urlopen(req_cat, timeout=15) as resp:
            data = json.loads(resp.read().decode('utf-8'))
            apps_count = len(data.get("apps", []))
            ok = (apps_count >= 50)
            log_test("8. Hermes Connectors Catalog (/bff/api/apps/catalog)", ok, {
                "categories": len(data.get("categories", [])),
                "apps_count": apps_count,
                "sample_app": data.get("apps", [{}])[0].get("name")
            })
    except Exception as e:
        log_test("8. Hermes Connectors Catalog (/bff/api/apps/catalog)", False, str(e))

    # 9. All 7 Official Bots Active
    try:
        url_bots = f"{BASE_URL}/bff/api/bots"
        req_bots = urllib.request.Request(url_bots, headers={"X-Pegawai-AI-Key": BFF_KEY})
        with urllib.request.urlopen(req_bots, timeout=15) as resp:
            bots_data = json.loads(resp.read().decode('utf-8'))
            active_ids = {b["id"] for b in bots_data}
            expected = {"bimo", "meda", "raka", "bram", "vina", "siti", "hendra"}
            ok = expected.issubset(active_ids)
            log_test("9. Multi-Agent 7 Profiles Active (/bff/api/bots)", ok, {
                "total_bots": len(bots_data),
                "active_ids": sorted(list(active_ids))
            })
    except Exception as e:
        log_test("9. Multi-Agent 7 Profiles Active (/bff/api/bots)", False, str(e))

    # 10. Token Usage Cost in USD
    try:
        url_usg = f"{BASE_URL}/bff/api/usage"
        req_usg = urllib.request.Request(url_usg, headers={"X-Pegawai-AI-Key": BFF_KEY})
        with urllib.request.urlopen(req_usg, timeout=15) as resp:
            usg_data = json.loads(resp.read().decode('utf-8'))
            ok = (usg_data.get("currency") == "USD" and "cost" in usg_data and "limit" in usg_data)
            log_test("10. Token Cost & Spending Limits (/bff/api/usage)", ok, {
                "currency": usg_data.get("currency"),
                "cost_label": usg_data.get("cost", {}).get("label"),
                "limit_label": usg_data.get("limit", {}).get("label")
            })
    except Exception as e:
        log_test("10. Token Cost & Spending Limits (/bff/api/usage)", False, str(e))

    # 11. WhatsApp Web Simulator
    try:
        resp = urllib.request.urlopen(f"{BASE_URL}/wa-tester.html", timeout=15)
        html = resp.read().decode('utf-8')
        ok = (resp.status == 200 and "Colorbox WhatsApp CS Simulator" in html)
        log_test("11. WhatsApp Web Simulator (/wa-tester.html)", ok, f"HTTP {resp.status}, length: {len(html)}")
    except Exception as e:
        log_test("11. WhatsApp Web Simulator (/wa-tester.html)", False, str(e))

    # 12. VPS Host Resource & Stability Inspection (SSH)
    try:
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh.connect(VPS_HOST, port=22, username=VPS_USER, password=VPS_PASS, timeout=10)
        
        stdin, stdout, stderr = ssh.exec_command("free -m; uptime; df -h /")
        sys_info = stdout.read().decode('utf-8')
        stdin, stdout, stderr = ssh.exec_command("systemctl is-active pegawai-ai-bff hermes-gateway nginx")
        svc_info = stdout.read().decode('utf-8').splitlines()
        ssh.close()
        
        services_ok = (svc_info == ["active", "active", "active"])
        log_test("12. Host OS Health & Daemons (SSH)", services_ok, {
            "services": {"bff": svc_info[0], "hermes": svc_info[1], "nginx": svc_info[2]},
            "metrics_raw": sys_info.strip().splitlines()[:3]
        })
    except Exception as e:
        log_test("12. Host OS Health & Daemons (SSH)", False, str(e))

    print("\n=====================================================")
    passed = sum(1 for v in results.values() if v["success"])
    total = len(results)
    print(f"📊 HASIL AKHIR: {passed}/{total} Pengujian Lulus ({(passed/total)*100:.1f}%)")
    print("=====================================================")

    with open("day5_stability_results.json", "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2)

if __name__ == "__main__":
    main()
