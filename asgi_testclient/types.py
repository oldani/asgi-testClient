from typing import *


Scope = Dict[str, Any]
Message = Dict[str, Any]
Receive = Callable[[], Awaitable[Message]]
Send = Callable[[Dict[str, Any]], Awaitable[None]]


ASGIInstance = Callable[[Receive, Send], Awaitable[None]]
ASGI2App = Callable[[Scope], ASGIInstance]
ASGI3App = Callable[[Scope, Receive, Send], Awaitable[None]]

Headers = Union[Dict[str, str], List[Tuple[str, str]]]
ReqHeaders = List[Tuple[bytes, bytes]]
ResHeaders = List[Tuple[str, str]]
Params = Union[Dict[str, str], List[Tuple[str, str]]]
Url = Tuple[str, str, int, str, bytes]
