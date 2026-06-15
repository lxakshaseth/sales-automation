import httpx
import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient


def build_test_app() -> FastAPI:
    app = FastAPI()

    @app.get("/health")
    async def health():
        return {"status": "ok"}

    return app


@pytest.mark.integration
def test_fastapi_testclient_health_contract():
    client = TestClient(build_test_app())

    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


@pytest.mark.asyncio
@pytest.mark.integration
async def test_httpx_async_client_health_contract():
    transport = httpx.ASGITransport(app=build_test_app())
    async with httpx.AsyncClient(transport=transport, base_url="http://testserver") as client:
        response = await client.get("/health")

    assert response.status_code == 200
    assert response.json()["status"] == "ok"
