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
# Instagram Reel importer deployment (deployed 2026-10-17)

Dependency preparation on 2026-10-17: the Pi already had FFmpeg, Tesseract, and English OCR data. CMake 3.31.6 was installed without upgrading other packages; `yt-dlp==2026.8.19` was installed in the existing app virtual environment. whisper.cpp v1.9.4 (commit `927cfce34f31707e17f2bff35c349632fb9e2c3a`) was built at `/home/ealtenho/whisper.cpp`, and its `tiny.en` model passed the upstream SHA-1 check. A bundled 11-second speech sample transcribed in about 1.3 seconds and produced both `.txt` and `.srt` output. This is a dependency smoke test, not a cooking-video benchmark.

The importer source and service environment were deployed to the Pi on 2026-10-17. The pre-release data backup is `/home/ealtenho/recipe-book-backups/recipes-20261017T150743Z.zip`; the code archive is `/home/ealtenho/recipe-code-before-video-20261017T150743Z.tar.gz`. Verified copies of both are in `C:\Users\erica\Desktop\Codex\Recipe Book Backups`. The staged Pi suite passed 40 tests. A synthetic Pi video with spoken audio and an on-screen `2 tbsp olive oil` label passed FFmpeg decoding, Whisper transcription, Tesseract OCR, and draft quantity extraction. After release, `/health` and `/api/import-video/health` responded, all four tools reported ready, the Video link and `recipe-shell-v11` were served, invalid video URLs returned HTTP 400, and the nine existing recipe records plus one original file matched the backup. An unauthenticated public request still redirected to Cloudflare Access. A local browser flow passed at 390px and 1440px; authenticated iPhone use and a real Instagram Reel download remain for user testing.

The iPhone Instagram entry repair was deployed later on 2026-10-17. The Add Recipe method is labeled **Instagram Reel**. A Reel pasted into Website link now enters the video importer. `https://recipes.altylab.com/instagram` opens that panel using `/app-v12.js`, `/offline-v12.js`, and `/style-v12.css` aliases, which older service workers do not intercept. Service worker `recipe-shell-v12` caches the new shell; IndexedDB recipes and checklists are unaffected. When changing the shell again, update its cache version and versioned asset paths together. The pre-repair data backup is `/home/ealtenho/recipe-book-backups/recipes-20261017T152403Z.zip`, and the code archive is `/home/ealtenho/recipe-code-before-instagram-button-20261017T152403Z.tar.gz`; verified copies are in the same Windows backup folder. Local and staged Pi suites passed 41 tests, and a 390px/1440px browser check passed. After release, `/instagram` and the versioned assets loaded, the importer health check remained ready, all nine recipes and the original file matched the backup, and the public path still redirected unauthenticated visitors to Cloudflare Access. The actual iPhone flow and a real Instagram Reel remain for user testing.

The shell refresh fix uses `recipe-shell-v13`: current HTML and shell assets are fetched online at each reload, with cached copies as the offline fallback. `offline.js` reloads browsing pages when an updated worker takes control; an open editor instead displays a **Load website update** button so draft edits are not lost. `/refresh` and v13 asset URLs bypass the v12 worker for one-time migration. Retain `/refresh` as a stable recovery route and do not add any persistent recipe/checklist clearing. When changing the shell again, bump the cache and asset versions together. Verify an online reload, an offline reload, and an update while an editor is open. Older browsers may show one stale refresh before the new worker takes control; `/refresh` bypasses that transition.

Deployed the shell refresh fix on 2026-10-17. Before release, a consistent backup (`/home/ealtenho/recipe-book-backups/recipes-20261017T153752Z.zip`) and code archive (`/home/ealtenho/recipe-code-before-shell-refresh-20261017T153752Z.tar.gz`) were copied off the Pi and hash checked. The ZIP passed integrity checking and contained nine recipes and one original. Local and staged Pi suites passed 42 tests; browser checks passed in headless Edge for online reload, offline fallback, preserving an open editor, and the 390px/1440px recipe flow. Firefox automation could not be launched in this environment; an authenticated Firefox phone check remains outstanding. The live service is active, v13 shell routes and video tool health respond on the Pi, the unauthenticated public `/refresh` redirects to Cloudflare Access, and all nine recipe documents plus the original file match the pre-release backup. SQLite integrity is `ok`.

The browser may continue showing an offline recipe snapshot after its Cloudflare Access session expires: the shell opens from Cache Storage while `/api/recipes` cannot be fetched. `recipe-shell-v14` adds a visible reconnect link whenever the API fetch fails, leading through `/refresh` and the normal Access sign-in. This retains IndexedDB recipes and checklists. An old v12 or v13 page still requires direct navigation to `/refresh` once, because it has no reconnect link.

The follow-up v15 fix detects Cloudflare Access redirects on API requests and navigates automatically through the uncached `/refresh` route to sign-in. A normal online reload fetches the new shell; users should not need to remember a special URL. The route remains available for recovery but is no longer service-worker cached. Repeat redirects are limited to one automatic attempt per minute, and an open recipe editor is not interrupted. `video_import.py` now allows missing duration metadata through the bounded download and checks the actual file with FFprobe before transcription. The 180-second default limit remains; actual over-limit lengths are shown in the error. Debian's `ffmpeg` package supplies `ffprobe`; `RECIPE_FFPROBE` can override the binary path. Health checks now include FFprobe.

Deployed v15 on 2026-10-17 after backing up live data to `/home/ealtenho/recipe-book-backups/recipes-20261017T181637Z.zip` and code to `/home/ealtenho/recipe-code-before-recovery-20261017T181637Z.tar.gz`; verified copies are in the Windows backup folder. Local and staged Pi suites passed 45 tests. Headless browser checks passed at 390px and 1440px, including simulated Access redirects, preserved open editors, online reload, and offline fallback. Pi FFprobe measured a locally generated two-second video correctly. The live service and tunnel are active; v15 shell, all five importer tools, and `/refresh` respond from the Pi. The public unauthenticated hostname still redirects to Cloudflare Access. The nine live recipe documents and original file matched the backup and SQLite integrity was `ok`. A real Instagram Reel and the authenticated Firefox phone flow remain unverified until tested with a full Reel link and user session.

The source adds `/api/import-video` jobs. This changes no SQLite schema and must not replace `user_data`. The Pi's CPU, RAM, and timing for real clips have not been benchmarked yet; use a short public Reel for the first controlled smoke test while watching service memory and responsiveness.

Reel audio repair (2026-10-17): Instagram may advertise separate DASH video and audio formats alongside a progressive MP4. The importer now prefers a format with audio, checks the downloaded file with FFprobe, and downloads an allowed companion audio stream within the same total byte budget when needed. A real 25-second public Reel at shortcode `DeCU78_A6Fx` completed download, local transcription, OCR, and draft interpretation in about 9 seconds on the Pi staging copy. This is one clip, not a general Pi performance benchmark. Its ten caption ingredients and seven directions reached a draft; no recipe was saved during the check.

The repair was deployed on 2026-10-17 after backing up live data to `/home/ealtenho/recipe-book-backups/recipes-20261017T182956Z.zip` and code to `/home/ealtenho/recipe-code-before-reel-audio-20261017T182956Z.tar.gz`; hash-verified copies are in `C:\Users\erica\Desktop\Codex\Recipe Book Backups`. All 50 tests passed locally and on the Pi staging copy (the latter used the existing isolated ReportLab test dependency directory). The live `/api/import-video` job for that exact Reel completed with ten ingredients, seven directions, and the original source URL. The nine existing recipe documents and original PDF matched the pre-release backup, and SQLite integrity was `ok`. An unauthenticated public request still redirected to Cloudflare Access. The actual iPhone browser flow remains for the user to check.

The Reel field reset was deployed later on 2026-10-17 with `recipe-shell-v16`. Opening a new Add Recipe import clears the previous Reel URL; a failed import keeps it for retry. The v16 shell and assets were served by the Pi after restart. Local browser tests passed at 390px and 1440px, local and staged Pi suites passed 50 tests, and the 11 live recipe documents plus original PDF matched the pre-release backup with SQLite integrity `ok`. Data backup: `/home/ealtenho/recipe-book-backups/recipes-20261017T184648Z.zip`; prior code: `/home/ealtenho/recipe-code-before-clear-reel-20261017T184648Z.tar.gz`. Hash-verified copies are in the Windows backup folder. An authenticated iPhone refresh remains user verification.

Before copying code, run `cd /home/ealtenho/recipe-book && .venv/bin/python deploy/backup.py` on the Pi; copy the resulting ZIP off-device and verify `recipes.sqlite3` with `PRAGMA integrity_check`. Make a code archive excluding `user_data` and `.venv`. Transfer the reviewed source files, including the three new video modules and updated requirements, into the existing source directory without touching `user_data`. **After** the updated `requirements.txt` is on the Pi, install dependencies before restarting the service:

```bash
sudo apt update
sudo apt install -y ffmpeg tesseract-ocr tesseract-ocr-eng cmake build-essential
cd /home/ealtenho/recipe-book
.venv/bin/python -m pip install -r requirements.txt
cd /home/ealtenho
git clone --depth 1 --branch v1.9.4 https://github.com/ggml-org/whisper.cpp.git
cd whisper.cpp
cmake -B build -DCMAKE_BUILD_TYPE=Release
cmake --build build -j2
./models/download-ggml-model.sh tiny.en
```

`tiny.en` is a small English starting model (approximately 75 MB on disk); `base.en` improves some speech but costs more memory and CPU. Model storage and active inference memory are separate. Measure a representative clip on the actual Pi before increasing model size. Place these service environment entries in a systemd drop-in (use `sudo systemctl edit recipe-book.service`):

```ini
[Service]
Environment=RECIPE_WHISPER_CLI=/home/ealtenho/whisper.cpp/build/bin/whisper-cli
Environment=RECIPE_WHISPER_MODEL=/home/ealtenho/whisper.cpp/models/ggml-tiny.en.bin
Environment=RECIPE_YTDLP=/home/ealtenho/recipe-book/.venv/bin/yt-dlp
```

Optional bounds: `RECIPE_VIDEO_MAX_BYTES` (default 80000000, maximum 200000000), `RECIPE_VIDEO_MAX_SECONDS` (default 180, maximum 600), `RECIPE_VIDEO_MAX_FRAMES` (default 16, maximum 40), `RECIPE_VIDEO_PROCESS_TIMEOUT` (default 900 seconds). `RECIPE_FFMPEG` and `RECIPE_TESSERACT` can override binary paths. Only one job processes at a time; one more can wait. Completed results expire from RAM after 30 minutes, and process restart clears all jobs. A running import uses temporary disk for the bounded video, 16 kHz mono WAV (about 32 KB/second), and sampled JPEG frames; these are deleted on completion, failure, or cancellation.

Confirm the source transfer contains `video_import.py`, `video_recipe.py`, and `video_jobs.py`. Then run:

```bash
cd /home/ealtenho/recipe-book
.venv/bin/python -m unittest discover -s tests -q
sudo systemctl daemon-reload
sudo systemctl restart recipe-book.service
systemctl is-active recipe-book.service
curl -fsS http://127.0.0.1:8771/health
curl -fsS http://127.0.0.1:8771/api/import-video/health
```

Check that the new Video link appears after the service worker updates. First test an invalid Reel URL and a short, known public Reel, then review the draft without saving. Confirm normal browsing and an existing website/photo/PDF/text import, then test a deliberate save and reopen. Compare live recipe count and database integrity with the pre-release backup. The public route should still redirect an unauthenticated request to Cloudflare Access; do not change tunnel or Access configuration for this feature. A localhost HTTP response alone does not prove iPhone behavior.

If import says a binary is missing, check the service environment and executable permissions with `systemctl cat recipe-book.service` and `journalctl -u recipe-book.service -n 100`. Instagram can reject unauthenticated download despite a public browser page; do not add cookies or bypass access controls. If transcription times out, try a shorter video or benchmark a smaller model. If OCR is empty, inspect the video text size and Tesseract English installation.

Rollback: preserve `user_data` and the verified backup, restore the prior **code** archive over source files only, restore the previous systemd drop-in if changed, reload systemd, and restart `recipe-book.service`. Keep the new backup until code and saved recipes are verified after rollback. No database migration is needed.
