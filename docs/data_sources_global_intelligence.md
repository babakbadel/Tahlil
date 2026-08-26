# منابع داده موتور Global Intelligence / Clustered Rotation

این سند فهرست منابع پیشنهادی برای تغذیه مدل ۱۰۰۰+ عامل، خوشه‌ها، Lead/Lag، Velocity، Acceleration، Supply/Demand، Capital Flow و Future Demand است.

## 1. اقتصاد کلان و نقدینگی

- IMF Data / WEO: رشد، تورم، بدهی، تجارت و پیش‌بینی‌های اقتصاد کلان.
- BIS Statistics: اعتبار، بانکداری، نرخ‌ها و جریان‌های مالی بین‌المللی.
- World Bank Data / Commodity Markets: شاخص‌های اقتصاد جهانی و قیمت کالاها.
- OECD Data: فعالیت اقتصادی، تجارت، تورم و شاخص‌های ساختاری.
- FRED: نرخ بهره، پول، اعتبار، بازار کار و سری‌های مالی آمریکا.
- بانک‌های مرکزی: Fed، ECB، BoE، BoJ، PBoC و سایر بانک‌های مرکزی برای نرخ‌ها، ترازنامه و سیاست پولی.

## 2. کالاها و مواد اولیه

- USGS: تولید، ذخایر و زنجیره عرضه مواد معدنی.
- IEA: نفت، گاز، برق، انرژی پاک، تقاضای انرژی و سرمایه‌گذاری.
- EIA: تولید/مصرف/ذخایر انرژی آمریکا.
- World Bank Commodity Markets: قیمت‌های جهانی کالاها.
- LME/COMEX/CME: قیمت و معاملات فلزات و قراردادهای آتی.
- FAO: غذا، کشاورزی و شاخص‌های مواد غذایی.

## 3. طلا و فلزات گرانبها

- World Gold Council: تقاضای طلا، ETFها، بانک‌های مرکزی، عرضه و بخش فناوری.
- LBMA: قیمت‌های مرجع فلزات گرانبها.
- CME/COMEX: futures/options و positioning قابل دسترس.
- IMF/بانک‌های مرکزی: ذخایر رسمی طلا در صورت انتشار.

## 4. AI، دیتاسنتر و زیرساخت دیجیتال

- IEA: مصرف برق دیتاسنترها و اثر AI بر تقاضای انرژی.
- U.S. DOE/EIA: شبکه برق، ظرفیت تولید و مصرف.
- شرکت‌های فناوری و گزارش‌های مالی رسمی: CAPEX، GPU/CPU، دیتاسنتر و سفارش‌ها.
- SEC filings / annual & quarterly reports: سرمایه‌گذاری، درآمد، حاشیه سود و backlog.
- داده‌های شبکه برق و اپراتورهای منطقه‌ای: ظرفیت، load، transmission constraints و interconnection queues.

## 5. بازار سرمایه و جریان پول

- بورس‌ها و اپراتورهای رسمی: قیمت، حجم، ارزش معاملات و market breadth.
- SEC/EDGAR: گزارش‌های شرکت‌ها و مالکیت‌های افشاشده.
- CFTC COT: positioning در قراردادهای آتی.
- ETF issuers / fund reports: ورود و خروج سرمایه.
- گزینه‌ها و futures: open interest، volume، implied volatility و skew در صورت دسترسی معتبر.

## 6. مس و زنجیره مواد حیاتی

برای سناریوهایی مثل AI → برق → شبکه → مس، حداقل این متغیرها باید جمع‌آوری شوند:

`price + inventory + mine_supply + refined_supply + demand + imports + exports + smelter_activity + treatment_charges + capex + futures_curve + positioning`

منابع اصلی: USGS، IEA، World Bank، LME/CME، گمرکات رسمی، گزارش شرکت‌های معدنی و تولیدکنندگان.

## 7. ملک و ساخت‌وساز

- BIS/بانک‌های مرکزی: نرخ وام و شرایط اعتباری.
- World Bank/OECD: ساخت‌وساز و اقتصاد کلان.
- آمار رسمی کشورها: قیمت مسکن، معاملات، مجوز ساخت، starts/completions، اجاره و زمین.
- گزارش شرکت‌های ساختمانی و مصالح: backlog، CAPEX و هزینه نهاده‌ها.

## 8. تجارت، حمل‌ونقل و زنجیره تأمین

- UN Comtrade: تجارت کالا.
- WTO: تجارت جهانی و سیاست تجاری.
- UNCTAD: کشتیرانی و تجارت دریایی.
- Baltic Exchange و داده‌های حمل‌ونقل در صورت دسترسی.
- گمرکات رسمی کشورها: واردات/صادرات و حجم کالا.

## 9. ژئوپلیتیک و ریسک

- IMF/World Bank/OECD برای اثرات اقتصادی.
- IEA برای انرژی و شوک عرضه.
- داده‌های رسمی دولت‌ها و سازمان‌های بین‌المللی.
- Reuters و منابع خبری معتبر برای event detection؛ خبر باید به‌عنوان سیگنال ورودی استفاده شود، نه حقیقت بدون تأیید.

## 10. روش اتصال به مدل

برای هر عامل `i`، داده‌ها به این متغیرها تبدیل شوند:

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

امتیاز فرصت نباید صرفاً از قیمت ساخته شود:

`Opportunity = f(FutureDemand, DemandGrowth, SupplyConstraint, AttentionGap, Flow, Velocity, Acceleration, LeadLag, NetworkImpact, RelativeValue)`

## اولویت منابع

1. داده رسمی/اولیه
2. داده بازار با timestamp و methodology مشخص
3. گزارش مالی شرکت‌ها و filing رسمی
4. مؤسسات بین‌المللی معتبر
5. منابع خبری معتبر برای تشخیص رویداد
6. منابع ثانویه فقط برای cross-check

### نکته مهم

وجود هم‌زمان رشد قیمت، حجم یا معاملات بزرگ به‌تنهایی اثبات «انباشت توسط پولدارها» نیست. مدل باید آن را به‌عنوان `accumulation-compatible signal` ثبت کند و با جریان پول، موجودی، عرضه، معاملات و داده بنیادی مستقل تأیید کند.
