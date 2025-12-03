from google.protobuf.internal import containers as _containers
from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from collections.abc import Iterable as _Iterable
from typing import ClassVar as _ClassVar, Optional as _Optional

DESCRIPTOR: _descriptor.FileDescriptor

class HeartbeatRequest(_message.Message):
    __slots__ = ("timestamp",)
    TIMESTAMP_FIELD_NUMBER: _ClassVar[int]
    timestamp: int
    def __init__(self, timestamp: _Optional[int] = ...) -> None: ...

class HeartbeatResponse(_message.Message):
    __slots__ = ("worker_id", "current_task_count", "status", "in_progress_task_ids")
    WORKER_ID_FIELD_NUMBER: _ClassVar[int]
    CURRENT_TASK_COUNT_FIELD_NUMBER: _ClassVar[int]
    STATUS_FIELD_NUMBER: _ClassVar[int]
    IN_PROGRESS_TASK_IDS_FIELD_NUMBER: _ClassVar[int]
    worker_id: str
    current_task_count: int
    status: str
    in_progress_task_ids: _containers.RepeatedScalarFieldContainer[str]
    def __init__(self, worker_id: _Optional[str] = ..., current_task_count: _Optional[int] = ..., status: _Optional[str] = ..., in_progress_task_ids: _Optional[_Iterable[str]] = ...) -> None: ...

class TaskUpdateRequest(_message.Message):
    __slots__ = ("worker_id", "task_id", "status", "url", "error_message", "timestamp")
    WORKER_ID_FIELD_NUMBER: _ClassVar[int]
    TASK_ID_FIELD_NUMBER: _ClassVar[int]
    STATUS_FIELD_NUMBER: _ClassVar[int]
    URL_FIELD_NUMBER: _ClassVar[int]
    ERROR_MESSAGE_FIELD_NUMBER: _ClassVar[int]
    TIMESTAMP_FIELD_NUMBER: _ClassVar[int]
    worker_id: str
    task_id: str
    status: str
    url: str
    error_message: str
    timestamp: int
    def __init__(self, worker_id: _Optional[str] = ..., task_id: _Optional[str] = ..., status: _Optional[str] = ..., url: _Optional[str] = ..., error_message: _Optional[str] = ..., timestamp: _Optional[int] = ...) -> None: ...

class TaskUpdateResponse(_message.Message):
    __slots__ = ("acknowledged",)
    ACKNOWLEDGED_FIELD_NUMBER: _ClassVar[int]
    acknowledged: bool
    def __init__(self, acknowledged: bool = ...) -> None: ...

class WorkerStatusRequest(_message.Message):
    __slots__ = ("worker_id",)
    WORKER_ID_FIELD_NUMBER: _ClassVar[int]
    worker_id: str
    def __init__(self, worker_id: _Optional[str] = ...) -> None: ...

class WorkerStatusResponse(_message.Message):
    __slots__ = ("worker_id", "status", "last_heartbeat", "created_at", "current_task_count", "in_progress_task_ids")
    WORKER_ID_FIELD_NUMBER: _ClassVar[int]
    STATUS_FIELD_NUMBER: _ClassVar[int]
    LAST_HEARTBEAT_FIELD_NUMBER: _ClassVar[int]
    CREATED_AT_FIELD_NUMBER: _ClassVar[int]
    CURRENT_TASK_COUNT_FIELD_NUMBER: _ClassVar[int]
    IN_PROGRESS_TASK_IDS_FIELD_NUMBER: _ClassVar[int]
    worker_id: str
    status: str
    last_heartbeat: int
    created_at: int
    current_task_count: int
    in_progress_task_ids: _containers.RepeatedScalarFieldContainer[str]
    def __init__(self, worker_id: _Optional[str] = ..., status: _Optional[str] = ..., last_heartbeat: _Optional[int] = ..., created_at: _Optional[int] = ..., current_task_count: _Optional[int] = ..., in_progress_task_ids: _Optional[_Iterable[str]] = ...) -> None: ...
