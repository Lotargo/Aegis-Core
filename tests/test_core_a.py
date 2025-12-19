import pytest
import os
import asyncio
from unittest.mock import MagicMock, AsyncMock, patch

from fastapi.testclient import TestClient

# Mock grpc before importing core_a.main
with patch('grpc.aio.insecure_channel'):
    from aegis_core.core_a.main import app, crypto, wait_for_grpc_server

@pytest.fixture
def client():
    return TestClient(app)

@pytest.fixture
def mock_crypto():
    return crypto

def test_health_check_endpoint(client):
    response = client.get("/health")
    assert response.status_code == 200
    assert "status" in response.json()
    assert "session_ready" in response.json()

def test_proxy_request_without_session_key(client):
    # Ensure session key is None
    app.state.session_key = None
    response = client.get("/some/path")
    assert response.status_code == 503
    assert response.text == "Core A is not ready: session key is not established."

@pytest.mark.asyncio
async def test_wait_for_grpc_server_success():
    # Mock the stub and its response
    mock_stub = AsyncMock()
    mock_response = MagicMock()
    mock_response.status = 1 # ServingStatus.SERVING usually

    # We need to mock the enum specifically, so let's import the pb2
    from aegis_core import aegis_pb2
    mock_response.status = aegis_pb2.HealthCheckResponse.ServingStatus.SERVING
    mock_stub.HealthCheck.return_value = mock_response

    # Patch the stub in the main module
    with patch('aegis_core.core_a.main.stub', mock_stub):
        result = await wait_for_grpc_server()
        assert result is True

@pytest.mark.asyncio
async def test_startup_event_success():
    # Mock wait_for_grpc_server to return True
    with patch('aegis_core.core_a.main.wait_for_grpc_server', return_value=True):
        # Mock httpx.AsyncClient to return public key
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.content = b'mock_public_key'

        mock_http_client = AsyncMock()
        mock_http_client.__aenter__.return_value = mock_http_client
        mock_http_client.get.return_value = mock_response

        with patch('httpx.AsyncClient', return_value=mock_http_client):
            # Mock crypto.derive_shared_key
            with patch.object(crypto, 'derive_shared_key', return_value=b'shared_key_123'):
                await app.router.startup()
                assert app.state.session_key == b'shared_key_123'
