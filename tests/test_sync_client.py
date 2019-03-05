import concurrent.futures
import pytest
from starlette.applications import Starlette
from starlette.responses import JSONResponse

# from asgi_testclient.sync import TestClient


app = Starlette()


@app.route(
    "/", methods=["GET", "DELETE", "POST", "PUT", "PATCH", "HEAD", "PATCH", "OPTIONS"]
)
async def index(request):
    return JSONResponse({"hello": "world"})


@pytest.fixture(scope="module")
def client_class():
    from asgi_testclient.sync import TestClient

    return TestClient


@pytest.fixture(scope="module")
def client(client_class):
    return client_class(app)


@pytest.mark.sync
def test_methods(client):
    for method in ["GET", "DELETE", "POST", "PUT", "PATCH", "HEAD", "PATCH", "OPTIONS"]:
        meth = getattr(client, method.lower())
        response = meth("/")
        assert response.json() == {"hello": "world"}


@pytest.mark.sync
@pytest.mark.asyncio
async def test_loop_running(client_class):
    with pytest.raises(RuntimeError):
        client_class(app)


@pytest.mark.sync
@pytest.mark.asyncio
async def test_thread_loop(event_loop, client_class):
    def dummy():
        client = client_class(app)
        return client.loop.is_running()

    with concurrent.futures.ThreadPoolExecutor() as pool:
        result = await event_loop.run_in_executor(pool, dummy)
        assert not result
