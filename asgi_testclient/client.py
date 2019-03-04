from asyncio import Queue, ensure_future, sleep
import json as _json
from http import HTTPStatus
from urllib.parse import urlsplit, urlencode
from wsgiref.headers import Headers as _Headers
from asgi_testclient.types import (
    Scope,
    ASGIApp,
    Message,
    Headers,
    Params,
    Url,
    ReqHeaders,
    ResHeaders,
    Optional,
    List,
    Any,
    Union,
)

DEFAULT_PORTS = {"http": 80, "ws": 80, "https": 443, "wss": 443}


class HTTPError(Exception):
    pass


class WsDisconnect(Exception):
    pass


class Response:
    """
        TODO: Allow Response object to act as stream
    """

    def __init__(self, url: str, status_code: int, headers: ResHeaders) -> None:
        self.url = url
        self.status_code = status_code
        self.reason = HTTPStatus(status_code).phrase
        self.headers: _Headers = _Headers(headers)
        self._content: bytes = b""

    def __repr__(self):
        return f"<Response [{self.status_code}]>"

    def raise_for_status(self) -> None:
        """ Raises `HTTPError`, if one occurred. """
        if 400 <= self.status_code < 500:
            raise HTTPError(
                f"{self.status_code} Client Error: {self.reason} for url: {self.url}"
            )

        elif 500 <= self.status_code < 600:
            raise HTTPError(
                f"{self.status_code} Server Error: {self.reason} for url: {self.url}"
            )

    @property
    def ok(self) -> bool:
        """ Returns True if :attr:`status_code` is less than 400, False if not.

        This attribute checks if the status code of the response is between
        400 and 600 to see if there was a client error or a server error. If
        the status code is between 200 and 400, this will return True. 

        This is **not** a check to see if the response code is ``200 OK``. """
        try:
            self.raise_for_status()
        except HTTPError:
            return False
        return True

    @property
    def content(self) -> bytes:
        """ Content of the response, in bytes. """
        return self._content

    @content.setter
    def content(self, content: bytes):
        """ Allow streaming response by appending content. """
        if self._content:
            self._content += content
        else:
            self._content = content

    @property
    def text(self):
        """ Content of the response, in unicode. """
        return self.content.decode()

    def json(self, **kwargs):
        """ Returns the json-encoded content of a response, if any.

            :param **kwargs: Optional arguments that ``json.loads`` takes.
            :raises ValueError: If the response body does not contain valid json. """
        try:
            json = _json.loads(self.text, **kwargs)
            return json
        except _json.JSONDecodeError:
            raise ValueError(
                f"Response content is not JSON serializable. Text {self.text}"
            )


class WsSession:
    def __init__(self, app: ASGIApp, scope: Scope) -> None:
        self._handler = app(scope)
        self._scope = scope
        self._client: Queue = Queue()  # For ASGI app to send messages
        self._server: Queue = Queue()  # For client session to send message to ASGI app

        self._server_task = ensure_future(
            self._handler(self._server_receive, self._server_send)
        )

    async def _start(self) -> None:
        """ Start conmunication between client and ASGI app. """
        await self.send({"type": "websocket.connect"})
        await self.receive()

    async def _server_send(self, message: Message) -> None:
        """ Put a message in client queue where it can consume. """
        await self._client.put(message)

    async def _server_receive(self) -> Message:
        """ Read message from client. """
        return await self._server.get()

    async def send(self, message: Message) -> None:
        """ Put message on ASGI app queue where it can consume it. """
        await self._server.put(message)

    async def receive(self) -> Message:
        """ Read message from ASGI app. """
        message = await self._client.get()
        if message["type"] == "websocket.close":
            raise WsDisconnect
        return message

    async def send_text(self, message: str) -> None:
        await self.send({"type": "websocket.receive", "text": message})

    async def receive_text(self) -> Optional[str]:
        message = await self.receive()
        return message.get("text")

    async def send_bytes(self, message: bytes) -> None:
        await self.send({"type": "websocket.receive", "bytes": message})

    async def receive_bytes(self) -> Optional[bytes]:
        message = await self.receive()
        return message.get("bytes")

    async def send_json(self, message: str) -> None:
        message = _json.dumps(message)
        await self.send_text(message)

    async def receive_json(self):
        message = (await self.receive()).get("text")
        return _json.loads(message)

    async def close(self):
        """ Finish session with server, wait until handler is done. """
        await self.send({"type": "websocket.disconnect", "code": 1000})
        while not self._server_task.done():
            await sleep(0.1)


class WsContextManager:
    def __init__(self, ws_session):
        self.ws_session = ws_session

    async def __aenter__(self):
        self.ws_session = await self.ws_session
        return self.ws_session

    async def __aexit__(self, *args):
        await self.ws_session.close()


class TestClient:
    """
        Client for testing ASGI applications.
        Mimics ASGI server parsing requests and responses, replicating requests API.
        TODO:
            - Support Websockets client.
            - Cookies support.
            - Redirects. """

    __test__ = False  # For pytest
    default_headers: list = [
        (b"user-agent", b"testclient"),
        (b"accept-encoding", b"gzip, deflate"),
        (b"accept", b"*/*"),
        (b"connection", b"keep-alive"),
    ]

    def __init__(
        self,
        app: ASGIApp,
        raise_server_exceptions: bool = True,
        base_url: str = "http://testserver",
    ) -> None:
        self.app = app
        self.base_url = base_url
        self.raise_server_exceptions = raise_server_exceptions

    async def send(
        self,
        method: str,
        url: str,
        params: Params = {},
        data: dict = {},
        headers: Headers = {},
        json: dict = {},
        subprotocols: Optional[List[str]] = None,
        ws: bool = False,
    ) -> Union[Response, WsSession]:
        """ Handle request/response cycle seting up request, creating scope dict,
            calling the app and awaiting in the handler to return the response. """
        self.url = url
        scheme, host, port, path, query = self.prepare_url(url, params=params)
        req_headers: ReqHeaders = self.prepare_headers(host, headers)

        scope = {
            "http_version": "1.1",
            "method": method,
            "path": path,
            "root_path": "",
            "scheme": scheme,
            "query_string": query,
            "headers": req_headers,
            "client": ("testclient", 5000),
            "server": [host, port],
        }

        if ws:
            scope["type"] = "websocket"
            scope["scheme"] = "ws"
            scope["subprotocols"] = subprotocols or []
            session = WsSession(self.app, scope)
            await session._start()
            return session

        scope["type"] = "http"
        self.prepare_body(req_headers, data=data, json=json)
        try:
            self.__response_started = False
            self.__response_complete = False
            handler = self.app(scope)
            await handler(self._receive, self._send)
        except Exception as ex:
            if self.raise_server_exceptions:
                raise ex from None
        return self._response

    def prepare_url(self, url: str, params: Params) -> Url:
        """ Parse url and query params, run validation.
            return:
                - scheme: (http or https)
                - host: (IP or domain)
                - port: (Custon port, or default)
                - path: (Quoted url path)
                - query: (Encoded query)
        """
        if url.startswith("/"):
            url = f"{self.base_url}{url}"
        scheme, netloc, path, query, _ = urlsplit(url)

        if not scheme:
            raise ValueError(
                f"Invalid URL. No scheme supplied. Perhaps you meant http://{url}"
            )
        elif not netloc:
            raise ValueError(f"Invalid URL {url}. No host supplied")

        if not path:
            path = "/"

        host: str
        port: int
        if ":" in netloc:
            host, sport = netloc.split(":")
            port = int(sport)
        else:
            host, port = netloc, DEFAULT_PORTS.get(scheme, 80)

        # Query Params
        if params:
            if isinstance(params, (dict, list)):
                q = urlencode(params)
            if query:
                query = f"{query}&{q}"
            else:
                query = q

        return scheme, host, port, path, query.encode()

    def prepare_headers(self, host: str, headers: Headers = []) -> ReqHeaders:
        """ Prepares the given HTTP headers."""
        _headers: list = [(b"host", host.encode())]
        _headers += self.default_headers

        if headers:
            if isinstance(headers, dict):
                _headers += [(k.encode(), v.encode()) for k, v in headers.items()]
            elif isinstance(headers, list):
                _headers += [(k.encode(), v.encode()) for k, v in headers]
            else:
                raise ValueError("Headers must be Dict or List objects")
        return _headers

    def prepare_body(
        self, headers: ReqHeaders, data: dict = {}, json: dict = {}
    ) -> None:
        """ Prepares the given HTTP body data.
            TODO: Support files encoding
        """
        self._body: bytes = b""
        if not data and json:
            headers.append((b"content-type", b"application/json"))
            self._body = _json.dumps(json).encode()
        elif data:
            self._body = urlencode(data, doseq=True).encode()
            headers.append((b"content-type", b"application/x-www-form-urlencoded"))
        headers.append((b"content-length", str(len(self._body)).encode()))

    async def _send(self, message: Message) -> None:
        """ Mimic ASGI send awaitable, create and set response object. """
        if message["type"] == "http.response.start":
            assert (
                not self.__response_started
            ), 'Received multiple "http.response.start" messages.'
            self._response = Response(
                self.url,
                status_code=message["status"],
                headers=[(k.decode(), v.decode()) for k, v in message["headers"]],
            )
            self.__response_started = True
        elif message["type"] == "http.response.body":
            assert (
                self.__response_started
            ), 'Received "http.response.body" without "http.response.start".'
            assert (
                not self.__response_complete
            ), 'Received "http.response.body" after response completed.'
            self._response.content = message.get("body", b"")
            if not message.get("more_body", False):
                self.__response_complete = True

    async def _receive(self) -> Message:
        """ Mimic ASGI receive awaitable.
            TODO: Mimic Stream requests
        """
        return {"type": "http.request", "body": self._body, "more_body": False}

    async def get(self, url, **kwargs):
        return await self.send("GET", url, **kwargs)

    async def options(self, url, **kwargs):
        return await self.send("OPTIONS", url, **kwargs)

    async def head(self, url, **kwargs):
        return await self.send("HEAD", url, **kwargs)

    async def post(self, url, data=None, json=None, **kwargs):
        return await self.send("POST", url, data=data, json=json, **kwargs)

    async def put(self, url, data=None, **kwargs):
        return await self.send("PUT", url, data=data, **kwargs)

    async def delete(self, url, **kwargs):
        return await self.send("DELETE", url, **kwargs)

    async def patch(self, url, **kwargs):
        return await self.send("PATCH", url, **kwargs)

    async def ws_connect(self, url, subprotocols=None, **kwargs):
        return await self.send("GET", url, subprotocols=subprotocols, ws=True, **kwargs)

    def ws_session(self, url, subprotocols=None, **kwargs):
        return WsContextManager(
            self.send("GET", url, subprotocols=subprotocols, ws=True, **kwargs)
        )
