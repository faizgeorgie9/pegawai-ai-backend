import os
import tarfile
import paramiko
import time

VPS_HOST = "139.190.107.151"
VPS_USER = "ubuntu"
VPS_PASS = "@Baruk516"

def main():
    print("=== DEPLOYING SPRINT 5 DAY 1 TO VPS ===")
    
    # 1. Archive BFF updates
    print("1. Creating tarball of updated BFF files...")
    tar_path = "bff_update.tar.gz"
    with tarfile.open(tar_path, "w:gz") as tar:
        tar.add("bff/bff/auth.py", arcname="bff/auth.py")
        tar.add("bff/bff/main.py", arcname="bff/main.py")
        tar.add("bff/migrations/020_auth_users.sql", arcname="migrations/020_auth_users.sql")
        tar.add("bff/tests/test_auth.py", arcname="tests/test_auth.py")

    # 2. Archive frontend dist
    print("2. Creating tarball of frontend dist...")
    dist_tar = "dist.tar.gz"
    with tarfile.open(dist_tar, "w:gz") as tar:
        for root, dirs, files in os.walk("frontend/dist"):
            for f in files:
                full_p = os.path.join(root, f)
                rel_p = os.path.relpath(full_p, "frontend/dist")
                tar.add(full_p, arcname=rel_p)

    # 3. Upload to VPS via SFTP
    print("3. Uploading archives to VPS /tmp...")
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(VPS_HOST, port=22, username=VPS_USER, password=VPS_PASS, timeout=15)
    sftp = ssh.open_sftp()
    sftp.put(tar_path, "/tmp/bff_update.tar.gz")
    sftp.put(dist_tar, "/tmp/dist.tar.gz")
    sftp.close()

    # 4. Extract BFF updates on VPS
    print("4. Extracting BFF updates into /home/ubuntu/pegawai-ai/bff...")
    ssh.exec_command("tar -xzf /tmp/bff_update.tar.gz -C /home/ubuntu/pegawai-ai/bff")

    # 5. Extract Frontend to /var/www/pegawai-ai
    print("5. Deploying Frontend to /var/www/pegawai-ai...")
    deploy_cmds = [
        "sudo rm -rf /var/www/pegawai-ai/assets",
        "sudo tar -xzf /tmp/dist.tar.gz -C /var/www/pegawai-ai",
        "sudo chown -R www-data:www-data /var/www/pegawai-ai"
    ]
    for cmd in deploy_cmds:
        stdin, stdout, stderr = ssh.exec_command(cmd)
        stdout.channel.recv_exit_status()

    # 6. Update Nginx configuration with /demo support and Authorization header forwarding
    print("6. Updating Nginx configuration...")
    nginx_conf = """server {
    listen 80 default_server;
    listen [::]:80 default_server;
    server_name app.pegawaiAI.com 139.190.107.151.sslip.io 139.190.107.151 _;

    # Redirect all HTTP traffic to HTTPS
    return 301 https://$host$request_uri;
}

server {
    listen 443 ssl http2 default_server;
    listen [::]:443 ssl http2 default_server;
    server_name app.pegawaiAI.com 139.190.107.151.sslip.io;

    ssl_certificate /etc/letsencrypt/live/139.190.107.151.sslip.io/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/139.190.107.151.sslip.io/privkey.pem;

    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers HIGH:!aNULL:!MD5;

    # Security Headers
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-XSS-Protection "1; mode=block" always;
    add_header Referrer-Policy "strict-origin-when-cross-origin" always;
    add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;

    root /var/www/pegawai-ai;
    index index.html;

    # Demo route (Sprint 5 Day 1)
    location /demo {
        alias /var/www/pegawai-ai;
        try_files $uri $uri/ /index.html;
    }

    location / {
        try_files $uri $uri/ /index.html;
    }

    location /bff/ {
        limit_req zone=api_limit burst=50 nodelay;
        proxy_pass http://127.0.0.1:8090/;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto https;
        proxy_set_header X-Pegawai-AI-Key mh6IG_kqNfpu4YJe1Gi8FzM1tzejRPSbWfDSRNFriCI;
        proxy_set_header Authorization $http_authorization;

        proxy_http_version 1.1;
        proxy_set_header Connection "";
        proxy_buffering off;
        proxy_cache off;
        chunked_transfer_encoding off;
        proxy_read_timeout 86400s;
    }

    location /api/ {
        limit_req zone=api_limit burst=50 nodelay;
        proxy_pass http://127.0.0.1:8090/api/;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto https;
        proxy_set_header X-Pegawai-AI-Key mh6IG_kqNfpu4YJe1Gi8FzM1tzejRPSbWfDSRNFriCI;
        proxy_set_header Authorization $http_authorization;

        proxy_http_version 1.1;
        proxy_set_header Connection "";
        proxy_buffering off;
        proxy_cache off;
        chunked_transfer_encoding off;
        proxy_read_timeout 86400s;
    }
}
"""
    sftp = ssh.open_sftp()
    with sftp.open('/tmp/nginx_default_s5', 'w') as f:
        f.write(nginx_conf)
    sftp.close()

    ssh.exec_command("sudo cp /tmp/nginx_default_s5 /etc/nginx/sites-available/default && sudo nginx -t")
    ssh.exec_command("sudo systemctl reload nginx")

    # 7. Restart BFF daemon on VPS
    print("7. Restarting pegawai-ai-bff service on VPS...")
    ssh.exec_command("sudo systemctl restart pegawai-ai-bff")
    time.sleep(5)

    # 8. Check service status
    stdin, stdout, stderr = ssh.exec_command("systemctl is-active pegawai-ai-bff nginx hermes-gateway")
    statuses = stdout.read().decode('utf-8').splitlines()
    print("Services active:", statuses)

    ssh.close()
    print("✅ Deployment completed successfully!")

if __name__ == "__main__":
    main()
