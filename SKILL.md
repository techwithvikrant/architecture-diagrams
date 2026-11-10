---
name: architecture-diagrams
description: Create precise, customer-ready architecture diagrams as editable draw.io files plus PNG images and one combined PDF. Use this skill whenever the user wants to draw, recreate, clean up or redesign an architecture, data-flow, infrastructure, observability, network or deployment diagram; turn a screenshot or whiteboard photo of a diagram into a clean one; show current state vs target state; show a migration or modernization in phases (phase 1, phase 2 ... final); or build a roadmap or "as-is / to-be" deck for a customer, even if they only say "diagram", "draw this", "flow", "draw.io", "excalidraw" or "make it presentable".
---

# Architecture Diagrams (draw.io, presentation-grade)

Produces diagrams like a senior solutions architect would hand a customer: every arrow axis-aligned and
deliberately routed, no crossings, no text on lines, consistent colours that mean something, and a short
"why" panel on every slide. Output is always the full set:

| Deliverable | File |
| --- | --- |
| Editable source (all pages, native connected shapes) | `<Name>.drawio` |
| One image per page (2x, 3840x2160) | `PNG/NN_Page_Name.png` |
| Combined presentation (vector) | `<Name>.pdf` |

The engine is `scripts/drawio_lib.py`: you place boxes on an absolute 1920x1080 canvas and give every edge
explicit waypoints. A built-in geometry validator rejects crossings, arrows through boxes, overlapping
labels and off-canvas items. draw.io itself renders the PNG and PDF, so what the customer sees is exactly
what opens in their editor.

## Workflow (follow in order)

### 1. Set up (once per session, ~20 s)

```bash
bash <skill>/scripts/setup_drawio.sh
```

This puts the draw.io CLI at `/tmp/drawio-cli`. If the download is blocked, tell the user that the
container needs network access to github.com and cdn.jsdelivr.net.

### 2. Clarify before drawing

Read `references/clarifying-questions.md`. Ask **only** what you cannot infer from the request, the
screenshot or the conversation. Use `ask_user_input_v0` with at most 3 questions in one round, and skip
it entirely if everything is clear. Never ask about things that have a sensible default; state those
defaults in one line instead. The questions that most often matter:

- Which pages: current state only, target only, or the full story (current, roadmap, phases, target)?
- Anything unclear in the source: unreadable labels, arrows whose direction is ambiguous, components to drop.
- Customer name or branding on the cover, if the deck is customer-facing.

### 3. Inventory before layout

Write a plain list of every component and every flow (`A -> B : label`) from the source. For a
screenshot, go box by box and arrow by arrow, then re-check the image for anything missed, including
small text on arrows. "Recreate exactly" means every component and every flow survives; only the
layout gets cleaner.

### 4. Plan the layout on a grid, then route

Read `references/layout-playbook.md` before placing anything. In short:

1. **Columns by role, left to right in data-flow order**: sources, ingest/transport, processing,
   storage, visualization, access. Write the x-range of each lane.
2. **Rows by flow**: give each major flow its own y so that most edges are a single straight segment.
   Put a box's centre on the y of the flow that enters it, and make a box taller so it can accept
   several straight inputs.
3. **Order items inside a lane to match the order of their destinations.** This is what removes
   crossings. Where topology forces a crossing, use the playbook's fixes: nested elbows, a dedicated
   channel between lanes, a margin loop, or a separate band.
4. Use edge labels sparingly (2-3 words), placed 4 px or more above horizontal lines or beside vertical ones.

### 5. Write the build script

Create `/home/claude/<project>/build.py`. Start from `examples/monolith-to-microservices/build.py`,
a complete 5-page deck (cover, current, phase 1, phase 2, target) that works for any technology:
swap the boxes, icons and flows. The API is in `references/api.md`. Minimal shape:

```python
import sys; sys.path.insert(0, '<skill>/scripts')
from drawio_lib import Page, build

p = Page('cur', '1. Current State')                 # unique short id, tab name
p.header('Current State: Web Platform', 'As-is flow: ...')
p.legend([('existing', 'Existing component')])
p.lanes([(30, 300, 'CLIENTS'), (380, 490, 'APPLICATION')])
p.container('cApp', 30, 360, 300, 330, 'App servers')
p.node('app', 45, 478, 270, 44, 'Orders API', icon='openjdk')
p.node('db', 385, 470, 160, 60, 'PostgreSQL', icon='postgresql')
p.edge('e1', 'app', 'db', [(315, 500), (385, 500)])
p.label(350, 482, 'SQL')
p.why('Why change', ['<b>Point:</b> one-line reason', '...'])

build([p], out_dir='/mnt/user-data/outputs/<Project>', basename='<Project>_Architecture')
```

### 6. Build and fix until clean

Run `python3 build.py`. With `strict=True` (the default), the build stops on any **error**. Fix every
error by moving boxes or waypoints; don't silence them. Read every **warning**: text-wrap warnings are
fine if the render looks good, but fix any that show clipped or crowded text.

### 7. Look at every page (mandatory)

Open `/tmp/diagram-review/contact_sheet.png`, then each `/tmp/diagram-review/page_NN.png`, with the
`view` tool. Check it against the list below. Fix, rebuild and look again. Two passes are normal.

- [ ] Every component and flow from the inventory is present, with the correct arrow direction.
- [ ] No text overflows a box or touches a border; no label sits on a line or box.
- [ ] Nothing crosses; parallel lines are at least 12 px apart; arrows enter boxes cleanly.
- [ ] The colours match the legend; retired items are red dashed, new items green.
- [ ] Each "why" panel has 3-5 bullets, each a bold lead-in plus one plain sentence.
- [ ] Titles state the point ("Phase 2: Move Orders, Retire the Monolith"), not a topic ("Phase 2").
- [ ] No large empty areas, and nothing cramped against the page edge.

### 8. Deliver

Files are already in `/mnt/user-data/outputs/<Project>/`. Call `present_files` with the PDF first, then
the `.drawio`, then the PNGs. Reply in 3 to 6 lines covering what's in the deck (page list), how to edit
it (open the `.drawio` at app.diagrams.net or in draw.io Desktop; shapes stay connected), and any
assumption the user should verify.

## Visual language (fixed: consistency is what makes it look professional)

| Status | Box | Edge | Meaning |
| --- | --- | --- | --- |
| `existing` | white, slate border | slate solid | unchanged |
| `new` | light green, green border | green solid | added in this step |
| `modified` | light amber, amber border | amber solid | changed (new datasource, re-pointed flow) |
| `retire` | light red, red dashed, "RETIRE" tag | red dashed | being switched off in this step |

Other conventions:

- **Kubernetes:** use `p.k8s_zone(...)` around stateless tiers and `k8s=True` badges on the nodes.
- **Canvas and type:** 1920x1080 canvas, Helvetica, 26 px titles, 12 px box titles, 10 px sub-text and labels.
- **Footer:** every slide ends with `p.why(...)` at y=872.
- **Brand icons:** use Simple Icons slugs (`references/icons.md`), downloaded automatically and coloured per brand.
- **Generic icons:** `lb`, `db`, `server`, `apps`, `file`, `probe`, `cloud`, `queue`, `user`, `lock`, `gear`.

## Multi-page migration stories

When the user wants "current state, then phases, then final", read `references/migration-story.md`.
Use one shared layout for all phase pages so the customer sees the old stack shrink and the new one
grow in the same positions. Add a roadmap overview page and an optional cover page.

## Rules that keep quality high

- Never let draw.io auto-route edges. Every edge gets explicit waypoints, and every segment is horizontal or vertical.
- Prefer moving boxes over adding bends. One straight segment beats three.
- Keep one idea per slide. If a page needs more than about 35 boxes or 40 edges, split it.
- Box text: title of 3 words or fewer; sub-text of 1 to 2 short lines with explicit `<br>`.
- Don't invent components or numbers that the user didn't give. Mark assumptions in the why panel.
- Excalidraw requested: explain that draw.io is used because it gives exact, editable, connector-aware
  output and PDF export. Offer the `.drawio` file, which Excalidraw users can still view as PNG/PDF.

---
Skill author: Vikrant Nalawade (MIT licence).
