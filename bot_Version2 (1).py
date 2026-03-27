# بوت بث قانوني مع اشتراك/إلغاء اشتراك - python-telegram-bot v20+ (async)
import os
import sqlite3
import asyncio
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes

DB_PATH = "subscribers.db"
TOKEN = os.environ.get("TOKEN")  # 8589671547:AAHzs05mmv6NXyUg_-cmaFMeTCG4P7JocZY
 = int(os.environ.get("ADMIN_ID", "0"))  # @R_l_28
id 

# تحميل من مواقع التواصل الاجتماعي 
def init_db():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("""CREATE TABLE IF NOT EXISTS subscribers (
                    chat_id INTEGER PRIMARY KEY,
                    username TEXT,
                    joined_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )""")
    conn.commit()
    conn.close()

def add_subscriber(chat_id, username):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("INSERT OR IGNORE INTO subscribers(chat_id, username) VALUES(?, ?)", (chat_id, username))
    conn.commit()
    conn.close()

def remove_subscriber(chat_id):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("DELETE FROM subscribers WHERE chat_id = ?", (chat_id,))
    conn.commit()
    conn.close()

def list_subscribers():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT chat_id FROM subscribers")
    rows = c.fetchall()
    conn.close()
    return [r[0] for r in rows]

# الأوامر
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    add_subscriber(update.effective_chat.id, user.username if user else None)
    await update.message.reply_text("تم الاشتراك! ستتلقى الإشعارات من الآن. لإلغاء الاشتراك ارسل /stop")

async def stop(update: Update, context: ContextTypes.DEFAULT_TYPE):
    remove_subscriber(update.effective_chat.id)
    await update.message.reply_text("تم إلغاء الاشتراك. لن تتلقى المزيد من الإشعارات.")

async def stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        await update.message.reply_text("غير مسموح.")
        return
    subs = list_subscribers()
    await update.message.reply_text(f"عدد المشتركين: {len(subs)}")

# أمر البث (للإدارة فقط)
async def broadcast(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        await update.message.reply_text("غير مسموح.")
        return

    # الحصول على نص الرسالة: إما النص بعد الأمر أو الرسالة المقتبسة (reply)
    if context.args:
        text = " ".join(context.args)
    elif update.message.reply_to_message:
        # إرسال نص الرسالة المردودة
        replied = update.message.reply_to_message
        if replied.text or replied.caption:
            text = replied.text or replied.caption
        else:
            await update.message.reply_text("الرسالة المردودة لا تحتوي على نص.")
            return
    else:
        await update.message.reply_text("استخدم: /broadcast نص الرسالة  أو قم بالرد على رسالة ثم نفذ الأمر.")
        return

    subs = list_subscribers()
    await update.message.reply_text(f"بدء الإرسال إلى {len(subs)} مشترك(ين)...")

    sent = 0
    failed = 0
    for chat_id in subs:
        try:
            await context.bot.send_message(chat_id=chat_id, text=text)
            sent += 1
            await asyncio.sleep(0.12)  # تأخير بسيط لتقليل مخاطر تجاوز حدود المعدل
        except Exception as e:
            # هنا يمكن تسجيل الأخطاء أو حذف المشتركين الذين تم حظرهم
            failed += 1
            # مثال: إذا كانت Exception تشير إلى أنه تم حظر البوت من قبل المستخدم، يمكن حذف المشترك
            # (تحقق من نوع الخطأ قبل الحذف في تطبيق حقيقي)
    await update.message.reply_text(f"انتهى: تم الإرسال إلى {sent}، فشلت إلى {failed}.")

async def help_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("/start - الاشتراك\n/stop - إلغاء الاشتراك\n/stats - إحصاءات (للمشرف)\n/broadcast - بث رسالة (للمشرف)")

def main():
    init_db()
    app = ApplicationBuilder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("stop", stop))
    app.add_handler(CommandHandler("help", help_cmd))
    app.add_handler(CommandHandler("stats", stats))
    app.add_handler(CommandHandler("broadcast", broadcast))

    print("Bot is running...")
    app.run_polling()

if __name__ == "__main__":
    main()