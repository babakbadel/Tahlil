# Decision Engine Bootstrap — 2026-08-25

## آنچه انجام شد
1. **Decision Engine** اسکلت کامل در `app/decision/`:
   - models (Person, RoleEvent, InfluenceEdge, Evidence, NetworkSnapshot, DecisionPrediction, DecisionRecord)
   - InfluenceNetwork با snapshot(as_of)
   - DecisionHistory (JSONL append-only، بدون overwrite پیش‌بینی)
   - DecisionEngine.predict

2. **شبکه افراد** در `people/pezeshkian_network.json`:
   - پزشکیان، طیب‌نیا، آقاپور، عارف، قائم‌پناه
   - نقش‌ها و یال‌های اولیه با confidence موقت
   - هنوز نیازمند source_url و تاریخ‌های دقیق‌تر برای هر ادعا

3. **Option Ranking** در `app/options/ranking.py`:
   - فیلتر سخت expiry > as_of
   - بررسی timestamp_mismatch و missing synchronized data
   - در صورت نبود quote همزمان، rank نهایی مسدود می‌شود (مطابق قانون FMLI run)

## قوانین تثبیت‌شده
- پیش‌بینی تاریخی immutable است.
- قرارداد منقضی‌شده از universe فعال حذف می‌شود.
- بدون داده همزمان underlying + option، «بهترین آپشن امروز» اعلام نمی‌شود.

## قدم بعدی پیشنهادی
1. تکمیل evidence و source برای نقش‌های شبکه.
2. یک DecisionRecord نمونه واقعی (مثلاً سیاست اقتصادی اخیر) ثبت شود.
3. اتصال Decision summary به پایپ‌لاین آپشن در runtime.
4. Phase 3 realtime: Redis Streams + historical recorder.
