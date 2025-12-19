import pytest
from fastapi.testclient import TestClient
from unittest.mock import MagicMock, patch, AsyncMock
from aegis_core import aegis_pb2

# We need to mock things before import or manage env vars if needed
# For now, let's assume imports work fine
from aegis_core.core_b.main import app, AegisGatewayServicer, crypto

@pytest.fixture
def client():
    return TestClient(app)

def test_health_check_http(client):
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}

def test_public_key_endpoint(client):
    response = client.get("/public-key")
    assert response.status_code == 200
    assert response.content == crypto.public_key_bytes

def test_grpc_health_check():
    servicer = AegisGatewayServicer()
    response = servicer.HealthCheck(None, None)
    assert response.status == aegis_pb2.HealthCheckResponse.ServingStatus.SERVING

@pytest.mark.asyncio
async def test_grpc_process_new_session():
    servicer = AegisGatewayServicer()

    # Mock crypto and request
    client_crypto = MagicMock()
    # In a real scenario we'd need a valid public key from a peer
    # We can create a temporary crypto engine for the "client"
    from aegis_core.crypto import CryptoEngine
    client_crypto = CryptoEngine()

    # Create an encrypted payload
    # Note: The logic in Core B does:
    # 1. derive session key from client_pub_key
    # 2. decrypt payload
    # 3. make request to App B
    # 4. encrypt response

    # We will mock the crypto.decrypt to avoid complex setup
    # and mock the downstream HTTP call

    mock_request = MagicMock()
    mock_request.public_key = client_crypto.public_key_bytes
    mock_request.metadata = {"method": "GET", "path": "/test"}
    mock_request.encrypted_payload = b"encrypted_stuff"

    # Mocking internal components of Core B
    with patch('aegis_core.core_b.main.crypto') as mock_core_crypto:
        # derive_shared_key returns a dummy key
        mock_core_crypto.derive_shared_key.return_value = b'server_shared_key'

        # decrypt returns a valid json payload
        import json
        payload_data = {
            "headers": {"content-type": "application/json"},
            "body": "test_body"
        }
        mock_core_crypto.decrypt.return_value = json.dumps(payload_data).encode()

        # encrypt returns bytes
        mock_core_crypto.encrypt.return_value = b"encrypted_response"

        # Mock httpx client
        mock_http_response = MagicMock()
        mock_http_response.status_code = 200
        mock_http_response.headers = {"server": "test"}
        mock_http_response.text = "response_body"

        mock_client = AsyncMock()
        mock_client.__aenter__.return_value = mock_client
        mock_client.request.return_value = mock_http_response

        with patch('httpx.AsyncClient', return_value=mock_client):
            response = await servicer.Process(mock_request, None)

            assert response.fake_http_status == 200
            assert response.encrypted_payload == b"encrypted_response"
            assert response.metadata == {"status": "200"}
