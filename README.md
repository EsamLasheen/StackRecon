# StackRecon

> Automated weekly reconnaissance across every public bug bounty program.

**[🌐 Live Dashboard](https://esamlasheen.github.io/StackRecon/)** · **[798 Programs](https://esamlasheen.github.io/StackRecon/)** · **[6,000+ Live Hosts](https://esamlasheen.github.io/StackRecon/)** · **[Weekly Auto-Scan](https://esamlasheen.github.io/StackRecon/)**

---

StackRecon scans every public bug bounty program every week and fingerprints their entire tech stack — detecting technologies, exposed services, and real misconfigurations using **httpx** + **nuclei**.

Built for security researchers who want to find the right targets fast.

---

## What it does

Every Monday, a GitHub Actions workflow:

1. Pulls ~800 programs from [Chaos ProjectDiscovery](https://chaos.projectdiscovery.io/)
2. Generates ~102,000 subdomain candidates using 25 security-focused prefixes
3. Runs `httpx` with Wappalyzer fingerprints → detects 1,400+ technologies
4. Runs `nuclei` with custom templates → finds real misconfigs and CVEs
5. Scores programs by severity (Critical / High / Medium)
6. Publishes results to the live dashboard automatically

---

## Features

- **1,400+ technology fingerprints** via httpx + Wappalyzer
- **Custom nuclei templates** from the community for real vulnerability detection
- **Severity scoring** — programs ranked by actual findings
- **25 subdomain prefixes** targeting `admin.`, `api.`, `grafana.`, `jenkins.`, `k8s.`, `vault.`, `gitlab.`, and more
- **Scan status** — failed batches retain the last complete dashboard results
- **5 combinable filters** — tech stack, platform, reward type, severity, name
- **One-click subdomain copy** — filter by technology, copy all matching hosts
- **Shareable filter links** — state saved in URL hash
- **Pure static site** — no backend, no database, instant load

---

## Live Dashboard

👉 **[https://esamlasheen.github.io/StackRecon/](https://esamlasheen.github.io/StackRecon/)**

---

## Run locally

```bash
# Dependencies
go install github.com/projectdiscovery/httpx/cmd/httpx@latest
go install github.com/projectdiscovery/nuclei/v3/cmd/nuclei@latest

git clone https://github.com/EsamLasheen/StackRecon.git
cd StackRecon
pip install -r scanner/requirements.txt

# Quick test (5 programs)
python3 -m scanner.main --limit 5

# Full scan with custom templates
python3 -m scanner.main \
  --workers 100 \
  --templates /path/to/nuclei-templates \
  --progress docs/data/progress.json \
  --output docs/data/data.json
```

### CLI flags

| Flag | Default | Description |
|------|---------|-------------|
| `--workers N` | 50 | Concurrent threads |
| `--limit N` | all | Scan at most N programs |
| `--templates PATH` | built-in | Custom nuclei templates directory |
| `--progress PATH` | none | Write live progress JSON |
| `--output PATH` | `docs/data/data.json` | Output file |
| `--connect-timeout S` | 3 | TCP connect timeout |
| `--read-timeout S` | 7 | HTTP read timeout |
| `--program-index PATH` | none | Frozen program list shared by scan jobs |
| `--shard-index N` | 0 | Zero-based hostname batch |
| `--shard-count N` | 1 | Number of disjoint hostname batches |
| `--strict` | off | Reject failed or timed-out phases; required for batches |

### Weekly scan recovery

The workflow freezes the complete program index once, then divides its unique hostnames
across 16 jobs (at most four running together). No program limit is applied. Each job uses
75 httpx workers at 37 requests/second and Nuclei host-spray with concurrency/bulk size 10
at 250 requests/second. Strict phase budgets are one hour for httpx, up to 150 minutes for
Nuclei vulnerabilities, and up to 90 minutes for Nuclei information gathering.

Only the publisher writes to the repository. It validates every batch against the same
index, merges results, and computes the dashboard diff once. A missing, failed, or timed-out
batch blocks data publication. Re-run failed jobs to retry their complete batches; there
is no per-target resume. Batch artifacts are retained for seven days. Full report artifacts
follow the repository's access controls; they are not owner-only in a public repository.

The initial 16-job setting needs confirmation with a full run. Version output, periodic
resource samples, and process resource summaries are logged for diagnosis. The workflow
still uses the existing tool/template sources; it does not pin a speculative replacement
version. Dashboard progress is published at completion or failure, rather than from each
batch while it runs.

---

## Detection coverage

| Category | Examples |
|----------|---------|
| Monitoring | Grafana, Prometheus, Kibana, Datadog, Zabbix |
| CI/CD | Jenkins, GitLab, ArgoCD, TeamCity, Bamboo |
| Identity | Keycloak, HashiCorp Vault, Okta, Auth0 |
| CMS | WordPress, Drupal, Magento, Joomla |
| Frameworks | Spring Boot, Django, Laravel, Rails, Next.js |
| Web Servers | Nginx, Apache, Traefik, HAProxy, Caddy |
| Cloud/CDN | Cloudflare, AWS ALB, Akamai, Fastly |
| Containers | Portainer, Rancher, Kubernetes Dashboard |
| Databases | MySQL, PostgreSQL, MongoDB, Elasticsearch |
| + 1,300 more via Wappalyzer |

---

## Data source

Program list from [Chaos ProjectDiscovery](https://chaos.projectdiscovery.io/) — the largest public bug bounty recon dataset.

---

## License

MIT
