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
- **Live scan progress bar** — see the scan running in real time on the dashboard
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
