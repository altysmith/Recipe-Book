# Recipe Book deployment

Live URL: https://recipes.altylab.com

Pi: ealtenho@192.168.10.4. Source is installed at /home/ealtenho/recipe-book from the private GitHub main archive. User data was transferred separately using the SQLite backup export and compared exactly after restore (1 recipe at deployment).

Service: recipe-book.service, loopback port 8771. Existing altylab-tunnel.service routes the hostname and validates the Recipe Book Cloudflare Access audience. Cloudflare application Altylab Recipe Book uses the existing Erica only policy. No new LAN/router port is opened. HTTPS Origin is explicitly configured for saves.

Daily local backups: recipe-book-backup.timer at 03:30 Pi local time, persistent across missed runs; archives in /home/ealtenho/recipe-book-backups. Initial backup succeeded. These backups are on the same Pi; download/export copies off-device periodically. No automatic retention deletion is configured.

The Pi database is now the live collection. The Windows localhost database is a separate pre-deployment copy and will not synchronize edits automatically. Use the domain on both computer and phone. Open online once and wait for Saved on this device before offline use. Actual iPhone airplane-mode verification is still needed.

Updates: copy a new git archive into the existing source directory without overwriting user_data, install requirements if changed, and restart recipe-book.service. Back up data first. Preserve the tunnel's cards.altylab.com rule. Pre-recipe tunnel configuration is ~/.cloudflared/config.before-recipes.yml.
