"""Sprint 5 Day 5: Comprehensive QA & Security Isolation Verification Script.
Executes end-to-end tests across VPS Demo, Auth, KB, FastMCP, Master Templates,
Telegram Webhook, 5-Layer Memory Blueprint, and 5 Negative Threat Scenarios.
"""
import json
import os
import ssl
import time
import urllib.request
import paramiko

VPS_IP = "139.190.107.151"
KEY_FILE = "vps/key-pegawai-ai.pem"
BASE_URL = "https://139.190.107.151.sslip.io"
BFF_API_KEY = "mh6IG_kqNfpu4YJe1Gi8FzM1tzejRPSbWfDSRNFriCI"
TELEGRAM_TOKEN = "8642965347:AAG-Uz4QNGKZz5bNQeJxCuKGxgLWoEjt00w"

results = {
    "vps_hardening": {},
    "vps_resources": {},
    "remote_pytest": {},
    "live_demo_http": {},
    "live_auth_flow": {},
    "live_telegram_webhook": {},
    "live_memory_blueprint": {},
    "threat_scenarios_validation": {}
}

def make_https_request(url: str, method: str = "GET", headers: dict = None, data: dict = None):
    ctx = ssl.create_default_context()
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE
    
    encoded_data = json.dumps(data).encode("utf-8") if data is not None else None
    req = urllib.request.Request(url, data=encoded_data, headers=headers or {}, method=method)
    
    try:
        with urllib.request.urlopen(req, context=ctx, timeout=10) as resp:
            code = resp.getcode()
            body = resp.read().decode("utf-8")
            try:
                parsed_json = json.loads(body)
                return code, parsed_json
            except json.JSONDecodeError:
                return code, body
    except urllib.error.HTTPError as e:
        body = e.read().decode("utf-8")
        try:
            parsed_json = json.loads(body)
            return e.code, parsed_json
        except json.JSONDecodeError:
            return e.code, body
    except Exception as ex:
        return 0, str(ex)

def main():
    print("=================================================================")
    print("   SPRINT 5 DAY 5: FINAL QA & ARCHITECTURE AUDIT SUITE           ")
    print("=================================================================\n")

    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    print(f"[*] Connecting to VPS via SSH ({VPS_IP})...")
    ssh.connect(VPS_IP, username="ubuntu", key_filename=KEY_FILE)
    sftp = ssh.open_sftp()

    print("[*] Uploading updated Day 5 files to VPS...")
    sftp.put("bff/bff/memory_blueprint.py", "/home/ubuntu/pegawai-ai/bff/bff/memory_blueprint.py")
    sftp.put("bff/tests/test_day5_sprint5.py", "/home/ubuntu/pegawai-ai/bff/tests/test_day5_sprint5.py")
    sftp.close()
    print("    - memory_blueprint.py and test_day5_sprint5.py uploaded.")

    print("[*] Restarting pegawai-ai-bff service...")
    stdin, stdout, stderr = ssh.exec_command("sudo systemctl restart pegawai-ai-bff")
    stdout.channel.recv_exit_status()
    time.sleep(3)

    # 1. Audit VPS Hardening & Ports
    print("\n--- 1. AUDITING VPS HARDENING & PORTS ---")
    _, out_ufw, _ = ssh.exec_command("sudo ufw status verbose")
    ufw_text = out_ufw.read().decode().strip()
    print("[UFW Status]:\n" + ufw_text)
    results["vps_hardening"]["ufw"] = ufw_text

    _, out_ports, _ = ssh.exec_command("sudo ss -tulpn | grep LISTEN")
    ports_text = out_ports.read().decode().strip()
    print("\n[Listening Sockets]:\n" + ports_text)
    results["vps_hardening"]["ports"] = ports_text

    # 2. Audit VPS Resources
    print("\n--- 2. AUDITING VPS RESOURCES ---")
    _, out_uptime, _ = ssh.exec_command("uptime")
    uptime_text = out_uptime.read().decode().strip()
    print("[Uptime & Load]: " + uptime_text)
    results["vps_resources"]["uptime"] = uptime_text

    _, out_cpu, _ = ssh.exec_command('lscpu | grep "Model name\\|CPU(s):"')
    cpu_text = out_cpu.read().decode().strip()
    print("[CPU Info]:\n" + cpu_text)
    results["vps_resources"]["cpu"] = cpu_text

    _, out_ram, _ = ssh.exec_command("free -h")
    ram_text = out_ram.read().decode().strip()
    print("[RAM Usage]:\n" + ram_text)
    results["vps_resources"]["ram"] = ram_text

    _, out_disk, _ = ssh.exec_command("df -h /")
    disk_text = out_disk.read().decode().strip()
    print("[Disk Usage]:\n" + disk_text)
    results["vps_resources"]["disk"] = disk_text

    # 3. Run Remote Pytest Suite on VPS
    print("\n--- 3. RUNNING REMOTE PYTEST SUITE ON VPS ---")
    pytest_cmd = "cd /home/ubuntu/pegawai-ai/bff && /home/ubuntu/pegawai-ai/bff/.venv/bin/pytest tests/test_day5_sprint5.py tests/test_day4_sprint5.py -v"
    stdin, stdout, stderr = ssh.exec_command(pytest_cmd)
    exit_code = stdout.channel.recv_exit_status()
    pytest_out = stdout.read().decode()
    print(pytest_out)
    results["remote_pytest"]["exit_code"] = exit_code
    results["remote_pytest"]["output"] = pytest_out

    ssh.close()

    # 4. Live HTTPS Demo & Frontend Check
    print("\n--- 4. LIVE HTTPS DEMO & FRONTEND VERIFICATION ---")
    demo_url = f"{BASE_URL}/demo"
    code_demo, body_demo = make_https_request(demo_url)
    print(f"GET {demo_url} -> HTTP {code_demo}")
    has_html = "<!doctype html>" in body_demo.lower() or "<html" in body_demo.lower()
    has_root = 'id="root"' in body_demo
    print(f"    - HTML Present: {has_html}")
    print(f"    - React #root Present: {has_root}")
    results["live_demo_http"] = {
        "url": demo_url,
        "status_code": code_demo,
        "html_valid": has_html,
        "react_root_present": has_root
    }

    # 5. Live Auth Flow Verification (Demo Login & JWT)
    print("\n--- 5. LIVE AUTH FLOW VERIFICATION ---")
    login_url = f"{BASE_URL}/bff/api/auth/login"
    
    # 5a. Bad Password (should return 401)
    code_bad, res_bad = make_https_request(
        login_url,
        method="POST",
        headers={"Content-Type": "application/json"},
        data={"email": "demo@colorbox.co.id", "password": "WrongPassword123!"}
    )
    print(f"POST {login_url} (Wrong Password) -> HTTP {code_bad}")
    print(f"    - Response: {res_bad}")
    
    # 5b. Valid Login (or register if demo user not seeded on VPS)
    # Check if demo user exists, if not register demo account
    code_login, res_login = make_https_request(
        login_url,
        method="POST",
        headers={"Content-Type": "application/json"},
        data={"email": "demo@colorbox.co.id", "password": "DemoPegawai2026!"}
    )
    jwt_token = None
    if code_login == 200:
        jwt_token = res_login.get("token")
        print(f"POST {login_url} (Valid Login) -> HTTP 200, JWT generated: {jwt_token[:25]}...")
    else:
        print(f"Demo user not seeded yet, registering demo account...")
        reg_url = f"{BASE_URL}/bff/api/auth/register"
        code_reg, res_reg = make_https_request(
            reg_url,
            method="POST",
            headers={"Content-Type": "application/json"},
            data={
                "name": "Demo Client User",
                "email": "demo@colorbox.co.id",
                "password": "DemoPegawai2026!",
                "company": "Colorbox"
            }
        )
        print(f"POST {reg_url} -> HTTP {code_reg}, Response: {res_reg}")
        if code_reg == 200:
            jwt_token = res_reg.get("token")
        else:
            # Try login again
            code_login, res_login = make_https_request(
                login_url,
                method="POST",
                headers={"Content-Type": "application/json"},
                data={"email": "demo@colorbox.co.id", "password": "DemoPegawai2026!"}
            )
            jwt_token = res_login.get("token")

    # 5c. Protected /bff/api/auth/me without token (should return 401)
    me_url = f"{BASE_URL}/bff/api/auth/me"
    code_me_unauth, res_me_unauth = make_https_request(me_url)
    print(f"GET {me_url} (No Token) -> HTTP {code_me_unauth}")

    # 5d. Protected /bff/api/auth/me with Bearer JWT (should return 200)
    code_me_auth, res_me_auth = make_https_request(
        me_url,
        headers={"Authorization": f"Bearer {jwt_token}"}
    )
    print(f"GET {me_url} (With Bearer JWT) -> HTTP {code_me_auth}")
    print(f"    - User profile: {res_me_auth}")

    results["live_auth_flow"] = {
        "bad_password_status": code_bad,
        "valid_login_status": code_login if code_login == 200 else code_reg,
        "unauth_me_status": code_me_unauth,
        "auth_me_status": code_me_auth,
        "user_profile": res_me_auth
    }

    # 6. Live Telegram Webhook & Status Check
    print("\n--- 6. LIVE TELEGRAM WEBHOOK & BOT STATUS ---")
    tg_status_url = f"{BASE_URL}/bff/api/telegram/status"
    code_tg, res_tg = make_https_request(tg_status_url)
    print(f"GET {tg_status_url} -> HTTP {code_tg}")
    print(f"    - Telegram Status: {res_tg}")

    # Verify live webhook from Telegram official API
    tg_api_url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/getWebhookInfo"
    code_tg_api, res_tg_api = make_https_request(tg_api_url)
    print(f"GET {tg_api_url} -> HTTP {code_tg_api}")
    print(f"    - Telegram API Webhook Info: {res_tg_api}")

    results["live_telegram_webhook"] = {
        "bff_status": res_tg,
        "telegram_api_webhook_info": res_tg_api
    }

    # 7. Live 5-Layer Memory Blueprint & 7-Candidate Benchmark
    print("\n--- 7. LIVE MEMORY BLUEPRINT & BENCHMARK ---")
    bp_url = f"{BASE_URL}/bff/api/memory/blueprint"
    code_bp, res_bp = make_https_request(bp_url, headers={"X-Pegawai-AI-Key": BFF_API_KEY})
    print(f"GET {bp_url} -> HTTP {code_bp}")
    print(f"    - Layers Count: {len(res_bp.get('layers', []))}")
    print(f"    - Candidates Count: {len(res_bp.get('candidates_benchmark', {}))}")
    print(f"    - Primary MVP Recommendation: {res_bp.get('runtime_status', {}).get('primary_mvp_candidate')}")
    print(f"    - Explicit Deferred Items: {res_bp.get('explicit_deferred_scope')}")

    results["live_memory_blueprint"] = {
        "status_code": code_bp,
        "blueprint_version": res_bp.get("blueprint_version"),
        "layers": res_bp.get("layers"),
        "explicit_deferred_scope": res_bp.get("explicit_deferred_scope"),
        "runtime_status": res_bp.get("runtime_status")
    }

    # 8. Live 5 Threat Scenarios Tenant Isolation Validation
    print("\n--- 8. LIVE 5 THREAT SCENARIOS TENANT ISOLATION VALIDATION ---")
    threat_url = f"{BASE_URL}/bff/api/memory/tenant/validate-isolation"
    code_threat, res_threat = make_https_request(
        threat_url,
        method="POST",
        headers={"X-Pegawai-AI-Key": BFF_API_KEY, "Content-Type": "application/json"},
        data={"tenant_a": "tenant_alpha_corp", "tenant_b": "tenant_beta_ltd"}
    )
    print(f"POST {threat_url} -> HTTP {code_threat}")
    print(f"    - Isolation Verified: {res_threat.get('isolation_verified')}")
    print(f"    - Scenarios Tested: {res_threat.get('scenarios_tested')}")
    for sc in res_threat.get("scenarios", []):
        print(f"      * {sc.get('scenario')}: {sc.get('outcome')} ({sc.get('reason')})")

    results["threat_scenarios_validation"] = res_threat

    # Save complete audit results to JSON
    with open("vps/qa_day5_audit_results.json", "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2)
    print("\n[OK] Full QA audit results saved to vps/qa_day5_audit_results.json")

if __name__ == "__main__":
    main()
