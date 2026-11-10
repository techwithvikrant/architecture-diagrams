# Icons

`icon=` on `p.node(...)` accepts either a **Simple Icons slug** (brand logo, auto-downloaded from
cdn.jsdelivr.net/npm/simple-icons@13 and coloured with the brand colour) or a **built-in generic icon**.

## Built-in generic icons (no network)
`lb`, `db`, `server`, `apps`, `file`, `probe`, `cloud`, `queue`, `user`, `lock`, `gear`

## Bundled brand icons (offline)
opentelemetry, apachekafka, elasticsearch, logstash, kibana, beats, prometheus, grafana, postgresql,
clickhouse, kubernetes, ceph, oracle, openjdk, jaeger, redhatopenshift

## Other common slugs (fetched on demand)
nginx, redis, mysql, mongodb, rabbitmq, docker, apachespark, terraform, argo, helm, istio,
envoyproxy, python, nodedotjs, go, react, minio, apacheairflow, apachecassandra, apacheflink,
vault (hashicorp: `vault`), consul, githubactions, gitlab, jenkins, sonarqube, keycloak, traefikproxy,
datadog, splunk, dynatrace, newrelic, snowflake, databricks, mariadb, sqlite, nats

Notes:
- Simple Icons doesn't carry some corporate marks (Microsoft SQL Server, AWS service icons). Use the
  generic `db` / `cloud` icon with a clear label instead.
- If a slug isn't found, the build prints a warning and uses the generic `server` icon. Pick another slug or a generic icon.
- Add brand colours for new slugs in `BRAND` in `scripts/drawio_lib.py`.
- Brand logos are trademarks of their owners. Use them only to identify the product.
