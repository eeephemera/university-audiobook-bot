# English UI strings. Keys MUST stay in sync with ru.py.

EN: dict[str, str] = {
    # --- Screens ---
    "welcome": (
        "👋 <b>Welcome to {brand}!</b>\n\n"
        "Your one-stop bot for <b>audiobooks</b> and their <b>PDF</b> "
        "versions.\n\n"
        "📚 <b>How to use</b>\n"
        "1. Open “Books” and pick a book.\n"
        "2. Listen to chapters right inside Telegram — one tap each.\n"
        "3. Or use “Play the whole book” — chapters play automatically, "
        "one after another.\n"
        "4. Download the full PDF version.\n\n"
        "Choose an option 👇"
    ),
    "about": (
        "ℹ️ <b>{brand}</b>\n\n"
        "Listen to audiobooks and read their PDF versions right inside "
        "Telegram — fast and simple."
    ),
    "help": (
        "<b>Commands</b>\n"
        "/start — main menu\n"
        "/catalog — books\n"
        "/language — choose language\n"
        "/help — this help\n\n"
        "<i>Tip:</i> type a book title to search, "
        "or use the bot in any chat via <code>@{bot}</code>."
    ),
    "catalog_title": "📚 <b>Books</b>\n\nPick a book:",
    "catalog_empty": (
        "📭 No books yet.\n\n"
        "<i>Materials are being added. Check back soon.</i>"
    ),
    "chapters_title": "🎧 <b>{book}</b>\n\nChapters — tap to listen:",
    "parts_title": "🎧 <b>{book}</b>\n\nChoose a part:",
    "chapters_hint": "✅ — listened · 🔒 — coming soon",
    "language_choose": "🌐 <b>Choose interface language</b>",
    "language_set": "✅ Interface language: English",
    "search_prompt": "🔍 Type a book title or author:",
    "search_no_results": "😔 Nothing found for “<b>{query}</b>”.",
    "search_results_title": "🔍 Results for “<b>{query}</b>”:",
    # --- Buttons ---
    "menu_catalog": "📚 Books",
    "menu_about": "ℹ️ About",
    "menu_language": "🌐 Language",
    "menu_search": "🔍 Search a book",
    "menu_home": "🏠 Menu",
    "btn_back": "⬅️ Back",
    "btn_chapters": "🎧 Listen",
    "btn_play_all_book": "▶️ Play the whole book",
    "btn_play_all_part": "▶️ Play this part in order",
    "btn_open_book": "📖 Open the book",
    "btn_open_part": "📃 Open the part",
    "btn_choose_part": "📚 Choose a part",
    "btn_pdf": "📄 Download PDF",
    "btn_continue": "▶️ Continue — chapter {n}",
    "btn_prev": "⬅️ Prev",
    "btn_next": "Next ➡️",
    "btn_to_chapters": "📃 Chapter list",
    # --- Captions / labels ---
    "lbl_author": "Author",
    "lbl_part": "Part",
    "lbl_chapter": "Chapter",
    "lbl_chapters": "Chapters",
    "lbl_of": "of",
    "lbl_pdf_version": "PDF version",
    "coming_soon": (
        "🔒 Audio for this book is still being prepared.\n"
        "<i>Chapters will appear here very soon.</i>"
    ),
    "playall_sending": "▶️ Sending chapters in order…",
    "playall_done": (
        "✅ Done: {n} chapters sent.\n"
        "Tap ▶️ on the first one — Telegram will play them through to the end."
    ),
    "playall_error": "⚠️ Couldn't send all chapters. Please try again later.",
    # --- Alerts (toast popups) ---
    "alert_not_ready": "🔒 This chapter hasn't been uploaded yet",
    "alert_no_pdf": "📄 PDF isn't available for this book yet",
    "alert_pdf_not_ready": "📄 PDF is still being prepared",
    "alert_not_found": "Not found. Reopen the catalog: /start",
    # --- Inline mode ---
    "inline_book_description": "Audiobook · {chapters} chapters",
    # --- Signature footer (travels with forwarded messages) ---
    "sig_text": "📚 <b>{brand}</b>\n🔗 Listen in the bot: {link}",
}
