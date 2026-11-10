# Migration Story Template (current → roadmap → phases → target)

Use it for "show current state, then each phase, then the final state" requests, for any technology
(cloud migration, monolith to microservices, data platform, observability, network redesign). A worked
example is in `examples/monolith-to-microservices/build.py`.

## Page order

| # | Page | Purpose |
|---|------|---------|
| 0 | Cover | Title, subtitle, contents line (dark background, single accent bar) |
| 1 | Current state | Faithful, cleaned-up recreation of the as-is diagram. Its why panel says why change |
| 2 | Roadmap at a glance | One chevron per phase. For each, a card with ADDS / MOVES / RETIRES / EXIT GATE, plus a guiding-principles panel |
| 3..N | Phase k | Same shared layout every time. Only the statuses change |
| last | Target state | Clean end-state layout (its own layout), outcome cards, and why it's the end state |

## Shared phase layout (the key to readable phases)

Draw every phase page on **one fixed layout**, using horizontal bands:

- **Left:** clients or sources, which span all bands.
- **Top band:** the legacy platform.
- **Lower band:** the new platform (green tint), with a Kubernetes zone for stateless tiers where relevant.
- An optional third band for a second legacy pipeline.
- **Right:** shared services (for example operations or monitoring) that each band reaches with straight lines.

Bridges between old and new run vertically in the gap between bands, or in a channel beside the data
column. Examples are a gateway still routing some paths to the legacy app, or a data-sync link from an
old database to a new one.

Define `NODES` and `EDGES` once (coordinates and routes), then build each phase from two dicts:
`nodes = {key: status}` and `edges = {key: status}`. Leave a key out to mean the component is gone. See
`page()` in `examples/monolith-to-microservices/build.py`.

## Status rules per phase

| Status | Use for |
|--------|---------|
| `new` | Added in this phase only. In later phases it becomes `existing` |
| `modified` | Re-pointed or reconfigured in this phase (for example a load balancer now points at the gateway) |
| `retire` | Switched off at the end of this phase (red dashed + RETIRE tag). In the next phase it's removed from the page |
| removed | Not drawn at all, so the page visibly gets simpler |

Use a custom tag where it adds information, for example `tag='RETIRE AFTER DATA CUT-OVER'`.

## Default phasing logic (low-risk, enterprise)

1. **Parallel platform:** add the new stack and onboard new workloads only. Retire nothing.
2. **Lowest-risk component first:** the smallest, most standard or read-only piece.
3. **Biggest value or cost driver, in waves:** non-prod, then low, medium and critical workloads.
4. **Most critical function last:** for example payments or alerting, with a dual-run parity gate.
5. **Edge or agent changes last:** host by host, once every backend is proven.

Each phase states its **exit gate** (a measurable parity condition) in the why panel and on the roadmap card.

## Why-panel formula (every page)

3–5 bullets. Each bullet is a bold lead-in of 2–6 words followed by one plain sentence:

- **What and why now** (risk, value or cost logic)
- **How it avoids disruption** (parallel run, dual-write, gateway routing)
- **What it unlocks** (speed, resilience, savings)
- **Exit gate:** the measurable condition before moving on
