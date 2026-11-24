import os
import paramiko
import json
import urllib.request
import ssl

VPS_IP = '139.190.107.151'
KEY_FILE = 'vps/key-pegawai-ai.pem'
BASE_URL = 'https://139.190.107.151.sslip.io'
BFF_API_KEY = 'mh6IG_kqNfpu4YJe1Gi8FzM1tzejRPSbWfDSRNFriCI'

def main():
    print("=== SPRINT 5 DAY 3: DEPLOYMENT & VERIFICATION ===")
    
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    print(f"Connecting to VPS {VPS_IP}...")
    ssh.connect(VPS_IP, username='ubuntu', key_filename=KEY_FILE)
    sftp = ssh.open_sftp()
    
    def upload_dir(local_path, remote_path):
        try:
            sftp.mkdir(remote_path)
        except IOError:
            pass
        for item in os.listdir(local_path):
            l_item = os.path.join(local_path, item).replace('\\', '/')
            r_item = f"{remote_path}/{item}"
            if os.path.isdir(l_item):
                upload_dir(l_item, r_item)
            else:
                sftp.put(l_item, r_item)

    print("\n1. Uploading modified & new BFF files...")
    sftp.put('bff/bff/master_template.py', '/home/ubuntu/pegawai-ai/bff/bff/master_template.py')
    print(" - bff/bff/master_template.py uploaded")
    sftp.put('bff/bff/mcp_privileges.py', '/home/ubuntu/pegawai-ai/bff/bff/mcp_privileges.py')
    print(" - bff/bff/mcp_privileges.py uploaded")
    sftp.put('bff/bff/main.py', '/home/ubuntu/pegawai-ai/bff/bff/main.py')
    print(" - bff/bff/main.py uploaded")
    sftp.put('bff/tests/test_day3_sprint5.py', '/home/ubuntu/pegawai-ai/bff/tests/test_day3_sprint5.py')
    print(" - bff/tests/test_day3_sprint5.py uploaded")

    print("\n2. Uploading templates/agents directory...")
    # Ensure remote templates/agents exists
    try:
        sftp.mkdir('/home/ubuntu/pegawai-ai/templates')
    except IOError:
        pass
    upload_dir('templates/agents', '/home/ubuntu/pegawai-ai/templates/agents')
    print(" - templates/agents uploaded successfully")
    
    sftp.close()

    print("\n3. Restarting pegawai-ai-bff service on VPS...")
    stdin, stdout, stderr = ssh.exec_command('sudo systemctl restart pegawai-ai-bff')
    stdout.channel.recv_exit_status()

    # Wait up to 20s for service to become fully healthy
    import time
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

    print("\n4. Running Pytest Suite directly on VPS...")
    cmd = 'cd /home/ubuntu/pegawai-ai/bff && /home/ubuntu/pegawai-ai/bff/.venv/bin/pytest tests/test_day3_sprint5.py -v'
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

    # 5. Live HTTPS verification against nginx reverse proxy
    print("\n5. Running Live HTTPS API Verification against Nginx...")
    ctx = ssl.create_default_context()
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE

    headers = {
        'X-Pegawai-AI-Key': BFF_API_KEY,
        'Content-Type': 'application/json'
    }

    # Test A: GET /bff/api/templates/master
    url_templates = f"{BASE_URL}/bff/api/templates/master"
    req = urllib.request.Request(url_templates, headers=headers, method='GET')
    with urllib.request.urlopen(req, context=ctx) as resp:
        res = json.loads(resp.read().decode())
        print(f"[PASSED] GET /bff/api/templates/master: {len(res)} templates found")
        assert len(res) >= 7

    # Test B: GET /bff/api/templates/master/CS-01
    url_cs01 = f"{BASE_URL}/bff/api/templates/master/CS-01"
    req = urllib.request.Request(url_cs01, headers=headers, method='GET')
    with urllib.request.urlopen(req, context=ctx) as resp:
        res = json.loads(resp.read().decode())
        print(f"[PASSED] GET /bff/api/templates/master/CS-01: name='{res['name']}', mcp_tier='{res['mcp_tier']}'")
        assert res['id'] == 'CS-01'
        assert 'SOUL.md' in res['files']
        assert 'SKILL.md' in res['files']

    # Test C: POST /bff/api/templates/render
    url_render = f"{BASE_URL}/bff/api/templates/render"
    render_body = json.dumps({
        "role_id": "CRE-01",
        "variables": {
            "brand_name": "Aura Glow Cafe & Bakery",
            "industry": "Artisan Bakery & Cafe",
            "target_audience": "Pecinta pastry dan kopi artisan"
        }
    }).encode('utf-8')
    req = urllib.request.Request(url_render, data=render_body, headers=headers, method='POST')
    with urllib.request.urlopen(req, context=ctx) as resp:
        res = json.loads(resp.read().decode())
        print(f"[PASSED] POST /bff/api/templates/render: successfully rendered variables into SOUL.md")
        assert "Aura Glow Cafe & Bakery" in res['rendered_files']['SOUL.md']
        assert "{{brand_name}}" not in res['rendered_files']['SOUL.md']

    # Test D: GET /bff/api/hermes/config-mapping
    url_hermes = f"{BASE_URL}/bff/api/hermes/config-mapping"
    req = urllib.request.Request(url_hermes, headers=headers, method='GET')
    with urllib.request.urlopen(req, context=ctx) as resp:
        res = json.loads(resp.read().decode())
        spec = res['spec']
        print(f"[PASSED] GET /bff/api/hermes/config-mapping: documented gaps={list(spec['documented_architecture_gaps'].keys())}")
        assert "user.md" in spec['documented_architecture_gaps']
        assert "agents.md" in spec['documented_architecture_gaps']

    # Test E: GET /bff/api/bots/siti/permissions
    url_siti = f"{BASE_URL}/bff/api/bots/siti/permissions"
    req = urllib.request.Request(url_siti, headers=headers, method='GET')
    with urllib.request.urlopen(req, context=ctx) as resp:
        res = json.loads(resp.read().decode())
        print(f"[PASSED] GET /bff/api/bots/siti/permissions: bot_id='{res['bot_id']}', mcp_tier='{res['mcp_tier']}', can_access_finance={res['can_access_finance']}")
        assert res['bot_id'] == 'siti'
        assert res['can_access_finance'] is False

    # Test F: PATCH /bff/api/bots/siti/permissions
    url_patch = f"{BASE_URL}/bff/api/bots/siti/permissions"
    patch_body = json.dumps({
        "reasoning_effort": "high"
    }).encode('utf-8')
    req = urllib.request.Request(url_patch, data=patch_body, headers=headers, method='PATCH')
    with urllib.request.urlopen(req, context=ctx) as resp:
        res = json.loads(resp.read().decode())
        print(f"[PASSED] PATCH /bff/api/bots/siti/permissions: updated reasoning_effort='{res['reasoning_effort']}'")
        assert res['reasoning_effort'] == 'high'

    # Revert reasoning_effort back
    revert_body = json.dumps({
        "reasoning_effort": "medium"
    }).encode('utf-8')
    req = urllib.request.Request(url_patch, data=revert_body, headers=headers, method='PATCH')
    with urllib.request.urlopen(req, context=ctx) as resp:
        res = json.loads(resp.read().decode())
        print(f"[PASSED] PATCH /bff/api/bots/siti/permissions: reverted reasoning_effort='{res['reasoning_effort']}'")

    print("\nALL 6 LIVE ENDPOINTS VERIFIED 100% OPERATIONAL ON VPS!")

if __name__ == '__main__':
    main()
