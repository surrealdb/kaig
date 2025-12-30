import logging
from typing import Callable

from surrealdb import Value

from kaig.db import DB

from .definitions import Flow, Output, Record

logger = logging.getLogger(__name__)


class Executor:
    def __init__(self, db: DB):
        self.db: DB = db
        self._handlers: dict[str, Callable[[dict[str, Value]], None]] = {}

    def register_handler(
        self, flow: Flow, handler: Callable[[dict[str, Value]], None]
    ):
        print(flow.model_dump())
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
        processed.
        """
        results: dict[str, int] = {}
        flows = self.db.query(
            "SELECT * FROM flow ORDER BY priority DESC", {}, Flow
        )
        for flow in flows:
            if flow.name not in results:
                results[flow.name] = 0
            results[flow.name] += self.execute_flow(flow)

        return results

    def execute_flow(self, flow: Flow) -> int:
        count = 0
        # Find candidate records that fulfill the flow dependencies
        candidates = self.db.query(
            f"""SELECT * FROM {flow.table}
                WHERE {flow.output.field} IS NONE
                AND NONE NOT IN [{",".join(map(str, flow.dependencies))}]
            """,
            {},
            dict,
        )
        for candidate in candidates:
            # call flow handler for candidate
            if flow.name in self._handlers:
                self._handlers[flow.name](candidate)  # pyright: ignore[reportUnknownArgumentType]
                count += 1
            else:
                logger.error(f"No handler registered for flow '{flow.name}'")
        return count

    def flow(
        self,
        table: str,
        output: dict[str, str],
        dependencies: list[str] | None = None,
        priority: int = 1,
    ):
        def decorator(func: Callable[[Record], None]):
            flow = Flow(
                name=func.__name__,
                table=table,
                output=Output.model_validate(output),
                dependencies=dependencies or [],
                priority=priority,
            )
            self.register_handler(flow, func)
            return func

        return decorator
