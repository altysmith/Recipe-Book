"""Daily local backup; copy backups off the Pi separately."""
from datetime import datetime, timezone
from pathlib import Path
from urllib.request import urlopen
import zipfile
import io
root=Path('/home/ealtenho/recipe-book-backups')
root.mkdir(mode=0o700,exist_ok=True)
data=urlopen('http://127.0.0.1:8771/api/backup',timeout=120).read()
with zipfile.ZipFile(io.BytesIO(data)) as archive:
    if archive.testzip(): raise RuntimeError('Backup archive failed verification')
target=root/('recipes-'+datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')+'.zip')
target.write_bytes(data)
print(target.name)
