# The Little Recipe Box

A private browser recipe book with a SQLite database. The hosted copy runs on the Raspberry Pi behind Cloudflare Access. For a separate local copy, double-click **Start Recipe Book.bat**, then use http://127.0.0.1:8771.

Browse/search by title or ingredients, filter categories and favorites, sort, edit recipes, paste text or import PDFs into reviewable drafts, check ingredients, and print a clean recipe page. Directions are optional. Ingredient checkmarks persist on this device until reset; changing the ingredient list clears its old checklist to avoid mismatched checks.

Open online once and wait for “Saved on this device.” Recipes and the app shell then reopen offline, including the bundled recipe photo. Use Refresh saved recipes to download current records. Imports, edits, original PDFs, and external websites require a connection. Offline snapshots and checkmarks use browser storage, which browser settings or storage pressure can remove. They are separate from the server database and are not shared between devices. See NEXT_STEPS.md for URL import planning.

PDF import currently extracts embedded text and recognizes common section headings. It does not use OCR or AI, infer missing fields, or reliably resolve columns, multi-recipe files, line wrapping, and printed headers. Review drafts against the retained original PDF before saving. Scanned PDFs retain the original but require manual text entry. The turkey sample was manually visually verified.

Website imports: Add a recipe -> Website recipe URL -> Import from website. Reads Schema.org Recipe JSON-LD into an editable draft, including ingredient-only recipes. Multiple recipes present a chooser. Source attribution is retained. Pages that block requests or lack supported recipe data require pasting text or a print-page link. No recipe is saved until you review and select Save recipe. Refresh twice after an app update if the previous offline shell is still displayed.

## Data and privacy

Recipes live in `user_data/recipes.sqlite3`, originals in `user_data/originals`. These and intermediate files are ignored by Git. Canceled imports may leave an original PDF in that folder. The initial sample JSON is a historical import snapshot; the database is authoritative after editing. Use SQLite's backup API for live backups. Do not copy only the database while it is being written.

GitHub contains application source, not the live recipes or original uploads; the Pi's `user_data` is authoritative for the hosted copy.

To discuss the app in regular ChatGPT, share https://github.com/altysmith/Recipe-Book and ask it to inspect `web/index.html`, `web/style.css`, and `web/app.js`. Attach screenshots from your signed-in browser when you want feedback on the actual rendered site. GitHub source access does not grant access through Cloudflare Access or reveal the live recipe collection.

## Development

Python 3.11+ and `pip install -r requirements.txt`; run `python server.py`. The Windows launcher first looks for the bundled Codex Python, then Python on PATH. `RECIPE_DATA_DIR` selects a different data directory. `python -m unittest discover -s tests` uses temporary databases.

The local server binds to this computer's loopback interface. The Raspberry Pi deployment and its Cloudflare Access configuration are documented in `DEPLOYMENT.md`. Actual iPhone and home-screen testing still needs user confirmation.

## Photo and screenshot imports

Add a recipe -> Photo or screenshot -> choose up to four photos in page order -> Read recipe photos -> review -> Save recipe. Photos are read privately on the server with Tesseract English OCR; no external AI service or API key is used. Clear upright printed pages work best. Headings such as Ingredients and Directions help field recognition. Unfamiliar layouts may need manual corrections; all extracted text and resized source photos remain available in the review and saved record. Check fractions, quantities, temperatures, and completeness. No recipe is saved automatically.

Server setup: install `tesseract-ocr` and `tesseract-ocr-eng` on Debian/Raspberry Pi. Windows needs Tesseract on PATH, or set `RECIPE_TESSERACT` to its executable. Pillow is already installed through pdfplumber. Photo reading requires connectivity. Browser-readable images are resized to 2400 pixels before upload (up to 20 MB per original). If an HEIC photo cannot open in the browser, use a JPEG or PNG screenshot.

# Instagram Reel recipe import

On **Add a recipe → Video link**, paste a public `https://www.instagram.com/reel/<shortcode>/` URL copied from Instagram and choose **Import Recipe from Video**. The server retrieves metadata. When the caption is incomplete, it downloads a bounded copy of the media, uses local Whisper speech recognition, reads sampled frames with Tesseract, and builds an editable draft. Review the caption, transcript, on-screen text, and warnings in **Original extracted text**. Nothing enters the recipe database until **Save recipe**; the saved document uses the same SQLite schema and editor as every other recipe. The original Reel link remains in `source_url`.

This feature needs no paid API key. It requires server-installed yt-dlp, FFmpeg, Tesseract, and a local whisper.cpp `whisper-cli` binary plus an English model; see [DEPLOYMENT.md](DEPLOYMENT.md). The model is installed once by the operator, never downloaded during an import. The deterministic parser is conservative and may leave quantities or directions incomplete. It does not match the interpretation quality of a capable language model. Check all amounts, cooking temperatures, times, and food-safety instructions before saving.

Only public downloadable Instagram Reels are accepted. Private videos, videos requiring login, and DRM media are unsupported. Other platforms and file-upload fallback are future work. A Reel that yields no recipe returns an error instead of an empty saved recipe. Video import needs a connection; existing offline browsing and checklists still work.

The design was informed by [Pick-a-Recipe](https://github.com/pickeld/pick-a-recipe)'s retrieval → transcription → visual evidence → recipe pipeline. No source was copied; its repository did not expose a license file when reviewed. This app uses its own local extraction and existing editor/storage.
