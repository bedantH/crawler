from google.protobuf.internal import containers as _containers
from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from collections.abc import Iterable as _Iterable
from typing import ClassVar as _ClassVar, Optional as _Optional

DESCRIPTOR: _descriptor.FileDescriptor

class FrontierRequest(_message.Message):
    __slots__ = ("url", "depth", "crawl_id")
    URL_FIELD_NUMBER: _ClassVar[int]
    DEPTH_FIELD_NUMBER: _ClassVar[int]
    CRAWL_ID_FIELD_NUMBER: _ClassVar[int]
    url: _containers.RepeatedScalarFieldContainer[str]
    depth: int
    crawl_id: str
    def __init__(self, url: _Optional[_Iterable[str]] = ..., depth: _Optional[int] = ..., crawl_id: _Optional[str] = ...) -> None: ...

class FrontierResponse(_message.Message):
    __slots__ = ("status",)
    STATUS_FIELD_NUMBER: _ClassVar[int]
    status: str
    def __init__(self, status: _Optional[str] = ...) -> None: ...
