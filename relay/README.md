# BabiMind TSETMC Relay

این سرویس باید روی یک ماشین با **IP ایران** اجرا شود. GitHub Actions مستقیماً به TSETMC تکیه نمی‌کند؛ فقط به این Relay وصل می‌شود.

## اجرا با Docker

```bash
git clone https://github.com/babakbadel/Tahlil.git
cd Tahlil/relay
docker build -t babimind-tsetmc-relay .
docker run -d --restart unless-stopped --name babimind-tsetmc-relay -p 8080:8080 babimind-tsetmc-relay
```

تست:

```bash
curl http://127.0.0.1:8080/health
curl http://127.0.0.1:8080/market/watch
curl http://127.0.0.1:8080/options/watch
```

## بدون Docker

```bash
python3 -m venv .venv
. .venv/bin/activate
pip install -r requirements.txt
uvicorn tsetmc_relay:app --host 0.0.0.0 --port 8080
```

## اتصال GitHub Actions

آدرس HTTPS سرویس را در GitHub Actions Secret با نام زیر قرار بده:

`TSETMC_RELAY_URL`

مثال مقدار:

`https://YOUR-RELAY-DOMAIN`

بعد از تنظیم Secret، workflow `TSE Market and Options Live` در هر اجرای زمان‌بندی‌شده ابتدا Relay را امتحان می‌کند و سایر providerها را به‌عنوان fallback نگه می‌دارد.

## نکته امنیتی

Relay را بدون HTTPS عمومی نکن. اگر reverse proxy داری، TLS و rate-limit فعال کن. این سرویس read-only است و هیچ API key مربوط به TSETMC ندارد.
