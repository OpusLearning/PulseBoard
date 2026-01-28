# Pulseboard deploy (server-side)

This directory is a git repo.

## Local deploy (manual)
```bash
cd /var/www/pulseboard
# if a remote is configured:
# git pull --ff-only

# regenerate feed JSON
/usr/local/bin/pulseboard_build

# reload nginx (requires privilege)
# sudo systemctl reload nginx
```

## Notes
- `data/pulse.json` is generated and is not committed.
- Logs are written to `logs/` and not committed.
