import urllib.request
import json
import ssl

BASE_URL = "https://139.190.107.151.sslip.io"
BFF_KEY = "mh6IG_kqNfpu4YJe1Gi8FzM1tzejRPSbWfDSRNFriCI"

# Disable SSL verification for sslip.io self-signed or Let's Encrypt testing
ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE

def request(path, method="GET", data=None, token=None):
    url = f"{BASE_URL}{path}"
    headers = {
        "User-Agent": "Sprint5-Day2-Validator/1.0",
        "X-Pegawai-AI-Key": BFF_KEY
    }
    body = None
    if data is not None:
        headers["Content-Type"] = "application/json"
        body = json.dumps(data).encode("utf-8")
    if token:
        headers["Authorization"] = f"Bearer {token}"
        
    req = urllib.request.Request(url, data=body, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req, context=ctx, timeout=15) as resp:
            content = resp.read().decode("utf-8")
            try:
                parsed = json.loads(content)
            except Exception:
                parsed = content
            return resp.status, parsed
    except urllib.error.HTTPError as e:
        content = e.read().decode("utf-8")
        try:
            parsed = json.loads(content)
        except Exception:
            parsed = content
        return e.code, parsed

def run_tests():
    print("=" * 80)
    print("  SPRINT 5 DAY 2: LIVE VPS VALIDATION SUITE")
    print("  Target: https://139.190.107.151.sslip.io")
    print("=" * 80)

    results = {}
    
    # 0. Login as Owner to get Bearer Token
    status, body = request("/bff/api/auth/login", method="POST", data={
        "email": "owner@colorbox.co.id",
        "password": "Admin1234!"
    })
    assert status == 200, f"Login failed: {body}"
    token = body.get("token") or body.get("access_token")
    assert token, f"Token missing in response: {body}"
    print("✓ Successfully authenticated as Owner (JWT Token acquired)")

    # 1. KB Access Matrix
    status, body = request("/bff/api/kb/matrix", token=token)
    success = (
        status == 200 and
        body["agents"]["siti"]["can_access_finance"] is False and
        body["agents"]["diana"]["can_access_finance"] is False and
        body["agents"]["bimo"]["can_access_finance"] is True
    )
    results["1. KB Access Matrix API (/kb/matrix)"] = {
        "success": success,
        "details": f"Status {status}, CS Finance Allowed: {body['agents']['siti']['can_access_finance']}, Bimo Finance Allowed: {body['agents']['bimo']['can_access_finance']}"
    }
    print(f"[{'PASS' if success else 'FAIL'}] 1. KB Access Matrix API")

    # 2. KB Access Check: CS Denied Finance
    status, body = request("/bff/api/kb/access-check?bot_id=siti&category=finance", token=token)
    success = (status == 200 and body.get("allowed") is False and "terisolasi" in body.get("reason", "").lower())
    results["2. KB Access Check: CS Denied Finance"] = {
        "success": success,
        "details": body
    }
    print(f"[{'PASS' if success else 'FAIL'}] 2. KB Access Check: CS Denied Finance")

    # 3. KB Access Check: CS Allowed CS & Catalog
    status, body = request("/bff/api/kb/access-check?bot_id=siti&category=cs", token=token)
    success = (status == 200 and body.get("allowed") is True)
    results["3. KB Access Check: CS Allowed CS SOP"] = {
        "success": success,
        "details": body
    }
    print(f"[{'PASS' if success else 'FAIL'}] 3. KB Access Check: CS Allowed CS SOP")

    # 4. KB Access Check: Authorized Agent Allowed Finance
    status, body = request("/bff/api/kb/access-check?bot_id=bimo&category=finance", token=token)
    success = (status == 200 and body.get("allowed") is True)
    results["4. KB Access Check: PM/Admin Allowed Finance"] = {
        "success": success,
        "details": body
    }
    print(f"[{'PASS' if success else 'FAIL'}] 4. KB Access Check: PM/Admin Allowed Finance")

    # 5. MCP Privileges Directory API
    status, body = request("/bff/api/mcp/privileges", token=token)
    success = (status == 200 and "hierarchy" in body and "tools" in body and "accounts" in body)
    results["5. MCP Privileges Directory API (/mcp/privileges)"] = {
        "success": success,
        "details": f"Tools classified: {len(body.get('tools', {}))}, Registered Accounts: {len(body.get('accounts', {}))}"
    }
    print(f"[{'PASS' if success else 'FAIL'}] 5. MCP Privileges Directory API")

    # 6. MCP Verification: Read Tier Denied Write Tool
    status, body = request("/bff/api/mcp/verify", method="POST", data={
        "bot_id": "siti",
        "tool_name": "drive_create"
    }, token=token)
    success = (status == 200 and body.get("allowed") is False and "insufficient" in body.get("reason", "").lower())
    results["6. MCP Verification: Read Tier Denied Write Tool"] = {
        "success": success,
        "details": body
    }
    print(f"[{'PASS' if success else 'FAIL'}] 6. MCP Verification: Read Tier Denied Write Tool")

    # 7. MCP Verification: Write Tier Denied Admin Tool
    status, body = request("/bff/api/mcp/verify", method="POST", data={
        "bot_id": "bram",
        "tool_name": "drive_trash"
    }, token=token)
    success = (status == 200 and body.get("allowed") is False and "admin" in body.get("reason", "").lower())
    results["7. MCP Verification: Write Tier Denied Admin Tool"] = {
        "success": success,
        "details": body
    }
    print(f"[{'PASS' if success else 'FAIL'}] 7. MCP Verification: Write Tier Denied Admin Tool")

    # 8. MCP Verification: Admin Tier Allowed Admin Tool
    status, body = request("/bff/api/mcp/verify", method="POST", data={
        "bot_id": "bimo",
        "tool_name": "drive_trash"
    }, token=token)
    success = (status == 200 and body.get("allowed") is True)
    results["8. MCP Verification: Admin Tier Allowed All Tools"] = {
        "success": success,
        "details": body
    }
    print(f"[{'PASS' if success else 'FAIL'}] 8. MCP Verification: Admin Tier Allowed All Tools")

    # 9. MCP Cross-Account Violation Check
    status, body = request("/bff/api/mcp/verify", method="POST", data={
        "bot_id": "siti",
        "tool_name": "drive_search",
        "account_id": "acc_pm_bimo_01"
    }, token=token)
    success = (status == 200 and body.get("allowed") is False and "cross-account" in body.get("reason", "").lower())
    results["9. MCP Cross-Account Spoofing Blocked"] = {
        "success": success,
        "details": body
    }
    print(f"[{'PASS' if success else 'FAIL'}] 9. MCP Cross-Account Spoofing Blocked")

    # 10. WhatsApp Routing: Frontline Inbound (Siti)
    status, body = request("/bff/api/whatsapp/simulate", method="POST", data={
        "sender": "6281234567890",
        "customer_name": "Kak Sarah",
        "message": "Halo kak, produk denim jacket ukuran M ready stok?"
    }, token=token)
    success = (status == 200 and body.get("routed_bot") == "siti" and "Siti" in body.get("bot_name", ""))
    results["10. WhatsApp Routing: Frontline CS (Siti)"] = {
        "success": success,
        "details": {
            "routed_bot": body.get("routed_bot"),
            "intent": body.get("intent"),
            "priority": body.get("priority"),
            "reply_snippet": (body.get("reply") or "")[:80] + "..."
        }
    }
    print(f"[{'PASS' if success else 'FAIL'}] 10. WhatsApp Routing: Frontline CS (Siti)")

    # 11. WhatsApp Routing: Escalation / Complaint (Hendra)
    status, body = request("/bff/api/whatsapp/simulate", method="POST", data={
        "sender": "6289876543210",
        "customer_name": "Pak Budi",
        "message": "Pesanan saya jahitannya robek dan kotor! Saya minta ganti rugi atau refund!"
    }, token=token)
    success = (status == 200 and body.get("routed_bot") == "hendra" and body.get("priority") == "P1" and body.get("status") == "escalated")
    results["11. WhatsApp Routing: Escalation CS (Hendra)"] = {
        "success": success,
        "details": {
            "routed_bot": body.get("routed_bot"),
            "priority": body.get("priority"),
            "status": body.get("status"),
            "reply_snippet": (body.get("reply") or "")[:80] + "..."
        }
    }
    print(f"[{'PASS' if success else 'FAIL'}] 11. WhatsApp Routing: Escalation CS (Hendra)")

    # 12. WhatsApp Gateway Status & Config
    status, body = request("/bff/api/whatsapp/status", token=token)
    success = (status == 200 and body.get("status") == "ready" and body.get("channel") == "WhatsApp Business Cloud API")
    results["12. WhatsApp Gateway Health & Config Status"] = {
        "success": success,
        "details": body
    }
    print(f"[{'PASS' if success else 'FAIL'}] 12. WhatsApp Gateway Health & Config Status")

    # Save results to json
    with open("day2_sprint5_results.json", "w") as f:
        json.dump(results, f, indent=2)

    passed_count = sum(1 for r in results.values() if r["success"])
    total_count = len(results)
    print("\n" + "=" * 80)
    print(f"  TOTAL HASIL: {passed_count}/{total_count} PENGUJIAN LULUS ({passed_count/total_count*100:.1f}%)")
    print("=" * 80)

if __name__ == "__main__":
    run_tests()
