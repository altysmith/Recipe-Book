# Local features ready for use

- Recipe photo: Edit recipe -> Recipe photo -> Save recipe. JPEG/PNG and other browser-readable formats are resized locally to JPEG. Uploaded photos are included in device snapshots and database backups. A removed upload falls back to the original illustration/photo where available.
- Unsaved changes: leaving an editor or closing/reloading the tab warns before discarding edits. Save or explicitly discard before changing views.
- Recovery: Move to trash hides a recipe from the cookbook; Trash -> recipe -> Restore recipe brings it back. There is no permanent-delete control.
- Backup/export: Download backup & export creates a consistent SQLite snapshot plus recipes.json and originals. Photos are inside recipe records. Includes Trash, excludes device-specific checkmarks. Save a copy somewhere separate from this project.
- Restore: stop the app, keep a copy of the existing user_data folder, then extract recipes.sqlite3 and originals from the backup into user_data. Restart and refresh saved recipes. Never overwrite an open database. Restore was tested by opening the exported database and checking integrity.

The Raspberry Pi deployment, private Cloudflare Access route, and scheduled backups are documented in `DEPLOYMENT.md`. Real iPhone and home-screen testing still needs user confirmation. The local launcher uses a separate local database.

## September 10 update (deployed)

- Compact recipe shelf uses small thumbnails and 130px minimum rows on phones; category shortcuts are smaller and scroll horizontally.
- Categories are selected from 16 presets, with server validation. Existing names matching a preset are normalized; unmatched names appear uncategorized and can be reassigned in Edit recipe. No database migration was run.
- Website import reads the recipe's structured image field and downloads the selected recipe's photo into its review draft. Photos use public-address validation on every redirect, size limits, and JPEG resizing, and are included in offline snapshots and backups after saving. A failed image download leaves the recipe text available.
- Verified: 15 unit tests, JavaScript syntax check, and a 390px mobile browser check. Actual iPhone testing remains pending.
- Deployed successfully using the explicit SSH key ~/.ssh/altylab_pi_ed25519 and lowercase ealtenho. All 15 tests passed on the Pi. A live website photo import passed without saving the draft. All 3 recipe records exactly matched the pre-deployment backup.
