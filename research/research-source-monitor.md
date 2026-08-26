# BabiMind Research & News Monitor

## دامنه پایش
این مانیتور باید در کنار داده بازار، Codal و شبکه افراد، شواهد اقتصاد و سیاست‌گذاری را جمع‌آوری کند.

### دسته‌های منبع
1. خبرگزاری‌ها و رسانه‌های اقتصادی معتبر ایران
2. اطلاعیه‌ها و بیانیه‌های رسمی دولت و بانک مرکزی
3. IMF / World Bank / BIS / OECD
4. دانشگاه‌ها و مراکز پژوهشی
5. ژورنال‌های علمی و مقالات peer-reviewed
6. Working Papers و Research Papers
7. پایان‌نامه‌ها و رساله‌های دانشگاهی
8. گزارش‌های سیاستی و Policy Brief
9. داده‌های رسمی و سری‌های زمانی
10. گزارش‌های بخش خصوصی، اتاق بازرگانی و صنایع

## موضوعات اجباری
- تورم و انتظارات تورمی
- ارز و رژیم ارزی
- نقدینگی و پایه پولی
- بودجه و کسری بودجه
- نفت و درآمدهای ارزی
- تحریم و تجارت خارجی
- رشد و رکود
- بانک‌ها و ناترازی بانکی
- مسکن
- بازار سرمایه
- طلا و کامودیتی‌ها
- اشتغال و دستمزد
- سیاست پولی و مالی
- ژئوپلیتیک با اثر اقتصادی

## رتبه‌بندی شواهد
`primary_official > peer_reviewed > working_paper > institutional_report > reputable_news > secondary_commentary`

## اصل ضدشایعه
خبر یا ادعا تا زمانی که evidence کافی نداشته باشد فقط به‌عنوان `unverified` ذخیره می‌شود و وارد سیگنال قطعی BabiMind نمی‌شود.

## فیلدهای ذخیره‌سازی
`title, source, url, author, publication_date, event_date, topic, entities, claim, evidence, evidence_level, confidence, novelty, macro_impact, market_impact, geopolitical_impact, as_of`

## اتصال به مدل
خروجی این لایه باید به `Macro Engine + Decision Engine + Game Theory + Price Action + Market Data + Backtest` تحویل داده شود.
