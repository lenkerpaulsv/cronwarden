# cronwarden

> A CLI tool to audit and validate cron job schedules across multiple servers with conflict detection.

---

## Installation

```bash
pip install cronwarden
```

Or install from source:

```bash
git clone https://github.com/youruser/cronwarden.git && cd cronwarden && pip install .
```

---

## Usage

Audit cron jobs on one or more servers:

```bash
cronwarden audit --hosts server1.example.com server2.example.com
```

Validate a crontab file and detect scheduling conflicts:

```bash
cronwarden validate --file /etc/cron.d/myjobs
```

Check for overlapping schedules across a fleet:

```bash
cronwarden check-conflicts --config servers.yml --threshold 5m
```

**Example output:**

```
[WARN] Conflict detected: job "backup_db" on server1 overlaps with "backup_db" on server2 (offset: 2m)
[OK]   No invalid expressions found in /etc/cron.d/myjobs
[INFO] Audit complete: 3 jobs checked, 1 warning
```

Run `cronwarden --help` to see all available commands and options.

---

## Configuration

cronwarden accepts a YAML config file to define server groups and alert thresholds. See [`config.example.yml`](config.example.yml) for a full reference.

---

## License

This project is licensed under the [MIT License](LICENSE).