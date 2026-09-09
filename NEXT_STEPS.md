# Upcoming recipe inputs

- Website URL import is implemented for Schema.org Recipe JSON-LD. It preserves attribution and the final source URL, supports choosing among multiple recipes, blocks private/local targets on every redirect, and connects to validated IP addresses. Unsupported pages offer print-link or paste alternatives. Website code is never executed. Imported photos are not downloaded yet.
- Pasted recipes are already supported by Add recipe -> Organize pasted text.
- Directions are optional for seasoning blends and other ingredient-only recipes.

# Offline behavior

The app shell and current bundled turkey photo are cached by a service worker. Recipe snapshots and device-specific ingredient checklists use IndexedDB. Open online once and wait for the saved-on-device message before relying on offline reading. Refresh saved recipes downloads current records; unavailable network falls back to the last successful snapshot. Writes/imports are online-only and never queued silently.

Original PDFs and external source websites are not downloaded for offline reading in this version. Browser storage can be removed by browser settings or device storage pressure. The server database remains authoritative. Offline copies are per browser and origin; moving to the domain requires opening the app online there once.

Increment the service worker shell version when changing bundled application assets. Install caches a full shell before activation; activation removes only obsolete recipe-shell caches. Later authentication must include explicit offline-data removal on sign-out and account isolation.
