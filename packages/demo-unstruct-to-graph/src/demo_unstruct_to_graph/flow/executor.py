import asyncio
import logging
import re
from typing import Callable, cast

from surrealdb import Value

from kaig.db import DB

from .definitions import Flow, Output, Record

logger = logging.getLogger(__name__)

ALNUM_DASH_UNDERSCORE = re.compile(r"[0-9A-Za-z_-]+$")


class Executor:
    """
    Executor for executing flows. You need an instance of this.

    Full example in [./tests/flow_test.py](./tests/flow_test.py)
    """

    def __init__(self, db: DB):
        self.db: DB = db
        self._handlers: dict[str, Callable[[dict[str, Value]], None]] = {}
        self._stop: bool = False

    def stop(self):
        """
        Stop the executor. The will end the execution of the current flow and
        then break out of the loop.
        """
        self._stop = True

    def _register_handler(
        self, flow: Flow, handler: Callable[[dict[str, Value]], None]
    ):
        """
        Register a handler for a flow by inserting it into the database and
        registering it in the handlers dictionary.
        """
        logger.debug(f"Registering handler for {flow}")

        # Insert flow into database
        _ = self.db.sync_conn.query(
            "CREATE ONLY flow CONTENT $obj", {"obj": flow.model_dump()}
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
                "field": flow.output.field,
                "deps": cast(list[Value], flow.dependencies),
            },
            dict,
        )
        for candidate in candidates:
            # call flow handler for candidate
            if flow.name in self._handlers:
                try:
                    self._handlers[flow.name](candidate)  # pyright: ignore[reportUnknownArgumentType]
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
        output: dict[str, str],
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
            output (dict[str, str]): The output configuration (fields).
            dependencies (list[str] | None, optional): The dependencies of the flow. Defaults to None.
            priority (int, optional): The priority of the flow. Defaults to 1. The higher the priority, the earlier the flow will be executed.
        """

        def decorator(func: Callable[[Record], None]):
            flow = Flow(
                name=func.__name__,
                table=table,
                output=Output.model_validate(output),
                dependencies=dependencies or [],
                priority=priority,
            )
            self._register_handler(flow, func)
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
