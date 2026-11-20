import json
import urllib.request
import ssl
import time
import socket

BASE_URL = "https://139.190.107.151.sslip.io"
BFF_KEY = "mh6IG_kqNfpu4YJe1Gi8FzM1tzejRPSbWfDSRNFriCI"
VPS_HOST = "139.190.107.151"

results = {}

def log_test(name, success, details):
    status_str = "PASS" if success else "FAIL"
    print(f"[{status_str}] {name}")
    results[name] = {"success": success, "details": details}

def http_req(url, method="GET", data=None, headers=None):
    ctx = ssl.create_default_context()
    body = json.dumps(data).encode('utf-8') if data else None
    req = urllib.request.Request(url, data=body, method=method)
    req.add_header("User-Agent", "PegawaiAI-Sprint5-Tester")
    if data:
        req.add_header("Content-Type", "application/json")
    if headers:
        for k, v in headers.items():
            req.add_header(k, v)
    try:
        with urllib.request.urlopen(req, timeout=15, context=ctx) as resp:
            content = resp.read().decode('utf-8')
            return resp.status, resp.headers, content
    except urllib.error.HTTPError as e:
        content = e.read().decode('utf-8')
        return e.code, e.headers, content
    except Exception as e:
        return 0, {}, str(e)

def main():
    print("=====================================================")
    print("🚀 SPRINT 5 DAY 1: LIVE VPS DEMO & AUTH REGRESSION")
    print(f"Target: {BASE_URL}")
    print("=====================================================")

    # 1. Frontend SPA Root
    status, _, html = http_req(f"{BASE_URL}/")
    ok = (status == 200 and "<!doctype html>" in html.lower())
    log_test("1. Frontend SPA Root (HTTPS)", ok, f"HTTP {status}, length: {len(html)}")

    # 2. Demo URL Path (/demo)
    status, _, html = http_req(f"{BASE_URL}/demo")
    ok = (status == 200 and "<!doctype html>" in html.lower())
    log_test("2. Demo URL Path (/demo)", ok, f"HTTP {status}, length: {len(html)}")

    # 3. Login Failure with Invalid Password
    bad_payload = {"email": "owner@colorbox.co.id", "password": "WrongPassword123!"}
    status, _, resp_body = http_req(f"{BASE_URL}/bff/api/auth/login", method="POST", data=bad_payload)
    ok = (status == 401 and "Email atau kata sandi tidak cocok" in resp_body)
    log_test("3. Login Failure with Invalid Password (POST 401)", ok, f"HTTP {status}, body: {resp_body}")

    # 4. Login Success with Owner Account
    owner_payload = {"email": "owner@colorbox.co.id", "password": "Admin1234!"}
    status, _, resp_body = http_req(f"{BASE_URL}/bff/api/auth/login", method="POST", data=owner_payload)
    owner_token = None
    if status == 200:
        d = json.loads(resp_body)
        owner_token = d.get("token")
        ok = (d.get("user", {}).get("role") == "owner" and owner_token is not None)
    else:
        ok = False
    log_test("4. Login Success with Owner Account (POST 200 + JWT)", ok, {
        "status": status,
        "role": d.get("user", {}).get("role") if ok else None,
        "token_prefix": owner_token[:25] + "..." if owner_token else None
    })

    # 5. Login Success with Admin Account
    admin_payload = {"email": "admin@pegawai.ai", "password": "Admin1234!"}
    status, _, resp_body = http_req(f"{BASE_URL}/bff/api/auth/login", method="POST", data=admin_payload)
    admin_token = None
    if status == 200:
        d = json.loads(resp_body)
        admin_token = d.get("token")
        ok = (d.get("user", {}).get("role") == "admin" and admin_token is not None)
    else:
        ok = False
    log_test("5. Login Success with Admin Account (POST 200 + JWT)", ok, {
        "status": status,
        "role": d.get("user", {}).get("role") if ok else None,
        "token_prefix": admin_token[:25] + "..." if admin_token else None
    })

    # 6. Protected Access Denied without Token
    status, _, resp_body = http_req(f"{BASE_URL}/bff/api/auth/me", method="GET")
    ok = (status == 401)
    log_test("6. Protected Access Denied without Token (GET 401)", ok, f"HTTP {status}, body: {resp_body}")

    # 7. Protected Access Allowed with Valid Token
    if owner_token:
        status, _, resp_body = http_req(f"{BASE_URL}/bff/api/auth/me", method="GET", headers={"Authorization": f"Bearer {owner_token}"})
        if status == 200:
            d = json.loads(resp_body)
            u = d.get("user", {})
            ok = (u.get("email") == "owner@colorbox.co.id" and u.get("role") == "owner")
        else:
            ok = False
    else:
        ok = False
    log_test("7. Protected Access Allowed with Valid Token (GET 200 /auth/me)", ok, {
        "status": status,
        "user_name": u.get("name") if ok else None,
        "user_email": u.get("email") if ok else None,
        "user_role": u.get("role") if ok else None
    })

    # 8. User Registration Flow
    new_email = f"faiz_test_{int(time.time())}@colorbox.co.id"
    reg_payload = {"name": "Faiz New Member", "email": new_email, "password": "MemberPassword123!", "company": "Colorbox Fashion"}
    status, _, resp_body = http_req(f"{BASE_URL}/bff/api/auth/register", method="POST", data=reg_payload)
    if status == 200:
        d = json.loads(resp_body)
        reg_token = d.get("token")
        ok = (d.get("user", {}).get("email") == new_email and reg_token is not None)
    else:
        ok = False
    log_test("8. User Registration Endpoint (POST 200 /auth/register)", ok, {
        "status": status,
        "registered_email": new_email if ok else None,
        "token_issued": reg_token is not None if ok else False
    })

    # 9. Logout Endpoint
    status, _, resp_body = http_req(f"{BASE_URL}/bff/api/auth/logout", method="POST")
    ok = (status == 200 and "Berhasil logout" in resp_body)
    log_test("9. User Logout Endpoint (POST 200 /auth/logout)", ok, f"HTTP {status}, body: {resp_body}")

    # 10. Backend Healthcheck
    status, _, resp_body = http_req(f"{BASE_URL}/bff/api/health")
    if status == 200:
        d = json.loads(resp_body)
        ok = (d.get("ok") is True and d.get("db") is True and d.get("hermes") is True)
    else:
        ok = False
    log_test("10. Backend Healthcheck (/bff/api/health)", ok, d if ok else f"HTTP {status}")

    # 11. External Port Exposure Audit
    ports_to_test = {22: True, 80: True, 443: True, 5432: False, 8080: False, 8090: False, 8642: False}
    ports_safe = True
    port_details = {}
    for p, should_be_open in ports_to_test.items():
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.settimeout(2.0)
        res = s.connect_ex((VPS_HOST, p))
        s.close()
        is_open = (res == 0)
        safe = (is_open == should_be_open)
        if not safe:
            ports_safe = False
        port_details[f"port_{p}"] = "OPEN" if is_open else "BLOCKED/FILTERED"
    log_test("11. External Port Exposure & Firewall Audit (UFW)", ports_safe, port_details)

    # 12. HTTPS Security Headers Verification
    status, headers, _ = http_req(f"{BASE_URL}/bff/api/health")
    headers_dict = dict(headers)
    has_frame = "X-Frame-Options" in headers_dict
    has_nosniff = "X-Content-Type-Options" in headers_dict
    has_hsts = "Strict-Transport-Security" in headers_dict
    ok = (has_frame and has_nosniff and has_hsts)
    log_test("12. HTTPS Security Headers (X-Frame, NoSniff, HSTS)", ok, {
        "X-Frame-Options": headers_dict.get("X-Frame-Options"),
        "X-Content-Type-Options": headers_dict.get("X-Content-Type-Options"),
        "Strict-Transport-Security": headers_dict.get("Strict-Transport-Security")
    })

    print("\n=====================================================")
    passed = sum(1 for v in results.values() if v["success"])
    total = len(results)
    print(f"📊 HASIL AKHIR: {passed}/{total} Pengujian Lulus ({(passed/total)*100:.1f}%)")
    print("=====================================================")

    with open("day1_sprint5_results.json", "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2)

if __name__ == "__main__":
    main()
