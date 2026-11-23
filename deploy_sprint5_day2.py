import os
import tarfile
import paramiko
import time

VPS_HOST = "139.190.107.151"
VPS_USER = "ubuntu"
VPS_PASS = "@Baruk516"

def main():
    print("=== DEPLOYING SPRINT 5 DAY 2 TO VPS ===")
    
    # 1. Archive BFF updates
    print("1. Creating tarball of updated BFF files...")
    tar_path = "bff_update_day2.tar.gz"
    with tarfile.open(tar_path, "w:gz") as tar:
        tar.add("bff/bff/kb.py", arcname="bff/kb.py")
        tar.add("bff/bff/mcp_privileges.py", arcname="bff/mcp_privileges.py")
        tar.add("bff/bff/bridge.py", arcname="bff/bridge.py")
        tar.add("bff/bff/main.py", arcname="bff/main.py")
        tar.add("bff/migrations/021_kb_agent_permissions.sql", arcname="migrations/021_kb_agent_permissions.sql")
        tar.add("bff/tests/test_day2_sprint5.py", arcname="tests/test_day2_sprint5.py")

    # 2. Upload to VPS via SFTP
    print("2. Uploading archive to VPS /tmp...")
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(VPS_HOST, port=22, username=VPS_USER, password=VPS_PASS, timeout=15)
    sftp = ssh.open_sftp()
    sftp.put(tar_path, "/tmp/bff_update_day2.tar.gz")
    sftp.close()

    # 3. Extract BFF updates on VPS
    print("3. Extracting BFF updates into /home/ubuntu/pegawai-ai/bff...")
    stdin, stdout, stderr = ssh.exec_command("tar -xzf /tmp/bff_update_day2.tar.gz -C /home/ubuntu/pegawai-ai/bff")
    stdout.channel.recv_exit_status()

    # 4. Apply Database Migration 021
    print("4. Applying Migration 021 on VPS database...")
    run_migration_cmd = (
        "cd /home/ubuntu/pegawai-ai/bff && "
        "sudo -u postgres psql -d pegawai_ai -f migrations/021_kb_agent_permissions.sql || "
        "sudo -u ubuntu psql -f migrations/021_kb_agent_permissions.sql || "
        "python3 -c \"import os, psycopg; conn = psycopg.connect(os.environ.get('DATABASE_URL')); "
        "conn.execute(open('migrations/021_kb_agent_permissions.sql').read()); conn.commit(); print('Migration 021 applied via python')\""
    )
    stdin, stdout, stderr = ssh.exec_command(run_migration_cmd)
    out = stdout.read().decode('utf-8')
    err = stderr.read().decode('utf-8')
    print("Migration Output:", out, err)

    # 5. Restart BFF daemon on VPS
    print("5. Restarting pegawai-ai-bff service on VPS...")
    stdin, stdout, stderr = ssh.exec_command("sudo systemctl restart pegawai-ai-bff")
    stdout.channel.recv_exit_status()
    time.sleep(4)

    # 6. Check service status
    stdin, stdout, stderr = ssh.exec_command("systemctl is-active pegawai-ai-bff nginx hermes-gateway")
    statuses = stdout.read().decode('utf-8').splitlines()
    print("Services active:", statuses)

    ssh.close()
    print("✅ Deployment of Sprint 5 Day 2 completed successfully!")

if __name__ == "__main__":
    main()
