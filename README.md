# crontab-audit

> Parses and validates crontab entries across multiple hosts, flagging risky or overlapping schedules.

---

## Installation

```bash
pip install crontab-audit
```

Or install from source:

```bash
git clone https://github.com/youruser/crontab-audit.git && cd crontab-audit && pip install .
```

---

## Usage

Point `crontab-audit` at one or more crontab files or remote hosts and let it do the heavy lifting:

```bash
# Audit a local crontab file
crontab-audit audit --file /etc/crontab

# Audit crontabs across multiple hosts defined in a config file
crontab-audit audit --hosts hosts.yaml --output report.json
```

**Example output:**

```
[WARN] host1: /etc/cron.d/backup — schedule "*/5 * * * *" overlaps with job on host2
[ERROR] host3: /var/spool/cron/root — invalid expression "60 * * * *"
[WARN] host1: /etc/crontab — high-frequency job running as root (every 1 min)
```

### `hosts.yaml` format

```yaml
hosts:
  - name: host1
    address: 192.168.1.10
    user: admin
  - name: host2
    address: 192.168.1.11
    user: admin
```

### Flags

| Flag | Description |
|------|-------------|
| `--file` | Path to a local crontab file |
| `--hosts` | YAML file listing remote hosts |
| `--output` | Write results to a JSON file |
| `--strict` | Exit with non-zero status on any warning |

---

## License

This project is licensed under the [MIT License](LICENSE).