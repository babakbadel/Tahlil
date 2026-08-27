# BabiMind Graph Intelligence

## هدف
لایه Graph Intelligence روابط علّی، هم‌بستگی و مسیر انتقال اثر بین عوامل، دارایی‌ها، صنایع، اخبار و تصمیمات را مدل می‌کند و خروجی آن وارد امتیاز نهایی BabiMind می‌شود.

## Node
هر Node شامل این فیلدهاست:
- `id`
- `type`: factor | asset | sector | news | policy | actor | macro | commodity | option
- `name`
- `value`
- `timestamp`
- `source`
- `confidence`
- `freshness`

## Edge
هر Edge شامل:
- `source`
- `target`
- `direction`: positive | negative | mixed
- `weight`: 0..1
- `confidence`: 0..1
- `lag`: زمان تقریبی انتقال اثر
- `evidence_count`
- `timestamp`

## انواع رابطه
1. `causes` — اثر علّی
2. `correlates_with` — هم‌بستگی
3. `transmits_to` — انتقال اثر از یک بازار به بازار دیگر
4. `depends_on` — وابستگی بنیادی
5. `reacts_to` — واکنش بازار/دارایی
6. `influences` — اثر سیاست‌گذار/بازیگر

## Double Counting Penalty
سیگنال‌های هم‌ریشه نباید چندبار شمرده شوند. اگر چند عامل به یک شوک مشترک وابسته باشند، وزن مؤثر آن‌ها با ضریب هم‌بستگی کاهش می‌یابد.

`effective_weight = raw_weight * confidence * freshness * independence_factor`

`independence_factor` بین 0 و 1 است و برای عوامل بسیار هم‌بسته کاهش می‌یابد.

## Graph Score
برای هر دارایی:

`graph_score = normalized(sum(incoming_edge_effects))`

سپس:

`babimind_score = base_model_score + graph_adjustment - correlation_penalty`

Graph نباید به‌تنهایی تصمیم سرمایه‌گذاری ایجاد کند؛ فقط باید تصمیم لایه‌های دیگر را با شواهد شبکه‌ای تعدیل کند.

## Timestamp Rule
هر Node و Edge باید timestamp داشته باشد. داده جدید جایگزین تاریخچه نمی‌شود. برای تحلیل امروز فقط داده‌های معتبر تا timestamp اجرای مدل مجازند.

## Date Integrity
`analysis_date` باید از زمان واقعی اجرای pipeline تعیین شود. تاریخ‌های قدیمی فقط در backtest/historical context مجازند و نباید به‌عنوان وضعیت جاری بازار نمایش داده شوند.

## نمونه مسیر فملی
`دلار -> درآمد ریالی -> سود فملی`

`تقاضای جهانی مس -> قیمت مس -> درآمد/حاشیه سود فملی`

`ریسک سیاسی -> دلار/نرخ تنزیل -> valuation فملی`

مسیرها باید با confidence و lag ثبت شوند تا مدل بتواند اثر مستقیم و غیرمستقیم را جدا کند.
