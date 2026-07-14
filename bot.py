import os
import json
import secrets
import re
import logging
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

FIXED_LINK_CODE = "shahab"
ADMIN_ID = int(os.environ.get("ADMIN_ID", "0"))
BOT_USERNAME = os.environ.get("BOT_USERNAME", "your_bot")
BOT_TOKEN = os.environ.get("BOT_TOKEN", "")
STORAGE_FILE = "messages.json"
BLOCKED_FILE = "blocked.json"

logging.basicConfig(level=logging.INFO)

# ---------- ذخیره‌سازی ----------
def load_storage():
    if os.path.exists(STORAGE_FILE):
        with open(STORAGE_FILE, "r") as f:
            return json.load(f)
    return {}

def save_storage(data):
    with open(STORAGE_FILE, "w") as f:
        json.dump(data, f)

def load_blocked():
    if os.path.exists(BLOCKED_FILE):
        with open(BLOCKED_FILE, "r") as f:
            return json.load(f)
    return []

def save_blocked(data):
    with open(BLOCKED_FILE, "w") as f:
        json.dump(data, f)

# ---------- /start ----------
async def start(update, context):
    user = update.effective_user
    if user.id == ADMIN_ID:
        bot = await context.bot.get_me()
        link = f"https://t.me/{bot.username}?start={FIXED_LINK_CODE}"
        await update.message.reply_text(
            f"🔗 لینک ناشناس تو:\n\n{link}"
        )
    else:
        if context.args and context.args[0] == FIXED_LINK_CODE:
            context.user_data['verified'] = True
            await update.message.reply_text("✓ تایید شدی. پیامت رو بفرست.")
        else:
            await update.message.reply_text("لینک ناشناس نداری.")

# ---------- پیام‌ها ----------
async def handle_message(update, context):
    user = update.effective_user
    msg = update.message.text

    blocked = load_blocked()
    if user.id in blocked:
        return

    if user.id == ADMIN_ID and update.message.reply_to_message:
        target_text = update.message.reply_to_message.text or ""
        if "سیکتیر" in msg or "سکتیر" in msg:
            match = re.search(r'#(\d+)', target_text)
            if match:
                msg_id = match.group(1)
                storage = load_storage()
                target = storage.get(msg_id, {})
                target_id = target.get('user_id')
                if target_id:
                    blocked.append(target_id)
                    save_blocked(blocked)
                    try:
                        await context.bot.send_message(
                            chat_id=target_id,
                            text="بلاک شدی که عه"
                        )
                    except:
                        pass
                    await update.message.reply_text("✓ طرف بلاک شد.")
                    return
            await update.message.reply_text("نتونستم پیداش کنم.")
            return

    if not context.user_data.get('verified'):
        return

    storage = load_storage()
    msg_id = str(len(storage) + 1)
    storage[msg_id] = {
        "user_id": user.id,
        "username": user.username or "ندارد"
    }
    save_storage(storage)

    await context.bot.send_message(
        chat_id=ADMIN_ID,
        text=f"📩 پیام #{msg_id}\n\n{msg}"
    )
    await update.message.reply_text("✓ فرستاده شد.")

# ---------- ران ----------
def main():
    app = Application.builder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    app.run_polling()

if __name__ == "__main__":
    main()
