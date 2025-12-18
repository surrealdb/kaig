import dataclasses
import logging
import types
import typing
from typing import Any, TypeVar, cast, get_args, get_origin, get_type_hints

from surrealdb import (
    BlockingHttpSurrealConnection,
    BlockingWsSurrealConnection,
    Value,
)

from ..definitions import Object

RecordType = TypeVar("RecordType")


logger = logging.getLogger(__name__)


def _coerce_value(value: Any, target_type: Any) -> Any:  # pyright: ignore[reportExplicitAny, reportAny]
    """Recursively coerce SurrealDB-returned values (dict/list) into typed values.

    Intended primarily for nested dataclass graphs (e.g. dict -> dataclass, list[dataclass], etc.).
    """
    if target_type is Any or target_type is object:
        return value  # pyright: ignore[reportAny]

    if value is None:
        return None

    origin = get_origin(target_type)  # pyright: ignore[reportAny]
    args = get_args(target_type)

    # Optional[T] / Union[...]
    if target_type is None or target_type is type(None):
        return None
    if origin in (typing.Union, types.UnionType):  # pyright: ignore[reportDeprecated]
        # Best-effort: try each option and return the first successful conversion.
        for opt in args:  # pyright: ignore[reportAny]
            if opt is type(None):  # noqa: E721
                continue
            try:
                return _coerce_value(value, opt)  # pyright: ignore[reportAny]
            except Exception:
                continue
        return value  # pyright: ignore[reportAny]

    # dataclass types
    if isinstance(target_type, type) and dataclasses.is_dataclass(target_type):
        if isinstance(value, target_type):
            return value
        if isinstance(value, dict):
            return _coerce_dataclass(value, target_type)  # pyright: ignore[reportAny, reportUnknownArgumentType]
        return value  # pyright: ignore[reportAny]

    # Containers
    if origin in (list, tuple, set):
        inner_t = args[0] if len(args) >= 1 else Any
        if isinstance(value, list):
            coerced_list = [_coerce_value(v, inner_t) for v in value]  # pyright: ignore[reportUnknownVariableType]
            if origin is tuple:
                return tuple(coerced_list)
            if origin is set:
                return set(coerced_list)
            return coerced_list
        return value  # pyright: ignore[reportAny]

    if origin is dict:
        key_t, val_t = args if len(args) == 2 else (Any, Any)
        if isinstance(value, dict):
            return {
                _coerce_value(k, key_t): _coerce_value(v, val_t)
                for k, v in value.items()  # pyright: ignore[reportUnknownVariableType]
            }
        return value  # pyright: ignore[reportAny]

    # Primitive / passthrough
    if isinstance(target_type, type) and isinstance(value, target_type):
        return value  # pyright: ignore[reportAny]
    return value  # pyright: ignore[reportAny]


def _coerce_dataclass(data: dict[str, Any], cls: type[Any]) -> Any:  # pyright: ignore[reportExplicitAny, reportAny]
    """Build dataclass `cls` from dict `data`, recursively coercing nested fields."""
    type_hints = get_type_hints(cls)
    kwargs: dict[str, Any] = {}  # pyright: ignore[reportExplicitAny]
    for field in dataclasses.fields(cls):
        name = field.name
        if name not in data:
            continue
        kwargs[name] = _coerce_value(data[name], type_hints.get(name, Any))
    return cls(**kwargs)  # pyright: ignore[reportAny]


def parse_time(time: str) -> float:
    r"""
    Examples:
    - "123.456µs" => 0.123456
    - "1.939083ms" => 1.939083
    - "1ms" => 1
    - "1.2345s" => 1234.5
    """
    import re

    regex = re.compile(r"(\d+\.?\d*)s")
    match = regex.match(time)
    if match:
        return float(match.group(1)) * 1000
    regex = re.compile(r"(\d+\.?\d*)ms")
    match = regex.match(time)
    if match:
        return float(match.group(1))
    regex = re.compile(r"(\d+\.?\d*)µs")
    match = regex.match(time)
    if match:
        return float(match.group(1)) / 1000
    raise ValueError(f"Invalid time format: {time}")


def _query_aux(
    client: BlockingWsSurrealConnection | BlockingHttpSurrealConnection,
    query: str,
    vars: Object,
) -> Value:
    try:
        response = client.query(query, cast(dict[str, Value], vars))
        logger.debug(f"Query: {query} with {vars}, Response: {response}")
    except Exception as e:
        logger.error(f"Query execution error: {query} with {vars}, Error: {e}")
        raise e
    return response


def query(
    client: BlockingWsSurrealConnection | BlockingHttpSurrealConnection,
    query: str,
    vars: Object,
    record_type: type[RecordType],
) -> list[RecordType]:
    response = _query_aux(client, query, vars)
    if isinstance(response, list):
        if dataclasses.is_dataclass(record_type) and hasattr(
            record_type, "from_dict"
        ):
            cast_fn = getattr(record_type, "from_dict")  # pyright: ignore[reportAny]
            casted: list[RecordType] = [cast_fn.__call__(x) for x in response]  # pyright: ignore[reportAny]
            assert all(isinstance(x, record_type) for x in casted)
            return casted
        if dataclasses.is_dataclass(record_type):
            casted = [_coerce_value(x, record_type) for x in response]
            assert all(isinstance(x, record_type) for x in casted)
            # return cast(list[RecordType], casted)
            return casted
        else:
            return [record_type(**x) for x in response]
    else:
        raise TypeError(f"Unexpected response type: {type(response)}")


def query_one(
    client: BlockingWsSurrealConnection | BlockingHttpSurrealConnection,
    query: str,
    vars: Object,
    record_type: type[RecordType],
) -> RecordType | None:
    response = _query_aux(client, query, vars)
    if response is None:
        return None
    elif not isinstance(response, list):
        if dataclasses.is_dataclass(record_type) and hasattr(
            record_type, "from_dict"
        ):
            casted = getattr(record_type, "from_dict").__call__(response)  # pyright: ignore[reportAny]
            assert isinstance(casted, record_type)
            return casted
        if dataclasses.is_dataclass(record_type) and isinstance(response, dict):
            casted = _coerce_value(response, record_type)  # pyright: ignore[reportAny]
            assert isinstance(casted, record_type)
            return casted
        elif isinstance(response, dict):
            try:
                return record_type(**response)
            except Exception as e:
                print(f"Error creating record: {e}. Response: {response}")
                raise e

    raise TypeError(f"Unexpected response type: {type(response)}")
