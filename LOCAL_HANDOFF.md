# Local features ready for use

- Recipe photo: Edit recipe -> Recipe photo -> Save recipe. JPEG/PNG and other browser-readable formats are resized locally to JPEG. Uploaded photos are included in device snapshots and database backups. A removed upload falls back to the original illustration/photo where available.
- Unsaved changes: leaving an editor or closing/reloading the tab warns before discarding edits. Save or explicitly discard before changing views.
- Recovery: Move to trash hides a recipe from the cookbook; Trash -> recipe -> Restore recipe brings it back. There is no permanent-delete control.
- Backup/export: Download backup & export creates a consistent SQLite snapshot plus recipes.json and originals. Photos are inside recipe records. Includes Trash, excludes device-specific checkmarks. Save a copy somewhere separate from this project.
- Restore: stop the app, keep a copy of the existing user_data folder, then extract recipes.sqlite3 and originals from the backup into user_data. Restart and refresh saved recipes. Never overwrite an open database. Restore was tested by opening the exported database and checking integrity.

Raspberry Pi deployment, domain/HTTPS setup, private login, scheduled backups, and real iPhone/home-screen testing remain for the next session. Nothing was deployed publicly. Continue using the current local launcher.
