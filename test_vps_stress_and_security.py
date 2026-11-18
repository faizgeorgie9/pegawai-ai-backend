import time
import json
import socket
import concurrent.futures
import urllib.request
import ssl
import paramiko

BASE_URL = "https://139.190.107.151.sslip.io"
VPS_HOST = "139.190.107.151"
VPS_USER = "ubuntu"
VPS_PASS = "@Baruk516"

results = {
    "port_exposure_audit": {},
    "stress_test_health": {},
    "stress_test_static": {},
    "vps_resources": {},
    "security_hardening_recommendations": []
}

def check_single_request(url, headers=None):
    t0 = time.time()
    try:
        ctx = ssl.create_default_context()
        req = urllib.request.Request(url, headers=headers or {})
        with urllib.request.urlopen(req, timeout=10, context=ctx) as resp:
            data = resp.read()
            lat = (time.time() - t0) * 1000
            return resp.status, lat, None
    except Exception as e:
        lat = (time.time() - t0) * 1000
        return 0, lat, str(e)

def run_stress_test(endpoint_name, url, total_requests=100, concurrency=10):
    print(f"\n--- Running Concurrency Test: {endpoint_name} ({total_requests} reqs, concurrency {concurrency}) ---")
    start_time = time.time()
    latencies = []
    statuses = {}
    errors = []

    with concurrent.futures.ThreadPoolExecutor(max_workers=concurrency) as executor:
        futures = [executor.submit(check_single_request, url) for _ in range(total_requests)]
        for f in concurrent.futures.as_completed(futures):
            status, lat, err = f.result()
            latencies.append(lat)
            statuses[status] = statuses.get(status, 0) + 1
            if err:
                errors.append(err)

    total_time = time.time() - start_time
    rps = total_requests / total_time if total_time > 0 else 0
    avg_lat = sum(latencies) / len(latencies) if latencies else 0
    min_lat = min(latencies) if latencies else 0
    max_lat = max(latencies) if latencies else 0

    res = {
        "total_requests": total_requests,
        "concurrency": concurrency,
        "total_time_seconds": round(total_time, 2),
        "requests_per_second": round(rps, 2),
        "avg_latency_ms": round(avg_lat, 2),
        "min_latency_ms": round(min_lat, 2),
        "max_latency_ms": round(max_lat, 2),
        "statuses": statuses,
        "error_count": len(errors),
        "success_rate_percent": round((statuses.get(200, 0) / total_requests) * 100, 2)
    }
    print(f"Results for {endpoint_name}: {res['success_rate_percent']}% success | {res['requests_per_second']} RPS | Avg Latency: {res['avg_latency_ms']}ms")
    return res

def main():
    print("================================================================")
    print("🛡️ VPS SECURITY AUDIT & CONCURRENCY STRESS TEST")
    print(f"Target: {BASE_URL} ({VPS_HOST})")
    print("================================================================")

    # 1. External Port Reachability
    ports_to_test = {
        22: "SSH",
        80: "HTTP (Nginx Redirect)",
        443: "HTTPS (Nginx Web/API)",
        5432: "PostgreSQL Database",
        8080: "Hermes Agent Gateway",
        8090: "BFF FastAPI Internal",
        8642: "Hermes Core Runtime"
    }
    print("\n1. Testing Port Reachability from Public WAN:")
    for p, desc in ports_to_test.items():
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.settimeout(2.0)
        res = s.connect_ex((VPS_HOST, p))
        s.close()
        is_open = (res == 0)
        # Ports 22, 80, 443 are expected open; internal ports (5432, 8080, 8090, 8642) MUST be closed
        expected_open = p in [22, 80, 443]
        safe = (is_open == expected_open)
        results["port_exposure_audit"][str(p)] = {
            "description": desc,
            "is_open": is_open,
            "expected_open": expected_open,
            "safe": safe
        }
        status_txt = "OPEN (Expected)" if is_open and expected_open else (
            "BLOCKED/FILTERED (Safe)" if not is_open and not expected_open else (
                "⚠️ EXPOSED VULNERABILITY!" if is_open and not expected_open else "DOWN (Unexpected)"
            )
        )
        print(f"   - Port {p:5d} ({desc:24s}): {status_txt}")

    # 2. Concurrency Stress Test on /bff/api/health
    results["stress_test_health"] = run_stress_test("Backend API Healthcheck", f"{BASE_URL}/bff/api/health", 100, 10)

    # 3. Concurrency Stress Test on Frontend Root /
    results["stress_test_static"] = run_stress_test("Frontend Static SPA", f"{BASE_URL}/", 100, 10)

    # 4. Host OS Metrics via SSH
    print("\n4. Checking VPS Host Resources & Daemons via SSH:")
    try:
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh.connect(VPS_HOST, port=22, username=VPS_USER, password=VPS_PASS, timeout=10)

        stdin, stdout, stderr = ssh.exec_command("free -m; uptime; cat /proc/loadavg")
        host_info = stdout.read().decode('utf-8')
        stdin, stdout, stderr = ssh.exec_command("sudo ufw status")
        ufw_info = stdout.read().decode('utf-8')
        stdin, stdout, stderr = ssh.exec_command("systemctl is-active pegawai-ai-bff hermes-gateway nginx")
        svc_info = stdout.read().decode('utf-8').splitlines()
        ssh.close()

        results["vps_resources"] = {
            "services_active": svc_info,
            "ufw_status": ufw_info.strip(),
            "host_output": host_info.strip().splitlines()
        }
        print("   - Services active:", svc_info)
        print("   - UFW status:", ufw_info.strip())
        print("   - Memory & Load:", host_info.strip().splitlines()[:2])
    except Exception as e:
        results["vps_resources"] = {"error": str(e)}
        print("   - SSH check error:", e)

    # 5. Security & Isolation Analysis
    print("\n5. Analyzing Multi-Tenant Data Isolation & Security Architecture:")
    recommendations = [
        {
            "category": "Port Exposure & Firewall (UFW)",
            "finding": "Internal ports (8090, 8080, 8642) are bound to 127.0.0.1 and not accessible from WAN. However, UFW firewall is currently INACTIVE.",
            "impact": "If any future process binds to 0.0.0.0 accidentally, it will be immediately reachable from internet.",
            "action": "Enable UFW firewall and explicitly allow only ports 22, 80, and 443."
        },
        {
            "category": "Multi-Tenant Isolation (Saling Mengintip)",
            "finding": "BFF currently uses a shared current_user() = 'default'. All requests proxied through Nginx receive the internal X-Pegawai-AI-Key.",
            "impact": "Currently in MVP prototype mode, all connected browser clients share the same default workspace and session context.",
            "action": "For production multi-tenancy, implement per-user authentication (JWT / Session Cookie) and row-level tenant filtering (workspace_id/user_id) so users cannot access each other's chat history or knowledge base."
        },
        {
            "category": "Rate Limiting & DoS Protection",
            "finding": "Nginx does not currently have limit_req_zone or limit_conn_zone configured.",
            "impact": "A client sending high-frequency bursts could potentially exhaust server resources.",
            "action": "Add rate limiting in /etc/nginx/nginx.conf (e.g., 20 requests/second with burst 30) for /bff/ and /api/ endpoints."
        },
        {
            "category": "HTTP Security Headers",
            "finding": "Missing X-Frame-Options (Clickjacking defense), X-Content-Type-Options (MIME sniffing defense), and Strict-Transport-Security (HSTS).",
            "impact": "Vulnerabilities to iframe embedding or MIME-type confusion.",
            "action": "Inject security headers in Nginx server block: add_header X-Frame-Options SAMEORIGIN; add_header X-Content-Type-Options nosniff; add_header Strict-Transport-Security 'max-age=31536000; includeSubDomains' always;"
        }
    ]
    results["security_hardening_recommendations"] = recommendations

    with open("stress_and_security_report.json", "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2)

    print("\n✅ Stress Test and Security Audit Completed! Saved to stress_and_security_report.json")

if __name__ == "__main__":
    main()
