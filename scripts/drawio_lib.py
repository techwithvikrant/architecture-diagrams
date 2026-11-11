"""
drawio_lib: build precise, presentation-ready draw.io diagrams from Python.

Every box and arrow is a native, connected draw.io cell, so the .drawio file stays fully
editable. Coordinates are absolute (canvas pixels). Edges are drawn ONLY through explicit,
axis-aligned waypoints that you choose, so nothing is left to an auto-router.

Typical use (see SKILL.md and examples/):

    import sys; sys.path.insert(0, '<skill>/scripts')
    from drawio_lib import Page, build
    p = Page('cur', '1. Current State')
    p.header('Current State', 'one-line subtitle')
    p.node('a', 40, 100, 220, 50, 'Service A', 'what it does', icon='grafana')
    p.node('b', 400, 100, 220, 50, 'Service B')
    p.edge('ab', 'a', 'b', [(260, 125), (400, 125)])
    p.why('Why this matters', ['bullet one', 'bullet two'])
    build([p], out_dir='/mnt/user-data/outputs/My_Diagrams', basename='My_Architecture')

build() validates geometry (crossings, arrows through boxes, label collisions, text overflow),
writes the .drawio, exports one PNG per page and one combined vector PDF with draw.io itself,
and writes a contact sheet for visual review.
"""
import base64, html, json, os, re, subprocess, urllib.request

SKILL_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ICON_DIR = os.path.join(SKILL_DIR, 'assets', 'icons')
ICON_CACHE = os.environ.get('DIAGRAM_ICON_CACHE', '/tmp/diagram-icons')
DRAWIO_BIN = os.environ.get('DRAWIO_BIN', '/tmp/drawio-cli/opt/drawio/drawio')
FONT = 'Helvetica'

# ----------------------------------------------------------------------------- icons
# Brand colours (hex). Anything not listed falls back to Simple Icons' own colour, then slate.
BRAND = {
    'opentelemetry': '#425CC7', 'apachekafka': '#231F20', 'elasticsearch': '#00A9E5',
    'logstash': '#00BFB3', 'kibana': '#F04E98', 'beats': '#005571', 'prometheus': '#E6522C',
    'grafana': '#F46800', 'postgresql': '#336791', 'clickhouse': '#E0B400', 'kubernetes': '#326CE5',
    'ceph': '#EF5C55', 'oracle': '#F80000', 'openjdk': '#E76F00', 'jaeger': '#2BA3C4',
    'redhatopenshift': '#EE0000', 'nginx': '#009639', 'redis': '#DC382D', 'mysql': '#4479A1',
    'mongodb': '#47A248', 'rabbitmq': '#FF6600', 'docker': '#2496ED', 'apachespark': '#E25A1C',
    'grafana-loki': '#F46800', 'vault': '#FFEC6E', 'terraform': '#844FBA', 'argo': '#EF7B4D',
    'helm': '#0F1689', 'istio': '#466BB0', 'envoyproxy': '#AC6199', 'python': '#3776AB',
    'nodedotjs': '#5FA04E', 'go': '#00ADD8', 'react': '#61DAFB', 'minio': '#C72E49',
}
# Generic, vendor-neutral icons drawn in-house (safe for any diagram).
CUSTOM = {
    'lb': '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24"><circle cx="12" cy="12" r="10" fill="none" stroke="#7C3AED" stroke-width="2"/><path d="M12 5v14M8 9l4-4 4 4M8 15l4 4 4-4" stroke="#7C3AED" stroke-width="1.8" fill="none" stroke-linecap="round" stroke-linejoin="round"/></svg>',
    'db': '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24"><ellipse cx="12" cy="5" rx="8" ry="3" fill="none" stroke="#B91C1C" stroke-width="1.8"/><path d="M4 5v14c0 1.7 3.6 3 8 3s8-1.3 8-3V5M4 12c0 1.7 3.6 3 8 3s8-1.3 8-3" fill="none" stroke="#B91C1C" stroke-width="1.8"/></svg>',
    'file': '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24"><path d="M6 2h8l5 5v15H6z" fill="none" stroke="#475569" stroke-width="1.8" stroke-linejoin="round"/><path d="M14 2v5h5M9 12h7M9 16h7" stroke="#475569" stroke-width="1.6" fill="none"/></svg>',
    'server': '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24"><rect x="3" y="3" width="18" height="7" rx="1.5" fill="none" stroke="#334155" stroke-width="1.8"/><rect x="3" y="14" width="18" height="7" rx="1.5" fill="none" stroke="#334155" stroke-width="1.8"/><circle cx="7" cy="6.5" r="1.2" fill="#334155"/><circle cx="7" cy="17.5" r="1.2" fill="#334155"/></svg>',
    'apps': '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24"><rect x="3" y="3" width="8" height="8" rx="1.5" fill="none" stroke="#059669" stroke-width="1.8"/><rect x="13" y="3" width="8" height="8" rx="1.5" fill="none" stroke="#059669" stroke-width="1.8"/><rect x="3" y="13" width="8" height="8" rx="1.5" fill="none" stroke="#059669" stroke-width="1.8"/><path d="M17 13v8M13 17h8" stroke="#059669" stroke-width="1.8"/></svg>',
    'probe': '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24"><circle cx="12" cy="12" r="9" fill="none" stroke="#E6522C" stroke-width="1.8"/><path d="M3 12h18M12 3c3 3 3 15 0 18M12 3c-3 3-3 15 0 18" fill="none" stroke="#E6522C" stroke-width="1.5"/></svg>',
    'cloud': '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24"><path d="M7 18h10a4 4 0 0 0 .5-8A6 6 0 0 0 6 9.5 4.3 4.3 0 0 0 7 18z" fill="none" stroke="#0EA5E9" stroke-width="1.8" stroke-linejoin="round"/></svg>',
    'queue': '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24"><rect x="2" y="7" width="20" height="10" rx="2" fill="none" stroke="#0F766E" stroke-width="1.8"/><path d="M7 7v10M12 7v10M17 7v10" stroke="#0F766E" stroke-width="1.6"/></svg>',
    'user': '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24"><circle cx="12" cy="8" r="4" fill="none" stroke="#334155" stroke-width="1.8"/><path d="M4 21c0-4.4 3.6-7 8-7s8 2.6 8 7" fill="none" stroke="#334155" stroke-width="1.8"/></svg>',
    'lock': '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24"><rect x="5" y="10" width="14" height="11" rx="2" fill="none" stroke="#B45309" stroke-width="1.8"/><path d="M8 10V7a4 4 0 0 1 8 0v3" fill="none" stroke="#B45309" stroke-width="1.8"/></svg>',
    'gear': '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24"><circle cx="12" cy="12" r="3.2" fill="none" stroke="#475569" stroke-width="1.8"/><path d="M12 2v3M12 19v3M2 12h3M19 12h3M4.9 4.9l2.1 2.1M17 17l2.1 2.1M4.9 19.1 7 17M17 7l2.1-2.1" stroke="#475569" stroke-width="1.8"/></svg>',
}

def _simple_icon_svg(slug):
    for d in (ICON_DIR, ICON_CACHE):
        f = os.path.join(d, slug + '.svg')
        if os.path.exists(f):
            return open(f).read()
    os.makedirs(ICON_CACHE, exist_ok=True)
    try:
        url = f'https://cdn.jsdelivr.net/npm/simple-icons@13/icons/{slug}.svg'
        svg = urllib.request.urlopen(url, timeout=15).read().decode()
        open(os.path.join(ICON_CACHE, slug + '.svg'), 'w').write(svg)
        return svg
    except Exception:
        return None

def icon_uri(name):
    if name in CUSTOM:
        svg = CUSTOM[name]
    else:
        svg = _simple_icon_svg(name)
        if svg is None:
            print(f'WARNING: icon "{name}" not found on Simple Icons, using generic server icon')
            svg = CUSTOM['server']
        else:
            svg = svg.replace('<svg ', '<svg fill="%s" ' % BRAND.get(name, '#334155'), 1)
    return 'data:image/svg+xml,' + base64.b64encode(svg.encode()).decode()

# ----------------------------------------------------------------------------- styles
ST = {
    'existing': dict(fill='#FFFFFF', stroke='#94A3B8', font='#0F172A', sub='#475569', dash=0, sw=1.2),
    'new':      dict(fill='#ECFDF5', stroke='#059669', font='#064E3B', sub='#047857', dash=0, sw=1.8),
    'modified': dict(fill='#FFFBEB', stroke='#D97706', font='#78350F', sub='#92400E', dash=0, sw=1.8),
    'retire':   dict(fill='#FEF2F2', stroke='#DC2626', font='#7F1D1D', sub='#991B1B', dash=1, sw=1.6),
}
EST = {  # edge colour, width, dashed
    'existing': ('#64748B', 1.4, 0),
    'new': ('#059669', 2.0, 0),
    'modified': ('#D97706', 2.0, 0),
    'retire': ('#DC2626', 1.6, 1),
}
TAG_COLOR = {'retire': '#DC2626', 'new': '#059669', 'modified': '#D97706', 'existing': '#475569'}

def esc(s):
    return html.escape(s, quote=True)

def _plain(s):
    return re.sub(r'<[^>]+>', '', s.replace('<br>', '\n')).replace('&nbsp;', ' ').replace('&amp;', '&')

# ----------------------------------------------------------------------------- page
class Page:
    """One draw.io page (one slide). Default canvas is 1920 x 1080 (16:9)."""

    def __init__(self, pid, name, W=1920, H=1080):
        self.pid, self.name, self.W, self.H = pid, name, W, H
        self.cells, self.geo, self.meta, self.edges, self.labels = [], {}, {}, {}, []
        self.n = 0
        self._rect('frame', 0, 0, W, H, style='rounded=0;fillColor=#FFFFFF;strokeColor=none;', kind='frame')

    # --- primitives --------------------------------------------------------
    def _id(self, k):
        return f'{self.pid}-{k}'

    def _rect(self, k, x, y, w, h, value='', style='', kind='decor', info=None):
        assert k not in self.geo, f'duplicate key {k} on page {self.pid}'
        self.geo[k] = (x, y, w, h)
        self.meta[k] = dict(kind=kind, **(info or {}))
        self.cells.append(f'<mxCell id="{self._id(k)}" value="{esc(value)}" style="{style}" vertex="1" parent="1">'
                          f'<mxGeometry x="{x}" y="{y}" width="{w}" height="{h}" as="geometry"/></mxCell>')

    def rect(self, k, x, y, w, h, value='', style=''):
        """Free decorative shape (cards, bands, chevrons). Not collision-checked."""
        self._rect(k, x, y, w, h, value, style, kind='decor')

    def text(self, x, y, w, h, value, size=10, color='#475569', align='center', bold=False, bg=True,
             valign='middle', role='label'):
        """role='label' (edge labels: collision-checked) or 'decor' (titles, headings)."""
        self.n += 1
        st = (f'text;html=1;whiteSpace=wrap;align={align};verticalAlign={valign};fontFamily={FONT};fontSize={size};'
              f'fontColor={color};' + ('fontStyle=1;' if bold else '') + ('labelBackgroundColor=#FFFFFF;' if bg else '') + 'spacing=0;')
        k = f'tx{self.n}'
        self._rect(k, x, y, w, h, value, st, kind=role)
        if role == 'label':
            tw = len(_plain(value)) * size * 0.56
            tx = x if align == 'left' else (x + w - tw if align == 'right' else x + (w - tw) / 2)
            self.labels.append((k, tx, y + (h - size * 1.2) / 2, tw, size * 1.2, _plain(value)))

    def label(self, x, y, value, align='center', w=None, size=10):
        """Edge label. x,y = anchor (centre or left edge) of the text's baseline box, 14 px tall."""
        w = w or max(40, int(len(value) * size * 0.6) + 8)
        bx = x - w / 2 if align == 'center' else x
        self.text(bx, y, w, 14, value, size=size, align=align)

    def container(self, k, x, y, w, h, title, fill='#F8FAFC', stroke='#CBD5E1', dashed=False, font='#334155', size=13):
        """Grouping box with a title at the top-left. Edges may cross its border."""
        st = (f'rounded=1;arcSize=2;absoluteArcSize=1;html=1;whiteSpace=wrap;fillColor={fill};strokeColor={stroke};'
              f'verticalAlign=top;align=left;spacingLeft=12;spacingTop=6;fontStyle=1;fontSize={size};fontColor={font};fontFamily={FONT};'
              + ('dashed=1;dashPattern=6 4;' if dashed else ''))
        self._rect(k, x, y, w, h, title, st, kind='container')

    def k8s_zone(self, k, x, y, w, h, title='Kubernetes / OpenShift'):
        self.container(k, x, y, w, h, title, fill='none', stroke='#326CE5', dashed=True, font='#326CE5', size=10)

    def node(self, k, x, y, w, h, title, sub='', status='existing', icon=None, size=12, valign='middle',
             tag=None, k8s=False, align=None):
        """A component box. status: existing | new | modified | retire. tag: small caps line (e.g. 'RETIRE')."""
        s = ST[status]
        if tag is None and status == 'retire':
            tag = 'RETIRE'
        lab = f'<b>{title}</b>'
        if sub:
            lab += f'<br><font style="font-size:10px" color="{s["sub"]}">{sub}</font>'
        if tag:
            lab += f'<br><font style="font-size:9px" color="{TAG_COLOR[status]}"><b>{tag}</b></font>'
        st = (f'rounded=1;arcSize=10;whiteSpace=wrap;html=1;fontFamily={FONT};fontSize={size};fontColor={s["font"]};'
              f'fillColor={s["fill"]};strokeColor={s["stroke"]};strokeWidth={s["sw"]};verticalAlign={valign};')
        if s['dash']:
            st += 'dashed=1;dashPattern=5 3;'
        if icon:
            st = ('shape=label;' + st + f'align={align or "left"};spacingLeft=42;image={icon_uri(icon)};imageWidth=24;'
                  'imageHeight=24;imageAlign=left;imageVerticalAlign=' + ('top' if valign == 'top' else 'middle')
                  + ';spacingTop=' + ('10' if valign == 'top' else '0') + ';')
        else:
            st += f'align={align or "center"};'
        self._rect(k, x, y, w, h, lab, st, kind='node',
                   info=dict(title=title, sub=sub, tag=tag, icon=bool(icon), size=size, valign=valign))
        if k8s:
            self._rect(k + '_k8s', x + w - 22, y + 4, 18, 18, '',
                       f'shape=image;html=1;image={icon_uri("kubernetes")};imageAspect=1;', kind='badge')

    def actor(self, k, x, y, w, h, label='Users'):
        self._rect(k, x, y, w, h, label,
                   f'shape=umlActor;verticalLabelPosition=bottom;verticalAlign=top;html=1;outlineConnect=0;fillColor=#E2E8F0;'
                   f'strokeColor=#475569;fontFamily={FONT};fontSize=11;fontColor=#334155;', kind='node',
                   info=dict(title='', sub='', tag=None, icon=False, size=11, valign='middle', actor=True))

    def edge(self, k, src, dst, pts, status='existing', both=False):
        """pts = absolute waypoints. First point on src border, last on dst border, every segment
        horizontal or vertical. The arrow head is at dst (both=True adds one at src)."""
        sx, sy, sw, sh = self.geo[src]
        tx, ty, tw, th = self.geo[dst]
        (ax, ay), (bx, by) = pts[0], pts[-1]
        ex, ey = (ax - sx) / sw, (ay - sy) / sh
        nx, ny = (bx - tx) / tw, (by - ty) / th
        for v in (ex, ey, nx, ny):
            assert -0.001 <= v <= 1.001, f'{self.pid}/{k}: endpoint not on the box ({v:.3f})'
        for nm, fx, fy in ((src, ex, ey), (dst, nx, ny)):
            assert min(abs(fx), abs(fx - 1), abs(fy), abs(fy - 1)) < 0.01, \
                f'{self.pid}/{k}: endpoint must lie on a border of "{nm}", not inside it'
        col, w, d = EST[status]
        st = (f'html=1;rounded=0;edgeStyle=none;endArrow=blockThin;endFill=1;endSize=7;strokeColor={col};strokeWidth={w};'
              f'exitX={ex:.4f};exitY={ey:.4f};exitDx=0;exitDy=0;exitPerimeter=0;entryX={nx:.4f};entryY={ny:.4f};'
              f'entryDx=0;entryDy=0;entryPerimeter=0;')
        if d:
            st += 'dashed=1;dashPattern=6 4;'
        if both:
            st += 'startArrow=blockThin;startFill=1;startSize=7;'
        mids = ''.join(f'<mxPoint x="{x}" y="{y}"/>' for x, y in pts[1:-1])
        arr = f'<Array as="points">{mids}</Array>' if mids else ''
        assert k not in self.edges, f'duplicate edge {k}'
        self.edges[k] = (src, dst, list(pts))
        self.cells.append(f'<mxCell id="{self._id("e_" + k)}" style="{st}" edge="1" parent="1" source="{self._id(src)}" '
                          f'target="{self._id(dst)}"><mxGeometry relative="1" as="geometry">{arr}</mxGeometry></mxCell>')

    # --- page furniture ----------------------------------------------------
    def header(self, title, subtitle=''):
        self.text(30, 14, 1250, 34, title, size=26, color='#0F172A', align='left', bold=True, bg=False, role='decor')
        if subtitle:
            self.text(30, 48, 1250, 22, subtitle, size=14, color='#475569', align='left', bg=False, role='decor')

    def lanes(self, items, y=74):
        """Column headings: list of (x, w, 'TEXT')."""
        for x, w, t in items:
            self.text(x, y, w, 16, t, size=11, color='#64748B', bold=True, bg=False, role='decor')

    def legend(self, items, x=None, y=18, note='Arrows show the direction of data flow'):
        """items: list of (status, label); status may also be 'k8s'. Right-aligned when x is None."""
        widths = [28 + int(6.4 * len(lab)) + 18 for _, lab in items]
        if x is None:
            x = self.W - 30 - max(sum(widths), 300)
        cx = x
        for (st, lab), wdt in zip(items, widths):
            if st == 'k8s':
                self._rect(f'lg{cx}', cx, y + 4, 18, 18, '', f'shape=image;html=1;image={icon_uri("kubernetes")};imageAspect=1;')
            else:
                s = ST[st]
                self._rect(f'lg{cx}', cx, y + 4, 22, 16, '',
                           f'rounded=1;arcSize=20;fillColor={s["fill"]};strokeColor={s["stroke"]};strokeWidth={s["sw"]};'
                           + ('dashed=1;dashPattern=4 2;' if s['dash'] else ''))
            self.text(cx + 28, y, wdt - 28, 24, lab, size=11, color='#334155', align='left', bg=False, role='decor')
            cx += wdt
        if note:
            self.text(x, y + 28, min(600, self.W - 30 - x), 18, note, size=10, color='#64748B', align='left', bg=False, role='decor')

    def why(self, heading, bullets, y=872, h=180):
        """Reasoning panel at the bottom of the slide."""
        body = f'<b style="font-size:15px;color:#0F172A">{heading}</b><br>' + ''.join(
            f'<div style="margin-top:6px">&#8226;&nbsp; {b}</div>' for b in bullets)
        st = (f'rounded=1;arcSize=2;absoluteArcSize=1;html=1;whiteSpace=wrap;fillColor=#F1F5F9;strokeColor=#CBD5E1;'
              f'align=left;verticalAlign=top;spacingLeft=20;spacingTop=12;spacingRight=20;fontFamily={FONT};fontSize=13;fontColor=#1E293B;')
        self._rect('why', 30, y, self.W - 60, h, body, st, kind='panel')

    def card(self, k, x, y, w, h, heading, body, accent='#065F46', fill='#F0FDF4', stroke='#86EFAC'):
        self.rect(k, x, y, w, h, f'<b style="font-size:15px;color:{accent}">{heading}</b><div style="margin-top:8px">{body}</div>',
                  f'rounded=1;arcSize=4;absoluteArcSize=1;html=1;whiteSpace=wrap;fillColor={fill};strokeColor={stroke};'
                  f'align=left;verticalAlign=top;spacingLeft=18;spacingTop=14;spacingRight=16;fontFamily={FONT};fontSize=13;fontColor=#1E293B;')

    # --- validation --------------------------------------------------------
    def validate(self, allow_crossings=0):
        """Returns (errors, warnings). Errors must be fixed; warnings deserve a look in the render."""
        errs, warns = [], []
        boxes = {k: self.geo[k] for k, m in self.meta.items() if m['kind'] == 'node'}
        segs = []  # (edge, (x1,y1,x2,y2))
        for k, (s, d, pts) in self.edges.items():
            for (x1, y1), (x2, y2) in zip(pts, pts[1:]):
                if x1 != x2 and y1 != y2:
                    errs.append(f'edge {k}: diagonal segment {(x1, y1)}->{(x2, y2)}; use horizontal/vertical waypoints')
                segs.append((k, (x1, y1, x2, y2)))
        # 1. edges through boxes
        for k, (x1, y1, x2, y2) in segs:
            for b, (bx, by, bw, bh) in boxes.items():
                if _seg_hits_box(x1, y1, x2, y2, bx + 2, by + 2, bw - 4, bh - 4):
                    errs.append(f'edge {k} passes through box "{b}"')
        # 2. edge/edge crossings and overlaps
        crossings = []
        for i in range(len(segs)):
            for j in range(i + 1, len(segs)):
                (ka, a), (kb, b) = segs[i], segs[j]
                if ka == kb:
                    continue
                r = _seg_relation(a, b)
                if r == 'cross':
                    crossings.append(f'{ka} x {kb}')
                elif r == 'overlap':
                    errs.append(f'edges {ka} and {kb} run on top of each other')
                elif r == 'close':
                    warns.append(f'edges {ka} and {kb} run parallel closer than 10 px')
        if len(crossings) > allow_crossings:
            errs += [f'edge crossing: {c}' for c in crossings]
        # 3. box overlaps
        bl = list(boxes.items())
        for i in range(len(bl)):
            for j in range(i + 1, len(bl)):
                if _box_overlap(bl[i][1], bl[j][1], pad=0):
                    errs.append(f'boxes "{bl[i][0]}" and "{bl[j][0]}" overlap')
        # 4. labels vs edges, boxes, other labels
        for i, (k, lx, ly, lw, lh, txt) in enumerate(self.labels):
            lb = (lx - 2, ly - 1, lw + 4, lh + 2)
            for ek, (x1, y1, x2, y2) in segs:
                if _seg_hits_box(x1, y1, x2, y2, *lb):
                    errs.append(f'label "{txt}" sits on edge {ek}; move it 4+ px off the line')
            for b, g in boxes.items():
                if _box_overlap(lb, g, pad=0):
                    errs.append(f'label "{txt}" overlaps box "{b}"')
            for (k2, x2, y2, w2, h2, t2) in self.labels[i + 1:]:
                if _box_overlap(lb, (x2, y2, w2, h2), pad=0):
                    errs.append(f'labels "{txt}" and "{t2}" overlap')
        # 5. text fit (estimates; confirm in the render)
        for k, m in self.meta.items():
            if m['kind'] != 'node' or m.get('actor'):
                continue
            x, y, w, h = self.geo[k]
            pad = 48 if m['icon'] else 16
            lines = [(l, m['size'] * 0.56) for l in _plain(m['title']).split('\n')]
            lines += [(l, 10 * 0.5) for l in _plain(m['sub']).split('\n') if m['sub']]
            if m['tag']:
                lines.append((m['tag'], 9 * 0.62))
            for txt, cw in lines:
                if len(txt) * cw + pad > w + 1:
                    warns.append(f'box "{k}": "{txt[:40]}" will wrap ({int(len(txt) * cw + pad)} > {w} px); check the render')
            need = 12 + 14 * len(lines)
            if need > h + 2:
                warns.append(f'box "{k}": text needs about {need}px height (has {h})')
        # 6. canvas bounds
        for k, (x, y, w, h) in self.geo.items():
            if x < 0 or y < 0 or x + w > self.W or y + h > self.H:
                errs.append(f'"{k}" is outside the {self.W}x{self.H} canvas')
        return errs, warns

    def xml(self):
        return (f'<diagram name="{esc(self.name)}" id="{self.pid}"><mxGraphModel dx="0" dy="0" grid="0" gridSize="10" guides="1" '
                f'tooltips="1" connect="1" arrows="1" fold="1" page="1" pageScale="1" pageWidth="{self.W}" pageHeight="{self.H}" '
                f'math="0" shadow="0"><root><mxCell id="0"/><mxCell id="1" parent="0"/>{"".join(self.cells)}</root></mxGraphModel></diagram>')


def _seg_hits_box(x1, y1, x2, y2, bx, by, bw, bh):
    lo_x, hi_x, lo_y, hi_y = min(x1, x2), max(x1, x2), min(y1, y2), max(y1, y2)
    return lo_x < bx + bw and hi_x > bx and lo_y < by + bh and hi_y > by

def _box_overlap(a, b, pad=0):
    ax, ay, aw, ah = a
    bx, by, bw, bh = b
    return ax < bx + bw - pad and bx < ax + aw - pad and ay < by + bh - pad and by < ay + ah - pad

def _seg_relation(a, b):
    ax1, ay1, ax2, ay2 = a
    bx1, by1, bx2, by2 = b
    ah, bh = ay1 == ay2, by1 == by2
    if ah != bh:  # perpendicular
        h, v = (a, b) if ah else (b, a)
        hx1, hx2, hy = min(h[0], h[2]), max(h[0], h[2]), h[1]
        vy1, vy2, vx = min(v[1], v[3]), max(v[1], v[3]), v[0]
        if hx1 < vx < hx2 and vy1 < hy < vy2:
            return 'cross'
        return None
    if ah:  # both horizontal
        lo, hi = max(min(ax1, ax2), min(bx1, bx2)), min(max(ax1, ax2), max(bx1, bx2))
        if hi - lo > 1:
            if ay1 == by1:
                return 'overlap'
            if abs(ay1 - by1) < 10:
                return 'close'
    else:
        lo, hi = max(min(ay1, ay2), min(by1, by2)), min(max(ay1, ay2), max(by1, by2))
        if hi - lo > 1:
            if ax1 == bx1:
                return 'overlap'
            if abs(ax1 - bx1) < 10:
                return 'close'
    return None

# ----------------------------------------------------------------------------- build
def drawio_available():
    """True when the draw.io CLI and xvfb-run are usable (tries the setup script once)."""
    import shutil
    if os.path.exists(DRAWIO_BIN) and shutil.which('xvfb-run'):
        return True
    setup = os.path.join(SKILL_DIR, 'scripts', 'setup_drawio.sh')
    try:
        subprocess.run(['bash', setup], capture_output=True, text=True, timeout=240)
    except Exception:
        pass
    return os.path.exists(DRAWIO_BIN) and bool(shutil.which('xvfb-run'))

def _run_drawio(args):
    cmd = ['xvfb-run', '-a', DRAWIO_BIN, '-x'] + args + ['--no-sandbox', '--disable-gpu']
    r = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
    out = r.stdout + r.stderr
    if 'Export failed' in out or 'Error:' in out.replace('ERROR:bus', ''):
        raise SystemExit('draw.io export failed:\n' + '\n'.join(l for l in out.splitlines() if 'bus.cc' not in l))

def default_out_dir(project):
    """Claude: /mnt/user-data/outputs, ChatGPT: /mnt/data, otherwise ./outputs."""
    for base in ('/mnt/user-data/outputs', '/mnt/data'):
        if os.path.isdir(base) and os.access(base, os.W_OK):
            return os.path.join(base, project)
    return os.path.join(os.getcwd(), 'outputs', project)

def build(pages, out_dir, basename, png_names=None, allow_crossings=0, strict=True, scale=2, review_dir='/tmp/diagram-review'):
    """Validate every page, write <basename>.drawio, PNG per page (PNG/), combined PDF, and a review contact sheet."""
    ok = True
    for p in pages:
        errs, warns = p.validate(allow_crossings=allow_crossings)
        tag = f'[{p.pid}] {p.name}'
        if errs:
            ok = False
            print(f'\n{tag}: {len(errs)} ERROR(S)')
            for e in errs:
                print('  x', e)
        for w in warns:
            print(f'  ! {tag}: {w}')
    if not ok and strict:
        raise SystemExit('\nGeometry check failed. Fix the errors above, then build again.')
    ids = [p.pid for p in pages]
    assert len(ids) == len(set(ids)), 'page ids must be unique'
    os.makedirs(out_dir, exist_ok=True)
    drawio = os.path.join(out_dir, basename + '.drawio')
    open(drawio, 'w').write('<mxfile host="drawio" agent="architecture-diagrams-skill">' + ''.join(p.xml() for p in pages) + '</mxfile>')
    if not drawio_available():
        print(f'\nOK  {drawio}\n'
              'NOTE  The draw.io renderer could not be installed here (no internet access in this sandbox), '
              'so PNG and PDF were not produced.\n'
              '      Tell the user: open the .drawio file at https://app.diagrams.net, then\n'
              '      File > Export as > PDF (tick "All pages") and File > Export as > PNG (zoom 200%).')
        return dict(drawio=drawio, pdf=None, pngs=[], sheet=None)
    os.makedirs(os.path.join(out_dir, 'PNG'), exist_ok=True)
    pngs = []
    for i, p in enumerate(pages):
        name = (png_names[i] if png_names else f'{i:02d}_' + re.sub(r'[^A-Za-z0-9]+', '_', p.name).strip('_')) + '.png'
        out = os.path.join(out_dir, 'PNG', name)
        _run_drawio(['-f', 'png', '-s', str(scale), '-p', str(i), '-o', out, drawio])
        pngs.append(out)
    pdf = os.path.join(out_dir, basename + '.pdf')
    _run_drawio(['-f', 'pdf', '-a', '--crop', '-o', pdf, drawio])
    sheet = _contact_sheet(pngs, review_dir)
    print(f'\nOK  {drawio}\nOK  {pdf}\nOK  {len(pngs)} PNGs in {os.path.join(out_dir, "PNG")}\nREVIEW  {sheet} (+ one full-size PNG per page)')
    return dict(drawio=drawio, pdf=pdf, pngs=pngs, sheet=sheet)

def _contact_sheet(pngs, review_dir):
    from PIL import Image
    os.makedirs(review_dir, exist_ok=True)
    ims = [Image.open(p).convert('RGB') for p in pngs]
    tw = 960
    ims = [im.resize((tw, int(im.height * tw / im.width))) for im in ims]
    th = max(im.height for im in ims)
    cols = min(3, len(ims))
    rows = (len(ims) + cols - 1) // cols
    sheet = Image.new('RGB', (cols * tw, rows * th), 'white')
    for i, im in enumerate(ims):
        sheet.paste(im, ((i % cols) * tw, (i // cols) * th))
    out = os.path.join(review_dir, 'contact_sheet.png')
    sheet.save(out)
    for i, im in enumerate(ims):
        im.save(os.path.join(review_dir, f'page_{i:02d}.png'))
    return out
