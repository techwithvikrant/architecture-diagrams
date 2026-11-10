"""Generic worked example: monolith on VMs -> microservices on Kubernetes, told as a phased story.

Pattern shown: ONE shared layout (NODES + EDGES defined once), every page = a status map.
  status: existing | new | modified | retire ; leave a key out = component no longer drawn.
Run:  python3 build.py [out_dir]
"""
import os, sys
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, '..', '..', 'scripts'))
from drawio_lib import Page, build

# ---------------------------------------------------------------- shared layout (absolute px, 1920x1080)
NODES = {  # key: (x, y, w, h, title, sub, icon)
    'client':   (40, 400, 200, 70, 'Web & mobile clients', '', 'user'),
    'lb':       (300, 395, 180, 80, 'Load balancer', 'TLS termination', 'lb'),
    'monolith': (580, 160, 260, 120, 'Monolith app', 'Java EE on VMs<br>orders, catalog, payments', 'openjdk'),
    'oracle':   (1180, 160, 240, 60, 'Oracle DB', 'single primary', 'oracle'),
    'nfs':      (1180, 230, 240, 60, 'NFS file share', 'product images', 'file'),
    'nagios':   (1530, 150, 340, 70, 'VM monitoring', 'host checks, log files', 'gear'),
    'gw':       (580, 540, 220, 220, 'API gateway', 'routing, auth,<br>rate limits', 'nginx'),
    'catalog':  (860, 540, 220, 60, 'Catalog service', '', 'nodedotjs'),
    'orders':   (860, 620, 220, 60, 'Orders service', '', 'go'),
    'payments': (860, 700, 220, 60, 'Payments service', '', 'python'),
    's3':       (1180, 540, 240, 60, 'Object storage', 'S3-compatible', 'cloud'),
    'pg':       (1180, 620, 240, 60, 'PostgreSQL', 'managed, HA', 'postgresql'),
    'mq':       (1180, 700, 240, 60, 'Message queue', 'async events', 'queue'),
    'obs':      (1530, 560, 340, 90, 'Observability', 'metrics, logs, traces<br>dashboards and alerts', 'grafana'),
}
EDGES = {  # key: (src, dst, waypoints)
    'c_lb':     ('client', 'lb', [(240, 435), (300, 435)]),
    'lb_mono':  ('lb', 'monolith', [(390, 395), (390, 220), (580, 220)]),
    'mono_ora': ('monolith', 'oracle', [(840, 190), (1180, 190)]),
    'mono_nfs': ('monolith', 'nfs', [(840, 260), (1180, 260)]),
    'leg_mon':  ('cLegacy', 'nagios', [(1480, 185), (1530, 185)]),
    'lb_gw':    ('lb', 'gw', [(390, 475), (390, 595), (580, 595)]),
    'gw_mono':  ('gw', 'monolith', [(760, 540), (760, 280)]),
    'gw_cat':   ('gw', 'catalog', [(800, 570), (860, 570)]),
    'gw_ord':   ('gw', 'orders', [(800, 650), (860, 650)]),
    'gw_pay':   ('gw', 'payments', [(800, 730), (860, 730)]),
    'cat_s3':   ('catalog', 's3', [(1080, 570), (1180, 570)]),
    'ord_pg':   ('orders', 'pg', [(1080, 650), (1180, 650)]),
    'pay_mq':   ('payments', 'mq', [(1080, 730), (1180, 730)]),
    'nfs_s3':   ('nfs', 's3', [(1420, 260), (1440, 260), (1440, 570), (1420, 570)]),
    'ora_pg':   ('oracle', 'pg', [(1420, 190), (1460, 190), (1460, 650), (1420, 650)]),
    'new_obs':  ('cNew', 'obs', [(1480, 605), (1530, 605)]),
}
LABELS = {  # edge key: (x, y, text, align)
    'c_lb': (270, 418, 'HTTPS', 'center'),
    'gw_mono': (768, 400, 'legacy routes', 'left'),
}
LEGEND = [('existing', 'Existing / unchanged'), ('new', 'Added this phase'), ('modified', 'Changed'),
          ('retire', 'Retiring this phase'), ('k8s', 'Runs on Kubernetes')]


def page(pid, name, title, subtitle, nodes, edges, why_head, why, tags=None, legend=LEGEND):
    p = Page(pid, name)
    p.header(title, subtitle)
    p.legend(legend)
    p.lanes([(30, 240, 'CLIENTS'), (290, 200, 'EDGE'), (540, 560, 'APPLICATION'),
             (1160, 280, 'DATA'), (1530, 340, 'OPERATIONS')])
    legacy = any(k in nodes for k in ('monolith', 'oracle', 'nfs'))
    modern = any(k in nodes for k in ('gw', 'catalog', 'orders', 'payments'))
    if legacy:
        p.container('cLegacy', 540, 110, 940, 220, 'Legacy platform (VMs)')
    if modern:
        p.container('cNew', 540, 480, 940, 320, 'Cloud-native platform', fill='#F0FDF4', stroke='#86EFAC', font='#065F46')
        p.k8s_zone('k8s', 560, 515, 540, 265)
    for k, st in nodes.items():
        x, y, w, h, t, s, ic = NODES[k]
        p.node(k, x, y, w, h, t, s, status=st, icon=ic, valign='middle',
               tag=(tags or {}).get(k), k8s=k in ('gw', 'catalog', 'orders', 'payments'))
    for k, st in edges.items():
        a, b, pts = EDGES[k]
        p.edge(k, a, b, pts, status=st)
        if k in LABELS:
            x, y, t, al = LABELS[k]
            p.label(x, y, t, align=al)
    p.why(why_head, why)
    return p


def cover():
    p = Page('cov', '0. Cover')
    p.rect('bg', 0, 0, 1920, 1080, '', 'rounded=0;fillColor=#0F172A;strokeColor=none;')
    p.rect('bar', 120, 330, 10, 230, '', 'rounded=0;fillColor=#22C55E;strokeColor=none;')
    p.text(160, 320, 1500, 70, 'Application Modernization', size=54, color='#FFFFFF', align='left', bold=True, bg=False, role='decor')
    p.text(160, 400, 1500, 50, 'From a monolith on VMs to microservices on Kubernetes', size=28, color='#CBD5E1', align='left', bg=False, role='decor')
    p.text(160, 470, 1500, 40, 'Current state · Phase 1 · Phase 2 · Target state', size=20, color='#94A3B8', align='left', bg=False, role='decor')
    return p


E = 'existing'
pages = [cover()]
pages.append(page('cur', '1. Current State', 'Current State: Monolith on Virtual Machines',
    'One deployable unit, one database and one file share serve every feature', 
    {k: E for k in ('client', 'lb', 'monolith', 'oracle', 'nfs', 'nagios')},
    {k: E for k in ('c_lb', 'lb_mono', 'mono_ora', 'mono_nfs', 'leg_mon')},
    'Why change', [
        '<b>Every release ships everything:</b> a small catalog change needs a full regression and a maintenance window.',
        '<b>Scaling is all or nothing:</b> peak checkout traffic forces scaling the whole monolith and its VMs.',
        '<b>Single points of failure:</b> one database primary and one NFS share back every feature.',
        '<b>Limited visibility:</b> host checks and log files cannot trace a request across components.',
    ]))
pages.append(page('ph1', '2. Phase 1', 'Phase 1: Add an API Gateway and Extract the Catalog',
    'The gateway fronts all traffic; one low-risk domain moves to Kubernetes first',
    {'client': E, 'lb': E, 'monolith': E, 'oracle': E, 'nfs': E, 'nagios': E,
     'gw': 'new', 'catalog': 'new', 's3': 'new', 'obs': 'new'},
    {'c_lb': E, 'lb_mono': 'retire', 'mono_ora': E, 'mono_nfs': E, 'leg_mon': E,
     'lb_gw': 'new', 'gw_mono': 'new', 'gw_cat': 'new', 'cat_s3': 'new', 'nfs_s3': 'new', 'new_obs': 'new'},
    'Why start here', [
        '<b>Strangler pattern:</b> the gateway sends catalog calls to the new service and everything else to the monolith, so users see no change.',
        '<b>Lowest-risk domain first:</b> catalog is read-heavy and has no payment logic; images are copied from NFS to object storage.',
        '<b>Platform proven early:</b> Kubernetes, CI/CD and the new observability stack run real traffic from day one.',
        '<b>Exit gate:</b> catalog error rate and latency match the monolith for 2 weeks.',
    ]))
pages.append(page('ph2', '3. Phase 2', 'Phase 2: Move Orders and Payments, Retire the Monolith',
    'Core domains move with data sync, then the legacy platform is switched off',
    {'client': E, 'lb': E, 'monolith': 'retire', 'oracle': 'retire', 'nfs': 'retire', 'nagios': 'retire',
     'gw': E, 'catalog': E, 's3': E, 'obs': E, 'orders': 'new', 'payments': 'new', 'pg': 'new', 'mq': 'new'},
    {'c_lb': E, 'mono_ora': 'retire', 'mono_nfs': 'retire', 'leg_mon': 'retire', 'lb_gw': E,
     'gw_mono': 'retire', 'gw_cat': E, 'cat_s3': E, 'nfs_s3': 'retire', 'new_obs': E,
     'gw_ord': 'new', 'gw_pay': 'new', 'ord_pg': 'new', 'pay_mq': 'new', 'ora_pg': 'new'},
    'Why this order', [
        '<b>Data first, then traffic:</b> change data capture keeps PostgreSQL in sync with Oracle until cut-over.',
        '<b>Payments decoupled:</b> events on the message queue remove synchronous calls between orders and payments.',
        '<b>Clean retirement:</b> once no gateway route points at the monolith, the VMs, Oracle and NFS are switched off.',
        '<b>Exit gate:</b> zero legacy routes for 30 days and reconciled order and payment totals.',
    ]))
pages.append(page('tgt', '4. Target State', 'Target State: Microservices on Kubernetes',
    'Independent services, managed data stores and one observability platform',
    {k: 'new' for k in ('client', 'lb', 'gw', 'catalog', 'orders', 'payments', 's3', 'pg', 'mq', 'obs')},
    {k: 'new' for k in ('c_lb', 'lb_gw', 'gw_cat', 'gw_ord', 'gw_pay', 'cat_s3', 'ord_pg', 'pay_mq', 'new_obs')},
    'Why this is the end state', [
        '<b>Independent releases:</b> each service ships and scales on its own.',
        '<b>Resilient data:</b> managed, highly available stores replace single-instance Oracle and NFS.',
        '<b>End-to-end visibility:</b> metrics, logs and traces for every request in one place.',
    ], legend=[('new', 'Target component'), ('k8s', 'Runs on Kubernetes')]))

out = sys.argv[1] if len(sys.argv) > 1 else '/tmp/example-out'
build(pages, out, 'Modernization_Architecture',
      png_names=['00_Cover', '01_Current_State', '02_Phase1', '03_Phase2', '04_Target_State'])
