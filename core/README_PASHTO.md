# د ادارې متحد سیستم — Django نسخه

دا بسته د پخواني `د ادارې متحد سیستم (3).html` نمونې پر بنسټ د Django بشپړه پروژه جوړوي. پخوانۍ HTML نسخه په `reference/` کې د ډیزاین د مرجع په توګه ساتل شوې ده؛ د هغې د `localStorage` ډیمو پر ځای اوس معلومات په سرور ډیټابېس کې ثبتېږي.

## څه پکې شته؟

- د ننوتلو او نوي حساب ثبت؛ نوي حسابونه د عمومي مدیر تر تایید مخکې فعال نه وي.
- څلور رولونه: عمومي مدیر، مرستیال، د امریت مدیر، کارکوونکی.
- پنځه امریتونه چې د اصلي نمونې له مخې Seed کېږي.
- اسناد او راپورونه: ورځنی، اونیز، میاشتنی، شپږمیاشتنی، کلنی او بې‌مودې اسناد؛ ضمیمې، د کتنې حالت، آرشیف او لټون.
- د عمومي او مهمو خبرونو خپرول، ضمیمې، خوښې، نظرونه او `@mention` خبرتیاوې.
- لیکلي او غږیز پیغامونه: عمومي مدیر ټولو ته یا یو کاروونکي ته؛ د امریت مدیر خپل امریت ته یا د خپل امریت یو کارکوونکي/مرستیال ته. مرستیال او کارکوونکی پیغام نه شي لېږلای؛ لېږونکی او عمومي مدیر د پیغام د حذف اجازه لري.
- خبرتیاوې، د فعالیتونو تاریخچه، د کاروونکو مدیریت او د رولونو بدلول.
- AI د پوښتنو لپاره: یوازې د کاروونکي د صلاحیت له مخې د لیدلو وړ اسناد او خبرونه تحلیلوي. د Anthropic API کیلي یوازې د سرور په `.env` کې ساتل کېږي. که کیلي نه وي، یوازې احصایوي محلي لنډیز ښودل کېږي؛ دا د AI بشپړ ځواب نه دی.
- له HTTPS RSS سرچینو څخه د بهرنیو خبرونو راټولول.
- د Word او Excel په براوزري کاري پاڼه کې سمون، جدول/فورمولونه، چاپ او محلي ښکته کول؛ همدارنګه له سرور څخه اصلي `.docx` او `.xlsx` جوړول. د سرور DOCX/XLSX صادرات د اوسني متن/حجرو معلومات خوندي کوي، د ټولو ظاهري بڼو او Word انځورونو بشپړ نقل نه دی.
- د ژبې بنسټیز ملاتړ: پښتو، دري/فارسي، عربي او انګلیسي؛ د وخت سیمه د حساب په تنظیماتو کې ټاکل کېږي. د لمریز/میلادي/قمري تقویم انتخاب خوندي کېږي، خو ټولې نېټې لا په اتومات ډول نه اړوي؛ د رڼا/تیاره موضوع د همدې براوزر په localStorage کې ساتل کېږي. د ژبو ژباړه د انټرفېس په ټولو فرعي برخو کې بشپړه نه ده.

## مهمه خبره: GitHub د Django سرور نه دی

GitHub د پروژې د کوډ ساتلو او شریکولو ځای دی. یوازې ZIP په GitHub کې پورته کول Django نه چلوي. د پروژې د چلولو لپاره Python سرور/Hosting ته اړتیا ده. ZIP لومړی په کمپیوټر کې Extract کړئ؛ بیا د ZIP دننه فایلونه (د `manage.py` په ګډون) GitHub ته Upload کړئ. د ZIP د فایل په توګه پورته کول د source code د اجرا کولو بدیل نه دی.

## په Windows کې د لومړي ځل چلول

1. `agency_unified_system.zip` ډاونلوډ او Extract کړئ.
2. په Extract شوي فولډر کې باید `manage.py`، `config/`، `core/` او `requirements.txt` ښکاره وي.
3. Python 3.11 یا نوې نسخه نصب کړئ.
4. په همدې فولډر کې PowerShell/Terminal خلاص کړئ.
5. دا امرونه په همدې ترتیب اجرا کړئ:

```powershell
py -m venv .venv
.\.venv\Scripts\Activate.ps1
py -m pip install -r requirements.txt
Copy-Item .env.example .env
py manage.py migrate
py manage.py seed_departments
py manage.py create_gm
py manage.py check
py manage.py runserver
```

6. براوزر کې `http://127.0.0.1:8000/` خلاص کړئ او د عمومي مدیر ایمیل/پټنوم وکاروئ چې د `create_gm` امر پر مهال مو جوړ کړی و.
7. که PowerShell د Activate script اجازه نه ورکوي، د همدې Terminal لپاره دا امر یو ځل اجرا کړئ او بیا Activate وکړئ:

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
.\.venv\Scripts\Activate.ps1
```

په Windows کې د لنډې لارې لپاره `run_local.bat` هم شته؛ لومړی مدیر بیا په جلا ډول د `py manage.py create_gm` په امر جوړ کړئ.

## په Linux سرور کې چلول

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
# .env کې SECRET_KEY، DEBUG=False، ALLOWED_HOSTS او DATABASE_URL تنظیم کړئ
python manage.py migrate
python manage.py seed_departments
python manage.py create_gm
python manage.py collectstatic --noinput
python manage.py check --deploy
gunicorn config.wsgi:application --bind 0.0.0.0:8000
```

د تولید لپاره PostgreSQL وکاروئ او `DATABASE_URL` ورته برابر کړئ. SQLite یوازې د ازموینې/کوچني محلي کار لپاره دی. د رسنیو او ضمیمو لپاره د سرور دایمي disk/object storage هم تنظیم کړئ؛ که Hosting موقتي filesystem ولري، اپلوډ شوي فایلونه د بیا Deploy پر مهال له منځه تلای شي.

## GitHub ته د پورته کولو طریقه

1. ZIP Extract کړئ.
2. په GitHub کې خپل `myproject` Repository خلاص کړئ.
3. `Add file` → `Upload files` وټاکئ.
4. د ZIP دننه ټول فایلونه او فولډرونه انتخاب کړئ؛ **`manage.py` باید د Repository په root کې وي**، نه په بل nested فولډر کې.
5. `.env`، `db.sqlite3`، `.venv/` او `media/` هېڅکله GitHub ته مه پورته کوئ.
6. `Commit changes` وکړئ. په دې بسته کې د `.github/workflows/django-checks.yml` فایل شته؛ GitHub به د هر Push یا Pull Request پر مهال migrations، Django checks او tests وچلوي، خو دا workflow ویب‌سایټ نه خپروي.
7. د کوډ د چلولو لپاره Repository له Python Hosting/VPS سره وصل کړئ. د Hosting په Environment Variables کې د `.env` ارزښتونه ثبت کړئ.

## د لومړي عمومي مدیر حساب

هیڅ ډیمو ایمیل، عمومي پټنوم یا پټ Administrator حساب پکې نشته. لومړی مدیر په سرور کې داسې جوړېږي:

```bash
python manage.py create_gm
```

امر ایمیل، نوم او قوي پټنوم غواړي. د حساب د جوړېدو وروسته د کاروونکو برخه کې نور حسابونه او رولونه اداره کېدای شي.

## ایمیل تایید

په `.env` کې `EMAIL_VERIFICATION_REQUIRED=True` یوازې هغه وخت کړئ چې SMTP مو سم تنظیم کړی وي. د محلي ازموینې default ایمیل backend د تایید لینک د سرور په console/log کې چاپوي. که د ایمیل تایید بند وي، بیا هم نوی حساب د عمومي مدیر تر تایید مخکې ننوتلای نه شي.

## AI او RSS خبرونه

- AI: `ANTHROPIC_API_KEY` او د خپل Anthropic حساب له خوا منل شوی `AI_MODEL` په `.env` کې تنظیم کړئ. د اوسني تنظیم اصلي ماډل `claude-sonnet-5-5` دی؛ که ستاسې API حساب بل ماډل ته لاسرسی لري، ارزښت بدلولای شئ. کیلي په GitHub، HTML یا browser کې مه لیکئ.
- RSS: د `.env` په `NEWS_FEEDS_JSON` کې د HTTPS سرچینو JSON لېست واچوئ، بیا `python manage.py fetch_news_once` اجرا کړئ.
- تکراري راټولول: `python manage.py fetch_news_loop` په جلا terminal یا د systemd د `news-worker.service.example` په څېر جلا service کې وچلوئ. دا امر دوامداره چلېږي، نو د ویب سرور په هماغه terminal کې یې مه چلوئ.

## ازموینه او ساتنه

```bash
python manage.py test
python manage.py check
python manage.py check --deploy
```

- د هر Deploy مخکې د ډیټابېس backup واخلئ.
- د فایلونو اعظمي upload اندازه ۲۰ MB ده؛ د فایلونو اجازه لرونکي extensionونه محدود شوي دي.
- د اسنادو ضمیمې یوازې د سند د لیدلو مجاز کاروونکي ترلاسه کولای شي.
- عمومي مدیر ټول اسناد ویني او اداره کوي؛ د امریت مدیر خپل اسناد او د خپل امریت د کارکوونکو/مرستیالانو اسناد ویني او اداره کوي؛ مرستیال او کارکوونکی یوازې خپل اسناد ویني او اداره کوي.
- د فعالیتونو تاریخچه د عادي UI له لارې نه شي حذف کېدای؛ د Django admin کې هم د هغې د Add/Change/Delete اجازه بنده ده.

## د تطبیق حدود

دا پروژه د پخوانۍ HTML نمونې اصلي برخې د Django په server-backed ډول پلي کوي، خو دا د بهرني سرور/Database/SMTP/Anthropic/RSS خدمتونو د credentials پر ځای نه ده. د دې جوړولو چاپېریال کې Django نصب نه و او د انټرنېټ له لارې dependency نصب ممکن نه و؛ له همدې امله په دې ځای کې `manage.py check` او د Django integration tests نه شول اجرا کېدای. د Python syntax، JavaScript syntax، د اړینو فایلونو موجودیت او ZIP integrity وارزول شول. په خپل کمپیوټر یا سرور کې د `pip install` وروسته د پورته ازموینو اجرا ضروري ده.
