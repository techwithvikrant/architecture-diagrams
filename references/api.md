# drawio_lib API (scripts/drawio_lib.py)

```python
import sys; sys.path.insert(0, '<skill>/scripts')
from drawio_lib import Page, build
```

## Page(pid, name, W=1920, H=1080)
`pid`: short unique id (prefix for cell ids). `name`: tab name shown in draw.io, for example '3. Phase 1'.

### Furniture
| Call | What it draws |
|------|---------------|
| `p.header(title, subtitle)` | 26 px title + 14 px subtitle, top left |
| `p.legend([(status, label), ...], x=None)` | Swatches, right-aligned by default; status may be 'k8s' |
| `p.lanes([(x, w, 'TEXT'), ...], y=74)` | Small grey column headings |
| `p.why(heading, [bullets], y=872, h=180)` | Reasoning panel; bullets may use `<b>` |
| `p.card(k, x, y, w, h, heading, body)` | Green outcome card (target pages) |
| `p.rect(k, x, y, w, h, html, style)` | Any free decorative shape (chevrons, bands); not validated |
| `p.text(x, y, w, h, html, size, color, align, bold, bg, valign, role)` | Text; `role='decor'` for headings, `'label'` (default) is collision-checked |

### Structure
| Call | Notes |
|------|-------|
| `p.container(k, x, y, w, h, title, fill, stroke, dashed)` | Grouping box; edges may cross it |
| `p.k8s_zone(k, x, y, w, h)` | Blue dashed "Kubernetes / OpenShift" zone |
| `p.node(k, x, y, w, h, title, sub='', status='existing', icon=None, size=12, valign='middle', tag=None, k8s=False)` | Component box. `sub` may use `<br>`; status: existing/new/modified/retire; retire auto-tags "RETIRE" |
| `p.actor(k, x, y, w, h, 'Users')` | Stick figure |

### Edges and labels
| Call | Notes |
|------|-------|
| `p.edge(k, src, dst, [(x, y), ...], status='existing', both=False)` | First point on src border, last on dst border, axis-aligned segments only |
| `p.label(x, y, 'text', align='center', w=None)` | Edge label, 14 px tall; place 4 px or more off any line |

### Validation
`p.validate(allow_crossings=0)` returns `(errors, warnings)`. `build()` calls it for every page.

## build(pages, out_dir, basename, png_names=None, allow_crossings=0, strict=True, scale=2)
Validates every page, then writes:
- `out_dir/basename.drawio` (all pages)
- `out_dir/PNG/NN_<page>.png` (or `png_names`)
- `out_dir/basename.pdf` (vector, one page per diagram page, cropped to 16:9)
- `/tmp/diagram-review/contact_sheet.png` and `page_NN.png`, for your visual check (not delivered)

With `strict=True`, any error stops the build before export.

## Environment
- `DRAWIO_BIN` (default `/tmp/drawio-cli/opt/drawio/drawio`), set up by `scripts/setup_drawio.sh`
- Needs `xvfb-run`, Pillow and pypdf (the setup script installs what's missing)
