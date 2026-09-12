# BabiMind — Daily Energy Shock & Refinery-vs-Metals Monitor

این لایه از BabiMind در هر ران روزانه بررسی می‌شود و برای تشخیص چرخش احتمالی بین پالایشی‌ها و فلزات طراحی شده است.

## فاکتورهای اجباری روزانه

### انرژی و پالایشی
- Brent و WTI
- Diesel Crack Spread
- Gasoline Crack Spread
- VLCC / tanker freight
- tanker insurance premium
- اختلال عرضه و حمل فیزیکی
- ریسک Hormuz
- ریسک Bab el-Mandeb
- سطح strategic oil buffer
- global refining utilization
- refinery outages
- product inventory tightness

### فلزات
- LME Copper price و trend
- momentum / distance from recent high
- China industrial demand
- iron ore در صورت relevance
- جریان پول داخلی نمادهای فلزی

## قانون تصمیم

قیمت نفت بالا به‌تنهایی سیگنال خرید پالایشی نیست. BabiMind باید حداقل سه دسته شواهد را جداگانه بررسی کند:

1. **Crude:** سطح و روند نفت
2. **Products:** crack spread و tightness فرآورده‌ها
3. **Physical/Logistics:** اختلال عرضه، حمل، بیمه و مسیرهای Hormuz/Bab el-Mandeb

سپس اثر آن با fundamentals/Codal، money flow، price action، options و valuation ترکیب می‌شود.

## Freight-adjusted refinery margin

افزایش کرایه حمل دوطرفه است و نباید به‌صورت مستقل bullish یا bearish تفسیر شود. مدل باید بررسی کند آیا premium فرآورده‌ها و حاشیه پالایش، افزایش freight و هزینه‌های لجستیک را جبران می‌کند یا نه.

## Refinery-vs-Metals Rotation

پرچم چرخش به سمت پالایشی‌ها تقویت می‌شود وقتی:

- نفت بالا باقی بماند؛
- crack spread فرآورده‌ها قوی باشد؛
- اختلال فیزیکی/حمل تأیید شود؛
- جریان پول داخلی پالایشی مثبت باشد؛
- هم‌زمان momentum مس ضعیف یا نزولی شود.

پرچم علیه این چرخش کاهش می‌یابد اگر مس سقف اخیر را reclaim و تثبیت کند و جریان پول فملی تأیید شود.

هیچ سیگنال واحدی اجازه تصمیم نهایی ندارد. داده ناقص = `SKIP`، نه صفر.

## خروجی روزانه

هر ران باید حداقل این موارد را ثبت کند:

- `energy_shock_state`
- `refinery_score`
- `metals_score`
- `refinery_vs_metals_rotation`
- `evidence_sources`
- `as_of`
- `confidence`
- `risk_flags`
