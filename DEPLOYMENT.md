# Recipe Book deployment

Live URL: https://recipes.altylab.com

Pi: ealtenho@192.168.10.4. Source is installed at /home/ealtenho/recipe-book from the private GitHub main archive. User data was transferred separately using the SQLite backup export and compared exactly after restore (1 recipe at deployment).

Service: recipe-book.service, loopback port 8771. Existing altylab-tunnel.service routes the hostname and validates the Recipe Book Cloudflare Access audience. Cloudflare application Altylab Recipe Book uses the existing Erica only policy. No new LAN/router port is opened. HTTPS Origin is explicitly configured for saves.

Daily local backups: recipe-book-backup.timer at 03:30 Pi local time, persistent across missed runs; archives in /home/ealtenho/recipe-book-backups. Initial backup succeeded. These backups are on the same Pi; download/export copies off-device periodically. No automatic retention deletion is configured.

The Pi database is now the live collection. The Windows localhost database is a separate pre-deployment copy and will not synchronize edits automatically. Use the domain on both computer and phone. Open online once and wait for Saved on this device before offline use. Actual iPhone airplane-mode verification is still needed.

Updates: copy a new git archive into the existing source directory without overwriting user_data, install requirements if changed, and restart recipe-book.service. Back up data first. Preserve the tunnel's cards.altylab.com rule. Pre-recipe tunnel configuration is ~/.cloudflared/config.before-recipes.yml.

## September 10 compact shelf update

Deployed compact rows, 16 preset categories, and structured website photo downloads. Service worker version: recipe-shell-v4. All 15 tests passed on the Pi; a real website photo import succeeded. All 3 live recipe records exactly matched the pre-update backup after deployment.

SSH requires the explicit key: `ssh -i "$env:USERPROFILE/.ssh/altylab_pi_ed25519" ealtenho@192.168.10.4` in PowerShell.

Data backup: `/home/ealtenho/recipe-book-backups/recipes-20260911T024024Z.zip`. Previous application archive: `/home/ealtenho/recipe-code-before-20260911.tar`. Public domain still redirects unauthenticated requests to login. ReportLab was installed only in the update staging test-deps directory for PDF tests.

Photo-link update deployed: editor has Photo URL and Use photo link; downloads remain drafts until saved. Mobile browser checks passed for preview, failure preservation, and no automatic saves. Live service verified active with recipe-shell-v5. Backup: recipes-20260911T034421Z.zip. Previous UI: /home/ealtenho/recipe-before-photo-link.tar.

Import UI update deployed September 11: recipe-shell-v6. One method at a time, full-width website link, separate review step. Desktop (1440px) and mobile (390px) browser checks passed. Live web endpoints verified. Backup: recipes-20260911T181327Z.zip. Prior UI archive: /home/ealtenho/recipe-import-ui-before-v6.tar. Only four web files deployed; no recipe records changed.

Photo recipe import deployed September 11: recipe-shell-v8. Private Tesseract English OCR installed on the Pi; up to four browser-resized pages create an editable draft with source photos. Backup: recipes-20260911T185902Z.zip. Code backup: /home/ealtenho/recipe-before-photo-import-20260911T185902Z.tar. Local suite: 19 tests passed; Pi OCR suite: 4 passed; live synthetic image import passed and live recipe records were unchanged. Mobile-sized Edge check at 390px passed with no overflow or JavaScript errors. Real cookbook and actual iPhone testing remain pending.
