# Agent Memory: Cut Token Costs Without Cutting Corners

A [reveal.js](https://revealjs.com) deck on using agent memory in SurrealDB to
eliminate cold-start token waste — closing with the **Spectron** launch.

## Run

```bash
bun run dev      # serves on http://localhost:8000
```

Or open `index.html` directly (the deck loads reveal.js + fonts from CDN, so an
internet connection is needed for first paint; navigation works offline once
loaded).

## Structure

| File | Purpose |
| --- | --- |
| `index.html` | The deck — 7 slides |
| `css/theme.css` | Design system (colors, type) from `../design.md` |
| `css/diagrams.css` | Architecture-comparison & write-back-cycle diagrams |
| `outline.md` | Slide outline + speaker notes |
| `outline-draft.md` | Diagram ideas + `file` schema source |

## Slides

1. Title
2. The Problem — cold-start tax, redundant calls, runaway cost
3. Data Model — the `file` table (SurrealQL) + MTREE vector index
4. Architecture — cold-start vs. memory-enabled agent, both wired to a SurrealDB sidecar
5. Write-Back — the 5-step memory cycle
6. Spectron launch
7. CTAs

## Controls

`→ / Space` next · `←` back · `Esc` overview · `F` fullscreen · `S` speaker notes
