import asyncio
import hashlib
import inspect
import logging
import re
import textwrap
from collections.abc import Callable
from types import CodeType
from typing import Protocol, cast, runtime_checkable

from surrealdb import RecordID, Value

from kaig.db import DB

from .definitions import Flow, Record

logger = logging.getLogger(__name__)

ALNUM_DASH_UNDERSCORE = re.compile(r"[0-9A-Za-z_-]+$")

# TODO: make functions async
FlowHandler = Callable[[Record, str], None]


@runtime_checkable
class _HasCode(Protocol):
    __code__: CodeType


def stable_func_hash(func: Callable[..., object]) -> str:
    """
    Return a stable hash for a function's behavior.

    This intentionally ignores whitespace/comments/docstring-only edits by
    hashing the compiled code object rather than source text. Identical
    function bodies in different places can share the same hash.
    """
    # Prefer code-object hashing so non-semantic source edits don't count.
    if not isinstance(func, _HasCode):
        # Fallback for unusual callables; best-effort source hashing.
        src = inspect.getsource(func)
        src = textwrap.dedent(src).strip()
        return hashlib.blake2s(src.encode("utf-8"), digest_size=16).hexdigest()

    code = func.__code__

    # We avoid hashing file/line metadata (co_filename / co_firstlineno) so the
    # same function body can share the same hash across locations.
    #
    # NOTE: We use repr(...) for stable, deterministic serialization.
    parts: tuple[bytes, ...] = (
        code.co_code,
        repr(cast(object, code.co_consts)).encode("utf-8"),
        repr(cast(object, code.co_names)).encode("utf-8"),
        repr(cast(object, code.co_varnames)).encode("utf-8"),
        repr(cast(object, code.co_freevars)).encode("utf-8"),
        repr(cast(object, code.co_cellvars)).encode("utf-8"),
        repr(cast(object, code.co_flags)).encode("utf-8"),
        repr(cast(object, code.co_argcount)).encode("utf-8"),
        repr(cast(object, code.co_posonlyargcount)).encode("utf-8"),
        repr(cast(object, code.co_kwonlyargcount)).encode("utf-8"),
        repr(cast(object, code.co_nlocals)).encode("utf-8"),
        repr(cast(object, code.co_stacksize)).encode("utf-8"),
    )

    h = hashlib.blake2s(digest_size=16)
    for p in parts:
        h.update(p)
    return h.hexdigest()


class Executor:
    """
    Executor for executing flows. You need an instance of this.

    Full example in [./tests/flow_test.py](./tests/flow_test.py)
    """

    def __init__(self, db: DB):
        self.db: DB = db
        self._handlers: dict[str, FlowHandler] = {}
        self._stop: bool = False

    def stop(self):
        """
        Stop the executor. The will end the execution of the current flow and
        then break out of the loop.
        """
        self._stop = True

    def _register_handler(self, flow: Flow, handler: FlowHandler):
        """
        Register a handler for a flow by inserting it into the database and
        registering it in the handlers dictionary.
        """
        logger.debug(f"Registering handler for {flow}")

        # Insert flow into database
        _ = self.db.sync_conn.query(
            "UPSERT ONLY type::thing('flow', $name) CONTENT $obj",
            {"name": flow.name, "obj": flow.model_dump()},
        )

        # Register handler
        self._handlers[flow.name] = handler

    def execute_flows_once(self) -> dict[str, int]:
        """
        Execute all registered flows and return a dictionary of results, where
        the key is the flow name and the value is the number of records
        processed. The loop will break between executing flows if the executor
        is stopped.
        """
        results: dict[str, int] = {}
        flows = self.db.query(
            "SELECT * FROM flow ORDER BY priority DESC", {}, Flow
        )
        for flow in flows:
            if flow.name not in results:
                results[flow.name] = 0
            results[flow.name] += self.execute_flow(flow)
            if self._stop:
                break

        return results

    def execute_flow(self, flow: Flow) -> int:
        """
        Execute a flow and return the number of records processed. The loop will
        break between handling candidates if the executor is stopped.
        """
        count = 0

        # Find candidate records that fulfill the flow dependencies
        candidates = self.db.query(
            """SELECT * FROM type::table($table)
                WHERE type::field($field) IS NONE
                AND NONE NOT IN $deps.map(|$x| type::field($x))
            """,
            {
                "table": flow.table,
                "field": flow.stamp,
                "deps": cast(list[Value], flow.dependencies),
            },
            dict,
        )
        for candidate in candidates:
            # call flow handler for candidate
            if flow.name in self._handlers:
                try:
                    self._handlers[flow.name](candidate, flow.hash)  # pyright: ignore[reportUnknownArgumentType]
                    count += 1
                except Exception as e:
                    logger.error(f"Error executing flow '{flow.name}': {e}")
            else:
                logger.error(f"No handler registered for flow '{flow.name}'")
            if self._stop:
                break
        return count

    def flow(
        self,
        table: str,
        stamp: str,
        dependencies: list[str] | None = None,
        priority: int = 1,
    ):
        """
        Decorator to register a flow handler.

        Important: make sure your handler updates the record by setting its
        output field to prevent it from being processed again. The flow executor
        checks for this field to determine if the record has already been
        processed.

        Args:
            table (str): The table to query for candidate records.
            output (Output): The output configuration.
            dependencies (list[str] | None, optional): The dependencies of the flow. Defaults to None.
            priority (int, optional): The priority of the flow. Defaults to 1. The higher the priority, the earlier the flow will be executed.
        """

        def decorator(func: FlowHandler):
            flow = Flow(
                id=RecordID("flow", func.__name__),
                table=table,
                stamp=stamp,
                dependencies=dependencies or [],
                priority=priority,
                hash=stable_func_hash(func),
            )
            try:
                self._register_handler(flow, func)
            except Exception as e:
                logger.error(f"Error registering flow {flow.id}: {e}")
            return func

        return decorator

    async def run(
        self,
        delay_in_s: float = 1,
        max_delay_in_s: float = 60,
    ) -> None:
        """
        Run the flow executor.

        It will execute flows in the order of their priority, and will
        wait for a delay between executions if no records were processed.
        Exponential backoff is used to increase the delay between executions.

        Args:
            delay_in_s (float, optional): The initial delay between executions. Defaults to 1.
            max_delay_in_s (float, optional): The maximum delay between executions. Defaults to 60.
        """
        delay = delay_in_s
        while True:
            results = self.execute_flows_once()
            logger.info(f"Executed flows: {results}")
            if self._stop:
                break

            # exponential backoff if no records where processed
            if not sum(results.values()):
                await asyncio.sleep(delay)
                delay *= 2
                delay = min(delay, max_delay_in_s)
                continue
            else:
                delay = delay_in_s

            await asyncio.sleep(delay)
            # check if we need to stop before and after the delay
            if self._stop:
                break
