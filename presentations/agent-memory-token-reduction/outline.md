Title: TBD

Description: Token cost is an issue, and companies are looking at solutions. One solution is using agent memory to avoid cold starts and reduce token waste when generating repeated answers.

## Slide Outline + Speaker Notes (15-min run)

### Slide 01 — Title (1 min)
**"Agent Memory: Cut Token Costs Without Cutting Corners"**
- Introduce yourself and the topic
- Tease the surprise announcement at the end

### Slide 02 — The Problem (2 min)
**"Agents forget everything. Every. Single. Time."**
- Cold Start Tax: agents re-fetch context on every invocation
- Redundant Tool Calls: same questions answered repeatedly
- Runaway Costs: token bills grow linearly with users & requests
- Frame the solution: not bigger context windows, but smarter memory

### Slide 03 — Use Cases (2 min)
**"What institutional memory unlocks"**
- Use case 1 — Building with institutional memory: an engineer kicks off a feature via Claude Code + a custom `create-prd` skill; the agent queries Spectron and surfaces how similar features were designed and shipped (patterns, decisions, caveats) instead of inferring from scratch
- Use case 2 — Troubleshooting without re-reading the world: a developer hits a gnarly bug; Spectron surfaces a near-identical issue another engineer debugged last week — root cause, fix path, and the files that mattered — so the LLM never re-reads hundreds of lines
- Tie-back: the same recall that cuts tokens also carries hard-won context from one engineer to the next

### Slide 04 — Data Model (3 min)
**"Storing Memory in SurrealDB"**
- Walk through the simplified `memory` table schema in SurrealQL
- Highlight: `content` (text), `embedding` (vector), `session_id`, `expires_at`
- Point out the MTREE vector index for fast cosine similarity search
- Mention that SurrealDB handles vectors, graph, and relational data in one engine

### Slide 05 — Architecture Comparison (4 min)
**"Cold Start vs. Memory-Enabled Agent"**
- Left column: cold-start agent makes 2 redundant tool calls before generating answer → ~4,200 tokens
- Right column: memory-enabled agent does 1 memory.retrieve() → 1 answer tool call → ~1,100 tokens
- Both connect to SurrealDB (sidecar), but left agent's lines go "behind" the right
- Key takeaway: 74% fewer tokens with the same quality output

### Slide 06 — Memory Write-Back (3 min)
**"After the Run: Storing Context Back"**
- Show the 5-step cycle: Request → Retrieve → Execute → Distill → Store
- Emphasize the feedback loop: each run enriches memory for the next
- Memory compounds over time — the agent gets smarter (and cheaper) with every interaction

### Slide 07 — Close / Spectron Launch (1 min)
**"Introducing Spectron"**
- Coincidentally, today Wednesday June 3rd we are launching Spectron:
  memory and knowledge layer for AI agents, built on SurrealDB
- Zero cold starts, semantic retrieval, works with any agent framework

### Slide 08 — CTAs (1 min)
- Follow on LinkedIn: linkedin.com/in/martinschaer
- Learn more about Spectron and SurrealDB: surrealdb.com
- Join the newsletter: surrealdb.com/newsletter
- Read the blog: surrealdb.com/blog
- Thank you + open for questions
