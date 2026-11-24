import os
import paramiko
import json
import urllib.request
import ssl
import time

VPS_IP = '139.190.107.151'
KEY_FILE = 'vps/key-pegawai-ai.pem'
BASE_URL = 'https://139.190.107.151.sslip.io'
BFF_API_KEY = 'mh6IG_kqNfpu4YJe1Gi8FzM1tzejRPSbWfDSRNFriCI'
TELEGRAM_SECRET = 'pegawai_ai_telegram_secret_token_2026'

def main():
    print("=== SPRINT 5 DAY 4: DEPLOYMENT & VERIFICATION ===")
    
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    print(f"Connecting to VPS {VPS_IP}...")
    ssh.connect(VPS_IP, username='ubuntu', key_filename=KEY_FILE)
    sftp = ssh.open_sftp()
    
    print("\n1. Uploading Day 4 BFF files...")
    sftp.put('bff/bff/telegram.py', '/home/ubuntu/pegawai-ai/bff/bff/telegram.py')
    print(" - bff/bff/telegram.py uploaded")
    sftp.put('bff/bff/memory_blueprint.py', '/home/ubuntu/pegawai-ai/bff/bff/memory_blueprint.py')
    print(" - bff/bff/memory_blueprint.py uploaded")
    sftp.put('bff/bff/main.py', '/home/ubuntu/pegawai-ai/bff/bff/main.py')
    print(" - bff/bff/main.py uploaded")
    sftp.put('bff/tests/test_day4_sprint5.py', '/home/ubuntu/pegawai-ai/bff/tests/test_day4_sprint5.py')
    print(" - bff/tests/test_day4_sprint5.py uploaded")
    
    sftp.close()

    print("\n2. Restarting pegawai-ai-bff service on VPS...")
    stdin, stdout, stderr = ssh.exec_command('sudo systemctl restart pegawai-ai-bff')
    stdout.channel.recv_exit_status()

    # Wait up to 20s for service to become fully healthy
    for i in range(10):
        time.sleep(2)
        stdin, stdout, stderr = ssh.exec_command('curl -s -o /dev/null -w "%{http_code}" http://127.0.0.1:8090/healthz || true')
        code = stdout.read().decode().strip()
        if code in ("200", "404"):
            print(f"BFF responsive on port 8090 (status: {code}) after {(i+1)*2}s")
            break

    stdin, stdout, stderr = ssh.exec_command('sudo systemctl is-active pegawai-ai-bff')
    status = stdout.read().decode().strip()
    print("BFF status:", status)

    if status != "active":
        stdin, stdout, stderr = ssh.exec_command('sudo journalctl -u pegawai-ai-bff -n 40 --no-pager')
        print("Error logs:\n", stdout.read().decode())
        ssh.close()
        exit(1)

    print("\n3. Running Pytest Suite directly on VPS...")
    cmd = 'cd /home/ubuntu/pegawai-ai/bff && /home/ubuntu/pegawai-ai/bff/.venv/bin/pytest tests/test_day4_sprint5.py -v'
    stdin, stdout, stderr = ssh.exec_command(cmd)
    exit_code = stdout.channel.recv_exit_status()
    out = stdout.read().decode()
    err = stderr.read().decode()
    print("Pytest VPS Output:\n" + out)
    if exit_code != 0:
        print("Pytest VPS Error:\n" + err)
        ssh.close()
        exit(1)

    ssh.close()
    print("\nVPS Backend Deployment & Remote Pytest passed cleanly!")

    # 4. Live HTTPS verification against nginx reverse proxy
    print("\n4. Running Live HTTPS API Verification against Nginx...")
    ctx = ssl.create_default_context()
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE

    headers_auth = {
        'X-Pegawai-AI-Key': BFF_API_KEY,
        'Content-Type': 'application/json'
    }

    # Test A: GET /bff/api/telegram/status
    url_tg_status = f"{BASE_URL}/bff/api/telegram/status"
    req = urllib.request.Request(url_tg_status, headers=headers_auth, method='GET')
    with urllib.request.urlopen(req, context=ctx) as resp:
        res = json.loads(resp.read().decode())
        print(f"[PASSED] GET /bff/api/telegram/status: supported_commands={res['supported_commands']}")
        assert "/start" in res['supported_commands']
        assert res['max_message_chars'] == 4096

    # Test B: POST /bff/api/telegram/simulate (Command /start)
    url_sim = f"{BASE_URL}/bff/api/telegram/simulate"
    start_body = json.dumps({
        "text": "/start",
        "chat_id": 999333444,
        "sender_name": "Faiz Test"
    }).encode('utf-8')
    req = urllib.request.Request(url_sim, data=start_body, headers=headers_auth, method='POST')
    with urllib.request.urlopen(req, context=ctx) as resp:
        res = json.loads(resp.read().decode())
        print(f"[PASSED] POST /bff/api/telegram/simulate (/start): command='{res.get('command')}', reply length={len(res.get('reply', ''))}")
        assert res['status'] == 'command_handled'
        assert 'Selamat datang' in res['reply']

    # Test C: POST /bff/api/telegram/simulate (Customer Service Question)
    cs_body = json.dumps({
        "text": "Halo kak, bagaimana cara retur barang cacat?",
        "chat_id": 999333444,
        "sender_name": "Faiz Test"
    }).encode('utf-8')
    req = urllib.request.Request(url_sim, data=cs_body, headers=headers_auth, method='POST')
    with urllib.request.urlopen(req, context=ctx) as resp:
        res = json.loads(resp.read().decode())
        print(f"[PASSED] POST /bff/api/telegram/simulate (CS Question): bot_id='{res.get('bot_id')}', reply='{res.get('agent_reply')[:80]}...'")
        assert res['status'] == 'message_routed'
        assert 'retur' in res['agent_reply'].lower()

    # Test D: POST /bff/api/telegram/webhook (Direct Webhook with Secret Token)
    url_webhook = f"{BASE_URL}/bff/api/telegram/webhook"
    webhook_headers = {
        'Content-Type': 'application/json',
        'X-Telegram-Bot-Api-Secret-Token': TELEGRAM_SECRET
    }
    wh_body = json.dumps({
        "update_id": int(time.time()),
        "message": {
            "message_id": int(time.time()),
            "from": {"id": 888777666, "first_name": "Webhook Tester", "is_bot": False},
            "chat": {"id": 888777666, "type": "private"},
            "date": int(time.time()),
            "text": "/status"
        }
    }).encode('utf-8')
    req = urllib.request.Request(url_webhook, data=wh_body, headers=webhook_headers, method='POST')
    with urllib.request.urlopen(req, context=ctx) as resp:
        res = json.loads(resp.read().decode())
        print(f"[PASSED] POST /bff/telegram/webhook (Direct with secret): status='{res.get('status')}'")
        assert res['ok'] is True

    # Test E: GET /bff/api/memory/blueprint
    url_blueprint = f"{BASE_URL}/bff/api/memory/blueprint"
    req = urllib.request.Request(url_blueprint, headers=headers_auth, method='GET')
    with urllib.request.urlopen(req, context=ctx) as resp:
        res = json.loads(resp.read().decode())
        candidates = res['candidates_benchmark']
        print(f"[PASSED] GET /bff/api/memory/blueprint: {len(candidates)} candidates evaluated ({list(candidates.keys())})")
        assert len(candidates) == 7
        assert 'memo' in candidates
        assert 'obsidian' in candidates

    # Test F: GET /bff/api/memory/layers
    url_layers = f"{BASE_URL}/bff/api/memory/layers"
    req = urllib.request.Request(url_layers, headers=headers_auth, method='GET')
    with urllib.request.urlopen(req, context=ctx) as resp:
        res = json.loads(resp.read().decode())
        summary = res['status_summary']
        print(f"[PASSED] GET /bff/api/memory/layers: layer_1={summary['layer_1_session']}, layer_2={summary['layer_2_employee']}, layer_5={summary['layer_5_long_term']}")
        assert summary['layer_1_session'] == 'AVAILABLE'
        assert summary['layer_5_long_term'] == 'PLANNED'

    # Test G: POST /bff/api/memory/tenant/validate-isolation
    url_iso = f"{BASE_URL}/bff/api/memory/tenant/validate-isolation"
    iso_body = json.dumps({
        "tenant_a": "tenant_alpha_corp",
        "tenant_b": "tenant_beta_ltd"
    }).encode('utf-8')
    req = urllib.request.Request(url_iso, data=iso_body, headers=headers_auth, method='POST')
    with urllib.request.urlopen(req, context=ctx) as resp:
        res = json.loads(resp.read().decode())
        print(f"[PASSED] POST /bff/api/memory/tenant/validate-isolation: isolation_verified={res['isolation_verified']}, scenarios_tested={res['scenarios_tested']}")
        assert res['isolation_verified'] is True
        assert res['scenarios_tested'] == 5

    print("\nALL 7 LIVE ENDPOINTS VERIFIED 100% OPERATIONAL ON VPS!")

if __name__ == '__main__':
    main()
