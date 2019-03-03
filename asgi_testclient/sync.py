import asyncio
from asgi_testclient.client import TestClient as _TestClient


class TestClient(_TestClient):
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
