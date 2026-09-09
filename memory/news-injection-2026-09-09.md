# News Injection — 2026-09-09 (pre-open)

> Evidence for Event/Decision layers only. Not ground-truth market prices.
> Policy: external news ≠ synthetic signals; confidence tagged.

## A. Pezeshkian / Decision actors

| Event | as_of (approx) | Summary | Model impact | Confidence |
|-------|----------------|---------|--------------|------------|
| CBI coordination meeting | 1405/06/03 | پزشکیان + مدنی‌زاده + همتی: هماهنگی پولی/ارزی، مهار انتظارات تورمی، ثبات در شرایط جنگ/محاصره | وزن سناریوی «مدیریت تدریجی ارز» ↑؛ تعهد معتبر هنوز اعلام موضع است نه اجرا | 0.7 |
| Reforms under war | مرداد–شهریور ۱۴۰۵ | اصلاح بانک، ارز، انرژی، یارانه، حذف رانت؛ اصلاحات متوقف نمی‌شود | مسیر سناریوی اصلاح ساختاری باز می‌ماند ولی اجرای پرهزینه نامطمئن | 0.65 |
| Reciprocal MoU with US | ~۱۰ شهریور ۱۴۰۵ | اگر آمریکا به تعهدات یادداشت تفاهم بازگردد ایران عمل متقابل می‌کند | option value کاهش تنش؛ نه رژیم شیفت قطعی | 0.6 |
| Madani-zadeh vs Bessent | ۱۵ شهریور ۱۴۰۵ | اقتصاد را مردم می‌سازند نه فشار خارجی؛ تنوع شرکا، صادرات غیرنفتی، تورم | سیگنال مقاومت سیاسی در برابر فشار؛ اثر کوتاه‌مدت روی صرف ریسک محدود | 0.55 |
| Trade fall admission | ~اواخر مرداد | افت صادرات/واردات ~۲۵–۳۵٪؛ فشار درآمد نفت و مالیات | تقویت فاکتور monetization gap + fiscal stress | 0.75 |
| Fuel / subsidy stress | شهریور ۱۴۰۵ | بحث افزایش سهمیه سوم بنزین؛ کسری روزانه بنزین؛ ناترازی انرژی | حلقه بودجه–سوخت–تورم فعال | 0.7 |

## B. Macro / Oil / Hormuz

| Factor | Direction | Evidence | Confidence |
|--------|-----------|----------|------------|
| Oil export blockade / stockpiles | Negative for FX revenue | گزارش‌ها: کاهش شدید بارگیری، موجودی روی آب در حال اتمام (اکتبر؟) | 0.7 external |
| Brent ~$98–99 | Mixed | نفت بالا ≠ ارز قابل‌دسترس | 0.85 price, 0.5 transmission |
| Free USD ~229k toman | Negative equity pure risk-on | روند صعودی از ~۲۰۰ک پایان مرداد | 0.75 street quotes |
| Official vs free gap ~40%+ | Negative credibility | CBI ~1.62M IRR vs street ~2.28M | 0.75 |
| Inflation stress | Negative | گزارش‌های رسمی/رسانه‌ای فشار بالا | 0.65 |

## C. Bourse (external corroboration only)

| Claim | Note |
|-------|------|
| شاخص کل در جلسات اخیر به سمت کانال ۷ میلیون گزارش شده | فقط corroboration خارجی؛ snapshot داخلی Tahlil برای امروز validate نشده |
| رشد گسترده با هم‌وزن در برخی روزها؛ ورود حقیقی در یک گزارش ~۷.۵ همت | برای bias نیاز به تأیید API/جریان داخلی |
| فملی در یک گزارش از مؤثران رشد شاخص | thesis فملی همچنان volume+FX+copper |

**Rule:** تا snapshot داخلی تازه، equity breadth/flow در مدل `unverified` می‌ماند.

## D. Options

| Item | Status |
|------|--------|
| زنجیره فملی (ضملی و …) | فعال در بازار؛ اندازه قرارداد فملی تعدیل‌شده (مثلاً ۱۳۷۱) |
| قانون سخت | `expiry > now`؛ قرارداد منقضی در ranking ممنوع |
| داده زنده | اولویت BRS/realtime داخلی؛ وب فقط پشتیبان |
| Greeks/IV | فقط در صورت داده کافی؛ وگرنه partial |
| نمونه تاریخی | ضملی۷۰۶۱ و مشابه در آرشیو؛ برای امروز باید chain تازه ingest شود |

## E. Scenario weights (Decision layer update — conditional)

**تصمیم/مسیر کاهش تنش و ارز**
- تداوم مدیریت کنترلی بدون توافق بزرگ: ~45%
- گام محدود دیپلماسی/مسیر کشتیرانی: ~30%
- تشدید فشار/اقدام اضطراری‌تر: ~25%

اگر دلار آزاد شتاب بگیرد و flow سهام منفی شود → وزن سناریوی ۳↑.
اگر تثبیت ارز + ورود حقیقی → وزن سناریوی ۲↑ برای equity.

## F. Provenance
- منابع: مشرق/شفقنا/انتخاب/تابناک (پزشکیان)، جماران/شرق/برنا (بورس)، Reuters/WSJ-style/AlJazeera summaries (نفت/بلوکه)، ره‌آورد/آپشن‌باز (اختیار)
- Injected: 2026-09-09T pre-open
- No fabricated prices or option quotes
