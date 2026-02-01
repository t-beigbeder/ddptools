from google.protobuf.internal import containers as _containers
from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from collections.abc import Iterable as _Iterable
from typing import ClassVar as _ClassVar, Optional as _Optional

DESCRIPTOR: _descriptor.FileDescriptor

class DropRequest(_message.Message):
    __slots__ = ("miss_ok",)
    MISS_OK_FIELD_NUMBER: _ClassVar[int]
    miss_ok: bool
    def __init__(self, miss_ok: bool = ...) -> None: ...

class CreateRequest(_message.Message):
    __slots__ = ("exist_ok", "drop", "ddl")
    EXIST_OK_FIELD_NUMBER: _ClassVar[int]
    DROP_FIELD_NUMBER: _ClassVar[int]
    DDL_FIELD_NUMBER: _ClassVar[int]
    exist_ok: bool
    drop: bool
    ddl: str
    def __init__(self, exist_ok: bool = ..., drop: bool = ..., ddl: _Optional[str] = ...) -> None: ...

class CreateCategoryRequest(_message.Message):
    __slots__ = ("label", "content")
    LABEL_FIELD_NUMBER: _ClassVar[int]
    CONTENT_FIELD_NUMBER: _ClassVar[int]
    label: str
    content: str
    def __init__(self, label: _Optional[str] = ..., content: _Optional[str] = ...) -> None: ...

class UUID(_message.Message):
    __slots__ = ("uuid",)
    UUID_FIELD_NUMBER: _ClassVar[int]
    uuid: str
    def __init__(self, uuid: _Optional[str] = ...) -> None: ...

class Entity(_message.Message):
    __slots__ = ("session_uuid", "category", "key", "content", "additional_content")
    SESSION_UUID_FIELD_NUMBER: _ClassVar[int]
    CATEGORY_FIELD_NUMBER: _ClassVar[int]
    KEY_FIELD_NUMBER: _ClassVar[int]
    CONTENT_FIELD_NUMBER: _ClassVar[int]
    ADDITIONAL_CONTENT_FIELD_NUMBER: _ClassVar[int]
    session_uuid: str
    category: str
    key: str
    content: bytes
    additional_content: bytes
    def __init__(self, session_uuid: _Optional[str] = ..., category: _Optional[str] = ..., key: _Optional[str] = ..., content: _Optional[bytes] = ..., additional_content: _Optional[bytes] = ...) -> None: ...

class ReadEntityRequest(_message.Message):
    __slots__ = ("category", "key", "with_additional_content")
    CATEGORY_FIELD_NUMBER: _ClassVar[int]
    KEY_FIELD_NUMBER: _ClassVar[int]
    WITH_ADDITIONAL_CONTENT_FIELD_NUMBER: _ClassVar[int]
    category: str
    key: str
    with_additional_content: bool
    def __init__(self, category: _Optional[str] = ..., key: _Optional[str] = ..., with_additional_content: bool = ...) -> None: ...

class ReadEntitiesRequest(_message.Message):
    __slots__ = ("category", "with_additional_content", "with_keys_only", "keys")
    CATEGORY_FIELD_NUMBER: _ClassVar[int]
    WITH_ADDITIONAL_CONTENT_FIELD_NUMBER: _ClassVar[int]
    WITH_KEYS_ONLY_FIELD_NUMBER: _ClassVar[int]
    KEYS_FIELD_NUMBER: _ClassVar[int]
    category: str
    with_additional_content: bool
    with_keys_only: bool
    keys: _containers.RepeatedScalarFieldContainer[str]
    def __init__(self, category: _Optional[str] = ..., with_additional_content: bool = ..., with_keys_only: bool = ..., keys: _Optional[_Iterable[str]] = ...) -> None: ...

class ReadEntityResponse(_message.Message):
    __slots__ = ("key", "content", "additional_content", "ct_ref")
    KEY_FIELD_NUMBER: _ClassVar[int]
    CONTENT_FIELD_NUMBER: _ClassVar[int]
    ADDITIONAL_CONTENT_FIELD_NUMBER: _ClassVar[int]
    CT_REF_FIELD_NUMBER: _ClassVar[int]
    key: str
    content: bytes
    additional_content: bytes
    ct_ref: str
    def __init__(self, key: _Optional[str] = ..., content: _Optional[bytes] = ..., additional_content: _Optional[bytes] = ..., ct_ref: _Optional[str] = ...) -> None: ...

class ReadSessionRequest(_message.Message):
    __slots__ = ("category", "with_additional_content", "with_keys_only")
    CATEGORY_FIELD_NUMBER: _ClassVar[int]
    WITH_ADDITIONAL_CONTENT_FIELD_NUMBER: _ClassVar[int]
    WITH_KEYS_ONLY_FIELD_NUMBER: _ClassVar[int]
    category: str
    with_additional_content: bool
    with_keys_only: bool
    def __init__(self, category: _Optional[str] = ..., with_additional_content: bool = ..., with_keys_only: bool = ...) -> None: ...

class Bool(_message.Message):
    __slots__ = ("value",)
    VALUE_FIELD_NUMBER: _ClassVar[int]
    value: bool
    def __init__(self, value: bool = ...) -> None: ...

class Empty(_message.Message):
    __slots__ = ()
    def __init__(self) -> None: ...
