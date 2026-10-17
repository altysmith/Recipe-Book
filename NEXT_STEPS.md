# Upcoming recipe inputs

- Website URL import is implemented for Schema.org Recipe JSON-LD. It preserves attribution and the final source URL, supports choosing among multiple recipes, blocks private/local targets on every redirect, and connects to validated IP addresses. Unsupported pages offer print-link or paste alternatives. Website code is never executed. Structured recipe photos are downloaded into the selected draft when available; failed downloads allow manual photo upload.
- Pasted recipes are already supported by Add recipe -> Organize pasted text.
- Directions are optional for seasoning blends and other ingredient-only recipes.

# Offline behavior

The app shell and current bundled turkey photo are cached by a service worker. Recipe snapshots and device-specific ingredient checklists use IndexedDB. Open online once and wait for the saved-on-device message before relying on offline reading. Refresh saved recipes downloads current records; unavailable network falls back to the last successful snapshot. Writes/imports are online-only and never queued silently.

Original PDFs and external source websites are not downloaded for offline reading in this version. Browser storage can be removed by browser settings or device storage pressure. The server database remains authoritative. Offline copies are per browser and origin; moving to the domain requires opening the app online there once.

Increment the service worker shell version when changing bundled application assets. Install caches a full shell before activation; activation removes only obsolete recipe-shell caches. Later authentication must include explicit offline-data removal on sign-out and account isolation.

# Video import follow-ups

- Test a representative public Instagram Reel on the production Raspberry Pi after dependencies are installed; record extraction behavior and processing time. Platform access changes independently of this application.
- Add a bounded MP4/MOV upload fallback with streamed multipart handling, file signature and duration checks, and the same local extraction pipeline.
- Improve speech ingredient parsing, visual text relevance and frame timing, and handling of multiple recipes. Keep source conflicts visible.
- Add a schema-validated optional local language-model provider, and separately consider opt-in hosted AI. Neither is required or configured today.
- Test other platforms individually before adding their URL patterns and media-host allowlists.
- Revisit durable jobs only if Pi restarts during imports become a practical issue; current in-process jobs are canceled by restart.
- Investigate iOS Web Share Target support on the actual iPhone/Safari version before adding a share-sheet flow. Copy and paste is the supported route.
