# StackRecon

> Bug bounty technology intelligence — powered by httpx + nuclei.

**[🌐 Live Site](https://esamlasheen.github.io/StackRecon/)** · **[798 Programs](https://esamlasheen.github.io/StackRecon/)** · **[Daily Updates](https://esamlasheen.github.io/StackRecon/)**

---

## What is StackRecon?

StackRecon automatically scans every public bug bounty program and maps their entire tech stack — detecting 1,400+ technologies and real misconfigurations using industry-standard tools.

**Built for bug hunters who want to find the right targets fast.**

---

## Features

- **1,400+ Technology Detection** — powered by [httpx](https://github.com/projectdiscovery/httpx) with Wappalyzer fingerprints
- **Misconfiguration Detection** — [nuclei](https://github.com/projectdiscovery/nuclei) scans for exposed panels, default credentials, and misconfigs
- **Severity Scoring** — programs ranked Critical / High / Medium based on real findings
- **80+ Subdomain Prefixes** — probes `api.`, `admin.`, `grafana.`, `jenkins.`, `k8s.`, `vault.`, and more per domain
- **Daily Auto-Updates** — GitHub Actions runs the full scan every day automatically
- **5 Combinable Filters** — filter by technology, platform, reward type, severity, or name
- **Copy All Subdomains** — select a technology, copy every matching subdomain in one click
- **Shareable Links** — filter state saved in URL hash
- **Auto-Refresh** — frontend silently updates every 15 minutes without page reload
- **Pure Static Site** — no backend, no database, loads instantly

---

## Live Site

👉 **[https://esamlasheen.github.io/StackRecon/](https://esamlasheen.github.io/StackRecon/)**

---

## How It Works

```
GitHub Actions (daily at 02:00 UTC)
  ↓
Fetch 798 programs from Chaos ProjectDiscovery
  ↓
Generate ~64,000 subdomain candidates (80 prefixes × domains)
  ↓
httpx -tech-detect → 1,400+ Wappalyzer fingerprints
  ↓
nuclei (panel + exposure + misconfig + default-login templates)
  ↓
Severity scoring: Critical / High / Medium per program
  ↓
Commit data.json → GitHub Pages auto-deploys
```

---

## Scanner Setup (local)

Requires **httpx** and **nuclei** binaries on PATH:

```bash
# Install Go tools
go install github.com/projectdiscovery/httpx/cmd/httpx@latest
go install github.com/projectdiscovery/nuclei/v3/cmd/nuclei@latest
nuclei -update-templates

# Clone and install Python deps
git clone https://github.com/EsamLasheen/StackRecon.git
cd StackRecon
pip install -r scanner/requirements.txt

# Quick test (10 programs)
python3 -m scanner.main --limit 10

# Full scan
python3 -m scanner.main --workers 100 --output docs/data/data.json
```

### CLI Options

| Flag | Default | Description |
|------|---------|-------------|
| `--limit N` | all | Process at most N programs |
| `--workers N` | 50 | Concurrent threads |
| `--connect-timeout S` | 3 | TCP connect timeout |
| `--read-timeout S` | 7 | HTTP read timeout |
| `--output PATH` | `docs/data/data.json` | Output file |

---

## Detection Coverage

### Technologies (via httpx + Wappalyzer)

| Category | Examples |
|----------|---------|
| Monitoring | Grafana, Prometheus, Kibana, Datadog |
| CI/CD | Jenkins, GitLab CI, ArgoCD, TeamCity, GoCD |
| Identity/Auth | Keycloak, HashiCorp Vault, Okta |
| CMS | WordPress, Drupal, Magento, Shopify |
| Frameworks | Spring Boot, Django, Laravel, Rails, Express |
| Web Servers | Nginx, Apache, Traefik, HAProxy, Caddy |
| CDN/Cloud | Cloudflare, Fastly, AWS ALB, Akamai |
| Containers | Portainer, Rancher, Kubernetes Dashboard |
| Infrastructure | Consul, Nomad, etcd, RabbitMQ, Kafka |
| Registries | SonarQube, Nexus, Harbor, Artifactory |
| + 1,390 more via Wappalyzer fingerprints |

### Misconfigurations (via nuclei)

- Exposed admin panels (Jenkins no-auth, Grafana anonymous access)
- Default credentials on management interfaces
- Exposed `.git` repositories and `.env` files
- Spring Boot Actuator endpoints open
- Elasticsearch / Kibana unauthenticated
- phpMyAdmin publicly accessible
- 8,000+ nuclei community templates

---

## Development

```bash
# Run tests (87%+ coverage)
python3 -m pytest tests/unit/ tests/integration/ -q

# Lint + format
ruff check scanner/src/ scanner/main.py
black --check scanner/src/ scanner/main.py
```

---

## Data Source

Program list sourced from [Chaos ProjectDiscovery](https://chaos.projectdiscovery.io/) — the largest public bug bounty recon dataset.

---

## License

MIT
