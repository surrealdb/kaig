import dataclasses
import logging
from typing import TypeVar

from surrealdb import BlockingHttpSurrealConnection, BlockingWsSurrealConnection

from kaig.db.definitions import Object

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
) -> list[Object] | Object | None:
    try:
        response = client.query(query, vars)  # pyright: ignore[reportUnknownMemberType]
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
            return [
                getattr(record_type, "from_dict").__call__(x) for x in response
            ]
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
            return getattr(record_type, "from_dict").__call__(response)
        else:
            try:
                return record_type(**response)
            except Exception as e:
                print(f"Error creating record: {e}. Response: {response}")
                raise e
    else:
        raise TypeError(f"Unexpected response type: {type(response)}")
