import pytest
from app.models.user import User
from app.utils.security import hash_password, create_access_token


def test_login_invalid_credentials(client, db_session):
    resp = client.post("/auth/login", json={"username": "nonexistent", "password": "wrongpassword"})
    assert resp.status_code == 401
    assert "Incorrect username or password" in resp.json()["detail"]


def test_login_success(client, db_session):
    # Create test user
    user = User(
        username="secops",
        email="secops@netsecurelab.local",
        hashed_password=hash_password("SecOpsSecret123!"),
        role="operator",
        is_active=True,
    )
    db_session.add(user)
    db_session.commit()

    resp = client.post("/auth/login", json={"username": "secops", "password": "SecOpsSecret123!"})
    assert resp.status_code == 200
    data = resp.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"
    assert data["user"]["username"] == "secops"
    assert data["user"]["role"] == "operator"


def test_get_current_user_profile(client, db_session):
    # Unauthenticated request
    unauth_resp = client.get("/auth/me")
    assert unauth_resp.status_code == 401

    # Authenticated request
    user = User(
        username="auditor",
        email="auditor@netsecurelab.local",
        hashed_password=hash_password("AuditorSecret123!"),
        role="viewer",
        is_active=True,
    )
    db_session.add(user)
    db_session.commit()

    token = create_access_token({"sub": "auditor", "role": "viewer", "id": user.id})
    auth_resp = client.get("/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert auth_resp.status_code == 200
    assert auth_resp.json()["username"] == "auditor"
    assert auth_resp.json()["role"] == "viewer"


def test_admin_registration_and_rbac(client, db_session):
    # 1. Create an admin and an operator
    admin = User(
        username="admin_user",
        hashed_password=hash_password("AdminPass123!"),
        role="admin",
        is_active=True,
    )
    operator = User(
        username="operator_user",
        hashed_password=hash_password("OpPass123!"),
        role="operator",
        is_active=True,
    )
    db_session.add_all([admin, operator])
    db_session.commit()

    operator_token = create_access_token({"sub": "operator_user", "role": "operator", "id": operator.id})
    admin_token = create_access_token({"sub": "admin_user", "role": "admin", "id": admin.id})

    new_user_payload = {
        "username": "analyst1",
        "email": "analyst1@netsecurelab.local",
        "password": "AnalystPassword123!",
        "role": "viewer",
    }

    # Operator trying to register a user -> 403 Forbidden
    op_resp = client.post("/auth/register", json=new_user_payload, headers={"Authorization": f"Bearer {operator_token}"})
    assert op_resp.status_code == 403

    # Admin trying to register a user -> 201 Created
    adm_resp = client.post("/auth/register", json=new_user_payload, headers={"Authorization": f"Bearer {admin_token}"})
    assert adm_resp.status_code == 201
    assert adm_resp.json()["username"] == "analyst1"
