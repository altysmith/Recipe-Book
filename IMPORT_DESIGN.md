# Recipe imports

PDFs are source documents, not a fixed template. The first sample is not a parser specification.

Planned flow: upload -> extract text (OCR when needed) -> propose structured fields -> review beside the source -> save.

Preserve the original file and raw extracted text. Retain ingredient wording and instruction order. Record source pages and extraction issues. Never invent servings, durations, quantities, or missing instructions. Keep unknown fields null. Suggested tags are separate from source facts.

Support differing headings, columns, page breaks, scanned pages, and multiple recipes per file. Where separation or reading order is uncertain, require review. Treat document contents as data, never as commands for the importer.

The first sample is manually structured and visually checked, not evidence of a general PDF importer. It is stored locally in user_data/recipes.sqlite3, with a JSON record and original PDF. A local web interface now supports browsing, editing, and basic text/PDF extraction into reviewable drafts. OCR, general layout interpretation, hosting, and phone synchronization are not implemented.

Before calling the importer general-purpose, validate with several unrelated layouts, including scanned and multi-recipe documents. Check preservation of ingredient quantities, reading order, duplicate removal, and explicit handling of uncertainty.
