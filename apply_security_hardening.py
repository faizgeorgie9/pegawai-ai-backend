import paramiko

VPS_HOST = "139.190.107.151"
VPS_USER = "ubuntu"
VPS_PASS = "@Baruk516"

def main():
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(VPS_HOST, port=22, username=VPS_USER, password=VPS_PASS, timeout=10)

    print("1. Configuring UFW Firewall...")
    ufw_cmds = [
        "sudo ufw default deny incoming",
        "sudo ufw default allow outgoing",
        "sudo ufw allow 22/tcp comment 'SSH Access'",
        "sudo ufw allow 80/tcp comment 'HTTP Redirect'",
        "sudo ufw allow 443/tcp comment 'HTTPS Production'",
        "echo y | sudo ufw enable",
        "sudo ufw status verbose"
    ]
    for cmd in ufw_cmds:
        stdin, stdout, stderr = ssh.exec_command(cmd)
        out = stdout.read().decode('utf-8')
        print(f"[{cmd}] -> {out.strip()}")

    print("\n2. Updating Nginx with Security Headers & Rate Limiting...")
    # First inspect nginx.conf to see if limit_req_zone is already there
    stdin, stdout, stderr = ssh.exec_command("cat /etc/nginx/nginx.conf")
    nginx_conf = stdout.read().decode('utf-8')

    if "limit_req_zone" not in nginx_conf:
        # Add rate limit zone inside http block
        replacement = 'http {\n\tlimit_req_zone $binary_remote_addr zone=api_limit:10m rate=30r/s;\n'
        nginx_conf_updated = nginx_conf.replace('http {\n', replacement, 1)
        
        # Write to tmp and sudo cp
        sftp = ssh.open_sftp()
        with sftp.open('/tmp/nginx.conf', 'w') as f:
            f.write(nginx_conf_updated)
        sftp.close()
        
        stdin, stdout, stderr = ssh.exec_command("sudo cp /tmp/nginx.conf /etc/nginx/nginx.conf")
        print("Updated /etc/nginx/nginx.conf with api_limit zone.")

    # Now update sites-available/default
    nginx_site = """server {
    listen 80 default_server;
    listen [::]:80 default_server;
    server_name 139.190.107.151.sslip.io 139.190.107.151 _;

    # Redirect all HTTP traffic to HTTPS
    return 301 https://139.190.107.151.sslip.io$request_uri;
}

server {
    listen 443 ssl http2 default_server;
    listen [::]:443 ssl http2 default_server;
    server_name 139.190.107.151.sslip.io;

    ssl_certificate /etc/letsencrypt/live/139.190.107.151.sslip.io/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/139.190.107.151.sslip.io/privkey.pem;

    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers HIGH:!aNULL:!MD5;

    # Security Headers (Defense in Depth)
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-XSS-Protection "1; mode=block" always;
    add_header Referrer-Policy "strict-origin-when-cross-origin" always;
    add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;

    root /var/www/pegawai-ai;
    index index.html;

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
    with sftp.open('/tmp/nginx_default', 'w') as f:
        f.write(nginx_site)
    sftp.close()

    stdin, stdout, stderr = ssh.exec_command("sudo cp /tmp/nginx_default /etc/nginx/sites-available/default && sudo nginx -t")
    t_out = stdout.read().decode('utf-8')
    t_err = stderr.read().decode('utf-8')
    print("Nginx syntax test:", t_out, t_err)

    if "syntax is ok" in t_err or "syntax is ok" in t_out:
        stdin, stdout, stderr = ssh.exec_command("sudo systemctl reload nginx")
        print("Nginx reloaded successfully!")
    else:
        print("ERROR in Nginx config, not reloading!")

    ssh.close()
    print("\n✅ Security hardening applied!")

if __name__ == "__main__":
    main()
