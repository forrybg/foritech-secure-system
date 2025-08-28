# Backup / Diagnostics

## Quick diagnostics
Run:
./scripts/diag_status.sh
Shows repo/tags, Python & package versions, Foritech CLI path, keys dir, local PKI.

## Snapshot backup (local, out-of-git)
Run:

./scripts/backup_snapshot.sh
Creates `backups/<timestamp>/` with:
* `repo-tracked.tar.gz` — current tracked files
* `HEAD.txt`, `status.txt` — metadata
* `foritech-keys.tar.gz` — your `~/.foritech/keys` (if present)
* `pki.tar.gz` — local `./pki` (if present)

> **Important:** `backups/` is not tracked by git (recommended).  
> To hide it from `git status` locally:
> ```
> echo backups/ >> .git/info/exclude
> ```

## Offsite
Copy `backups/<timestamp>/` to an offline/secure location.

## Restore (example)
Untar what you need (repo snapshot, keys, pki). Keys & PKI contain secrets — handle with care.
