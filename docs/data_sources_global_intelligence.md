# منابع داده Global Intelligence / BabiMind

این سند **یکپارچه نهایی** منابع تغذیه مدل ۱۰۰۰+ عامل، خوشه‌های هم‌حرکت، Lead/Lag، Direction، Velocity، Acceleration، Supply/Demand، Capital Flow، Future Demand و Accumulation-compatible Signal است.

ساختار دو بعدی است:

1. **۱۰ دسته موضوعی** — «چه چیزی را اندازه می‌گیریم؟»
2. **۲۰ دسته نوع منبع** — «اطلاعات را از چه نوع منبعی می‌گیریم؟»

یک منبع می‌تواند هم‌زمان در چند دسته قرار بگیرد.

---

# بخش A — ۱۰ دسته موضوعی

## ۱. اقتصاد کلان، پول و اعتبار
- IMF Data / WEO / IFS / BOP / COFER
- BIS Statistics
- World Bank Data
- OECD Data
- FRED / ALFRED
- Fed، ECB، BoE، BoJ، PBoC و سایر بانک‌های مرکزی
- آمار رسمی کشورها

متغیرها: GDP، CPI/PPI، نرخ بهره، نقدینگی، اعتبار، بدهی، ترازنامه بانک مرکزی، ارز، کسری بودجه، جریان سرمایه و شرایط مالی.

## ۲. انرژی و مواد اولیه
- IEA
- EIA
- USGS
- World Bank Commodity Markets
- LME / CME / COMEX
- آمار رسمی و گزارش تولیدکنندگان

متغیرها: تولید، مصرف، ذخایر، موجودی، ظرفیت، قیمت، futures curve، CAPEX، lead time و supply constraint.

## ۳. طلا، نقره و ذخایر ارزش
- World Gold Council
- LBMA
- CME/COMEX
- IMF
- بانک‌های مرکزی
- ETF/fund reports

متغیرها: خرید بانک مرکزی، ETF flows، موجودی، futures/options، positioning، real rates و تقاضای سرمایه‌گذاری.

## ۴. فناوری، AI، تراشه و دیتاسنتر
- IEA
- DOE/EIA
- SEC/EDGAR
- گزارش‌های رسمی شرکت‌های فناوری
- اپراتورهای شبکه برق
- داده صنعت نیمه‌رسانا و تجهیزات

زنجیره کلیدی:
`AI → Chips → Data Centers → Electricity → Cooling → Grid → Copper/Aluminum → CAPEX → Corporate Profit`

متغیرها: CAPEX، سفارش، backlog، مصرف برق، ظرفیت دیتاسنتر، GPU/CPU، semiconductor capacity و lead time.

## ۵. بازار سرمایه، مشتقات و جریان سرمایه
- بورس‌ها و اپراتورهای رسمی
- SEC/EDGAR
- CFTC COT
- ETF issuers / fund reports
- Futures / Options venues
- market microstructure

متغیرها: Price، Volume، Value، Breadth، OI، IV، Skew، Put/Call، positioning، fund flow، ownership disclosures و liquidity.

## ۶. تجارت، کالا و زنجیره تأمین جهانی
- UN Comtrade
- WTO
- UNCTAD
- گمرکات رسمی
- Eurostat
- FAO
- داده حمل‌ونقل و کشتیرانی

متغیرها: Import، Export، volume، value، trade balance، freight، bottleneck و تغییر سهم تأمین‌کنندگان.

## ۷. ملک، ساخت‌وساز و زیرساخت فیزیکی
- بانک‌های مرکزی و BIS
- World Bank / OECD
- آمار رسمی مسکن
- permits / starts / completions
- اجاره و قیمت زمین
- گزارش شرکت‌های ساختمانی و تولیدکنندگان مصالح

متغیرها: قیمت، اجاره، معاملات، mortgage rates، permits، starts، completions، vacancy، land prices و construction costs.

## ۸. غذا، کشاورزی، آب و اقلیم
- FAO / FAOSTAT
- USDA
- World Bank
- IEA
- داده‌های رسمی هواشناسی و اقلیمی
- IPCC و پژوهش‌های معتبر

متغیرها: تولید، سطح زیرکشت، موجودی، قیمت غذا، کود، آب، خشکسالی، دما، بارش و ریسک اقلیمی.

## ۹. صنعت، سلامت، نیروی کار و تقاضای مصرف‌کننده
- ILO / ILOSTAT
- WHO
- OECD
- آمار رسمی
- SEC/گزارش شرکت‌ها
- PMI و نظرسنجی‌های معتبر

متغیرها: اشتغال، دستمزد، بهره‌وری، مصرف، درآمد، PMI، ظرفیت صنعتی، سفارش‌ها، حاشیه سود، تقاضای مصرف‌کننده و کمبود نیروی متخصص.

## ۱۰. ژئوپلیتیک، سیاست، خبر و شوک
- دولت‌ها و سازمان‌های بین‌المللی
- IMF / World Bank / OECD
- IEA برای شوک‌های انرژی
- Reuters و سایر منابع خبری معتبر برای Event Detection
- گزارش‌های رسمی تحریم، جنگ، تعرفه، انتخابات و سیاست‌گذاری

قاعده: خبر ابتدا `event signal` است؛ برای تبدیل به داده قطعی باید با منبع اولیه یا داده مستقل تأیید شود.

---

# بخش B — ۲۰ دسته نوع منبع

## ۱. رسمی / Official
دولت، بانک مرکزی، بورس، نهاد آماری، رگولاتور و سازمان بین‌المللی.

نمونه: IMF، BIS، World Bank، OECD، Fed، ECB، SEC، CFTC، UN، Eurostat و بانک‌های مرکزی.

کاربرد: Ground Truth، سیاست، اقتصاد کلان، تجارت و بازار سرمایه.

## ۲. غیررسمی / Unofficial
شرکت‌ها، انجمن‌ها، پژوهشگران مستقل، فعالان بازار و پایگاه‌های تخصصی.

کاربرد: Discovery و Signal؛ ادعاهای مهم باید Cross-check شوند.

## ۳. مقاله / Article
مقالات تحلیلی، خبری و تخصصی.

خروجی: Event، Narrative، Hypothesis و Attention.

## ۴. تحقیق / Research & Academic
ژورنال علمی، Working Paper، اقتصادسنجی، مالی، مهندسی و علوم داده.

نمونه: NBER، SSRN، arXiv، دانشگاه‌ها و پژوهش‌های بانک‌های مرکزی.

کاربرد: علیت، Lead/Lag، کشش تقاضا، پیش‌بینی و آزمون فرضیه.

## ۵. گزارش / Reports
Annual/Quarterly Report، Industry Report، Commodity Outlook و Economic Outlook.

کاربرد: CAPEX، backlog، supply/demand، guidance، سودآوری و سناریوها.

## ۶. مصاحبه / Interviews & Speeches
مدیران، سیاست‌گذاران، اقتصاددانان، متخصصان و فعالان زنجیره تأمین.

کاربرد: Forward Guidance، انتظارات و تغییر Narrative.

وزن آن پایین‌تر از داده سخت است مگر اینکه با داده واقعی تأیید شود.

## ۷. آرشیو / Archives & Historical Data
قیمت تاریخی، گزارش‌های قبلی، خبرهای قدیمی، snapshot و vintage data.

نمونه: ALFRED.

کاربرد: Backtest و جلوگیری از Look-ahead Bias.

## ۸. ترید / Trading & Market Microstructure
- Trades
- Order Book
- Bid/Ask
- Volume
- Open Interest
- Futures
- Options
- IV/Greeks
- Skew
- Positioning
- ETF Flows

کاربرد: Flow، Liquidity، Momentum، Accumulation-compatible و Regime Detection.

## ۹. APIهای رایگان / Free & Freemium APIs
- FRED / ALFRED API
- ECB Data API
- IMF Data API
- World Bank API
- UN/Comtrade APIs
- Alpha Vantage free tier
- APIهای رسمی بورس‌ها و نهادهای آماری

محدودیت quota، latency، revision و terms باید در Adapter ثبت شود.

## ۱۰. سایت‌های معتبر / Trusted Websites
IMF، BIS، World Bank، OECD، IEA، EIA، USGS، WGC، LBMA، SEC، CFTC، UN، FAO، ILO، WHO، Reuters و منابع رسمی مشابه.

قاعده: نام معتبر کافی نیست؛ provenance و timestamp باید ثبت شود.

## ۱۱. داده خام / Primary Raw Data
سنسور، کنتور، تولید واقعی، موجودی انبار، shipment، load برق، تولید معدن و ظرفیت کارخانه.

کاربرد: Supply/Demand با کمترین واسطه.

## ۱۲. Alternative Data
ترافیک، حمل‌ونقل، مصرف برق، داده اپلیکیشن، تراکنش تجمیعی، تصاویر ماهواره‌ای و جست‌وجوی اینترنتی.

کاربرد: تشخیص تغییر قبل از انتشار آمار رسمی.

## ۱۳. Satellite & Geospatial
تصاویر ماهواره‌ای، کشتی‌ها، بنادر، معدن، زمین کشاورزی، ساخت‌وساز، نور شب و سطح آب.

کاربرد: اندازه‌گیری فعالیت فیزیکی.

## ۱۴. Patent / R&D / Innovation
Patent filings، R&D spending، publications، product launches و research grants.

کاربرد: Future Demand و فناوری‌های نوظهور با افق چندساله.

## ۱۵. Procurement / Contracts
قرارداد دولتی، مناقصه، سفارش بزرگ، procurement، قرارداد زیرساخت و خرید تجهیزات.

کاربرد: تشخیص CAPEX پیش از اثرگذاری کامل بر صورت مالی.

## ۱۶. Labor & Hiring
آگهی استخدام، دستمزد، مهارت، کمبود نیروی متخصص و جریان مهاجرت کاری.

کاربرد: تشخیص رشد/کاهش تقاضای واقعی نیروی کار و فناوری.

## ۱۷. Attention & Sentiment
جست‌وجوی اینترنتی، رسانه، شبکه اجتماعی، sentiment و engagement.

کاربرد: Attention Gap و تغییر Narrative.

این داده‌ها Signal هستند، نه Ground Truth.

## ۱۸. Physical Flow
کشتی، کانتینر، بنادر، برق، خط لوله، حمل‌ونقل، موجودی و جریان فیزیکی کالا.

کاربرد: Supply/Demand و Bottleneck Detection.

## ۱۹. Network & Dependency
Supplier/Customer، Input-Output، مالکیت، وابستگی کشورها، جایگزین‌ها و گلوگاه‌ها.

کاربرد: Network Centrality، Shock Propagation و Second/Third-Order Effects.

## ۲۰. Point-in-Time / Vintage Data
داده نسخه‌گذاری‌شده همراه با زمان انتشار واقعی، revision و vintage.

کاربرد حیاتی: Backtest بدون Look-ahead Bias.

---

# بخش C — استاندارد امتیازدهی منبع

برای هر منبع این متادیتا ثبت شود:

`source_id`
`source_type`
`topic_cluster`
`publisher`
`url`
`api_endpoint`
`frequency`
`release_timestamp`
`observation_timestamp`
`vintage_timestamp`
`revision_risk`
`authority`
`independence`
`timeliness`
`coverage`
`historical_depth`
`reproducibility`
`api_reliability`
`manipulation_risk`
`point_in_time_quality`
`confidence`

## اولویت پایه

`Official/Primary → Market Data → Corporate Filings → Physical/Alternative Data → International Research → Verified News → Secondary Cross-check → Unverified Signal`

هیچ منبعی فقط به‌خاطر «رسمی بودن» همیشه برنده نیست؛ برای هر متغیر باید بهترین منبع بر اساس تازگی، دقت، پوشش، revision و استقلال انتخاب شود.

---

# بخش D — تبدیل منبع به سیگنال BabiMind

هر داده پس از ingestion باید به متغیرهای استاندارد تبدیل شود:

`current_value`
`change_1d`
`change_7d`
`change_30d`
`trend`
`direction`
`velocity`
`acceleration`
`demand_growth`
`supply_growth`
`supply_constraint`
`inventory_change`
`capital_flow`
`future_demand`
`attention`
`attention_gap`
`lead_lag`
`network_centrality`
`accumulation_signal`
`macro_sensitivity`
`geopolitical_sensitivity`
`relative_value`
`confidence`

امتیاز فرصت:

`Opportunity = f(FutureDemand, DemandGrowth, SupplyConstraint, AttentionGap, Flow, Velocity, Acceleration, LeadLag, NetworkImpact, RelativeValue, Confidence)`

---

# بخش E — قواعد ضدخطا

1. خبر، مصاحبه یا شبکه اجتماعی به‌تنهایی نباید Ground Truth شود.
2. «انباشت سرمایه‌دار» فقط `accumulation-compatible signal` است، نه اثبات نیت.
3. داده اصلاح‌شده باید با vintage اصلی در Backtest نگهداری شود.
4. هر observation باید `observation_timestamp` و `release_timestamp` داشته باشد.
5. چند منبع مستقل برای سیگنال‌های مهم ترجیح داده شود.
6. وابستگی دو منبع به یک upstream source باید در independence لحاظ شود.
7. API رایگان فقط در صورت کافی بودن کیفیت، پوشش و SLA وارد مسیر اصلی شود؛ در غیر این صورت fallback باشد.
8. برای داده‌های بازار، timezone و session باید استاندارد شود.
9. داده‌های missing، stale و revised باید امتیاز confidence را کاهش دهند.
10. هر سیگنال باید provenance قابل بازتولید داشته باشد.

---

# بخش F — اتصال به مدل ۱۰۰۰+ عامل

`Sources (20 Types)`
`→ 10 Topic Domains`
`→ Subclusters`
`→ 1000+ Factors`
`→ Direction`
`→ Velocity`
`→ Acceleration`
`→ Lead/Lag`
`→ Supply/Demand`
`→ Capital Flow`
`→ Future Demand`
`→ Network Propagation`
`→ Opportunity Ranking`

هدف نهایی BabiMind این نیست که فقط بگوید «چه چیزی امروز بالا رفت»؛ بلکه باید تشخیص دهد:

**چه چیزی در حال مهم‌تر شدن است، کدام خوشه شتاب می‌گیرد، رهبر و دنباله‌رو کدام‌اند، چه چیزی هنوز توجه بازار را نگرفته، پول جدید با چه سرعتی وارد شده و شوک بعدی احتمالاً به کجا منتقل می‌شود.**

---

# منابع و اعتبارسنجی

IMF مجموعه‌ای از منابع رسمی و بین‌المللی مانند BIS، ECB، Eurostat، ILO، OECD، UN و World Bank را به‌عنوان منابع داده معرفی می‌کند. citeturn0search0turn0search3

IMF Data API دسترسی برنامه‌ای به داده‌ها را از طریق SDMX 2.1 و SDMX 3.0 فراهم می‌کند. citeturn0search5

منابع بین‌المللی همچنین از داده‌های شریک/ملی، آمار بانکی BIS، داده‌های IMF، OECD و World Bank و داده‌های تجاری/بازاری برای cross-check استفاده می‌کنند. citeturn0search1turn0search6


---

## Automated refresh metadata
Last catalog refresh: 2026-09-05T09:46:45Z

Refresh cadence: every 4 days
