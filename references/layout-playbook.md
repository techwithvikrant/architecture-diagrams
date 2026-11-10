# Layout & Routing Playbook

How to get a diagram with zero crossings on the first build. Read it fully before placing boxes.

## Contents
1. Canvas and grid
2. Lanes (columns)
3. Rows and box sizing
4. Ordering to remove crossings
5. Routing patterns
6. Labels
7. Text sizing
8. Common fixes for validator errors

## 1. Canvas and grid

| Region | y range | Contents |
| --- | --- | --- |
| Title area | 0–70 | Title at y 14 (26 px), subtitle at y 48 (14 px), legend at top right |
| Lane headings | 72–90 | Optional |
| Diagram area | 95–850 | All boxes and edges |
| Why panel | 872–1052 | Created by `p.why(...)` |

The canvas is 1920 x 1080 and the horizontal margins are 30 px. Snap coordinates to multiples of 5.

## 2. Lanes (columns)

Assign roles to columns in data-flow order. A typical layout:

| Lane | x | Width | Typical contents |
| --- | --- | --- | --- |
| Clients / sources | 30–330 | 300 | Users, devices, upstream systems |
| Gap | 330–380 | 50 | Channel for vertical edge segments |
| Edge / ingest | 380–870 | 490 | Load balancers, gateways, queues |
| Application / processing | 910–1110 | 200 | Services, workers, pipelines |
| Data | 1150–1410 | 260 | Databases, caches, storage |
| Consumers / UI | 1460–1670 | 210 | Dashboards, portals, reports |
| Operations / access | 1700–1900 | 200 | Monitoring, admin access |

Leave a gap of 30–50 px between lanes. Gaps are where vertical segments run, so never put boxes there.

## 3. Rows and box sizing

- Decide the y of each flow first, then place boxes so their **centre or an edge point** sits on that y.
- A box that receives N inputs on one side should be tall enough for N straight inputs at least 20 px
  apart. For example, an API gateway 220 px tall can feed three stacked services with straight lines.
- Standard box sizes:

| Box type | Height | Width |
| --- | --- | --- |
| Single line | 40 | At least title chars × 7 + 60 (with icon) |
| Title plus 1 sub line | 50–60 | Same rule |
| Title plus 2 sub lines | 70–90 | Same rule |

- Stacked boxes need a vertical gap of at least 10 px, and at least 20 px if a line passes between them.
- Containers have a 30 px title strip at the top. Children start 30 px or more below the container's
  top and sit 15 px in from its sides.
- Tall "hub" boxes (a gateway, a dashboard or a bus spanning several rows) are fine and often the
  cleanest answer. Use `valign='top'` when the box is very tall.

## 4. Ordering to remove crossings

Crossings come from order mismatches. Two edges leaving one column cross if their order on the left
is the reverse of their targets' order on the right.

1. List the sources in a lane top to bottom, and write each one's destination row.
2. Reorder the sources (and the items inside host containers) so the destination rows increase monotonically.
3. If two groups each need both a top and a bottom destination (the classic `[A, B][A, B]` problem,
   for example two servers that both write to a database and to a log store), no ordering works. Use a
   pattern from section 5:
   - give one flow its own **band**,
   - route one edge around the **outside margin** (a "margin loop"),
   - or split a source box by flow (for example "servers: app traffic" above and "servers: monitoring" below).
4. Hub targets that receive from both above and below should be tall boxes, so every input arrives as
   a straight horizontal line.
5. Two "sync" links that leave one column and come back to it must nest: the pair with the wider
   vertical span takes the outer channel. If the spans interleave, reorder the boxes so they nest.

## 5. Routing patterns

All points are absolute. The first point lies on the source border, the last on the target border.

- **Straight:** `[(x1, y), (x2, y)]`. Align the boxes so most edges look like this.
- **Single elbow:** `[(x1, y1), (xc, y1), (xc, y2), (x2, y2)]`, with `xc` in a lane gap.
- **Nested elbows:** several sources in one column join a target from the side. Give the topmost
  source the outermost channel (largest x) and the highest entry y, and step each lower source 10–15 px
  inward and lower. The edges then nest without crossing.
- **Vertical tap between bands:** exit the bottom of a box at an x where nothing lies below it in its
  band, drop into the gap between bands, run horizontally in that gap, then drop into the target's top.
  Example: a gateway routing back up to a legacy app.
- **Margin loop:** exit the left side of a source, run down the outer margin (x around 14) and along the
  bottom margin (y around 830), then come up into the target's bottom. It costs a long line but no
  crossing. Label it.
- **Around the top or right edge:** the same idea, for a target that is otherwise boxed in.
- **Bidirectional:** use `both=True` for flows such as storage tiering (hot to cold and back).
- **Fan-in to a container:** an edge may target a container. This is useful when the internal
  structure is shown but the exact entry node doesn't matter (for example "Legacy stack").

Spacing:

| Situation | Minimum |
| --- | --- |
| Parallel lines | 12 px apart (the validator warns under 10) |
| A line and an unrelated box | 8 px |
| Last bend before an arrowhead | 20 px from the target (keeps the head visible) |

## 6. Labels

- Add them with `p.label(x, y, 'text')`, centred on x, or with `align='left'`. The box is 14 px tall.
- For a horizontal edge at height Y, put the label at `y = Y - 17` (it sits above the line).
- For a vertical edge at X, use `p.label(X + 8, ymid, 'text', align='left')`.
- Keep labels to 1–4 words. The validator rejects a label that touches a line, a box or another label.
- Don't label obvious edges. Topic names, box names and the legend already say a lot.

## 7. Text sizing

Approximate widths for estimating box sizes (Helvetica):

| Text | Width per character |
| --- | --- |
| 12 px bold title | ~6.7 px |
| 10 px sub-text | ~5 px |
| 9 px tag | ~5.6 px |

An icon takes 48 px on the left. Break long sub-text with `<br>` rather than letting it wrap.

## 8. Common fixes for validator errors

| Error | Fix |
| --- | --- |
| `edge crossing: a x b` | Reorder the sources (section 4), move one bend into a different channel, or use a band or margin loop |
| `edge X passes through box B` | Move the waypoint into a lane gap, or move B |
| `edges a and b run on top of each other` | Offset one by 12–15 px |
| `label ... sits on edge` | Move the label 4 px or more off the line, or shorten it |
| `boxes overlap` | Fix the coordinates; check that the widths add up inside the lane |
| `endpoint must lie on a border` | Use the box's x, x+w, y or y+h exactly for one coordinate |
| `outside the canvas` | Keep everything within 0–1920 × 0–1080 |
