# Decision Engine

## هدف
موتور تصمیم‌گیری زمان‌مند و شواهد‌محور برای اتصال شبکه افراد مؤثر، رویدادها و تحلیل بازار (بابی هوش).

## اصل ضد look-ahead
- هر پیش‌بینی با `as_of` ثبت می‌شود.
- فقط شواهد و نقش‌هایی که تا `as_of` قابل مشاهده بوده‌اند وارد ورودی می‌شوند.
- تاریخچه پیش‌بینی immutable است؛ نتیجه واقعی فقط به‌صورت رکورد الحاقی ثبت می‌شود.

## ساختار فایل‌ها
```
app/decision/
  models.py      # Person, RoleEvent, InfluenceEdge, Evidence, DecisionRecord, ...
  network.py     # InfluenceNetwork + snapshot(as_of)
  history.py     # DecisionHistory (JSONL append-only)
  engine.py      # DecisionEngine.predict(...)
  __init__.py
```

## داده شبکه افراد
`people/pezeshkian_network.json` — بارگذاری با `InfluenceNetwork.load_from_json(...)`.

فیلدهای نقش و رابطه باید در طول زمان با `source_url` و `source_published_at` تکمیل شوند.

## Decision History
مسیر پیش‌فرض: `data/decision_history.jsonl`

هر خط یک `DecisionRecord` است. به‌روزرسانی نتیجه با `record_outcome` یک خط جدید می‌سازد و خط اصلی را تغییر نمی‌دهد.

## اتصال به Option Ranking
لایه ۱۲–۱۴ پایپ‌لاین آپشن (`graph/option-ranking-pipeline.md`) باید از `DecisionEngine.network_summary(as_of)` و در صورت وجود، آخرین DecisionRecord مرتبط با رژیم فعلی استفاده کند.

## وضعیت پیاده‌سازی
- [x] Schema و مدل‌ها
- [x] Network snapshot با as_of
- [x] Decision History append-only
- [x] DecisionEngine اسکلت (سناریوهای صریح توسط caller)
- [ ] کالیبراسیون تاریخی و Brier score خودکار
- [ ] اتصال زنده به اخبار/Codal event stream
- [ ] امتیازدهی خودکار سناریو با game theory
