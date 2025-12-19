import os
import grpc
import httpx
import asyncio
import json

from fastapi import FastAPI, Request, Response
from fastapi.responses import PlainTextResponse

from .. import aegis_pb2_grpc
from .. import aegis_pb2
from ..crypto import CryptoEngine

# --- Конфигурация ---
CORE_B_GRPC_TARGET = os.getenv("CORE_B_GRPC_TARGET", "localhost:50052")
CORE_B_HTTP_URL = os.getenv("CORE_B_HTTP_URL", "http://localhost:8001")

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
            # Используем await для асинхронного вызова
            response = await stub.HealthCheck(request, timeout=1)
            if response.status == aegis_pb2.HealthCheckResponse.ServingStatus.SERVING:
                print("Core A: gRPC сервер Core B готов.")
                return True
        except grpc.aio.AioRpcError:
            print(f"Core A: gRPC сервер Core B еще не готов (попытка {attempt + 1}).")
            await asyncio.sleep(retry_delay)
    return False

@app.on_event("startup")
async def startup_event():
    """
    При старте сначала дожидается готовности gRPC сервера Core B,
    а затем получает публичный ключ.
    """
    if not await wait_for_grpc_server():
        print("Core A: Не удалось подключиться к gRPC серверу Core B.")
        return

    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(f"{CORE_B_HTTP_URL}/public-key", timeout=5.0)
            response.raise_for_status()
            peer_public_key_bytes = response.content
            app.state.session_key = crypto.derive_shared_key(peer_public_key_bytes)
            print("Core A: Сессионный ключ успешно создан.")
        except httpx.RequestError as e:
            print(f"Core A: Не удалось получить ключ от Core B: {e}")
            app.state.session_key = None

@app.get("/health")
def health_check():
    return {"status": "ok", "session_ready": app.state.session_key is not None}

@app.api_route("/{path:path}", methods=["GET", "POST", "PUT", "DELETE", "PATCH", "HEAD", "OPTIONS"])
async def proxy_request(request: Request, path: str):
    if not app.state.session_key:
        return PlainTextResponse("Core A is not ready: session key is not established.", status_code=503)

    session_key = app.state.session_key

    full_path = f"/{path}?{request.url.query}"
    headers = {k: v for k, v in request.headers.items() if k.lower() != "host"}
    body = await request.body()

    payload_to_encrypt = { "headers": headers, "body": body.decode("utf-8", "ignore") }
    payload_bytes = json.dumps(payload_to_encrypt).encode()

    associated_data = json.dumps({ "method": request.method, "path": full_path }).encode()

    encrypted_payload = crypto.encrypt(session_key, payload_bytes, associated_data)

    aegis_req = aegis_pb2.AegisRequest(
        encrypted_payload=encrypted_payload,
        public_key=crypto.public_key_bytes,
        metadata={ "method": request.method, "path": full_path }
    )

    try:
        # Используем await для асинхронного вызова
        aegis_res = await stub.Process(aegis_req)

        response_ad = json.dumps(dict(aegis_res.metadata)).encode()

        decrypted_response_payload = crypto.decrypt(session_key, aegis_res.encrypted_payload, response_ad)
        response_data = json.loads(decrypted_response_payload)

        return Response(
            content=response_data["body"],
            status_code=response_data["status_code"],
            headers=response_data["headers"],
        )
    except grpc.aio.AioRpcError as e:
        return PlainTextResponse(f"gRPC Error: {e.details()}", status_code=503)
