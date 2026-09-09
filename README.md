# تحلیل بابک — Tahlil

مخزن مرکزی **BabiMind / تحلیل بابک** برای جمع‌آوری داده، مدل‌سازی، تحلیل و پیش‌بینی بازارهای مالی و اقتصاد ایران.

هدف پروژه این است که هر داده، تحلیل، مدل، نتیجهٔ ران و تجربهٔ حاصل از خطاها به‌صورت قابل‌ردگیری وارد سیستم شود و به‌مرور یک **مغز مرکزی تحلیل مالی و اقتصادی (Multi-Layer Financial & Economic Intelligence)** ساخته شود.

**Repository:** `babakbadel/Tahlil` · **مدل مرکزی:** `BabiMind`

---

## 🧠 BabiMind چیست؟

**BabiMind** مغز مرکزی پروژه است؛ نه یک اسکریپت یا یک مدل منفرد.

لایه‌های اطلاعات روی هم قرار می‌گیرند و برای بازار، سناریو، احتمال و تصمیم خروجی می‌سازند.

### لایه‌های اصلی

1. **Market Data** — قیمت، حجم، ارزش معاملات، جریان سفارش
2. **Codal / Fundamental** — صورت‌های مالی و گزارش‌های کدال
3. **Technical Analysis** — اندیکاتور، روند، حمایت/مقاومت
4. **Price Action** — رفتار قیمت، شکست، نقدینگی، مومنتوم
5. **Options** — اختیار، ارزش ذاتی/زمانی، IV، Greeks، سناریو سود/زیان
6. **Flow & Rotation** — ورود/خروج نقدینگی و چرخش صنایع
7. **Macro Economy** — تورم، نقدینگی، نرخ، بودجه، ارز، تجارت
8. **Gold & Dollar** — دلار آزاد/رسمی، اونس، طلا، سکه
9. **International Factors** — نفت، کامودیتی، DXY، چین، ژئوپلیتیک
10. **Decision Engine / مدل تصمیم** — بازیگران، شواهد زمان‌مند، سناریو
11. **Game Theory** — دولت، بانک مرکزی، بازار، بازیگران خارجی
12. **System Dynamics** — حلقه‌های بازخورد و اثرات مرتبه ۲/۳
13. **Event Time / News** — تزریق اخبار با provenance و confidence
14. **Forecasting & Scenario** — سناریو چندافقه و احتمال
15. **Backtesting** — ارزیابی تاریخی و کالیبراسیون
16. **Model Memory** — حافظه ران‌ها، outcome، خطاها
17. **Economic Graph** — گراف علّی بازار (جدا از Graphify کد)
18. **Graphify** — گراف ساختاری کدبیس برای عامل‌ها

**هیچ لایهٔ منفردی به‌تنهایی تصمیم نهایی نیست.**

---

## 📁 نقشهٔ ریپو (آنچه واقعاً پیاده شده)

### هستهٔ اپلیکیشن — `app/`

| مسیر | نقش |
|------|-----|
| `app/data/brsapi/` | کلاینت BRS، realtime، stream hub، فیلدهای آپشن |
| `app/data/finpy_tse_adapter.py` | آداپتر FinPy-TSE |
| `app/decision/` | **Decision Engine**: models، network (as_of)، history (JSONL append-only)، engine |
| `app/economic_graph/` | **EconomicGraphStore**: node/edge زمان‌مند، snapshot، score_target |
| `app/forecasting/` | historical forecaster، regimes، walk-forward |
| `app/options/` | ranking اختیار |
| `app/rotation/` | cluster engine چرخش صنایع |

### اسکریپت‌های عملیاتی — `scripts/`

| گروه | نمونه‌ها |
|------|----------|
| Pipeline | `babimind_pipeline.py`، `babimind_v1.py`، `babimind_factor_*` |
| داده بازار | `collect_finpy_tse.py`، `scan_market.py`، `ingest_*`، `backfill.py` |
| آپشن | `rank_options_babimind.py`، `score_options_*`، `collect_tse_option_chain.py`، `fetch_options_realtime.py` |
| کلان/جهانی | `babimind_global_market.py`، `score_dollar_experts.py` |
| حافظه/گراف | `babimind_memory.py`، `babimind_graph.py`، `load_economic_graph_seed.py` |
| اخبار/تصمیم | `babimind_pezeshkian_news.py`، `babimind_llm_router.py`، `babimind_gemini.py` |
| realtime | `run_realtime_api.py` |

### مدل پزشکیان و نظریه بازی

| مسیر | محتوا |
|------|--------|
| `docs/pezeshkian-model.md` | طراحی مدل تصمیم پزشکیان |
| `config/babimind_pezeshkian_model.yml` | تنظیمات |
| `memory/pezeshkian-decision-system-dynamics-*.md` | پویایی سیستم + سناریو سه‌گانه |
| `people/` | شبکه افراد/مشاوران |
| `app/decision/network.py` | snapshot نفوذ با as_of |

**قواعد:** سمت رسمی ≠ نفوذ واقعی · پیش‌بینی immutable · outcome فقط الحاقی · سه سناریو با مجموع احتمال ۱.

### Price Action / تکنیکال / جریان

- لایهٔ مفهومی در README لایه‌ها + Feature Panel (`docs/feature-panel-schema.md`)
- Rotation: `app/rotation/cluster_engine.py`، `docs/babimind_clustered_rotation.md`
- قوانین باطل‌کننده: جهش دلار + خروج حقیقی + افت AD

### اختیار معامله (Options)

| جزء | مسیر |
|-----|------|
| نرمال‌سازی realtime | `app/data/brsapi/` |
| Ranking | `app/options/ranking.py` + `scripts/rank_options_*` |
| Pipeline قوانین | `graph/option-ranking-pipeline.md` |
| **قانون سخت** | فقط `expiry > now`؛ منقضی در universe فعال ممنوع |

### اخبار و Event Time

| مسیر | نقش |
|------|-----|
| `config/babimind_news_sources.json` | کاتالوگ منابع |
| `scripts/babimind_pezeshkian_news.py` | جمع‌آوری خبر پزشکیان |
| `memory/news-injection-*.md` | تزریق ساختارمند به مدل |
| `artifacts/babimind_news_injection_*.json` | ingest ماشینی |
| `docs/news-trigger.md` | تریگر خبر |

### گراف و حافظه

| مسیر | نقش |
|------|-----|
| `graph/babimind-graph-schema.md` | اسکیمای Graph Intelligence |
| `app/economic_graph/` + `docs/economic-graph-store.md` | گراف اقتصادی بازار |
| `config/economic_graph_seed.json` | بذر یال‌های هسته (دلار، مس، فملی، …) |
| `graphify-out/` | خروجی Graphify از کد |
| `scripts/babimind_memory.py` | حافظه ران LLM (dedupe، سقف حجم) |
| `memory/` | Decision History، outcome، پوزیشن، news |
| `reports/` | خروجی pipeline، graph، coverage |

### کلان و جهانی

| مسیر | نقش |
|------|-----|
| `docs/macro-layer-design.md` | طراحی لایه کلان |
| `config/babimind_iran_macro_priorities.json` | اولویت فاکتورهای ایران |
| `config/babimind_global_market_map.yml` | انتقال جهانی→بخش |
| `scripts/babimind_global_market.py` | snapshot جهانی |
| `config/dollar_expert_ensemble.yaml` | ensemble دلار |

### Workflows — `.github/workflows/`

- `babimind-unified-pipeline.yml` — هوش روزانه
- `babimind-global-macro.yml`
- `babimind-research.yml`
- `tse-market-options.yml`
- `tahlil-maintenance.yml`

### سایر

- `realtime_api.py` + `Dockerfile.realtime` / `docker-compose.realtime.yml`
- `tests/` — realtime و stream hub
- `chats/` — آرشیو تصمیم‌های معماری
- `config/babimind_factors.json` / factor registry / source health
- `docs/` — discovery، decision-engine، forecasting، trello، checklist

---

## 🎯 خروجی نهایی مدل

برای هر دارایی/بازار:

- وضعیت و رژیم · عوامل مؤثر · سناریوهای صعودی/خنثی/نزولی + احتمال
- محدوده‌های قیمت · ریسک · R/R · confidence · تغییر نسبت به ران قبل
- پیشنهاد: خرید / نگهداری / کاهش ریسک / فروش / **عدم اقدام**

---

## 📊 بازارهای تحت پوشش

**بورس ایران** — شاخص، صنعت، نماد، حجم، جریان، بنیادی، تکنیکال، Price Action، Rotation  
**اختیار** — زنجیره داخلی، intrinsic/time، Greeks/IV در صورت داده، پوزیشن ترکیبی  
**دلار و طلا** — آزاد/رسمی، اونس، سکه، ارتباط با سهام

---

## 🔌 اولویت منابع داده

1. API داخلی پروژه (BRS، realtime، …)  
2. داده مستقیم بازار  
3. رسمی (Codal، CBI، …)  
4. منابع معتبر عمومی  
5. وب به‌عنوان fallback  

**خرابی یک API کل ران را متوقف نمی‌کند** · `MISSING_IS_NOT_ZERO` · confidence پایین با داده ناقص.

---

## 🔄 چرخهٔ تحلیل

```text
Data Collection → Validation → Features
    → Market / Fundamental / Technical / Price Action
    → Options + Flow + Macro + International
    → News/Event + Game Theory + Decision + System Dynamics
    → Economic Graph score
    → Scenario & Forecast → Risk/Confidence
    → Final View → Backtest → Model Memory → Next Run
```

---

## ⏱️ اجرای خودکار

- هدف روزانه: **09:00** و **12:00** (تقویم محلی پروژه)
- Workflowها مستقل؛ شکست یک منبع زنجیره را کامل قطع نمی‌کند

### دستورهای پرکاربرد

```bash
pip install -r requirements.txt   # در صورت وجود؛ وگرنه requirements-*.txt
python scripts/babimind_pipeline.py
python scripts/load_economic_graph_seed.py
python scripts/babimind_memory.py --prepare
python scripts/rank_options_babimind.py
```

---

## 🧪 Backtest و حافظه تصمیم

- Decision History: `app/decision/history.py` → JSONL append-only  
- Outcome فقط خط جدید؛ پیش‌بینی قفل‌شده با `as_of`  
- معیارها: جهت، خطا، Brier در صورت تکمیل، MDD، پایداری رژیم  

---

## 🗂️ ساختار دانش

```
chats/          آرشیو چت معماری
memory/         decision history، news injection، dynamics پزشکیان
reports/        خروجی ران‌ها
artifacts/      snapshot و inject ماشینی
docs/           طراحی لایه‌ها
config/         factors، sources، seed گراف، priorities
```

---

## 🛠️ اصول توسعه

- اولویت با مدل مرکزی BabiMind  
- قابلیت جدید → اتصال به یک لایه  
- timestamp + منبع + confidence روی خروجی  
- ضد look-ahead  
- هیچ نتیجهٔ مهمی فقط در چت نماند  

---

## ⚠️ وضعیت

پروژه در حال توسعه است. برخی APIها و snapshotهای روزانه ممکن است partial باشند.  
**پیش‌بینی ≠ قطعیت.** خروجی را با کیفیت داده تفسیر کنید.

آخرین تزریق خبر مدل: `memory/news-injection-2026-09-09.md`  
Pre-open: `reports/preopen_2026-09-09.md`
