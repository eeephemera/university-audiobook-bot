# Persian (Farsi) UI strings. Keys MUST stay in sync with ru.py.
# Interface only — book/chapter/part content stays in its original language.

FA: dict[str, str] = {
    # --- Screens ---
    "welcome": (
        "👋 <b>به {brand} خوش آمدید!</b>\n\n"
        "اینجا <b>کتاب‌های صوتی</b> و نسخه‌های <b>PDF</b> آن‌ها گردآوری شده — "
        "همه در یک ربات.\n\n"
        "📚 <b>نحوهٔ استفاده</b>\n"
        "1. «کتاب‌ها» را باز کنید و کتابی را انتخاب کنید.\n"
        "2. فصل‌ها را همین‌جا در تلگرام گوش دهید — با یک لمس.\n"
        "3. می‌توانید «پخش کل کتاب» را فعال کنید تا فصل‌ها پشت‌سرهم پخش شوند.\n"
        "4. نسخهٔ کامل PDF را دانلود کنید.\n\n"
        "یک گزینه را انتخاب کنید 👇"
    ),
    "about": (
        "ℹ️ <b>{brand}</b>\n\n"
        "کتاب‌های صوتی را گوش دهید و نسخه‌های PDF آن‌ها را همین‌جا در تلگرام "
        "بخوانید — سریع و آسان."
    ),
    "help": (
        "<b>دستورها</b>\n"
        "/start — منوی اصلی\n"
        "/catalog — کتاب‌ها\n"
        "/language — انتخاب زبان\n"
        "/help — همین راهنما\n\n"
        "<i>نکته:</i> برای جستجوی کتاب نام آن را بنویسید، یا ربات را در هر "
        "گفتگو با <code>@{bot}</code> استفاده کنید."
    ),
    "catalog_title": "📚 <b>کتاب‌ها</b>\n\nیک کتاب انتخاب کنید:",
    "catalog_empty": (
        "📭 هنوز کتابی نیست.\n\n"
        "<i>در حال افزودن مطالب. بعداً سر بزنید.</i>"
    ),
    "chapters_title": "🎧 <b>{book}</b>\n\nفصل‌ها — برای گوش دادن لمس کنید:",
    "parts_title": "🎧 <b>{book}</b>\n\nیک بخش را انتخاب کنید:",
    "chapters_hint": "✅ — گوش‌داده‌شده · 🔒 — به‌زودی",
    "language_choose": "🌐 <b>زبان رابط را انتخاب کنید</b>",
    "language_set": "✅ زبان رابط: فارسی",
    "search_prompt": "🔍 نام کتاب یا نویسنده را وارد کنید:",
    "search_no_results": "😔 برای «<b>{query}</b>» چیزی پیدا نشد.",
    "search_results_title": "🔍 نتایج برای «<b>{query}</b>»:",
    # --- Buttons ---
    "menu_catalog": "📚 کتاب‌ها",
    "menu_about": "ℹ️ درباره",
    "menu_language": "🌐 زبان (languages)",
    "menu_search": "🔍 جستجو",
    "menu_home": "🏠 منو",
    "btn_back": "⬅️ بازگشت",
    "btn_chapters": "🎧 گوش دادن",
    "btn_play_all_book": "▶️ پخش کل کتاب پشت‌سرهم",
    "btn_play_all_part": "▶️ پخش کل این بخش",
    "btn_open_book": "📖 باز کردن کتاب",
    "btn_open_part": "📃 باز کردن بخش",
    "btn_choose_part": "📚 انتخاب بخش",
    "btn_pdf": "📄 دانلود PDF",
    "btn_continue": "▶️ ادامه — فصل {n}",
    "btn_prev": "⬅️ قبلی",
    "btn_next": "بعدی ➡️",
    "btn_to_chapters": "📃 فهرست فصل‌ها",
    # --- Captions / labels ---
    "lbl_author": "نویسنده",
    "lbl_part": "بخش",
    "lbl_chapter": "فصل",
    "lbl_chapters": "فصل‌ها",
    "lbl_of": "از",
    "lbl_pdf_version": "نسخهٔ PDF",
    "coming_soon": (
        "🔒 صدای این کتاب هنوز در حال آماده‌سازی است.\n"
        "<i>به‌زودی فصل‌ها اینجا قرار می‌گیرند.</i>"
    ),
    "playall_sending": "▶️ در حال ارسال فصل‌ها به‌ترتیب…",
    "playall_done": (
        "✅ انجام شد: {n} فصل ارسال شد.\n"
        "روی اولی ▶️ بزنید — تلگرام آن‌ها را پشت‌سرهم تا انتها پخش می‌کند."
    ),
    "playall_error": "⚠️ ارسال همهٔ فصل‌ها ناموفق بود. بعداً دوباره تلاش کنید.",
    # --- Alerts (toast popups) ---
    "alert_not_ready": "🔒 این فصل هنوز بارگذاری نشده است",
    "alert_no_pdf": "📄 PDF این کتاب هنوز در دسترس نیست",
    "alert_pdf_not_ready": "📄 PDF هنوز در حال آماده‌سازی است",
    "alert_not_found": "پیدا نشد. کاتالوگ را دوباره باز کنید: /start",
    # --- Inline mode ---
    "inline_book_description": "کتاب صوتی · {chapters} فصل",
    # --- Signature footer (travels with forwarded messages) ---
    "sig_text": "📚 <b>{brand}</b>\n🔗 گوش دادن در ربات: {link}",
}
