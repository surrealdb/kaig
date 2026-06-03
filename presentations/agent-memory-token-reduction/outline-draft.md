Description: Token cost is an issue, and companies are looking at solutions. One solution is using agent memory to avoid cold starts and reduce token waste when generating repeated answers.

Slides:
- show a `file` table schema (kaig-app/migrations/V5__files.surql simplify without owner, flow_*, and anything not relevant for a minimal example)
- a side-by-side comparison of an agent starting with an empty memory and using tool calling to build its context, and another agent using a memory toolkit to retrieve from the memory the context. Both agents, after building their context, execute a few more tool calls to generate an answer. All tool calls are connected with dotted lines to SurrealDB (sitting as a sidecar a the far right of the slide). The dotted lines from the left agent column to SurrealDB should go behind the other agent, which is connected to SurrealDB by the same lines.
- a diagram showing how the agent execution ends by storing relevant context in the memory

Close: Coincidentally, today Wednesday 3rd of June, we are launching Spectron: memory and knowledge layer for AI agents.
