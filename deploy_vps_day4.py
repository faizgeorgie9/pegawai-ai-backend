import os
import time
import json
import urllib.request
import paramiko

VPS_HOST = "139.190.107.151"
VPS_USER = "ubuntu"
VPS_PASS = "@Baruk516"
BFF_KEY = "mh6IG_kqNfpu4YJe1Gi8FzM1tzejRPSbWfDSRNFriCI"

def main():
    print("[1/4] Connecting to VPS via SSH & SFTP...")
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(VPS_HOST, port=22, username=VPS_USER, password=VPS_PASS, timeout=10)
    sftp = ssh.open_sftp()

    print("[2/4] Uploading backend files...")
    sftp.put("bff/migrations/019_whatsapp_messages.sql", "/home/ubuntu/pegawai-ai/bff/migrations/019_whatsapp_messages.sql")
    sftp.put("bff/bff/whatsapp.py", "/home/ubuntu/pegawai-ai/bff/bff/whatsapp.py")
    sftp.put("bff/bff/main.py", "/home/ubuntu/pegawai-ai/bff/bff/main.py")
    print(" - Uploaded 019_whatsapp_messages.sql, whatsapp.py, and main.py")

    print("[3/4] Uploading frontend build...")
    stdin, stdout, stderr = ssh.exec_command("rm -rf /tmp/fe_dist && mkdir -p /tmp/fe_dist")
    stdout.channel.recv_exit_status()

    dist_dir = "frontend/dist"
    for root, dirs, files in os.walk(dist_dir):
        rel_dir = os.path.relpath(root, dist_dir)
        target_dir = f"/tmp/fe_dist/{rel_dir}".replace("\\", "/").rstrip("/.")
        stdin, stdout, stderr = ssh.exec_command(f"mkdir -p {target_dir}")
        stdout.channel.recv_exit_status()
        for file in files:
            local_f = os.path.join(root, file)
            remote_f = f"{target_dir}/{file}".replace("\\", "/")
            sftp.put(local_f, remote_f)

    stdin, stdout, stderr = ssh.exec_command("sudo cp -r /tmp/fe_dist/* /var/www/pegawai-ai/html/ && sudo chown -R www-data:www-data /var/www/pegawai-ai/html/")
    stdout.channel.recv_exit_status()
    print(" - Frontend build copied to /var/www/pegawai-ai/html/")

    sftp.close()

    print(" - Restarting pegawai-ai-bff service...")
    stdin, stdout, stderr = ssh.exec_command("sudo systemctl restart pegawai-ai-bff")
    stdout.channel.recv_exit_status()
    time.sleep(3)
    
    stdin, stdout, stderr = ssh.exec_command("systemctl is-active pegawai-ai-bff")
    print("Service status:", stdout.read().decode().strip())
    ssh.close()

    print("[4/4] Running live tests on VPS endpoints...")
    time.sleep(10) # wait for startup & migration

    # 1. Test WhatsApp status
    url_st = f"http://{VPS_HOST}/bff/api/whatsapp/status"
    req_st = urllib.request.Request(url_st, headers={"X-Pegawai-AI-Key": BFF_KEY})
    with urllib.request.urlopen(req_st, timeout=25) as resp:
        st_data = json.loads(resp.read().decode("utf-8"))
        print("\n=== [1] WHATSAPP STATUS ===")
        print(json.dumps(st_data, indent=2))

    # 2. Test WhatsApp Webhook Verification
    url_verify = f"http://{VPS_HOST}/bff/api/whatsapp/webhook?hub.mode=subscribe&hub.verify_token=pegawai_ai_wa_verify_secret&hub.challenge=live_test_12345"
    req_v = urllib.request.Request(url_verify)
    with urllib.request.urlopen(req_v, timeout=25) as resp:
        challenge_res = resp.read().decode("utf-8")
        print("\n=== [2] WEBHOOK VERIFICATION (GET) ===")
        print("Status:", resp.status, "| Returned Challenge:", challenge_res)

    # 3. Test WhatsApp Inbound Meta Cloud API Webhook
    url_wh = f"http://{VPS_HOST}/bff/api/whatsapp/webhook"
    meta_payload = {
        "object": "whatsapp_business_account",
        "entry": [{
            "id": "1002938475",
            "changes": [{
                "value": {
                    "messaging_product": "whatsapp",
                    "contacts": [{"wa_id": "6281234567890", "profile": {"name": "Citra Lestari"}}],
                    "messages": [{
                        "from": "6281234567890",
                        "id": "wamid.HBgLMDYyODEyMzQ1Njc4OTA=",
                        "timestamp": "1731901200",
                        "type": "text",
                        "text": {"body": "Halo Colorbox, apakah ada koleksi Liunic yang tote bag ecru?"}
                    }]
                },
                "field": "messages"
            }]
        }]
    }
    req_wh = urllib.request.Request(url_wh, data=json.dumps(meta_payload).encode("utf-8"), headers={"Content-Type": "application/json"}, method="POST")
    with urllib.request.urlopen(req_wh, timeout=25) as resp:
        wh_data = json.loads(resp.read().decode("utf-8"))
        print("\n=== [3] WEBHOOK POST (META CLOUD FORMAT) ===")
        print(json.dumps(wh_data, indent=2))

    # 4. Test WhatsApp Simulation: Severe Complaint (Escalation to Hendra)
    url_sim = f"http://{VPS_HOST}/bff/api/whatsapp/simulate"
    esc_payload = {
        "sender": "6289876543210",
        "customer_name": "Dimas Saputra",
        "message": "Baju pesanan saya yang sampai robek di bagian lengan! Saya minta pertanggungjawaban manajer toko!"
    }
    req_sim = urllib.request.Request(url_sim, data=json.dumps(esc_payload).encode("utf-8"), headers={"Content-Type": "application/json", "X-Pegawai-AI-Key": BFF_KEY}, method="POST")
    with urllib.request.urlopen(req_sim, timeout=25) as resp:
        esc_data = json.loads(resp.read().decode("utf-8"))
        print("\n=== [4] SIMULATION: COMPLAINT ESCALATION (ROUTED TO HENDRA) ===")
        print(json.dumps(esc_data, indent=2))

    # 5. Test Third-Party Tools Unified Overview
    url_tools = f"http://{VPS_HOST}/bff/api/tools/integrations"
    req_tools = urllib.request.Request(url_tools, headers={"X-Pegawai-AI-Key": BFF_KEY})
    with urllib.request.urlopen(req_tools, timeout=25) as resp:
        tools_data = json.loads(resp.read().decode("utf-8"))
        print("\n=== [5] THIRD-PARTY TOOLS INTEGRATION API ===")
        print(json.dumps(tools_data, indent=2))

    # 6. Test WhatsApp Messages History
    url_msgs = f"http://{VPS_HOST}/bff/api/whatsapp/messages"
    req_msgs = urllib.request.Request(url_msgs, headers={"X-Pegawai-AI-Key": BFF_KEY})
    with urllib.request.urlopen(req_msgs, timeout=25) as resp:
        msgs_data = json.loads(resp.read().decode("utf-8"))
        print(f"\n=== [6] WHATSAPP MESSAGES LOGGED ({len(msgs_data)}) ===")
        for m in msgs_data[:5]:
            print(f" - [{m['created_at']}] From {m['customer_name']} ({m['sender']}): {m['message'][:40]}... -> Handled by {m['bot_id']} ({m['status']})")

if __name__ == "__main__":
    main()
