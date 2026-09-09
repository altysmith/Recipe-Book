# The Little Recipe Box

A local browser recipe book with a SQLite database. Double-click **Start Recipe Book.bat**, then use http://127.0.0.1:8771. The server runs in the background; opening the launcher again reuses it.

Browse/search by title or ingredients, filter categories and favorites, sort, edit recipes, paste text or import PDFs into reviewable drafts, check ingredients, and print a clean recipe page. Directions are optional. Ingredient checkmarks persist on this device until reset; changing the ingredient list clears its old checklist to avoid mismatched checks.

Open online once and wait for “Saved on this device.” Recipes and the app shell then reopen offline, including the bundled recipe photo. Use Refresh saved recipes to download current records. Imports, edits, original PDFs, and external websites require a connection. Offline snapshots and checkmarks use browser storage, which browser settings or storage pressure can remove. They are separate from the server database and are not shared between devices. See NEXT_STEPS.md for URL import planning.

PDF import currently extracts embedded text and recognizes common section headings. It does not use OCR or AI, infer missing fields, or reliably resolve columns, multi-recipe files, line wrapping, and printed headers. Review drafts against the retained original PDF before saving. Scanned PDFs retain the original but require manual text entry. The turkey sample was manually visually verified.

Website imports: Add a recipe -> Website recipe URL -> Import from website. Reads Schema.org Recipe JSON-LD into an editable draft, including ingredient-only recipes. Multiple recipes present a chooser. Source attribution is retained. Pages that block requests or lack supported recipe data require pasting text or a print-page link. No recipe is saved until you review and select Save recipe. Refresh twice after an app update if the previous offline shell is still displayed.

## Data and privacy

Recipes live in `user_data/recipes.sqlite3`, originals in `user_data/originals`. These and intermediate files are ignored by Git. Canceled imports may leave an original PDF in that folder. The initial sample JSON is a historical import snapshot; the database is authoritative after editing. Use SQLite's backup API for live backups. Do not copy only the database while it is being written.

This folder is currently under OneDrive, so local files may also be synchronized by your OneDrive settings.

## Development / later Raspberry Pi move

Python 3.11+ and `pip install -r requirements.txt`; run `python server.py`. The Windows launcher first looks for the bundled Codex Python, then Python on PATH. `RECIPE_DATA_DIR` selects a different data directory. `python -m unittest discover -s tests` uses temporary databases.

The server binds to this computer's loopback interface. Offline reading is implemented; home-screen installation and actual iPhone testing remain ahead. Raspberry Pi deployment still needs a production server, private authentication, HTTPS/domain routing, backups, and explicit network configuration. No hosting or public access is enabled.
