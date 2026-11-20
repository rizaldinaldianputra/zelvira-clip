import urllib.request
import json

def test():
    base_url = "http://127.0.0.1:8000/api/v1"

    # 1. Login or register
    email = "gatewayuser@test.com"
    pwd = "TestPassword123!"

    reg_payload = json.dumps({"email": email, "password": pwd, "full_name": "Gateway User"}).encode("utf-8")
    req = urllib.request.Request(f"{base_url}/auth/register", data=reg_payload, headers={"Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(req) as resp:
            data = json.loads(resp.read().decode())
            token = data["access_token"]
    except Exception:
        # If already registered, login
        login_data = f"username={email}&password={pwd}".encode("utf-8")
        req_l = urllib.request.Request(f"{base_url}/auth/login", data=login_data, headers={"Content-Type": "application/x-www-form-urlencoded"})
        with urllib.request.urlopen(req_l) as resp:
            data = json.loads(resp.read().decode())
            token = data["access_token"]

    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}

    # 2. Get Providers
    req_p = urllib.request.Request(f"{base_url}/ai/providers", headers=headers)
    with urllib.request.urlopen(req_p) as resp:
        provs = json.loads(resp.read().decode())
        print(f"[OK] Providers received: {len(provs)} providers")
        for p in provs:
            print(f"  - {p['name']} ({p['category']}): connected={p['connected']}")

    # 3. Get Models
    req_m = urllib.request.Request(f"{base_url}/ai/models", headers=headers)
    with urllib.request.urlopen(req_m) as resp:
        models = json.loads(resp.read().decode())
        print(f"[OK] Models in Registry: {len(models)} models")

    # 4. Get Usage
    req_u = urllib.request.Request(f"{base_url}/ai/usage", headers=headers)
    with urllib.request.urlopen(req_u) as resp:
        usage = json.loads(resp.read().decode())
        print(f"[OK] Usage history received: total_requests={usage['total_requests']}")

if __name__ == "__main__":
    test()
