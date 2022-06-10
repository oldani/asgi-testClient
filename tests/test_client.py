import pytest
from starlette.applications import Starlette
from starlette.responses import JSONResponse, PlainTextResponse, StreamingResponse

from asgi_testclient import TestClient, HTTPError
from asgi_testclient.client import Response


app = Starlette()


@app.route("/", methods=["GET", "DELETE"])
async def index(request):
    return JSONResponse({"hello": "world"})


@app.route("/text")
async def text(request):
    return PlainTextResponse("testing content")


@app.route("/headers")
async def headers(request):
    return JSONResponse(request.headers.items())


@app.route("/args")
async def args(request):
    response = request.query_params._dict  # query_params save values in internal _dict
    _list = request.query_params.get("list")
    if _list:  # Test passing same query arg with multiple values
        response = request.query_params.getlist(_list)
    return JSONResponse(response)


@app.route("/json", methods=["POST", "PUT", "PATCH"])
async def json(request):
    return JSONResponse(await request.json())


@app.route("/data", methods=["POST", "PUT", "PATCH"])
async def data(request):
    form = await request.form()
    return JSONResponse(form._dict)  # form save values in internal _dict


@app.route("/stream")
async def strem(request):
    async def gen():
        for s in "=" * 10:
            yield s

    return StreamingResponse(gen())


@app.route("/server")
async def server(request):
    return JSONResponse({"hello": "world"}, status_code=501)


@pytest.fixture
def client():
    return TestClient(app)


async def test_headers(client):
    headers = [["X-Token", "test-token"]]
    response = await client.get("/headers", headers=headers)
    response = dict(response.json())

    assert headers[0][0] in response
    assert headers[0][1] in response.values()

    response = await client.get("/headers", headers=dict(headers))
    response = dict(response.json())

    assert headers[0][0] in response
    assert headers[0][1] in response.values()


async def test_invalid_headers(client):
    headers = "no upported"
    with pytest.raises(ValueError):
        await client.get("/headers", headers=headers)


async def test_get(client):
    response = await client.get("http://test")
    assert response.json() == {"hello": "world"}


async def test_delete(client):
    response = await client.delete("/")
    assert response.json() == {"hello": "world"}


async def test_get_text(client):
    response = await client.get("/text")
    assert response.text == "testing content"


async def test_get_content(client):
    response = await client.get("/stream")
    assert response.content == (b"=" * 10)


async def test_get_args(client):
    params = {"name": "test", "age": "1", "space": " str"}
    response = await client.get("/args", params=params)
    assert response.json() == params

    response = await client.get("/args?name=test2&list=name", params=params)
    assert response.json() == ["test2", "test"]


async def test_post_json(client):
    json = {"user": "test", "age": "1", "pass": "123456"}
    response = await client.post("/json", json=json)
    assert response.json() == json


async def test_post_data(client):
    data = {"user": "test", "age": "1", "pass": "123456"}
    response = await client.post("/data", data=data)
    assert response.json() == data


async def test_put_json(client):
    json = {"user": "test", "age": "1", "pass": "123456"}
    response = await client.put("/json", json=json)
    assert response.json() == json


async def test_patch_json(client):
    json = {"user": "test", "age": "1", "pass": "123456"}
    response = await client.patch("/json", json=json)
    assert response.json() == json


async def test_response_ok(client):
    response = await client.get("/")
    assert response.ok

    response = await client.get("/notfound")
    assert not response.ok


async def test_response_raise_for(client):
    response = await client.get("/notfound")

    with pytest.raises(HTTPError):
        assert not response.raise_for_status()

    response = await client.get("/server")

    with pytest.raises(HTTPError):
        assert not response.raise_for_status()


async def test_response_str(client):
    response = await client.get("/")
    assert str(response) == "<Response [200]>"


def test_response_invalid_json():
    respose = Response("url", 200, [])
    respose.content = b")(_)(_*)(_*9"

    with pytest.raises(ValueError):
        respose.json()


async def test_client_raise():
    @app.route("/app/error")
    def error(request):
        raise ValueError("error")

    client = TestClient(app, raise_server_exceptions=True)

    with pytest.raises(ValueError):
        await client.get("/app/error")


async def test_client_bad_scheme(client):

    with pytest.raises(ValueError):
        await client.get("noscheme/")


async def test_client_bad_netloc():

    client = TestClient(app, base_url="http:netloc")
    with pytest.raises(ValueError):
        await client.get("/nonetloc")
