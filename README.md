# 🌲 Barkod Özet Telegram Botu

Excel dosyasından barkod aralığı özeti çıkaran Telegram botu.

---

## 📋 Kurulum Adımları

### 1. Bot Token Al (BotFather)

1. Telegram'da **@BotFather**'ı aç
2. `/newbot` yaz
3. Bot için bir isim gir (örn: `Akfırat Barkod Botu`)
4. Kullanıcı adı gir, sonu `bot` ile bitmeli (örn: `akfirat_barkod_bot`)
5. BotFather sana bir **token** verir → kopyala, kaydet

---

### 2. Railway'e Deploy Et (Ücretsiz)

**a)** [railway.app](https://railway.app) → GitHub ile giriş yap

**b)** "New Project" → "Deploy from GitHub repo"

**c)** Bu 4 dosyayı GitHub'a yükle:
- `bot.py`
- `requirements.txt`
- `Procfile`
- `README.md`

**d)** Railway'de projeyi oluşturduktan sonra:
- **Variables** sekmesine git
- `TELEGRAM_BOT_TOKEN` adında değişken ekle
- Değer: BotFather'dan aldığın token

**e)** Deploy otomatik başlar → Bot çalışmaya başlar ✅

---

### 3. Render'e Deploy Et (Alternatif, Ücretsiz)

1. [render.com](https://render.com) → GitHub ile giriş yap
2. "New" → "Background Worker"
3. GitHub reposunu seç
4. Build Command: `pip install -r requirements.txt`
5. Start Command: `python bot.py`
6. Environment Variables: `TELEGRAM_BOT_TOKEN` = token
7. "Create Background Worker" → Deploy başlar ✅

---

### 4. Lokal Test (İsteğe Bağlı)

```bash
pip install -r requirements.txt
export TELEGRAM_BOT_TOKEN="buraya_token_yaz"   # Mac/Linux
set TELEGRAM_BOT_TOKEN=buraya_token_yaz        # Windows
python bot.py
```

---

## 🤖 Bot Kullanımı

1. `/start` yaz
2. Excel dosyasını (.xls / .xlsx) gönder
3. Başlangıç barkodunu yaz (örn: `A00297343`)
4. Bitiş barkodunu yaz (örn: `A00297527`)
5. Çap özeti + indirilebilir XLSX dosyası gelir ✅

---

## 📁 Dosya Yapısı

```
barkod_bot/
├── bot.py           # Ana bot kodu
├── requirements.txt # Python kütüphaneleri
├── Procfile         # Railway/Heroku için
└── README.md        # Bu dosya
```

---

## ❓ Sorun Giderme

| Hata | Çözüm |
|------|-------|
| `TELEGRAM_BOT_TOKEN` hatası | Ortam değişkenini kontrol et |
| Dosya okunamadı | Excel sütun sırası doğru olmalı (en az 12 sütun) |
| Barkod bulunamadı | Barkod tam olarak yazılmalı (büyük/küçük harf dahil) |
