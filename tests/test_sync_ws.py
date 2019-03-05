import pytest
from starlette.websockets import WebSocket


class App:
    def __init__(self, scope):
        assert scope["type"] == "websocket"
        self.scope = scope

    async def __call__(self, receive, send):
        websocket = WebSocket(self.scope, receive=receive, send=send)
        await websocket.accept()
        if websocket.url.path == "/":
            await websocket.send_text("Hello, world!")

        if websocket.url.path == "/bytes":
            message = await websocket.receive_bytes()
            await websocket.send_bytes(message)

        if websocket.url.path == "/json":
            message = await websocket.receive_json()
            await websocket.send_json(message)
        await websocket.close()


@pytest.fixture(scope="module")
def client():
    from asgi_testclient.sync import TestClient

    return TestClient(App)


@pytest.mark.sync
def test_send_receive_bytes(client):
    websocket = client.ws_connect("/bytes")

    byte_msg = b"test"
    websocket.send_bytes(byte_msg)
    response = websocket.receive_bytes()

    assert response == byte_msg
    websocket.close()


@pytest.mark.sync
def test_send_receive_json(client):
    websocket = client.ws_connect("/json")

    json_msg = {"hello": "test"}
    websocket.send_json(json_msg)
    response = websocket.receive_json()

    assert response == json_msg
    websocket.close()


@pytest.mark.sync
def test_ws_context(client):
    with client.ws_session("/") as websocket:
        data = websocket.receive_text()
        assert data == "Hello, world!"
