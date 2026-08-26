# منابع داده موتور Global Intelligence / Clustered Rotation

این سند منابع تغذیه مدل ۱۰۰۰+ عامل، خوشه‌ها، Lead/Lag، Velocity، Acceleration، Supply/Demand، Capital Flow و Future Demand را در **۱۰ دسته استاندارد** سازمان‌دهی می‌کند.

## ۱. اقتصاد کلان، پول و اعتبار

- IMF Data / WEO / IFS / BOP / COFER
- BIS Statistics
- World Bank Data
- OECD Data
- FRED
- Fed، ECB، BoE، BoJ، PBoC و سایر بانک‌های مرکزی
- آمار رسمی کشورها

**متغیرها:** GDP، CPI/PPI، نرخ بهره، نقدینگی، اعتبار، بدهی، ترازنامه بانک مرکزی، ارز، کسری بودجه و جریان سرمایه.

## ۲. انرژی و مواد اولیه

- IEA
- EIA
- USGS
- World Bank Commodity Markets
- LME / CME / COMEX
- گزارش تولیدکنندگان و آمار رسمی

**متغیرها:** تولید، مصرف، ذخایر، موجودی، ظرفیت، قیمت، منحنی آتی، CAPEX و محدودیت عرضه.

## ۳. طلا، نقره و ذخایر ارزش

- World Gold Council
- LBMA
- CME/COMEX
- IMF
- بانک‌های مرکزی
- ETF/fund reports

**متغیرها:** خرید بانک‌های مرکزی، ETF flows، موجودی، futures/options، positioning، real rates و تقاضای سرمایه‌گذاری.

## ۴. فناوری، AI، تراشه و دیتاسنتر

- IEA
- DOE/EIA
- SEC/EDGAR
- گزارش‌های رسمی شرکت‌های فناوری
- اپراتورهای شبکه برق
- داده‌های صنعت نیمه‌رسانا و تجهیزات

**زنجیره کلیدی:**

`AI → Chips → Data Centers → Electricity → Cooling → Grid → Copper/Aluminum → CAPEX → Corporate Profit`

**متغیرها:** CAPEX، سفارش، backlog، مصرف برق، ظرفیت دیتاسنتر، GPU/CPU، semiconductor capacity و lead time.

## ۵. بازار سرمایه، مشتقات و جریان سرمایه

- بورس‌ها و اپراتورهای رسمی
- SEC/EDGAR
- CFTC COT
- ETF issuers / fund reports
- Futures / Options venues
- داده‌های معتبر market microstructure

**متغیرها:** Price، Volume، Value، Breadth، OI، IV، Skew، Put/Call، positioning، fund flow، insider/ownership disclosures و market breadth.

## ۶. تجارت، کالا و زنجیره تأمین جهانی

- UN Comtrade
- WTO
- UNCTAD
- گمرکات رسمی کشورها
- Eurostat
- FAO
- داده‌های حمل‌ونقل و کشتیرانی

UN Comtrade داده تجارت را مستقیماً از نهادهای آماری رسمی کشورها دریافت می‌کند. citeturn0search1

**متغیرها:** Import، Export، volume، value، trade balance، مسیر تجارت، freight، bottleneck و تغییر سهم تأمین‌کنندگان.

## ۷. ملک، ساخت‌وساز و زیرساخت فیزیکی

- بانک‌های مرکزی و BIS
- World Bank / OECD
- آمار رسمی مسکن کشورها
- مجوز ساخت و starts/completions
- داده اجاره و قیمت زمین
- گزارش شرکت‌های ساختمانی و تولیدکنندگان مصالح

**متغیرها:** قیمت مسکن، اجاره، معاملات، mortgage rates، permits، starts، completions، vacancy، land prices و construction costs.

## ۸. غذا، کشاورزی، آب و اقلیم

- FAO / FAOSTAT
- USDA
- World Bank
- IEA
- داده‌های هواشناسی و اقلیمی رسمی
- IPCC و منابع پژوهشی معتبر

**متغیرها:** تولید، سطح زیرکشت، موجودی، قیمت غذا، کود، آب، خشکسالی، دما، بارش و ریسک اقلیمی.

## ۹. صنعت، سلامت، نیروی کار و تقاضای مصرف‌کننده

- ILO / ILOSTAT
- WHO و منابع رسمی سلامت
- OECD
- آمار رسمی کشورها
- SEC/گزارش شرکت‌ها
- PMI و نظرسنجی‌های معتبر

**متغیرها:** اشتغال، دستمزد، بهره‌وری، مصرف، درآمد، PMI، ظرفیت صنعتی، سفارش‌ها، حاشیه سود، تقاضای مصرف‌کننده و کمبود نیروی متخصص.

## ۱۰. ژئوپلیتیک، سیاست، خبر و رویدادهای شوک‌آور

- دولت‌ها و سازمان‌های بین‌المللی
- IMF / World Bank / OECD
- IEA برای شوک‌های انرژی
- Reuters و سایر منابع خبری معتبر برای Event Detection
- گزارش‌های رسمی تحریم، جنگ، تعرفه، انتخابات و سیاست‌گذاری

**قاعده:** خبر ابتدا `event signal` است؛ برای تبدیل شدن به داده قطعی باید با منبع اولیه یا داده مستقل تأیید شود.

---

# لایه استانداردسازی برای BabiMind

هر منبع باید پس از دریافت به متغیرهای استاندارد تبدیل شود:

`current_price`
`demand_growth`
`supply_growth`
`supply_constraint`
`inventory_change`
`capital_flow`
`future_demand`
`attention`
`velocity`
`acceleration`
`lead_lag`
`network_centrality`
`accumulation_signal`
`macro_sensitivity`
`geopolitical_sensitivity`

امتیاز فرصت:

`Opportunity = f(FutureDemand, DemandGrowth, SupplyConstraint, AttentionGap, Flow, Velocity, Acceleration, LeadLag, NetworkImpact, RelativeValue)`

## اولویت منابع

`Official/Primary → Market Data → Corporate Filings → International Institutions → Verified News → Secondary Cross-check`

IMF نیز منابعی مانند BIS، ECB، Eurostat، ILO، OECD، UN و World Bank را در مجموعه منابع داده بین‌المللی خود معرفی می‌کند. citeturn0search0turn0search2

برای تجارت، UN Comtrade داده را از نهادهای آماری رسمی کشورها دریافت می‌کند. citeturn0search1

برای کالاها، داده‌های مورد استفاده در پژوهش‌های IMF/World Bank نیز ترکیبی از منابعی مانند FAO، IEA، USGS، UN Comtrade و منابع بازار کالا هستند. citeturn0search12turn0search13

### نکته مهم درباره «انباشت»

رشد هم‌زمان قیمت، حجم یا معاملات بزرگ به‌تنهایی اثبات نمی‌کند که «افراد پولدار در حال جمع‌آوری» هستند. مدل فقط باید آن را به‌عنوان `accumulation-compatible signal` ثبت کند و با جریان پول، موجودی، عرضه، معاملات و داده بنیادی مستقل تأیید کند.
