import pytest

@pytest.mark.asyncio
async def test_register_and_login_flow(client):
    # 1. Register
    reg_payload = {"email": "testuser@zelvira.com", "password": "password123"}
    reg_res = await client.post("/api/v1/auth/register", json=reg_payload)
    assert reg_res.status_code == 201
    data = reg_res.json()
    assert "access_token" in data
    assert data["user"]["email"] == "testuser@zelvira.com"

    # 2. Register Duplicate Email Fails
    dup_res = await client.post("/api/v1/auth/register", json=reg_payload)
    assert dup_res.status_code == 400

    # 3. Login with Correct Credentials
    login_res = await client.post("/api/v1/auth/login", json=reg_payload)
    assert login_res.status_code == 200
    token = login_res.json()["access_token"]
    assert token

    # 4. Login with Incorrect Password Fails
    bad_login = await client.post("/api/v1/auth/login", json={"email": "testuser@zelvira.com", "password": "wrong"})
    assert bad_login.status_code == 401

@pytest.mark.asyncio
async def test_health_endpoint(client):
    res = await client.get("/health")
    assert res.status_code == 200
    data = res.json()
    assert "status" in data
    assert "database" in data
