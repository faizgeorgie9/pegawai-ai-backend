import paramiko

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect('139.190.107.151', username='ubuntu', key_filename='vps/key-pegawai-ai.pem')

cmds = [
    ('UFW FIREWALL', 'sudo ufw status verbose || true'),
    ('LISTENING PORTS', 'sudo ss -tulpn | grep LISTEN'),
    ('SYSTEM UPTIME & LOAD', 'uptime'),
    ('CPU INFO', 'lscpu | grep "Model name\\|CPU(s):"'),
    ('RAM USAGE', 'free -h'),
    ('RAM DETAILS (MB)', 'free -m'),
    ('DISK USAGE', 'df -h /'),
    ('SERVICES STATUS', 'systemctl is-active pegawai-ai-bff nginx postgresql docker || true')
]

for title, cmd in cmds:
    stdin, stdout, stderr = ssh.exec_command(cmd)
    print(f'=== {title} ===')
    print(stdout.read().decode().strip())
    print()

ssh.close()
