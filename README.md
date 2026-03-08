# StackRecon

> Discover what technologies are running behind every public bug bounty program.

**[🌐 Live Site](https://esamlasheen.github.io/StackRecon/)** · **[798 Programs](https://esamlasheen.github.io/StackRecon/)** · **[47+ Technologies](https://esamlasheen.github.io/StackRecon/)**

---

## What is StackRecon?

StackRecon scans all public bug bounty programs and detects the technologies running on their domains — helping bug hunters quickly find the right targets based on the tech stack they know best.

**Find programs running Grafana, Jenkins, Keycloak, WordPress, and 44+ more technologies — instantly.**

![StackRecon Screenshot](https://esamlasheen.github.io/StackRecon/)

---

## Features

- **47+ Technology Signatures** — Grafana, Jenkins, Keycloak, WordPress, GitLab, Jira, Confluence, Kibana, Elasticsearch, Spring Boot, Laravel, Django, Cloudflare, and more
- **4 Combinable Filters** — filter by technology, platform, reward type, or company name
- **Shareable Links** — filter state is saved in the URL hash, share searches with your team
- **Weekly Auto-Updates** — data refreshes automatically every Sunday via GitHub Actions
- **Fast & Offline-Capable** — pure static site, no backend, loads instantly

---

## Live Site

👉 **[https://esamlasheen.github.io/StackRecon/](https://esamlasheen.github.io/StackRecon/)**

---

## Usage

### Run the Scanner Locally

```bash
git clone https://github.com/EsamLasheen/StackRecon.git
cd StackRecon/scanner
pip install -r requirements.txt

# Scan all programs
python3 -m scanner.main

# Quick test with 10 programs
python3 -m scanner.main --limit 10

# Custom workers and output
python3 -m scanner.main --workers 100 --output docs/data/data.json
```

### CLI Options

| Flag | Default | Description |
|------|---------|-------------|
| `--limit N` | all | Process at most N programs |
| `--workers N` | 50 | Concurrent HTTP probe workers (1–500) |
| `--connect-timeout S` | 3 | TCP connect timeout in seconds |
| `--read-timeout S` | 7 | HTTP read timeout in seconds |
| `--output PATH` | `docs/data/data.json` | Output file path |

---

## How It Works

1. **Fetches** the public bug bounty program list from [Chaos ProjectDiscovery](https://github.com/projectdiscovery/public-bugbounty-programs)
2. **Probes** each program's domains with 50 concurrent workers
3. **Detects** technologies from HTTP headers and response bodies using 47+ YAML signatures
4. **Writes** results to a single `data.json` file atomically
5. **Serves** via GitHub Pages — no backend needed

---

## Technology Detection

StackRecon detects technologies across 12 categories:

| Category | Examples |
|----------|---------|
| Monitoring | Grafana, Prometheus, Kibana |
| CI/CD | Jenkins, GitLab CI, ArgoCD, TeamCity |
| Identity/Auth | Keycloak, HashiCorp Vault |
| CMS | WordPress, Drupal, Magento, Shopify |
| Frameworks | Spring Boot, Django, Laravel, Rails |
| Web Servers | Nginx, Apache, Traefik, HAProxy |
| CDN | Cloudflare, Fastly, AWS ALB |
| Search/Data | Elasticsearch, MinIO, Redis |
| Containers | Portainer, Rancher |
| Infrastructure | Consul, Nomad, etcd, RabbitMQ |
| Artifact Registries | SonarQube, Nexus, Harbor |
| DevOps/VCS | GitLab, Gitea, Bitbucket Server |

---

## Development

```bash
# Run tests
python3 -m pytest tests/unit/ tests/integration/ -q

# Check coverage
python3 -m pytest tests/unit/ --cov=scanner/src

# Lint
ruff check scanner/src/
```

---

## Data Source

Program data sourced from [Chaos ProjectDiscovery](https://chaos.projectdiscovery.io/) — the largest public bug bounty recon dataset.

---

## License

MIT
