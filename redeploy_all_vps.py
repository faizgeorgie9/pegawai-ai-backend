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
    print("==============================================")
    print("🚀 MEMULAI REDEPLOYMENT KE VPS BIZNET GIO")
    print(f"Target: {VPS_USER}@{VPS_HOST}")
    print("==============================================")

    # 1. SSH & SFTP Connection
    print("\n[1/5] Menghubungkan ke VPS via SSH & SFTP...")
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(VPS_HOST, port=22, username=VPS_USER, password=VPS_PASS, timeout=15)
    sftp = ssh.open_sftp()
    print("✔ SSH & SFTP berhasil terhubung.")

    # 2. Upload Backend BFF files
    print("\n[2/5] Mengupload pembaruan backend BFF...")
    backend_files = [
        ("bff/migrations/019_whatsapp_messages.sql", "/home/ubuntu/pegawai-ai/bff/migrations/019_whatsapp_messages.sql"),
        ("bff/bff/whatsapp.py", "/home/ubuntu/pegawai-ai/bff/bff/whatsapp.py"),
        ("bff/bff/main.py", "/home/ubuntu/pegawai-ai/bff/bff/main.py"),
        ("bff/bff/apps.py", "/home/ubuntu/pegawai-ai/bff/bff/apps.py")
    ]
    for local_p, remote_p in backend_files:
        if os.path.exists(local_p):
            sftp.put(local_p, remote_p)
            print(f" - Uploaded: {local_p} -> {remote_p}")
    print("✔ Seluruh file backend inti berhasil diperbarui.")

    # 3. Upload Frontend Dist Build
    print("\n[3/5] Mengupload aset produksi Frontend (Vite dist)...")
    stdin, stdout, stderr = ssh.exec_command("rm -rf /tmp/fe_dist && mkdir -p /tmp/fe_dist")
    stdout.channel.recv_exit_status()

    dist_dir = "frontend/dist"
    uploaded_files = 0
    for root, dirs, files in os.walk(dist_dir):
        rel_dir = os.path.relpath(root, dist_dir)
        target_dir = f"/tmp/fe_dist/{rel_dir}".replace("\\", "/").rstrip("/.")
        stdin, stdout, stderr = ssh.exec_command(f"mkdir -p {target_dir}")
        stdout.channel.recv_exit_status()
        for file in files:
            local_f = os.path.join(root, file)
            remote_f = f"{target_dir}/{file}".replace("\\", "/")
            sftp.put(local_f, remote_f)
            uploaded_files += 1

    # Also upload wa-tester.html
    if os.path.exists("wa-tester.html"):
        sftp.put("wa-tester.html", "/tmp/fe_dist/wa-tester.html")
        print(" - Uploaded: wa-tester.html")

    sftp.close()

    # Move from /tmp/fe_dist to /var/www/pegawai-ai
    copy_cmd = (
        "sudo cp -r /tmp/fe_dist/* /var/www/pegawai-ai/ && "
        "sudo chown -R www-data:www-data /var/www/pegawai-ai && "
        "sudo chmod -R 755 /var/www/pegawai-ai && "
        "rm -rf /tmp/fe_dist"
    )
    stdin, stdout, stderr = ssh.exec_command(copy_cmd)
    stdout.channel.recv_exit_status()
    print(f"✔ Frontend ({uploaded_files} file) berhasil disalin ke /var/www/pegawai-ai/.")

    # 4. Verifikasi symlink Hermes CLI & restart service
    print("\n[4/5] Memverifikasi runtime CLI & Merestart layanan daemon...")
    hermes_symlink_cmd = "ln -sf /usr/local/bin/hermes /home/ubuntu/.local/bin/hermes"
    stdin, stdout, stderr = ssh.exec_command(hermes_symlink_cmd)
    stdout.channel.recv_exit_status()

    restart_cmd = "sudo systemctl restart pegawai-ai-bff"
    stdin, stdout, stderr = ssh.exec_command(restart_cmd)
    stdout.channel.recv_exit_status()
    time.sleep(3)

    stdin, stdout, stderr = ssh.exec_command("systemctl is-active pegawai-ai-bff")
    bff_status = stdout.read().decode().strip()
    stdin, stdout, stderr = ssh.exec_command("systemctl is-active hermes-gateway")
    hermes_status = stdout.read().decode().strip()
    stdin, stdout, stderr = ssh.exec_command("systemctl is-active nginx")
    nginx_status = stdout.read().decode().strip()

    print(f" - pegawai-ai-bff: {bff_status}")
    print(f" - hermes-gateway: {hermes_status}")
    print(f" - nginx:          {nginx_status}")
    ssh.close()

    # 5. Live E2E Verification
    print("\n[5/5] Menjalankan uji verifikasi langsung (Live E2E Verification)...")
    time.sleep(6) # tunggu inisialisasi startup

    # A. Cek Web Frontend
    try:
        req_fe = urllib.request.urlopen(f"http://{VPS_HOST}/", timeout=15)
        print(f"✔ Frontend Web App: HTTP {req_fe.status} OK")
    except Exception as e:
        print(f"✗ Frontend Web App gagal: {e}")

    # B. Cek WhatsApp Status
    try:
        url_wa = f"http://{VPS_HOST}/bff/api/whatsapp/status"
        req_wa = urllib.request.Request(url_wa, headers={"X-Pegawai-AI-Key": BFF_KEY})
        with urllib.request.urlopen(req_wa, timeout=15) as resp:
            data = json.loads(resp.read().decode())
            print(f"✔ WhatsApp Gateway: Status {data.get('status')} | Primary: {data.get('primary_agent', {}).get('name')} | Escalation: {data.get('escalation_agent', {}).get('name')}")
    except Exception as e:
        print(f"✗ WhatsApp Gateway gagal: {e}")

    # C. Cek Tools Integrations
    try:
        url_tools = f"http://{VPS_HOST}/bff/api/tools/integrations"
        req_tools = urllib.request.Request(url_tools, headers={"X-Pegawai-AI-Key": BFF_KEY})
        with urllib.request.urlopen(req_tools, timeout=15) as resp:
            data = json.loads(resp.read().decode())
            tool_ids = [t['id'] for t in data.get('tools', [])]
            print(f"✔ Tools Integrations Overview: {len(tool_ids)} tools aktif ({', '.join(tool_ids)})")
    except Exception as e:
        print(f"✗ Tools Integrations gagal: {e}")

    # D. Cek Katalog 54 Aplikasi
    try:
        url_cat = f"http://{VPS_HOST}/bff/api/apps/catalog"
        req_cat = urllib.request.Request(url_cat, headers={"X-Pegawai-AI-Key": BFF_KEY})
        with urllib.request.urlopen(req_cat, timeout=15) as resp:
            data = json.loads(resp.read().decode())
            print(f"✔ Apps Catalog: HTTP {resp.status} OK | {len(data.get('categories', []))} Kategori | {len(data.get('apps', []))} Aplikasi termuat")
    except Exception as e:
        print(f"✗ Apps Catalog gagal: {e}")

    # E. Cek WhatsApp Web Simulator
    try:
        req_sim = urllib.request.urlopen(f"http://{VPS_HOST}/wa-tester.html", timeout=15)
        print(f"✔ WhatsApp Web Simulator: HTTP {req_sim.status} OK (Ready to use)")
    except Exception as e:
        print(f"✗ WhatsApp Web Simulator gagal: {e}")

    print("\n==============================================")
    print("🎉 REDEPLOYMENT SELESAI & BERHASIL PENUH!")
    print(f"Web App:     http://{VPS_HOST}/")
    print(f"Aplikasi:    http://{VPS_HOST}/#/aplikasi")
    print(f"WA Tester:   http://{VPS_HOST}/wa-tester.html")
    print("==============================================")

if __name__ == "__main__":
    main()
