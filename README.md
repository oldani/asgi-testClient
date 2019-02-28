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

The client replicates the requests API, so if you have used request you should feel comfortable.

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

I have used `pytest` in this example but you can use whichever runner you prefer. *Note:* the client method are coroutines `get, post, delete, put, patch, etc..`.

## TODO:
- [ ] Support Websockets client.
- [ ] Cookies support.
- [ ] Redirects.
- [ ] Support files encoding
- [ ] Stream request & response


## Credits

- `Tom Christie`: I brought inspiration from the `starlette` test client.
- `Kenneth ☤ Reitz`: This package tries to replicate `requests` API.