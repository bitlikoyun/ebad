import os
import io
import logging
import pandas as pd
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    ConversationHandler,
    CallbackQueryHandler,
    filters,
    ContextTypes,
)

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Konuşma adımları
DOSYA_BEKLE, BASLANGIC_BEKLE, BITIS_BEKLE = range(3)


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "👋 Merhaba! Ben *Barkod Özet Botuyum*.\n\n"
        "📋 Kullanım:\n"
        "1️⃣ Excel dosyanı (.xls / .xlsx) gönder\n"
        "2️⃣ Başlangıç barkodunu yaz\n"
        "3️⃣ Bitiş barkodunu yaz\n"
        "4️⃣ Özet tablosunu al ✅\n\n"
        "Başlamak için Excel dosyasını gönder.",
        parse_mode="Markdown"
    )
    return DOSYA_BEKLE


async def dosya_al(update: Update, context: ContextTypes.DEFAULT_TYPE):
    dosya = update.message.document
    if not dosya:
        await update.message.reply_text("❌ Lütfen bir Excel dosyası (.xls veya .xlsx) gönder.")
        return DOSYA_BEKLE

    dosya_adi = dosya.file_name.lower()
    if not (dosya_adi.endswith(".xls") or dosya_adi.endswith(".xlsx")):
        await update.message.reply_text("❌ Sadece .xls veya .xlsx dosyaları kabul edilir.")
        return DOSYA_BEKLE

    await update.message.reply_text("⏳ Dosya okunuyor...")

    try:
        tg_dosya = await dosya.get_file()
        dosya_bytes = await tg_dosya.download_as_bytearray()
        buffer = io.BytesIO(bytes(dosya_bytes))

        df = pd.read_excel(buffer, header=0)

        # Sütun indekslerine göre al (HTML'deki mantıkla aynı)
        cols = df.columns.tolist()
        if len(cols) < 12:
            await update.message.reply_text(
                f"❌ Dosyada yeterli sütun yok. Beklenen en az 12 sütun, bulunan: {len(cols)}"
            )
            return DOSYA_BEKLE

        veri = []
        for _, row in df.iterrows():
            veri.append({
                "agacId":        row.iloc[0],
                "agacAdi":       row.iloc[1],
                "odunId":        row.iloc[2],
                "odunAdi":       row.iloc[3],
                "kaliteSinifi":  row.iloc[4],
                "boySinifi":     row.iloc[5],
                "adet":          int(row.iloc[6]) if pd.notna(row.iloc[6]) else 0,
                "cap":           row.iloc[7],
                "boy":           row.iloc[8],
                "hacim":         float(row.iloc[9]) if pd.notna(row.iloc[9]) else 0.0,
                "uretimTarihi":  row.iloc[10],
                "barkodNo":      str(row.iloc[11]).strip() if pd.notna(row.iloc[11]) else "",
            })

        context.user_data["veri"] = veri
        context.user_data["dosya_adi"] = dosya.file_name

        toplam = len(veri)
        await update.message.reply_text(
            f"✅ Dosya okundu! *{toplam}* kayıt bulundu.\n\n"
            f"📌 Başlangıç barkodunu yaz (örn: A00297343):",
            parse_mode="Markdown"
        )
        return BASLANGIC_BEKLE

    except Exception as e:
        logger.error(f"Dosya okuma hatası: {e}")
        await update.message.reply_text(f"❌ Dosya okunamadı: {e}")
        return DOSYA_BEKLE


async def baslangic_al(update: Update, context: ContextTypes.DEFAULT_TYPE):
    baslangic = update.message.text.strip()
    veri = context.user_data.get("veri", [])
    barkodlar = [r["barkodNo"] for r in veri]

    if baslangic not in barkodlar:
        await update.message.reply_text(
            f"❌ *{baslangic}* barkodu dosyada bulunamadı.\n"
            "Lütfen geçerli bir başlangıç barkodu yaz:",
            parse_mode="Markdown"
        )
        return BASLANGIC_BEKLE

    context.user_data["baslangic"] = baslangic
    await update.message.reply_text(
        f"✅ Başlangıç: *{baslangic}*\n\n"
        f"📌 Bitiş barkodunu yaz (örn: A00297527):",
        parse_mode="Markdown"
    )
    return BITIS_BEKLE


async def bitis_al(update: Update, context: ContextTypes.DEFAULT_TYPE):
    bitis = update.message.text.strip()
    veri = context.user_data.get("veri", [])
    baslangic = context.user_data.get("baslangic", "")
    barkodlar = [r["barkodNo"] for r in veri]

    if bitis not in barkodlar:
        await update.message.reply_text(
            f"❌ *{bitis}* barkodu dosyada bulunamadı.\n"
            "Lütfen geçerli bir bitiş barkodu yaz:",
            parse_mode="Markdown"
        )
        return BITIS_BEKLE

    idx_bas = barkodlar.index(baslangic)
    idx_bit = barkodlar.index(bitis)

    # Sıra ters geldiyse düzelt
    if idx_bas > idx_bit:
        idx_bas, idx_bit = idx_bit, idx_bas

    secilen = veri[idx_bas: idx_bit + 1]

    # Çap özeti
    ozet = {}
    for r in secilen:
        cap = r["cap"]
        if cap not in ozet:
            ozet[cap] = {"adet": 0, "hacim": 0.0}
        ozet[cap]["adet"] += r["adet"]
        ozet[cap]["hacim"] += r["hacim"]

    # Çapa göre sırala
    try:
        sirali_capler = sorted(ozet.keys(), key=lambda x: float(x))
    except Exception:
        sirali_capler = sorted(ozet.keys())

    toplam_adet = sum(v["adet"] for v in ozet.values())
    toplam_hacim = round(sum(v["hacim"] for v in ozet.values()), 4)

    # Mesaj oluştur
    mesaj = (
        f"🌲 *AKFIRAT ORMAN İŞLETME ŞEFLİĞİ*\n"
        f"📊 *Çap Özeti*\n"
        f"🔖 `{baslangic}` → `{bitis}`\n"
        f"{'─'*30}\n"
        f"{'Çap':<8} {'Adet':>6} {'Hacim (m³)':>12}\n"
        f"{'─'*30}\n"
    )

    for cap in sirali_capler:
        adet = ozet[cap]["adet"]
        hacim = round(ozet[cap]["hacim"], 4)
        mesaj += f"`{str(cap):<8}` `{adet:>6}` `{hacim:>12.4f}`\n"

    mesaj += (
        f"{'─'*30}\n"
        f"`{'TOPLAM':<8}` `{toplam_adet:>6}` `{toplam_hacim:>12.4f}`\n"
    )

    # Excel çıktısı oluştur
    excel_buffer = io.BytesIO()
    satirlar = [["Çap", "Adet", "Toplam Hacim (m³)"]]
    for cap in sirali_capler:
        satirlar.append([cap, ozet[cap]["adet"], round(ozet[cap]["hacim"], 4)])
    satirlar.append(["TOPLAM", toplam_adet, toplam_hacim])

    df_ozet = pd.DataFrame(satirlar[1:], columns=satirlar[0])
    df_ozet.to_excel(excel_buffer, index=False)
    excel_buffer.seek(0)

    dosya_cikti_adi = f"ozet_{baslangic}_{bitis}.xlsx"

    # Yeni arama butonu
    klavye = InlineKeyboardMarkup([
        [InlineKeyboardButton("🔄 Yeni Arama (Aynı Dosya)", callback_data="yeni_aramaAyniDosya")],
        [InlineKeyboardButton("📂 Yeni Dosya Yükle", callback_data="yeni_dosya")],
    ])

    await update.message.reply_text(f"```\n{mesaj}\n```", parse_mode="Markdown")
    await update.message.reply_document(
        document=excel_buffer,
        filename=dosya_cikti_adi,
        caption="📥 XLSX olarak indir",
        reply_markup=klavye
    )

    return ConversationHandler.END


async def buton_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    if query.data == "yeni_aramaAyniDosya":
        if not context.user_data.get("veri"):
            await query.message.reply_text("❌ Dosya verisi bulunamadı. Lütfen yeni dosya yükle.")
            return DOSYA_BEKLE
        await query.message.reply_text(
            "✅ Aynı dosya kullanılıyor.\n\n📌 Başlangıç barkodunu yaz:"
        )
        return BASLANGIC_BEKLE

    elif query.data == "yeni_dosya":
        context.user_data.clear()
        await query.message.reply_text("📂 Yeni Excel dosyasını gönder:")
        return DOSYA_BEKLE


async def iptal(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data.clear()
    await update.message.reply_text("❌ İşlem iptal edildi. /start ile yeniden başlayabilirsin.")
    return ConversationHandler.END


async def hata_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    logger.error(f"Hata: {context.error}")


def main():
    token = os.environ.get("TELEGRAM_BOT_TOKEN")
    if not token:
        raise ValueError("TELEGRAM_BOT_TOKEN ortam değişkeni ayarlanmamış!")

    app = Application.builder().token(token).build()

    conv_handler = ConversationHandler(
        entry_points=[
            CommandHandler("start", start),
            MessageHandler(filters.Document.ALL, dosya_al),
        ],
        states={
            DOSYA_BEKLE: [
                MessageHandler(filters.Document.ALL, dosya_al),
                CallbackQueryHandler(buton_handler),
            ],
            BASLANGIC_BEKLE: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, baslangic_al),
                CallbackQueryHandler(buton_handler),
            ],
            BITIS_BEKLE: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, bitis_al),
                CallbackQueryHandler(buton_handler),
            ],
        },
        fallbacks=[CommandHandler("iptal", iptal)],
        allow_reentry=True,
    )

    app.add_handler(conv_handler)
    app.add_error_handler(hata_handler)

    print("✅ Bot başlatıldı...")
    app.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()
