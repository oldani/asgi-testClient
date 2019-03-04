import asyncio
import json
from asgi_testclient import client
from asgi_testclient.types import Optional


class WsSession(client.WsSession):
    def __init__(self, *args):
        self._loop = asyncio.get_event_loop()
        super().__init__(*args)

    def send_text(self, message: str) -> None:  # type: ignore
        self._loop.run_until_complete(super().send_text(message))

    def receive_text(self) -> Optional[str]:  # type: ignore
        return self._loop.run_until_complete(super().receive_text())

    def send_bytes(self, message: bytes) -> None:  # type: ignore
        self._loop.run_until_complete(super().send_bytes(message))

    def receive_bytes(self) -> Optional[bytes]:  # type: ignore
        return self._loop.run_until_complete(super().receive_bytes())

    def send_json(self, message: str) -> None:  # type: ignore
        _message = {"type": "websocket.receive", "text": json.dumps(message)}
        self._loop.run_until_complete(super().send(_message))

    def receive_json(self):
        return self._loop.run_until_complete(super().receive_json())

    def close(self):
        return self._loop.run_until_complete(super().close())


client.WsSession = WsSession  # type: ignore


class WsContextManager(client.WsContextManager):
    def __enter__(self):
        return self.ws_session

    def __exit__(self, *args):
        return self.ws_session.close()


class TestClient(client.TestClient):
    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        try:
            self.loop = asyncio.get_event_loop()
        except RuntimeError:  # Allow run in threads
            self.loop = asyncio.new_event_loop()
            asyncio.set_event_loop(self.loop)

        if self.loop.is_running():  # If running is an async app, why use this clas?
            raise RuntimeError("Event loop already running. User async client.")

    def get(self, url, **kwargs):
        response = self.loop.run_until_complete(self.send("GET", url, **kwargs))
        return response

    def options(self, url, **kwargs):
        response = self.loop.run_until_complete(self.send("OPTIONS", url, **kwargs))
        return response

    def head(self, url, **kwargs):
        response = self.loop.run_until_complete(self.send("HEAD", url, **kwargs))
        return response

    def post(self, url, data=None, json=None, **kwargs):
        response = self.loop.run_until_complete(
            self.send("POST", url, data=data, json=json, **kwargs)
        )
        return response

    def put(self, url, data=None, **kwargs):
        response = self.loop.run_until_complete(
            self.send("PUT", url, data=data, **kwargs)
        )
        return response

    def delete(self, url, **kwargs):
        response = self.loop.run_until_complete(self.send("DELETE", url, **kwargs))
        return response

    def patch(self, url, **kwargs):
        response = self.loop.run_until_complete(self.send("PATCH", url, **kwargs))
        return response

    def ws_connect(self, url, subprotocols=None, **kwargs):
        websocket = self.loop.run_until_complete(
            self.send("GET", url, subprotocols=subprotocols, ws=True, **kwargs)
        )
        return websocket

    def ws_session(self, url, subprotocols=None, **kwargs):
        ws_session = self.loop.run_until_complete(
            self.send("GET", url, subprotocols=subprotocols, ws=True, **kwargs)
        )
        return WsContextManager(ws_session)
