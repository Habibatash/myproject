# د ادارې متحد سیستم — د Django اصلاحاتي بسته

دا بسته ستا د ورکړل شوي HTML ډیزاین ساتي او د موجود Django `agency` او `core` پروژې لپاره لاندې شاتني بدلونونه ورزیاتوي.

## څه پکې اصلاح شوي؟

- د راپورونو لیدل: عمومي مدیر ټول راپورونه ویني؛ امیر د خپل امریت او کارکوونکو راپورونه ویني؛ کارمند یوازې خپل راپورونه ویني.
- د راپورونو، پوسټونو او تبصرو د اصلاح/حذف اجازه په Django سرور کې تاییدېږي، نه یوازې په HTML کې.
- د عمومي او مهمو خبرونو پوسټونه ټولو ننوتلو کاروونکو ته ښکاري. د پوسټ په درې‌ټکي مینو کې د کاروونکي د اجازې مطابق اصلاح او حذف راځي.
- د `@` له لارې د فعالو کاروونکو لټون او منشن؛ د تبصرې د ثبت پر مهال منشن شوي کاروونکي ته د سیستم خبرتیا استول کېږي. د موبایل Push لپاره د VAPID او `services.notify` موجوده تنظیمات باید سم وي. که VAPID کلیدونه نه لرې، لومړی `python manage.py generate_vapid` وچلوه، Django بیاچالان کړه او د خبرتیاوو په برخه کې د موبایل خبرتیاوو تڼۍ کېکاږه.
- د ثبت پر مهال د ایمیل تایید؛ د تایید لینک بیا لېږلو تڼۍ هم شته. د SMTP له تنظیم پرته لینک یوازې د Django په ټرمینل کې چاپېږي.
- د AI غوښتنه د براوزر پر ځای د Django سرور ته ځي. API key په براوزر کې نه ساتل کېږي. د AI متن د کاروونکي د لیدلو وړ داخلي خبرونو، راپورونو او د لوستلو وړ ضمیمو څخه جوړېږي؛ د داخلي موادو په منځ کې بهرني خبرونه نه ګډېږي. د هر ډول تر ټولو وروستي ۱۵۰ پوسټونه/اسناد او تر ۶۰ زرو تورو پورې متن د یوې پوښتنې لپاره لېږل کېږي؛ د ډېر لوی آرشیف لپاره باید د موضوع/مودې له مخې جلا پوښتنې وشي.
- د Excel او Word فایلونه په اصلي `.xlsx` او `.docx` بڼه صادرېږي او د همدې بڼو د پرانیستلو تڼۍ هم لري.
- د «نور راپورونه» فلټر د امریت په جزئیاتو کې ساتل شوی او له `له راپور سره تړاو نه لري` مودې سره کار کوي.
- د افغانستان، نړۍ، پاکستان، ایران او امریکا خبرونه له RSS فیډونو راټولېږي او د عاجل، سیاسي، امنیتي، اقتصادي، ټکنالوژۍ، ټولنیز او نورو موضوعاتو له مخې ډلبندي کېږي.

## مهم محدودیتونه چې باید پوه شې

1. **دا د ستا د بشپړې Django پروژې بدیل نه دی.** په دې خبرو کې ستا HTML او د `settings.py`، `views.py`، `ai.py` او `office.py` ځینې کوډونه راکړل شوي وو؛ خو د پروژې بشپړ `models.py`، `permissions.py`، `services.py`، `urls.py`، migrations او requirements نه وو راکړل شوي. نصب‌کوونکی د موجودو فایلونو پر سر اصلاحاتي کوډ ورزیاتوي، خو د هماغې پروژې له بشپړ فایلونو پرته د بې‌خطا چلولو تضمین ممکن نه دی.
2. د Excel/Word دا موجود ساده ایډیټر د کمپیوټر د Microsoft Office ټول امکانات نه لري. اوسنی صادرول/پرانیستل ریښتیني `.xlsx` او `.docx` جوړوي، خو د څو-پاڼو پیچلي فورمولونه، VBA/Macros، Pivot، Track Changes، SmartArt او د Office ټول پرمختللي امکانات نه رانغاړي. د بشپړ کمپیوټري Office تجربې لپاره باید ONLYOFFICE Docs یا Collabora په سرور کې نصب او ورسره مدغم شي.
3. د ۲۴ ساعته خبرونو لپاره د RSS سرچینې په ټاکلې وقفه کې لوستل کېږي. ټولنیزې شبکې لکه Facebook، X، Instagram او نور د رسمي API، مجاز ټوکن یا عامه RSS فیډ پرته په خوندي او باوري ډول نه شي لوستل کېدای. بسته د ننوتلو/خصوصي حسابونو scraping نه کوي.
4. د فایلونو د متن تحلیل د TXT/CSV/JSON/XML/MD، DOCX، XLSX او PDF د لوستلو وړ متن رااخلي. د انځورونو OCR، د ویډیو غږیز transcript او د غږونو transcription پکې نه دي فعال شوي؛ نو AI د دغو فایلونو د محتوا ادعا نه کوي.
5. د ۲۴ ساعته worker باید تل چالان وساتل شي. یوازې `NEWS_AUTOFETCH=True` کافي نه دی؛ د `fetch_news_loop` پروسه باید د systemd، Supervisor یا Windows Task Scheduler له لارې د سرور له reboot وروسته هم بېرته پورته شي.

## د نصبولو طریقه

1. د پروژې له اصلي فولډر څخه backup واخله. په هماغه فولډر کې باید `manage.py`، `core/` او د Django تنظیماتو فولډر (اکثر `agency/`) موجود وي.
2. د `install_django_upgrade.py` فایل د پروژې اصلي فولډر ته کاپي کړه.
3. په CMD/PowerShell/Terminal کې د پروژې اصلي فولډر ته لاړ شه او دا چلوه:

```bash
python install_django_upgrade.py
```

یا که پروژه بل ځای وي:

```bash
python install_django_upgrade.py --project-root "C:\path\to\your\django-project"
```

نصب‌کوونکی د بدلولو مخکې د فایلونو backup په `_agency_upgrade_backups/` کې ساتي، نوي فایلونه ځای پر ځای کوي او هڅه کوي migrations، migrate او `manage.py check` وچلوي. که اتومات migration ناکامه شي، لاندې لاس‌لارې امرونه په خپله اجرا کړه:

```bash
python manage.py makemigrations core
python manage.py migrate
python manage.py check
```

## اړین Python کڅوړې

د پروژې د requirements مطابق Django باید له مخکې نصب وي. د Word/Excel او PDF د AI لوستلو لپاره:

```bash
pip install python-docx openpyxl pypdf pywebpush cryptography
```

که د Push لپاره `pywebpush` او `cryptography` لا نه وي نصب:

```bash
pip install pywebpush cryptography
```

## اړین چاپېریالي متغیرونه

دا ارزښتونه د سرور Environment Variables کې تنظیم کړه؛ په Python فایلونو او HTML کې پټنومونه مه لیکه.

```text
DJANGO_SECRET_KEY=ستاسې-اوږده-تصادفي-پټه-کیلي
DJANGO_DEBUG=0
DJANGO_ALLOWED_HOSTS=your-domain.com,www.your-domain.com
DJANGO_HTTPS=1
DJANGO_CSRF_TRUSTED_ORIGINS=https://your-domain.com
SITE_URL=https://your-domain.com

EMAIL_HOST=smtp.your-provider.com
EMAIL_PORT=587
EMAIL_HOST_USER=no-reply@your-domain.com
EMAIL_HOST_PASSWORD=د-ایمیل-اپ-پټنوم
EMAIL_USE_TLS=1
EMAIL_USE_SSL=0
DEFAULT_FROM_EMAIL=no-reply@your-domain.com
EMAIL_VERIFICATION_REQUIRED=1

ANTHROPIC_API_KEY=ستاسې-Anthropic-API-key
AI_MODEL=claude-sonnet-5

NEWS_AUTOFETCH=1
NEWS_FETCH_INTERVAL_MIN=15
NEWS_KEEP_DAYS=14
```

- که SMTP تنظیم نه وي، `EMAIL_BACKEND` به کنسولي وي او د تایید لینک به د Django د سرور په ټرمینل کې ښکاري. دا په production کې د ایمیل لېږلو بدیل نه دی.
- د `DJANGO_DEBUG=0`، د خپل اصلي host، HTTPS، CSRF trusted origin او یو ثابت `DJANGO_SECRET_KEY` تنظیمول په production کې ضروري دي.
- د `NEWS_FEEDS_JSON` له لارې خپل RSS فیډونه هم ورزیاتولای شې. بڼه یې د JSON لېست دی:

```json
[
  {"country":"afghanistan","source":"زما سرچینه","url":"https://example.com/rss.xml","language":"ps"},
  {"country":"world","source":"بله سرچینه","url":"https://example.org/feed","language":"en"}
]
```

که دا متغیر تش پرېښودل شي، په بسته کې ټاکل شوې عامه سرچینې کارول کېږي. د RSS فیډونو شتون، جوړښت او د لاسرسي اجازه د سرچینې له خوا بدلېدای شي؛ که کوم فیډ کار ونه کړي، worker یې په log کې د خطا په توګه ثبتوي او نور فیډونه لوستلو ته دوام ورکوي.

## د موبایل Push خبرتیاوو لپاره (یو ځل):

```bash
python manage.py generate_vapid
```

دا امر `vapid_private.pem` او `vapid_public.txt` جوړوي. خصوصي کلید هېڅکله چا ته مه لېږه. د Django سرور له بیاچالانولو وروسته د خبرتیاوو له پاڼې څخه «په موبایل کې خبرتیاوې فعالول» کېکاږه.

## د سرور چلول

د Django وېب سرور:

```bash
python manage.py runserver
```

د خبرونو یو ځل راوړل او ازموینه:

```bash
python manage.py fetch_news_once
```

د خبرونو دوامداره ۲۴ ساعته راټولول (په جلا Terminal کې):

```bash
python manage.py fetch_news_loop
```

د production لپاره دا وروستۍ پروسه د systemd/Supervisor/Windows Task Scheduler له لارې د اتومات بیاچالانېدو سره تنظیم کړه. یوازې Terminal وتړل شي، worker هم بندېږي.

## د نصب وروسته ازموینې

- د کارمند له حسابه د بل امیر راپور باید په `reports`، `documents` او `departments` کې ښکاره نه شي.
- د امیر له حسابه د بل امریت راپور باید ښکاره نه شي، خو د خپل امریت د کارمندانو راپورونه باید ښکاره شي.
- د عمومي مدیر له حسابه ټول راپورونه ښکاره شي.
- په عمومي او مهمو خبرونو کې د ټولو مجازو پوسټونو لیدل، منشن، تبصره، اصلاح او حذف د نقش مطابق وازمویه.
- د ثبت وروسته ایمیل او تایید لینک، د AI پوښتنه، `.xlsx` او `.docx` صادرات/واردات او د خبرونو RSS worker په جلا جلا ډول وازمویه.
- په دوه جلا براوزر/حسابونو کې هم د لاسرسي ازموینه وکړه؛ یوازې د مدیر د حساب څخه کتل بسنه نه کوي.
