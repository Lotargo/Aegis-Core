import os
import grpc
import httpx
import asyncio
import json
import uuid

from fastapi import FastAPI, Request, Response, HTTPException
from fastapi.responses import PlainTextResponse

from .. import aegis_pb2_grpc
from .. import aegis_pb2
from ..crypto import CryptoEngine

# --- Конфигурация ---
CORE_B_GRPC_TARGET = os.getenv("CORE_B_GRPC_TARGET", "localhost:50052")
CORE_B_HTTP_URL = os.getenv("CORE_B_HTTP_URL", "http://localhost:8001")
MAX_REQUEST_SIZE = int(os.getenv("MAX_REQUEST_SIZE", 10 * 1024 * 1024))  # 10 MB

# --- Приложение и Крипто-движок ---
app = FastAPI(title="Aegis Core A")
crypto = CryptoEngine()
app.state.session_key = None

# --- gRPC Клиент (асинхронный) ---
# Создаем асинхронный канал
channel = grpc.aio.insecure_channel(CORE_B_GRPC_TARGET)
stub = aegis_pb2_grpc.AegisGatewayStub(channel)

async def wait_for_grpc_server():
    """Ожидает, пока gRPC сервер в Core B не станет доступен (асинхронная версия)."""
    max_retries = 10
    retry_delay = 1
    for attempt in range(max_retries):
        try:
            request = aegis_pb2.HealthCheckRequest()
            response = await stub.HealthCheck(request, timeout=1)
            if response.status == aegis_pb2.HealthCheckResponse.ServingStatus.SERVING:
                print("Core A: gRPC сервер Core B готов.")
                return True
        except grpc.aio.AioRpcError:
            print(f"Core A: gRPC сервер Core B еще не готов (попытка {attempt + 1}).")
            await asyncio.sleep(retry_delay)
    return False

async def perform_handshake():
    """
    Выполняет обмен ключами с Core B.
    """
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(f"{CORE_B_HTTP_URL}/public-key", timeout=5.0)
            response.raise_for_status()
            peer_public_key_bytes = response.content
            app.state.session_key = crypto.derive_shared_key(peer_public_key_bytes)
            print("Core A: Сессионный ключ успешно создан (обновлен).")
            return True
        except httpx.RequestError as e:
            print(f"Core A: Не удалось получить ключ от Core B: {e}")
            app.state.session_key = None
            return False

@app.on_event("startup")
async def startup_event():
    if not await wait_for_grpc_server():
        print("Core A: Не удалось подключиться к gRPC серверу Core B.")
        return
    await perform_handshake()

@app.get("/health")
def health_check():
    return {"status": "ok", "session_ready": app.state.session_key is not None}

@app.api_route("/{path:path}", methods=["GET", "POST", "PUT", "DELETE", "PATCH", "HEAD", "OPTIONS"])
async def proxy_request(request: Request, path: str):
    # 1. DoS Protection: Content-Length Check
    content_length = request.headers.get('content-length')
    if content_length:
        try:
            if int(content_length) > MAX_REQUEST_SIZE:
                 return Response(content="Payload Too Large", status_code=413)
        except ValueError:
            return Response(content="Invalid Content-Length", status_code=400)

    # 2. DoS Protection: Stream Read Check
    body_chunks = []
    body_size = 0
    async for chunk in request.stream():
        body_size += len(chunk)
        if body_size > MAX_REQUEST_SIZE:
             return Response(content="Payload Too Large (Stream)", status_code=413)
        body_chunks.append(chunk)
    body = b"".join(body_chunks)

    if not app.state.session_key:
        # Try to reconnect if key is missing
        if not await perform_handshake():
             return PlainTextResponse("Core A is not ready: session key establishment failed.", status_code=503)

    session_key = app.state.session_key

    # --- MTD: Path Hiding ---
    # We move real path/method inside the encrypted payload.
    # The 'metadata' sent in cleartext will contain fake or empty values.

    full_path = f"/{path}?{request.url.query}" if request.url.query else f"/{path}"
    headers = {k: v for k, v in request.headers.items() if k.lower() != "host"}

    payload_to_encrypt = {
        "method": request.method,
        "path": full_path,
        "headers": headers,
        "body": body.decode("utf-8", "ignore")
    }
    payload_bytes = json.dumps(payload_to_encrypt).encode()

    # Minimal Associated Data (could be a request ID or timestamp)
    # MUST match what Core B expects.
    request_metadata = {"trace_id": str(uuid.uuid4())}
    associated_data = json.dumps(request_metadata, sort_keys=True).encode()

    encrypted_payload = crypto.encrypt(session_key, payload_bytes, associated_data)

    aegis_req = aegis_pb2.AegisRequest(
        encrypted_payload=encrypted_payload,
        public_key=crypto.public_key_bytes,
        metadata=request_metadata
    )

    try:
        aegis_res = await stub.Process(aegis_req)
    except grpc.aio.AioRpcError as e:
        # --- MTD: Auto-Reconnection ---
        if e.code() == grpc.StatusCode.UNAUTHENTICATED:
            print("Core A: Session expired. Renewing key...")
            if await perform_handshake():
                # Retry with new key
                session_key = app.state.session_key
                encrypted_payload = crypto.encrypt(session_key, payload_bytes, associated_data)
                aegis_req.encrypted_payload = encrypted_payload
                try:
                     aegis_res = await stub.Process(aegis_req)
                except grpc.aio.AioRpcError as e2:
                     return PlainTextResponse(f"gRPC Retry Error: {e2.details()}", status_code=503)
            else:
                 return PlainTextResponse("Session renewal failed.", status_code=503)
        else:
            return PlainTextResponse(f"gRPC Error: {e.details()}", status_code=503)

    # --- MTD: Deception Handling ---
    # We completely IGNORE aegis_res.fake_http_status
    # We trust only the inner encrypted payload.

    response_ad = json.dumps(dict(aegis_res.metadata)).encode()

    try:
        decrypted_response_payload = crypto.decrypt(session_key, aegis_res.encrypted_payload, response_ad)
        response_data = json.loads(decrypted_response_payload)
    except Exception as e:
         print(f"Decryption error on response: {e}")
         return PlainTextResponse("Secure Channel Error: Bad Response", status_code=502)

    return Response(
        content=response_data["body"],
        status_code=response_data["status_code"],
        headers=response_data["headers"],
    )
