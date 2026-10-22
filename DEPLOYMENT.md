# Recipe Book deployment

## 2026-10-21 Safari update recovery

Commit `42ab3d8` adds a no-store `/api/site-version` check when the app opens, returns to the foreground, and remains open. An available update loads through the uncached `/refresh` route, then restores the normal cached address for offline use. Open recipe, weekly-menu, and grocery drafts show a **Load website update** button instead of being replaced. Shell and asset version: `recipe-shell-v28`. If a phone is still running a pre-v28 saved screen, open `https://recipes.altylab.com/refresh` once in Safari to enter the new update path.

The pre-release data backup is `/home/ealtenho/recipe-book-backups/recipes-20261022T010652Z.zip`, with a hash-matched off-Pi copy in `C:\Users\erica\Desktop\Codex\Recipe Book Backups`. The prior code is `/home/ealtenho/recipe-release-safari-20261021/before-code.tar.gz`; the off-Pi copy is `recipe-safari-20261021-before-code.tar.gz`. The local and Pi staging suites each passed 57 tests, and the browser shell test passed online refresh, offline fallback, draft protection, and version-check recovery. The five deployed files matched the tested source hashes. A 390px Pi-origin browser session opened 14 recipes and the weekly menu with no page errors or horizontal overflow. The service and tunnel are active, the public hostname still redirects anonymous requests to Cloudflare Access, and the Pi serves v28. The post-release backup `/home/ealtenho/recipe-book-backups/recipes-20261022T010936Z.zip` matched the pre-release recipe, menu, grocery, and original-file exports byte for byte; SQLite integrity is `ok`. Audrey's authenticated iPhone Safari behavior still requires a check on her device.

## 2026-10-21 multiline groceries follow-up

Commit `26a9474` changes grocery entry to a multiline draft with a Save button below it. Each nonempty line becomes one shared checklist item in one transaction; existing items remain. An unsaved draft prompts before navigation and is protected from an automatic service-worker reload. The shell is `recipe-shell-v27`.

Pre-release data backup: `/home/ealtenho/recipe-book-backups/recipes-20261022T003141Z.zip`. Prior code archive: `/home/ealtenho/recipe-release-bulk-groceries-20261021/before-code.tar.gz`. Hash-matched copies are in `C:\Users\erica\Desktop\Codex\Recipe Book Backups`. Local and Pi staging suites passed 57 tests; the local shared-list and weekly-menu browser checks passed at 390px and 1440px. A read-only Pi-origin browser check at 320px, 390px, and 1440px confirmed the textarea, Save button, and no checklist write before Save, with no horizontal overflow or page errors. The service and tunnel are active, v27 assets respond, and the public hostname redirects anonymous requests to Cloudflare Access. The post-release backup `/home/ealtenho/recipe-book-backups/recipes-20261022T003328Z.zip` matched all 13 recipes, one weekly menu, zero grocery items, and one original PDF from the pre-release backup; SQLite integrity remained `ok`. Authenticated phone interaction remains unverified.

## 2026-10-21 shared groceries release

Commit `dc78cf8` adds a shared grocery list to Lolo’s Kitchen. Eric and Audrey can add items, check them off, remove one item, clear checked items, or reset the whole list. The items live in `user_data/recipes.sqlite3` and are included in `/api/backup` as a table and `groceries.json`. The shell is `recipe-shell-v26`.

Pre-release data backup: `/home/ealtenho/recipe-book-backups/recipes-20261022T002227Z.zip`. Prior code archive: `/home/ealtenho/recipe-release-groceries-20261021/before-code.tar.gz`. Hash-matched copies are in `C:\Users\erica\Desktop\Codex\Recipe Book Backups`. The seven changed source files were staged and the Pi suite passed 56 tests using the existing isolated ReportLab test dependency. Local 56-test and two-browser grocery checks passed. The production service and tunnel are active, and the Pi origin serves v26 assets and an empty `/api/groceries` list. A read-only browser check through the Pi origin passed at 390px and 1440px, with no horizontal overflow or page errors. A post-release backup at `/home/ealtenho/recipe-book-backups/recipes-20261022T002400Z.zip` showed unchanged 13 recipes, one weekly menu, and one original PDF, SQLite integrity `ok`, and no grocery items. The public hostname redirects anonymous requests to Cloudflare Access. Authenticated phone interaction remains unverified.

## 2026-10-21 paired mobile header buttons

Commit `471829b` places **Weekly menu** and **+ Add a recipe** side by side in the phone header. At 370px and below, the two buttons share a second header row. The shell is `recipe-shell-v25`. The pre-release data backup is `/home/ealtenho/recipe-book-backups/recipes-20261021T220000Z.zip`; the prior code is `/home/ealtenho/recipe-release-mobile-header-20261021/before-code.tar.gz`. Hash-matched copies of both are in `C:\Users\erica\Desktop\Codex\Recipe Book Backups`.

All 54 tests passed locally and in Pi staging. Browser checks through the Pi origin at 390px and 320px found both header buttons visible and side by side, with no horizontal overflow or page errors. The service and tunnel are active; v25 assets and `/menu` respond. SQLite integrity is `ok`, the 13 recipe rows and original PDF retain their pre-release digests, and the saved weekly menu remains present. The public hostname still redirects unauthenticated requests to Cloudflare Access. The user's physical phone remains the final visual check.

## 2026-10-21 mobile menu entry repair

Commit `419b597` deployed a direct `/menu` page that bypasses older service-worker shell caches, opens the weekly menu, and shows a Weekly menu button in the mobile header. `recipe-shell-v24` also keeps an open menu in view when a worker update arrives. The pre-release data backup is `/home/ealtenho/recipe-book-backups/recipes-20261021T215347Z.zip`; the code rollback archive is `/home/ealtenho/recipe-release-mobile-menu-20261021/before-code.tar.gz`. Both have hash-matched off-device copies in `C:\Users\erica\Desktop\Codex\Recipe Book Backups`.

All 54 tests passed in Pi staging, and the local weekly-menu browser check passed at 390px and 1440px. A phone-width, touch-enabled browser check through the Pi origin opened `/menu` directly, showed the header and bottom menu controls, found all seven day fields, and had no horizontal overflow or page errors. The Pi service and tunnel are active, `/menu` and v24 assets respond, 13 recipe rows and the original PDF retain their pre-release digests, and SQLite integrity is `ok`. The public `/menu` route redirects unauthenticated requests to Cloudflare Access. The user's actual phone screen still needs confirmation.

## 2026-10-21 weekly menu release

Commit `5c1776c` deployed the Saturday–Friday weekly menu, Snacks, Lunches, Sweet treats, and the compact saved-menu view. The live app serves `recipe-shell-v23`. The pre-release database backup is `/home/ealtenho/recipe-book-backups/recipes-20261021T141525Z.zip`; the code rollback archive is `/home/ealtenho/recipe-release-saved-menu-20261021/before-code.tar.gz`. Hash-matched copies of both are in `C:\Users\erica\Desktop\Codex\Recipe Book Backups`.

All 54 tests passed locally and in a Pi staging copy. The Pi service and tunnel are active, and the weekly-menu API and v23 assets respond. The 13 recipe rows and original PDF match the pre-release backup byte-for-byte by digest; SQLite integrity is `ok`. A read-only browser check through the Pi origin passed at 390px and 1440px with no overflow or page errors. At 390px, a sample menu supplied only to the browser verified the saved view and Edit menu without writing production data. The public hostname redirects unauthenticated visitors to Cloudflare Access. Authenticated phone interaction remains unverified.

## 2026-10-21 ChatGPT paste release

Follow-up commit `34ff19d` restores **Paste or type text** and adds **Paste ChatGPT recipe** as a separate Add a recipe method with its own paste box. It uses `recipe-shell-v21`. The pre-release database backup is `/home/ealtenho/recipe-book-backups/recipes-20261021T104554Z.zip` (copied off the Pi and verified); the code rollback archive is `/home/ealtenho/recipe-release-two-paste-20261021/before-code.tar.gz`. All 52 local tests and the shell browser test passed. A 390px browser check through the Pi origin used both methods and reached editable drafts with no page errors or horizontal overflow. The Pi focused import test passed; 12 saved recipes and SQLite integrity `ok` remained unchanged. Authenticated iPhone interaction remains unverified.

Follow-up commit `4449d4e` places **Paste ChatGPT recipe** among the **Add a recipe** method buttons and removes the front-page shortcut. It uses `recipe-shell-v20`. The pre-release database backup is `/home/ealtenho/recipe-book-backups/recipes-20261021T104019Z.zip` (copied off the Pi and verified); the code rollback archive is `/home/ealtenho/recipe-release-add-chatgpt-20261021/before-code.tar.gz`. All 52 local tests and the shell browser test passed. A 390px browser check through the Pi origin selected **Add a recipe → Paste ChatGPT recipe**, created an editable draft, and had no page errors or horizontal overflow. The Pi focused import test passed; the 12 saved recipes and SQLite integrity `ok` were unchanged. Authenticated iPhone interaction remains unverified.

Follow-up commit `07807f0` moves the shortcut from below the shelves into the opening banner and updates the cache to `recipe-shell-v19`. The pre-release database backup is `/home/ealtenho/recipe-book-backups/recipes-20261021T102355Z.zip` (also copied off the Pi); the code rollback archive is `/home/ealtenho/recipe-release-paste-top-20261021/before-code.tar.gz`. The 52-test local suite and shell browser test passed. A browser check against the Pi origin at 390px placed the button at y=354px on the first screen, opened an editable draft, found no page errors or horizontal overflow, and did not save a recipe. The Pi focused import test passed; 12 recipe records and SQLite integrity `ok` remained after deployment. Authenticated iPhone interaction is still user verification.

Commit `99c13c5` is live on the Pi with `recipe-shell-v18`. It adds the **Paste ChatGPT recipe** shortcut and improves text draft parsing; the previously prepared Home Screen icons and manifest are included. The live database was backed up to `/home/ealtenho/recipe-book-backups/recipes-20261021T101329Z.zip` and copied to `C:\Users\erica\Desktop\Codex\Recipe Book Backups`. The ZIP passed integrity checks, and its SQLite database contained 12 recipes with `PRAGMA integrity_check = ok`. Prior application code is archived at `/home/ealtenho/recipe-release-chatgpt-20261021/before-code.tar.gz`; restore it into the app directory and restart `recipe-book.service` to roll back code without replacing `user_data`.

The local 52-test suite and shell browser test passed. The Pi focused import test passed. A live draft import returned the expected title, ingredients, steps, time, servings, and notes; recipe count stayed 12 and database integrity remained `ok`. A 390px browser check through the Pi origin opened the paste shortcut and review draft with no page errors or horizontal overflow. The public URL still redirects anonymous requests to Cloudflare Access. Authenticated iPhone interaction was not tested.

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

## Weekly menu

The weekly menu stores one Saturday-starting plan per week in the existing `user_data/recipes.sqlite3` database. The `weekly_menus` table is created automatically on startup. The normal `/api/backup` ZIP includes the table in `recipes.sqlite3` and a readable `weekly-menus.json` export. Back up the live database before installing this release. Keep `user_data` in place when updating code; a code-only rollback leaves saved menus available for a later release.
