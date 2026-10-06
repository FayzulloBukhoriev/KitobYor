"""Binary-safe PostgreSQL backup for Windows and Linux: python deploy/backup.py."""
import os
import subprocess
from datetime import datetime,timezone
from pathlib import Path

root=Path(__file__).resolve().parent.parent
folder=root/'backups';folder.mkdir(mode=0o700,exist_ok=True)
target=folder/f'kitobyor-{datetime.now(timezone.utc):%Y%m%dT%H%M%S%fZ}.dump'
partial=target.with_suffix('.part')
try:
    with partial.open('xb') as output:
        try:os.chmod(partial,0o600)
        except OSError:pass
        subprocess.run(['docker','compose','exec','-T','db','sh','-c','exec pg_dump -U "$POSTGRES_USER" -d "$POSTGRES_DB" -Fc'],cwd=root,stdout=output,check=True)
    partial.replace(target)
    print(f'Backup saved: {target} ({target.stat().st_size} bytes)')
except BaseException:
    partial.unlink(missing_ok=True)
    raise
