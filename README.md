# asgi-testClient
![Travis (.org)](https://img.shields.io/travis/oldani/asgi-testClient.svg)
![PyPI - Python Version](https://img.shields.io/pypi/pyversions/asgi-testClient.svg)
![PyPI](https://img.shields.io/pypi/v/asgi-testClient.svg)
[![codecov](https://codecov.io/gh/oldani/asgi-testClient/branch/master/graph/badge.svg)](https://codecov.io/gh/oldani/asgi-testClient)
![PyPI - Downloads](https://img.shields.io/pypi/dm/asgi-testClient.svg)
[![black](https://img.shields.io/badge/code_style-black-000000.svg)](https://github.com/ambv/black)

Testing ASGI applications made easy!


## The why?

**Why** would you build this when all web frameworks come with one? Well, because mostly all those web frameworks have to build their own. I was building my own web framework perhaps (research & learning purpose) and got to the point where a needed a `TestClient` but then a asked my self **why does anybody building web frameworks have to build their own TestClient when there's a standard?**. Ok, then just install `starlette` a use it test client; would you install a library just to use a tiny part of it? **This client does not have any dependencies**.

## Requirements

`Python 3.6+`

It should run on Python 3.5 but I haven' tested it.

## Installation

`pip install asgi-testclient`


## Usage

The client replicates the requests API, so if you have used request you should feel comfortable. **Note:** the client method are coroutines `get, post, delete, put, patch, etc..`.

```python
import pytest
from asgi_testclient import TestClient

from myapp import API

@pytest.fixture
def client():
    return TestClient(API)

@pytest.mark.asyncio
async def test_get(client):
    response = await client.get("/")
    assert response.json() == {"hello": "world"}
    assert response.status_code == 200
```

I have used `pytest` in this example but you can use whichever runner you prefer.

If you still prefer simple functions to coroutines, you can use the sync interface:

```python
import pytest
from asgi_testclient.sync import TestClient

@pytest.fixture
def client():
    return TestClient(API)

def test_get(client):
    response = client.get("/")
    assert response.json() == {"hello": "world"}
    assert response.status_code == 200
```

**Take in account that if you're running inside an async app you should use the async client, yet you can run the sync one inside threads is still desired.**


## Websockets

If you're using ASGI you may be doing some web-sockets stuff. We have added support for it also, so you can test it easy.

```python
from asgi_testclient import TestClient
from myapp import API

async def test_send():
    echo_server = TestClient(API)
    websocket = await echo_server.ws_connect("/")
    for msg in ["Hey", "Echo", "Back"]:
        await websocket.send_text(msg)
        data = await websocket.receive_text()
        assert data == msg
    await websocket.close()

async def test_ws_context():
    client = TestClient(API)
    async with client.ws_session("/") as websocket:
        data = await websocket.receive_text()
        assert data == "Hello, world!"
```

Few things to take in count here:
1. When using `ws_connect` you must call `websocket.close()` to finish up your APP task.
2. For using websockets in context manager you must use `ws_session` instead of `ws_connect`.
3. When waiting on server response `websocker.receive_*` it may raise a `WsDisconnect`.

And one more time for those who don't want to this async we got the sync version:p

```python
from asgi_testclient.sync import TestClient
from myapp import API

client = TestClient(API)

def test_send_receive_json():
    websocket = client.ws_connect("/json")

    json_msg = {"hello": "test"}
    websocket.send_json(json_msg)

    assert websocket.receive_json() == json_msg
    websocket.close()

def test_ws_context():
    with client.ws_session("/") as websocket:
        data = websocket.receive_text()
        assert data == "Hello, world!"
```

**Important:** In the sync version you cannot use `send` or `receive` since they're coroutines, instead use their children `send_*` or `receive_*` `text|bytes|json`.

Also sync version is done throw `monkey patching` so you can't use both version `async & sync` at the same time.

## TODO:
- [x] Support Websockets client.
- [ ] Cookies support.
- [ ] Redirects.
- [ ] Support files encoding
- [ ] Stream request & response


## Credits

- `Tom Christie`: I brought inspiration from the `starlette` test client.
- `Kenneth ☤ Reitz`: This package tries to replicate `requests` API.