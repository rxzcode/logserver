import hashlib
import jwt
from datetime import datetime, timedelta
from fastapi.testclient import TestClient
from main import app  # adjust path if needed

client = TestClient(app)
SECRET = "secret"
ALGORITHM = "HS256"
AUD = "logserver"
ISS = "issuer"


def make_secret(tenant_id: str) -> str:
    return hashlib.md5((tenant_id + SECRET).encode("utf-8")).hexdigest()


def create_token(payload: dict, secret: str, exp_minutes: int = 15) -> str:
    now = datetime.utcnow()
    payload = payload.copy()
    payload.update({
        "iat": now,
        "exp": now + timedelta(minutes=exp_minutes),
        "aud": AUD,
        "iss": ISS
    })
    return jwt.encode(payload, secret, algorithm=ALGORITHM)


def test_validate_token_success():
    tenant_id = "abc"
    secret = make_secret(tenant_id)
    token = create_token({
        "sub": "01",
        "tenant": tenant_id,
        "role": "admin"
    }, secret)

    headers = {"Authorization": f"Bearer {token}"}
    response = client.get("/auth/validate", headers=headers)

    assert response.status_code == 200
    assert response.headers["x-auth-sub"] == "01"
    assert response.headers["x-auth-tenant"] == tenant_id
    assert response.headers["x-auth-role"] == "admin"


def test_missing_tenant_claim():
    secret = make_secret("abc")
    token = create_token({
        "sub": "user1",
        "role": "admin"
    }, secret)

    headers = {"Authorization": f"Bearer {token}"}
    response = client.get("/auth/validate", headers=headers)

    assert response.status_code == 401
    assert "x-auth-sub" not in response.headers
    assert "x-auth-tenant" not in response.headers
    assert "x-auth-role" not in response.headers


def test_invalid_signature():
    tenant_id = "abc"
    wrong_secret = "badsecret"
    token = create_token({
        "sub": "user1",
        "tenant": tenant_id,
        "role": "admin"
    }, wrong_secret)

    headers = {"Authorization": f"Bearer {token}"}
    response = client.get("/auth/validate", headers=headers)

    assert response.status_code == 401
    assert "x-auth-sub" not in response.headers


def test_expired_token():
    tenant_id = "abc"
    secret = make_secret(tenant_id)
    token = create_token({
        "sub": "user1",
        "tenant": tenant_id,
        "role": "admin"
    }, secret, exp_minutes=-1)

    headers = {"Authorization": f"Bearer {token}"}
    response = client.get("/auth/validate", headers=headers)

    assert response.status_code == 401
    assert "x-auth-sub" not in response.headers


def test_rbac_failure_viewer_accessing_admin_path():
    tenant_id = "abc"
    secret = make_secret(tenant_id)
    token = create_token({
        "sub": "user1",
        "tenant": tenant_id,
        "role": "viewer"
    }, secret)

    headers = {
        "Authorization": f"Bearer {token}",
        "x-auth-request-redirect": "/api/v1/tenant/stuff"
    }
    response = client.get("/auth/validate", headers=headers)

    assert response.status_code == 401
    assert "x-auth-sub" not in response.headers


def test_token_in_query_param():
    tenant_id = "abc"
    secret = make_secret(tenant_id)
    token = create_token({
        "sub": "user1",
        "tenant": tenant_id,
        "role": "admin"
    }, secret)

    response = client.get(f"/auth/validate?token={token}")
    assert response.status_code == 200
    assert response.headers["x-auth-sub"] == "user1"
    assert response.headers["x-auth-tenant"] == tenant_id
    assert response.headers["x-auth-role"] == "admin"
