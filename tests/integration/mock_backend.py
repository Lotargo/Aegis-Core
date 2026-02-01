from fastapi import FastAPI, Request
import uvicorn
import sys

app = FastAPI()

@app.api_route("/{path:path}", methods=["GET", "POST", "PUT", "DELETE"])
async def catch_all(path: str, request: Request):
    return {
        "status": "ok",
        "method": request.method,
        "path": request.url.path,
        "query": request.url.query,
        "headers": dict(request.headers),
        "body": (await request.body()).decode("utf-8")
    }

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8081)
