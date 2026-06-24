# Russian UI strings. HTML parse mode. {placeholders} are filled via str.format.
# Rich entities used: <b>, <i>, <blockquote>, <blockquote expandable> (Bot API 7.4+).

RU: dict[str, str] = {
    # --- Screens ---
    "welcome": (
        "👋 <b>Добро пожаловать в {brand}!</b>\n\n"
        "Здесь собраны <b>аудиокниги</b> и их <b>PDF-версии</b> — "
        "всё в одном боте.\n\n"
        "📚 <b>Как пользоваться</b>\n"
        "1. Откройте «Книги» и выберите книгу.\n"
        "2. Слушайте главы прямо в Telegram — в одно нажатие.\n"
        "3. Можно включить «Слушать всю книгу подряд» — главы проиграются "
        "автоматически, одна за другой.\n"
        "4. Скачивайте полную PDF-версию.\n\n"
        "Выберите действие 👇"
    ),
    "about": (
        "ℹ️ <b>{brand}</b>\n\n"
        "Слушайте аудиокниги и читайте их PDF-версии прямо в Telegram — "
        "быстро и удобно."
    ),
    "help": (
        "<b>Команды</b>\n"
        "/start — главное меню\n"
        "/catalog — книги\n"
        "/language — выбрать язык\n"
        "/help — эта справка\n\n"
        "<i>Подсказка:</i> напишите название книги, чтобы найти её, "
        "или используйте бот в любом чате через <code>@{bot}</code>."
    ),
    "catalog_title": "📚 <b>Книги</b>\n\nВыберите книгу:",
    "catalog_empty": (
        "📭 Книг пока нет.\n\n"
        "<i>Материалы добавляются. Загляните позже.</i>"
    ),
    "chapters_title": "🎧 <b>{book}</b>\n\nГлавы — нажмите, чтобы слушать:",
    "parts_title": "🎧 <b>{book}</b>\n\nВыберите часть:",
    "chapters_hint": "✅ — прослушано · 🔒 — скоро появится",
    "language_choose": "🌐 <b>Выберите язык интерфейса</b>",
    "language_set": "✅ Язык интерфейса: Русский",
    "search_prompt": "🔍 Введите название книги или автора:",
    "search_no_results": "😔 По запросу «<b>{query}</b>» ничего не найдено.",
    "search_results_title": "🔍 Результаты по запросу «<b>{query}</b>»:",
    # --- Buttons ---
    "menu_catalog": "📚 Книги",
    "menu_about": "ℹ️ О боте",
    "menu_language": "🌐 Язык (languages)",
    "menu_search": "🔍 Поиск",
    "menu_home": "🏠 В меню",
    "btn_back": "⬅️ Назад",
    "btn_chapters": "🎧 Слушать",
    "btn_play_all_book": "▶️ Слушать всю книгу подряд",
    "btn_play_all_part": "▶️ Слушать всю часть подряд",
    "btn_open_book": "📖 Открыть книгу",
    "btn_open_part": "📃 Открыть часть",
    "btn_choose_part": "📚 Выбрать часть",
    "btn_pdf": "📄 Скачать PDF",
    "btn_continue": "▶️ Продолжить — глава {n}",
    "btn_prev": "⬅️ Пред.",
    "btn_next": "След. ➡️",
    "btn_to_chapters": "📃 К списку глав",
    # --- Captions / labels ---
    "lbl_author": "Автор",
    "lbl_part": "Часть",
    "lbl_chapter": "Глава",
    "lbl_chapters": "Главы",
    "lbl_of": "из",
    "lbl_pdf_version": "PDF-версия",
    "coming_soon": (
        "🔒 Аудио для этой книги ещё готовится.\n"
        "<i>Совсем скоро здесь появятся главы.</i>"
    ),
    "playall_sending": "▶️ Отправляю главы по порядку…",
    "playall_done": (
        "✅ Готово: отправлено глав — {n}.\n"
        "Нажмите ▶️ на первой — Telegram проиграет их подряд до конца."
    ),
    "playall_error": "⚠️ Не удалось отправить все главы. Попробуйте ещё раз позже.",
    # --- Alerts (toast popups) ---
    "alert_not_ready": "🔒 Эта глава ещё не загружена",
    "alert_no_pdf": "📄 PDF для этой книги пока недоступен",
    "alert_pdf_not_ready": "📄 PDF ещё готовится",
    "alert_not_found": "Не найдено. Откройте каталог заново: /start",
    # --- Inline mode ---
    "inline_book_description": "Аудиокнига · {chapters} глав",
    # --- Signature footer (travels with forwarded messages) ---
    "sig_text": "📚 <b>{brand}</b>\n🔗 Слушать в боте: {link}",
}
