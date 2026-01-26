from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from typing import ClassVar as _ClassVar, Optional as _Optional

DESCRIPTOR: _descriptor.FileDescriptor

class Key(_message.Message):
    __slots__ = ("key",)
    KEY_FIELD_NUMBER: _ClassVar[int]
    key: str
    def __init__(self, key: _Optional[str] = ...) -> None: ...

class KeyValue(_message.Message):
    __slots__ = ("key", "value")
    KEY_FIELD_NUMBER: _ClassVar[int]
    VALUE_FIELD_NUMBER: _ClassVar[int]
    key: str
    value: bytes
    def __init__(self, key: _Optional[str] = ..., value: _Optional[bytes] = ...) -> None: ...

class TopicConfig(_message.Message):
    __slots__ = ("topic", "size", "max_value_size")
    TOPIC_FIELD_NUMBER: _ClassVar[int]
    SIZE_FIELD_NUMBER: _ClassVar[int]
    MAX_VALUE_SIZE_FIELD_NUMBER: _ClassVar[int]
    topic: str
    size: int
    max_value_size: int
    def __init__(self, topic: _Optional[str] = ..., size: _Optional[int] = ..., max_value_size: _Optional[int] = ...) -> None: ...

class Topic(_message.Message):
    __slots__ = ("topic",)
    TOPIC_FIELD_NUMBER: _ClassVar[int]
    topic: str
    def __init__(self, topic: _Optional[str] = ...) -> None: ...

class ShutdownRequest(_message.Message):
    __slots__ = ("topic", "immediate")
    TOPIC_FIELD_NUMBER: _ClassVar[int]
    IMMEDIATE_FIELD_NUMBER: _ClassVar[int]
    topic: str
    immediate: bool
    def __init__(self, topic: _Optional[str] = ..., immediate: bool = ...) -> None: ...

class TopicValue(_message.Message):
    __slots__ = ("topic", "value")
    TOPIC_FIELD_NUMBER: _ClassVar[int]
    VALUE_FIELD_NUMBER: _ClassVar[int]
    topic: str
    value: bytes
    def __init__(self, topic: _Optional[str] = ..., value: _Optional[bytes] = ...) -> None: ...

class ValueOrNone(_message.Message):
    __slots__ = ("value", "is_none")
    VALUE_FIELD_NUMBER: _ClassVar[int]
    IS_NONE_FIELD_NUMBER: _ClassVar[int]
    value: bytes
    is_none: bool
    def __init__(self, value: _Optional[bytes] = ..., is_none: bool = ...) -> None: ...

class Value(_message.Message):
    __slots__ = ("value",)
    VALUE_FIELD_NUMBER: _ClassVar[int]
    value: bytes
    def __init__(self, value: _Optional[bytes] = ...) -> None: ...

class Bool(_message.Message):
    __slots__ = ("value",)
    VALUE_FIELD_NUMBER: _ClassVar[int]
    value: bool
    def __init__(self, value: bool = ...) -> None: ...

class Empty(_message.Message):
    __slots__ = ()
    def __init__(self) -> None: ...
