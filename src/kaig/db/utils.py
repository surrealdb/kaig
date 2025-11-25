import dataclasses
import logging
from typing import TypeVar, cast

from surrealdb import (
    BlockingHttpSurrealConnection,
    BlockingWsSurrealConnection,
    Value,
)

from .definitions import Object

RecordType = TypeVar("RecordType")


logger = logging.getLogger(__name__)


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
        elif isinstance(response, dict):
            try:
                return record_type(**response)
            except Exception as e:
                print(f"Error creating record: {e}. Response: {response}")
                raise e

    raise TypeError(f"Unexpected response type: {type(response)}")
