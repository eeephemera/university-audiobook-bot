# Architecture

## Layers (top → bottom)

```
Telegram  ──updates──▶  Dispatcher
                          │
              ContextMiddleware  ── opens 1 DB session / update,
                          │         upserts user, resolves language,
                          │         injects: session, catalog, user, lang
                          ▼
                      Handlers            app/handlers/*  (thin: parse → call → render)
                          │
                      Services            app/services/   (business logic, admin-ready)
                          │
                    Repositories          app/repositories/  (the ONLY SQL)
                          │
                      Models / DB          app/db/  (SQLAlchemy 2.0 async + SQLite)
```

Cross-cutting:
- `app/formatting/` — rich text + the forward-signature footer + `sendRichMessage` fallback.
- `app/keyboards/` + `app/callbacks.py` — inline UI and typed callback data.
- `app/i18n/` — UI strings (RU/EN) and localized-content resolution.
- `app/views.py` — pure text+keyboard builders (no I/O).

### Why these boundaries
- **Handlers never touch SQL.** They go through `CatalogService`, which goes
  through repositories. SQL lives in exactly one layer.
- **One session per update**, committed/rolled-back by the middleware, so
  handlers don't manage transactions.
- **Content (audio/PDF) is referenced by Telegram `file_id`**, never stored as
  blobs — uploaded once, re-sent instantly forever.

## Data model

- `Book` — slug (deep links), localized `title`/`description` (JSON map),
  `cover_file_id`, `pdf_file_id`, `is_published`, `sort_order`.
- `Chapter` — `book_id`, `section` (part number, 1 for flat books), `number`
  (within the part), localized `title`, `audio_file_id`, `duration`.
  `is_ready` = published **and** has audio. Global order is `(section, number)`.
- A book's part titles live in `Book.sections` (JSON, keyed by section number).
  >1 section ⇒ a part-selection screen; otherwise the chapter list is flat.
- `User` — Telegram id, language preference, profile, timestamps.
- `Progress` — last listened chapter per (user, book) → “continue listening”.

Localized fields are JSON `{"ru": "...", "en": "..."}`. Adding a language is a
**data** change, not a migration.

## Request flow examples

- **Browse:** `/catalog` → `CatalogService.page()` → `catalog_keyboard` (edits
  one message as the user navigates — no chat spam).
- **Listen:** tap chapter → `DeliveryService.send_chapter()` sends the audio by
  `file_id` with a signed caption + prev/next keyboard, and saves progress.
- **Share:** forwarded audio/PDF/card keeps its caption → recipient sees the
  signature + a working deep link back into the bot.

## The future admin panel — already wired for

It is **not built** (see `app/handlers/admin.py`), but everything beneath it is:

1. **Writes exist.** `BookRepository.create/update/delete`,
   `ChapterRepository.upsert` are implemented and used by `scripts/`.
2. **Gating exists.** `app/filters/admin.py::IsAdmin` + `ADMIN_IDS`; the admin
   router already applies it.
3. **file_id capture exists.** `scripts/import_media.py` is the exact pattern an
   in-chat “send me the audio” admin step will reuse.

Building it later ≈ add FSM wizards in `handlers/admin.py` that call the
existing services. Recommended before going live with multi-step admin flows:
swap the in-memory FSM storage for Redis, and adopt Alembic for migrations.

## Deliberate scope choices

- **SQLite + long polling** — perfect for one VPS; `DATABASE_URL` swaps to
  Postgres and the repository layer is unchanged. No webhook/TLS needed.
- **In-memory FSM** — fine for a single instance; documented Redis path for HA.
- **Rich Messages behind a flag** — Bot API 10.1 is ~2 weeks old; we use the
  stable rich entities now and can flip the flag once the schema settles.
