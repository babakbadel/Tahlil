# BabiMind — Hidden Factor Discovery

## هدف
این لایه هر ران، علاوه بر بررسی Factor Registry موجود، جست‌وجوی عوامل جدید و غیرتکراری را انجام می‌دهد. عامل جدید تا قبل از آزمون تاریخی و out-of-sample فقط «candidate» است و وارد سیگنال نهایی نمی‌شود.

## اصل ضد تکرار
هر candidate باید با عوامل موجود مقایسه شود. اگر اطلاعات جدیدی نسبت به عامل موجود اضافه نکند، رد می‌شود؛ حتی اگر همبستگی ظاهری بالایی داشته باشد.

## Pipeline

```text
Tahlil internal data / project APIs / official data / web fallback
        ↓
Validation + provenance + timestamps
        ↓
Feature Factory
        ↓
Candidate Factors
        ↓
Pearson/Spearman + lagged correlation
        ↓
Partial correlation / mutual information
        ↓
Multiple-testing correction
        ↓
Granger / predictive tests where assumptions permit
        ↓
Correlation clustering + redundancy penalty
        ↓
Regime stability
        ↓
Walk-forward / out-of-sample validation
        ↓
Factor Discovery Score
        ↓
Candidate / Watch / Promote / Reject
        ↓
Factor Registry + Model Memory
```

## کشف‌های اولویت‌دار

| عامل | رابطه‌ای که باید تست شود | نقش احتمالی |
|---|---|---|
| FX Allocation Waiting Time | lead روی PPI/CPI، واردات و فروش صنعتی | پیشرو |
| Trade Settlement Lag | lead روی landed cost و موجودی | پیشرو |
| Shipping Risk Premium | lead روی هزینه واردات و تورم وارداتی | پیشرو |
| Inventory Stress | رابطه با کمبود، PPI و تولید | پیشرو |
| Bank Credit Rationing | رابطه با سرمایه در گردش و تولید | پیشرو |
| Deposit Duration | رابطه با نقدینگی/سرعت گردش و دارایی‌ها | رژیمی |
| Policy Reversal Frequency | رابطه با uncertainty و سرمایه‌گذاری | رفتاری |
| Decision Latency | رابطه با اثربخشی سیاست و واکنش بازار | تصمیم |
| Credibility Gap | رابطه با انتظارات تورمی و ارز | تصمیم/انتظارات |
| Cash-to-Goods Speed | رابطه با velocity و تورم | پیشرو |
| Option IV Skew | رابطه با tail-risk و بازده underlying | بازار |
| OI Concentration | رابطه با رفتار expiry و pinning | آپشن |
| Commodity-FX Decoupling | رابطه با بازده صادرکنندگان و EPS | تعاملی |
| Receivables/DSO Stress | رابطه با کیفیت سود و رکود | بنیادی |

## آزمون آماری

- Pearson و Spearman برای رابطه هم‌زمان.
- Lagged correlation برای کشف تقدم زمانی.
- Partial correlation برای کنترل عوامل مشترک.
- Mutual Information برای روابط غیرخطی.
- Granger فقط وقتی طول سری، ایستایی و ساختار داده اجازه دهد؛ نتیجه آن «شواهد پیش‌بینی» است، نه اثبات علیت.
- Multiple testing با FDR کنترل شود تا کشف‌های کاذب زیاد نشوند.
- در صورت وجود ساختار چند رژیمی، آزمون جداگانه برای هر رژیم انجام شود.
- Walk-forward و out-of-sample اجباری است؛ split تصادفی برای سری زمانی مجاز نیست.

## Discovery Score

```text
FDS =
  0.25 Predictive
+ 0.20 Stability
+ 0.15 Lead
+ 0.15 CausalEvidence
+ 0.10 RegimeStability
+ 0.10 Novelty
+ 0.05 DataQuality
```

### Promotion gates

1. حداقل سه پنجره out-of-sample.
2. حداقل Discovery Score برابر 0.65.
3. منبع و timestamp معتبر.
4. عدم هم‌پوشانی اطلاعاتی با Factor Registry.
5. پایداری قابل‌قبول در رژیم‌های مختلف.
6. عدم استفاده از مقدار یا سیگنال ساختگی.

## خروجی هر ران

برای هر candidate این فیلدها ثبت شوند:

- `factor_id`
- `definition`
- `source_ids`
- `observed_at`
- `direction`
- `effect_size`
- `lead_lag`
- `p_value`
- `q_value`
- `predictive_score`
- `stability_score`
- `novelty_score`
- `regime_score`
- `discovery_score`
- `redundancy_cluster`
- `status`: `candidate | watch | promoted | rejected`
- `reason`
- `previous_run_delta`

هیچ candidate بدون عبور از promotion gates نباید به عامل مؤثر در تصمیم نهایی تبدیل شود.
