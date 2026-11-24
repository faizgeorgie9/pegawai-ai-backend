import os
import paramiko

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect('139.190.107.151', username='ubuntu', key_filename='d:/ai_developer/project6/vps/key-pegawai-ai.pem')

stdin, stdout, stderr = ssh.exec_command('rm -rf /tmp/frontend_dist && mkdir -p /tmp/frontend_dist/assets')
stdout.channel.recv_exit_status()

sftp = ssh.open_sftp()
local_dist = 'd:/ai_developer/project6/frontend/dist'

print("Uploading frontend dist files...")
for fname in os.listdir(local_dist):
    lpath = os.path.join(local_dist, fname).replace('\\', '/')
    if os.path.isfile(lpath):
        rpath = f"/tmp/frontend_dist/{fname}"
        print(f"Uploading {fname}...")
        sftp.put(lpath, rpath)

local_assets = os.path.join(local_dist, 'assets').replace('\\', '/')
if os.path.exists(local_assets):
    for fname in os.listdir(local_assets):
        lpath = os.path.join(local_assets, fname).replace('\\', '/')
        if os.path.isfile(lpath):
            rpath = f"/tmp/frontend_dist/assets/{fname}"
            sftp.put(lpath, rpath)

sftp.close()
print("All files uploaded to /tmp/frontend_dist.")

print("Moving to /var/www/pegawai-ai...")
cmd = "sudo cp -r /tmp/frontend_dist/* /var/www/pegawai-ai/ && sudo chown -R www-data:www-data /var/www/pegawai-ai && sudo systemctl reload nginx"
stdin, stdout, stderr = ssh.exec_command(cmd)
stdout.channel.recv_exit_status()

stdin, stdout, stderr = ssh.exec_command('ls -la /var/www/pegawai-ai/assets/*.js')
print("Live JS assets:")
print(stdout.read().decode())

ssh.close()
print("Frontend deployment to VPS finished successfully!")
