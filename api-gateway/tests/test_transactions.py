"""
Transaction endpoint tests.

Covers:
    - Creating a transaction (authentication required)
    - Listing user transactions
    - Retrieving a transaction by ID
"""

from unittest.mock import patch, MagicMock

import pytest
from httpx import AsyncClient


async def _register_and_login(client: AsyncClient, email: str = "txuser@example.com") -> str:
    """Helper — register a user and return a valid JWT."""
    await client.post(
        "/api/v1/auth/register",
        json={"email": email, "password": "SecureP@ss123"},
    )
    login_resp = await client.post(
        "/api/v1/auth/login",
        data={"username": email, "password": "SecureP@ss123"},
    )
    return login_resp.json()["access_token"]


@pytest.mark.asyncio
async def test_create_transaction(client: AsyncClient):
    """Authenticated users can submit a transaction."""
    token = await _register_and_login(client)

    with patch("app.services.transaction_service.celery_app") as mock_celery:
        mock_celery.send_task = MagicMock()
        response = await client.post(
            "/api/v1/transactions/",
            json={
                "amount": 1500.00,
                "currency": "USD",
                "location": "New York",
                "device_id": "device-abc",
                "ip_address": "192.168.1.1",
                "transaction_time": "2025-06-15T14:30:00Z",
            },
            headers={"Authorization": f"Bearer {token}"},
        )

    assert response.status_code == 201
    data = response.json()
    assert data["amount"] == 1500.0
    assert data["status"] == "PENDING"
    assert data["currency"] == "USD"


@pytest.mark.asyncio
async def test_create_transaction_unauthenticated(client: AsyncClient):
    """Unauthenticated users get 401."""
    response = await client.post(
        "/api/v1/transactions/",
        json={"amount": 100.0},
    )
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_list_transactions(client: AsyncClient):
    """Users can list their own transactions."""
    token = await _register_and_login(client, email="listuser@example.com")

    with patch("app.services.transaction_service.celery_app") as mock_celery:
        mock_celery.send_task = MagicMock()
        await client.post(
            "/api/v1/transactions/",
            json={"amount": 200.0, "transaction_time": "2025-06-15T14:30:00Z"},
            headers={"Authorization": f"Bearer {token}"},
        )

    response = await client.get(
        "/api/v1/transactions/",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["total"] >= 1
    assert len(data["items"]) >= 1


@pytest.mark.asyncio
async def test_get_transaction_by_id(client: AsyncClient):
    """Users can retrieve their own transaction by UUID."""
    token = await _register_and_login(client, email="getuser@example.com")

    with patch("app.services.transaction_service.celery_app") as mock_celery:
        mock_celery.send_task = MagicMock()
        create_resp = await client.post(
            "/api/v1/transactions/",
            json={"amount": 500.0, "transaction_time": "2025-06-15T14:30:00Z"},
            headers={"Authorization": f"Bearer {token}"},
        )
    txn_id = create_resp.json()["id"]

    response = await client.get(
        f"/api/v1/transactions/{txn_id}",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 200
    assert response.json()["id"] == txn_id
