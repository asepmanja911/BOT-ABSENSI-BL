import os
import random
import pytz
from datetime import datetime, time
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes

TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
if not TOKEN:
    raise ValueError("No TELEGRAM_BOT_TOKEN found in environment variables")

# Zona waktu Medan (WIB)
timezone = pytz.timezone("Asia/Jakarta")

# Store user attendance data
user_data = {}

def get_time():
    return datetime.now(timezone).strftime("%H:%M:%S")

def get_now():
    return datetime.now(timezone)

def time_to_seconds(t):
    return t.hour * 3600 + t.minute * 60 + t.second

# Work schedule
NORMAL_START = time(10, 0, 0)
EARLY_START = time(9, 30, 0)
NORMAL_END = time(22, 0, 0)
LATE_END = time(23, 0, 0)

start_messages = [
    "Semangat ya, {name}! Jangan lupa ngopi biar makin produktif! ☕🔥",
    "Jangan lupa senyum ya, {name}, biar kerja nggak terasa berat! 😊",
    "Yuk, kita mulai hari ini dengan penuh semangat! {name}, you got this! 💪",
    "Hayoo kerja yang rajin ya, {name}, acek ngeliatin tuh! 👀😂"
]

off_messages = [
    "Good job hari ini, {name}! Jangan lupa istirahat yang cukup ya! 🌙✨",
    "Akhirnya bisa rebahan juga ya, {name}? Nikmati malamnya! 🛌",
    "Kerja kerasmu luar biasa, {name}! Sekarang saatnya rileks! 🍵",
    "Udah pulang kerja nih, {name}! Besok lanjut lagi ya! 💼💪"
]

async def start_work(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user = update.message.from_user
    full_name = user.full_name
    time_now = get_now()
    user_id = user.id

    if user_id in user_data and "masuk" in user_data[user_id]:
        await update.message.reply_text("⚠️ Kamu sudah absen masuk kerja! Tekan /pulangkerja dulu sebelum absen lagi.")
        return

    user_data[user_id] = {"masuk": time_now}
    message = random.choice(start_messages).format(name=full_name)

    # Check lateness
    if time_now.replace(microsecond=0).time() > NORMAL_START:
        late_seconds = time_to_seconds(time_now.time()) - time_to_seconds(NORMAL_START)
        late_hours, remainder = divmod(late_seconds, 3600)
        late_minutes, late_seconds = divmod(remainder, 60)
        message += f"\n⏳ Kamu telat *{late_hours} jam {late_minutes} menit {late_seconds} detik*! Jangan diulang ya! 😆"
    elif time_now.replace(microsecond=0).time() < EARLY_START:
        message += "\n🔥 Kamu masuk lebih awal! Segera depo biar makin lancar ya! 💰💪"

    await update.message.reply_text(f"✅ {full_name} telah masuk kerja! 💼\n{message}\n🕒 Waktu Masuk: *{get_time()}*")

async def off_work(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user = update.message.from_user
    full_name = user.full_name
    time_now = get_now()
    user_id = user.id

    if user_id not in user_data or "masuk" not in user_data[user_id]:
        await update.message.reply_text("⚠️ Kamu belum absen masuk kerja!")
        return

    masuk_time = user_data[user_id]["masuk"]
    work_duration = time_now - masuk_time
    work_hours, remainder = divmod(work_duration.total_seconds(), 3600)
    work_minutes, work_seconds = divmod(remainder, 60)
    work_duration_str = f"{int(work_hours)} jam {int(work_minutes)} menit {int(work_seconds)} detik"
    message = random.choice(off_messages).format(name=full_name)

    if time_now.replace(microsecond=0).time() >= LATE_END:
        message += "\n🔥 Kerja keras banget hari ini! Jangan lupa depo biar makin semangat besok! 💰"

    await update.message.reply_text(
        f"👋 {full_name} telah pulang kerja! 🏡\n{message}\n🕒 Waktu Pulang: *{get_time()}*\n⏳ Total Kerja: *{work_duration_str}*"
    )
    del user_data[user_id]

async def break_activity(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user = update.message.from_user
    full_name = user.full_name
    time_now = get_now()  # Gunakan get_now untuk mengambil waktu sekarang di zona Medan
    user_id = user.id
    command = update.message.text.lower()  # Ambil perintah yang dikirim oleh user (harus kecil semua)

    if user_id not in user_data:
        await update.message.reply_text("⚠️ Kamu belum absen masuk kerja! Gunakan /masukkerja dulu.")
        return

    if "break" in user_data[user_id]:
        await update.message.reply_text("⚠️ Kamu sedang istirahat! Tekan /back dulu sebelum istirahat lagi!")
        return

    activities = {
        "/smoke": ["🚬 Lagi merokok! Jangan kelamaan ya, {name}! 🔥😆", "{name} ngudud dulu. Jangan kelamaan biar kerjaan ga numpuk! 🍂"],
        "/toilet": ["🚽 Ke toilet dulu ya! Jangan main HP lama-lama, {name}! 🤣", "{name} ke toilet. Mudah-mudahan bukan baca komik lama-lama ya! 📖🤣"],
        "/pipis": ["💦 {name} pipis dulu! Jangan kelamaan ya! 🚽", "Hayo {name} jangan main air! 💦😆"],
        "/bab": ["💩 {name} BAB dulu! Take your time ya! 🚽", "{name} lagi BAB nih. Semoga lancar ya! 💩😅"]
    }

    if command not in activities:
        return

    message = random.choice(activities[command]).format(name=full_name)
    user_data[user_id]["break"] = time_now  # Menandai bahwa user sedang istirahat
    work_duration = time_now - user_data[user_id]["masuk"]
    work_hours, remainder = divmod(work_duration.total_seconds(), 3600)
    work_minutes, work_seconds = divmod(remainder, 60)
    work_duration_str = f"{int(work_hours)} jam {int(work_minutes)} menit {int(work_seconds)} detik"

    await update.message.reply_text(
        f"{message}\n🕒 Waktu: *{get_time()}*\n⏳ Total Kerja: *{work_duration_str}*"
    )

async def back_from_break(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user = update.message.from_user
    full_name = user.full_name
    time_now = get_now()
    user_id = user.id

    if user_id not in user_data or "break" not in user_data[user_id]:
        await update.message.reply_text("⚠️ Kamu belum istirahat!")
        return

    break_time = user_data[user_id]["break"]
    duration = time_now - break_time
    duration_hours, remainder = divmod(duration.total_seconds(), 3600)
    duration_minutes, duration_seconds = divmod(remainder, 60)
    duration_str = f"{int(duration_hours)} jam {int(duration_minutes)} menit {int(duration_seconds)} detik"

    await update.message.reply_text(
        f"✅ {full_name} kembali dari istirahat!\n⏳ Total Istirahat: *{duration_str}*\nSekarang lanjut kerja lagi ya! 💪"
    )
    user_data[user_id].pop("break", None)

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    full_name = update.message.from_user.full_name
    commands = f"""
🤖 *Halloo "{full_name}"*
Gunakan perintah berikut untuk absensi:
/start - Tampilkan Menu Utama
/masuk_kerja - Masuk kerja
/pulang_kerja - Pulang kerja
/smoke - Merokok
/pipis - Buang air kecil
/bab - Buang air besar
/back - Kembali dari istirahat
"""
    await update.message.reply_text(commands, parse_mode='Markdown')

async def error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    print(f"Error occurred: {context.error}")

def main():
    print("Bot Sedang Dimulai...")
    application = Application.builder().token(TOKEN).build()

    # Add handlers
    application.add_handler(CommandHandler("start", start_command))
    application.add_handler(CommandHandler("masuk_kerja", start_work))
    application.add_handler(CommandHandler("masukkerja", start_work))
    application.add_handler(CommandHandler("pulang_kerja", off_work))
    application.add_handler(CommandHandler("pulangkerja", off_work))
    application.add_handler(CommandHandler("smoke", break_activity))
    application.add_handler(CommandHandler("pipis", break_activity))
    application.add_handler(CommandHandler("bab", break_activity))
    application.add_handler(CommandHandler("back", back_from_break))

    # Add error handler
    application.add_error_handler(error_handler)

    try:
        print("Bot Sedang Berjalan...")
        application.run_polling(allowed_updates=Update.ALL_TYPES)
    except Exception as e:
        print(f"Kesalahan Kritis: {e}")
        application.stop()

if __name__ == "__main__":
    main()