"""
Authentication endpoint tests.

Covers:
    - User registration (success + duplicate email)
    - User login (success + invalid credentials)
    - /auth/me (token validation)
"""

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_register_user(client: AsyncClient):
    """Registering a new user returns 201 and the user profile."""
    response = await client.post(
        "/api/v1/auth/register",
        json={"email": "alice@example.com", "password": "SecureP@ss123"},
    )
    assert response.status_code == 201
    data = response.json()
    assert data["email"] == "alice@example.com"
    assert data["role"] == "USER"
    assert "id" in data


@pytest.mark.asyncio
async def test_register_duplicate_email(client: AsyncClient):
    """Registering with an existing email returns 409."""
    payload = {"email": "bob@example.com", "password": "SecureP@ss123"}
    await client.post("/api/v1/auth/register", json=payload)
    response = await client.post("/api/v1/auth/register", json=payload)
    assert response.status_code == 409


@pytest.mark.asyncio
async def test_login_success(client: AsyncClient):
    """Valid credentials return a JWT access token."""
    await client.post(
        "/api/v1/auth/register",
        json={"email": "charlie@example.com", "password": "SecureP@ss123"},
    )

    response = await client.post(
        "/api/v1/auth/login",
        data={"username": "charlie@example.com", "password": "SecureP@ss123"},
    )
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"


@pytest.mark.asyncio
async def test_login_invalid_password(client: AsyncClient):
    """Wrong password returns 401."""
    await client.post(
        "/api/v1/auth/register",
        json={"email": "dave@example.com", "password": "SecureP@ss123"},
    )

    response = await client.post(
        "/api/v1/auth/login",
        data={"username": "dave@example.com", "password": "WrongPass"},
    )
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_login_nonexistent_user(client: AsyncClient):
    """Login with unknown email returns 401."""
    response = await client.post(
        "/api/v1/auth/login",
        data={"username": "ghost@example.com", "password": "any"},
    )
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_me_endpoint(client: AsyncClient):
    """/auth/me returns the current user when a valid token is supplied."""
    await client.post(
        "/api/v1/auth/register",
        json={"email": "eve@example.com", "password": "SecureP@ss123"},
    )
    login_resp = await client.post(
        "/api/v1/auth/login",
        data={"username": "eve@example.com", "password": "SecureP@ss123"},
    )
    token = login_resp.json()["access_token"]

    response = await client.get(
        "/api/v1/auth/me",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 200
    assert response.json()["email"] == "eve@example.com"


@pytest.mark.asyncio
async def test_me_no_token(client: AsyncClient):
    """/auth/me without a token returns 401."""
    response = await client.get("/api/v1/auth/me")
    assert response.status_code == 401
