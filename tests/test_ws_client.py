import pytest
from starlette.websockets import WebSocket, WebSocketDisconnect

from asgi_testclient import TestClient, WsDisconnect


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


class Echo:
    async def __call__(self, scope, receive, send):
        assert scope["type"] == "websocket"
        websocket = WebSocket(scope, receive=receive, send=send)
        await websocket.accept()
        while True:
            try:
                message = await websocket.receive_text()
            except WebSocketDisconnect:
                break
            await websocket.send_text(message)


@pytest.fixture
def client():
    return TestClient(App)


@pytest.fixture
def echo_server():
    return TestClient(Echo())


async def test_ws(client):
    async with client.ws_session("/") as websocket:
        data = await websocket.receive_text()
        assert data == "Hello, world!"


async def test_ws_disconnect(client):
    async with client.ws_session("/") as websocket:
        await websocket.receive_text()

        with pytest.raises(WsDisconnect):
            await websocket.receive_text()


async def test_send(echo_server):
    async with echo_server.ws_session("/") as websocket:
        for msg in ["Hey", "Echo", "Back"]:
            await websocket.send_text(msg)
            data = await websocket.receive_text()
            assert data == msg


async def test_send_receive_bytes(client):
    async with client.ws_session("/bytes") as websocket:
        byte_msg = b"test"
        await websocket.send_bytes(byte_msg)
        response = await websocket.receive_bytes()

        assert response == byte_msg


async def test_send_receive_json(client):
    async with client.ws_session("/json") as websocket:
        json_msg = {"hello": "test"}
        await websocket.send_json(json_msg)
        response = await websocket.receive_json()

        assert response == json_msg


async def test_ws_context(client):
    async with client.ws_session("/") as websocket:
        data = await websocket.receive_text()
        assert data == "Hello, world!"
