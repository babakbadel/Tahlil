# تریگر و جمع‌آوری روزانه اخبار اقتصادی

## اتومیشن دستی/Grok (ساعتی بازار)
| فیلد | مقدار |
|------|--------|
| نام | `tahlil-news-scan` |
| شناسه | `760c9d17-b96f-4a77-a462-988d1195402a` |
| زمان | ساعتی ۰۸:۰۰–۱۴:۰۰ Asia/Tehran |
| روزها | شنبه–چهارشنبه |

## جمع‌آوری خودکار ریپو (روزانه)

| جزء | مسیر |
|------|------|
| Collector عمومی | `scripts/babimind_daily_economic_news.py` |
| Collector پزشکیان | `scripts/babimind_pezeshkian_news.py` |
| کاتالوگ منابع | `config/babimind_news_sources.json` |
| خروجی JSON | `artifacts/babimind_daily_economic_news.json` |
| Digest مارک‌داون | `memory/news-daily-latest.md` |
| CI | `.github/workflows/babimind-unified-pipeline.yml` (قبل از LLM) |

### حوزه‌های query
بورس · جریان حقیقی · دلار/ارز · تورم/نقدینگی · نفت · پزشکیان · اختیار · هرمز/تحریم · طلا · بازیگران سیاست پولی

### اجرا دستی
```bash
python scripts/babimind_daily_economic_news.py
python scripts/babimind_pezeshkian_news.py
```

## دامنه محتوایی
- بازار سرمایه ایران
- کدال / افشای بااهمیت (در صورت پوشش RSS)
- سیاست اقتصادی، ارز، نرخ، بودجه
- شبکه افراد: پزشکیان، طیب‌نیا، عارف، آقاپور، قائم‌پناه، مدنی‌زاده، همتی

## خروجی
حداکثر چند ده تیتر تازه در digest؛ کل آرشیو JSON تا ~۲۵۰۰ آیتم (dedupe با hash).

سطر آخر digest: `NEWS_DIGEST | تاریخ | N new | total`

## سیاست مدل
خبر = **شواهد رویداد/روایت**، نه حقیقت اقتصادی و نه سیگنال قیمت ساختگی.
قبل از امتیازدهی: mapping به فاکتور + confidence + freshness + در صورت امکان cross-check Tier A.
