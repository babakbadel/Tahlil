# EconomicGraphStore Schema

## هدف
ذخیرهٔ زمان‌مند روابط علّی و انتقال اثر بین عوامل اقتصادی، دارایی‌ها، صنایع، ارز، کالا، سیاست و جریان پول — جدا از گراف کدبیس Graphify.

خروجی این لایه فقط **تعدیل‌کننده** امتیاز BabiMind است و به‌تنهایی تصمیم سرمایه‌گذاری نمی‌سازد.

## اصول
1. **Anti look-ahead:** هر query فقط از طریق `snapshot(as_of=...)`؛ دادهٔ بعد از `as_of` دیده نمی‌شود.
2. **Append-only:** خطوط JSONL بازنویسی نمی‌شوند؛ ادعای جدید = خط جدید.
3. **Missing ≠ zero:** نبود value یا state=unavailable سیگنال نزولی نیست.
4. **Double-counting control:** `independence_factor` + diminishing returns روی منبع تکراری.
5. **Provenance:** هر node/edge می‌تواند `evidence_ids` داشته باشد.

## ذخیره‌سازی
```
data/economic_graph/
  nodes.jsonl
  edges.jsonl
  evidence.jsonl
  snapshots/          # اختیاری، snapshot ماده‌سازی‌شده
```

## Node
| فیلد | نوع | توضیح |
|------|-----|--------|
| node_id | str | کلید پایدار (مثلاً `usd_free`, `femli`, `copper`) |
| type | enum | factor, asset, sector, macro, commodity, fx, option, news, policy, actor, flow, regime |
| name | str | برچسب انسانی |
| value | float? | مقدار عددی؛ برای گره‌های ساختاری می‌تواند خالی باشد |
| unit | str? | IRR, USD, percent, index_pts, ... |
| timestamp | str? | زمان مشاهدهٔ value |
| as_of | str? | مرز information set هنگام ثبت |
| source | str? | BRS_API, CBI, manual, ... |
| confidence | 0..1 | |
| freshness | 0..1 | با half-life قابل decay |
| state | enum | active, stale, unavailable, hypothesis |
| evidence_ids | list | |
| tags | list | |
| meta | object | آزاد |

## Edge
| فیلد | نوع | توضیح |
|------|-----|--------|
| edge_id | str | پایدار در طول نسخه‌ها (مثلاً `usd_free__causes__femli`) |
| source_id / target_id | str | ارجاع به node_id |
| relation | enum | causes, correlates_with, transmits_to, depends_on, reacts_to, influences, hedges, substitutes, leads, lags |
| direction | enum | positive, negative, mixed, neutral |
| weight | 0..1 | شدت |
| confidence | 0..1 | |
| lag_days | float? | تأخیر تقریبی انتقال اثر |
| independence_factor | 0..1 | برای جریمهٔ هم‌بستگی مشترک |
| valid_from / valid_to | str? | پنجرهٔ اعتبار |
| state | enum | active, stale, deprecated, hypothesis |
| evidence_ids / evidence_count | | |
| timestamp / as_of | str? | |
| tags / meta | | |

### وزن مؤثر
```
sign(direction) * weight * confidence * node_freshness * independence_factor
```

## Snapshot
نمای نقطه‌ای در `as_of`:
- برای هر `node_id` آخرین مشاهده با `as_of|timestamp <= as_of`
- برای هر `edge_id` آخرین claim معتبر در آن زمان
- فقط یال‌هایی که هر دو سر در مجموعهٔ node باشند

## Scoring (`score_target`)
1. یال‌های ورودی به `target_id`
2. حذف source با state=unavailable یا confidence≤0
3. یک‌بار شمردن هر جفت (source, target)
4. diminishing returns: `value * (0.70 ** source_repeat_count)`
5. نرمال‌سازی به بازهٔ تقریبی [-1, 1]
6. regime: bullish (≥0.20) / bearish (≤-0.20) / neutral / unavailable

```
babimind_score ≈ base_model_score + graph_adjustment − correlation_penalty
```

## نمونه یال‌های هسته (بازار ایران)
| source | relation | target | direction | توضیح |
|--------|----------|--------|-----------|--------|
| usd_free | causes | femli | positive | درآمد ریالی صادراتی |
| copper | transmits_to | femli | positive | قیمت جهانی مس |
| political_risk | influences | usd_free | positive | صرف ریسک |
| political_risk | influences | femli | negative | valuation / risk premium |
| real_inflow | reacts_to | market_index | positive | جریان حقیقی |

## اتصال به لایه‌های دیگر
- **Decision Engine:** actor/policy nodes می‌توانند به همین store لینک شوند.
- **babimind_graph.py:** می‌تواند از `EconomicGraphStore.score_target` هم بخواند.
- **Option ranking:** لایه‌های 11–14 از graph_score و regime استفاده می‌کنند.
- **Run memory:** fingerprint اسنپ‌شات در context تاریخی؛ هرگز به‌عنوان دادهٔ جاری.

## API حداقلی
```python
store = EconomicGraphStore("data/economic_graph")
store.add_evidence(ev)
store.upsert_node(node)
store.upsert_edge(edge)
snap = store.snapshot(as_of="2026-09-08T12:00:00+00:00")
score = store.score_target(as_of=..., target_id="femli", snapshot=snap)
```

## وضعیت پیاده‌سازی
- [x] Schema و مدل‌ها
- [x] Store JSONL + snapshot + score_target
- [ ] Seed loader از config/economic_graph_seed.json
- [ ] Decay خودکار freshness در pipeline روزانه
- [ ] اتصال رسمی به babimind_pipeline / option ranking
- [ ] کالیبراسیون وزن یال‌ها از Decision History outcomes
