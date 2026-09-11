# BabiMind — Intermarket & Howard Marks Extension

این README مکمل، مدل جدید BabiMind را بر اساس چهار اثر مرجع تعریف می‌کند:

- John J. Murphy — *Intermarket Technical Analysis*
- John J. Murphy — *Trading with Intermarket Analysis*
- Howard Marks — *Mastering the Market Cycle*
- Howard Marks — *The Most Important Thing*

## What changed

BabiMind دیگر بازار را فقط به‌صورت تک‌نماد تحلیل نمی‌کند. قبل از تحلیل سهم/آپشن، وضعیت بین‌بازاری و چرخه بررسی می‌شود.

`Global/Local Macro → Intermarket State → Capital Rotation → Sector → Stock → Option`

### Added components

- `docs/babimind-intermarket-marks-framework.md` — دانش و قواعد عملیاتی
- `config/babimind_intermarket_marks.yml` — تنظیمات و وزن‌های نسخه ۱
- `app/intermarket/model.py` — موتور امتیازدهی، divergence، regime و second-level gate

## Core model

چهار بلوک Murphy:

`Stocks ↔ Bonds/Real Rates ↔ Commodities ↔ Currencies`

با سازگارسازی ایران:

`تورم + نقدینگی + نرخ حقیقی + دلار + طلا + مسکن + درآمد ثابت + خودرو + بورس + نفت + مس + چین/جهان`

سپس:

`Relative Return + Flow + Macro Fit + Valuation + Cycle + Catalyst + Positioning`

به **Rotation Score** تبدیل می‌شود.

## Howard Marks layer

قبل از تصمیم نهایی:

- چرخه در چه نقطه‌ای است؟
- چه چیزی در قیمت لحاظ شده؟
- consensus چیست و BabiMind چه تفاوتی با آن دارد؟
- downside و asymmetry چگونه است؟
- آیا ریسک با بازده مورد انتظار جبران می‌شود؟
- چه چیزی thesis را باطل می‌کند؟

## Divergence

اگر قیمت صعودی باشد ولی جریان پول، بازارهای تأییدکننده یا macro fit ضعیف شوند، BabiMind آن را **Intermarket Divergence** ثبت و confidence را کاهش می‌دهد.

اگر رابطه تاریخی بازارها تغییر کند، رابطه قدیمی معتبر فرض نمی‌شود و باید با داده تاریخی دوباره کالیبره شود.

## Options

آپشن در این مدل downstream است:

`Underlying Intermarket Score → Directional Edge → IV → OI/Flow → Greeks → Event Risk → Option Score`

بنابراین «صعودی بودن سهم» به‌تنهایی مجوز خرید Call نیست.

## Important limitation

این فایل ترجمه یا بازتولید متن کتاب‌ها نیست. برای پیاده‌سازی، از اطلاعات کتاب‌شناختی، فهرست مطالب و پیش‌نمایش‌ها/منابع عمومی قابل‌دسترسی استفاده شده است. اگر نسخه قانونی کامل هر کتاب در اختیار پروژه قرار گیرد، می‌توان لایه دانش را با مطالعه همان نسخه دقیق‌تر و فصل‌به‌فصل کالیبره کرد.
