import os
import json
import secrets
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

REQUIRED_CHANNEL = os.environ.get("REQUIRED_CHANNEL", "@your_channel")
ADMIN_ID = int(os.environ.get("ADMIN_ID", "0"))
BOT_USERNAME = os.environ.get("BOT_USERNAME", "your_bot")
STORAGE_FILE = "messages.json"
BLOCKED_FILE = "blocked.json"
CONFIG_FILE = "config.json"

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

def load_config():
    if os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, "r") as f:
            return json.load(f)
    return {"link_secret": secrets.token_urlsafe(8)}

def save_config(data):
    with open(CONFIG_FILE, "w") as f:
        json.dump(data, f)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    blocked = load_blocked()

    if user.id in blocked:
        return

    if user.id == ADMIN_ID:
        config = load_config()
        link = f"https://t.me/{BOT_USERNAME}?start={config['link_secret']}"
        await update.message.reply_text(
            f"🔗 لینک ناشناس تو:\n\n{link}\n\n"
            f"هرکی این لینک رو باز کنه می‌تونه ناشناس بهت پیام بده.\n\n"
            f"⚠️ فقط کسایی که این لینک رو دارن می‌تونن پیام بدن.\n\n"
            f"برای عوض کردن لینک: /newlink"
        )
        return

    if context.args and len(context.args) > 0:
        config = load_config()
        if context.args[0] == config['link_secret']:
            try:
                member = await context.bot.get_chat_member(REQUIRED_CHANNEL, user.id)
                if member.status not in ['member', 'administrator', 'creator']:
                    await update.message.reply_text(
                        f"اول عضو کانال شو:\n"
                        f"https://t.me/{REQUIRED_CHANNEL[1:]}\n\n"
                        f"بعدش دوباره روی لینک بزن."
                    )
                    return
            except:
                await update.message.reply_text("ربات رو ادمین کانال کن.")
                return

            storage = load_storage()
            authorized = storage.get("authorized_users", [])
            if user.id not in authorized:
                authorized.append(user.id)
                storage["authorized_users"] = authorized
                save_storage(storage)

            await update.message.reply_text("✓ می‌تونی ناشناس پیام بدی. سوالت رو بنویس:")
            context.user_data['verified'] = True
            return

    await update.message.reply_text("⛔️ لینک ناشناس نداری.")

async def newlink_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        return
    config = load_config()
    config['link_secret'] = secrets.token_urlsafe(8)
    save_config(config)

    storage = load_storage()
    storage["authorized_users"] = []
    save_storage(storage)

    link = f"https://t.me/{BOT_USERNAME}?start={config['link_secret']}"
    await update.message.reply_text(
        f"✓ لینک جدید:\n\n{link}\n\n"
        f"⚠️ لینک قبلی دیگه کار نمی‌کنه."
    )

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    msg = update.message.text

    blocked = load_blocked()
    if user.id in blocked:
        return

    if user.id == ADMIN_ID and context.user_data.get('waiting_reply'):
        target = context.user_data.get('reply_to_user')
        try:
            await context.bot.send_message(chat_id=target, text=f"💬 جواب:\n\n{msg}")
            await update.message.reply_text("✓ جواب رفت.")
        except:
            await update.message.reply_text("✗ طرف بلاک کرده.")
        context.user_data['waiting_reply'] = False
        return

    if not context.user_data.get('verified'):
        return

    storage = load_storage()
    msg_id = str(len([k for k in storage.keys() if k != "authorized_users"]) + 1)
    storage[msg_id] = {"user_id": user.id, "username": user.username or "ندارد", "text": msg}
    save_storage(storage)

    context.user_data['waiting_reply'] = True
    context.user_data['reply_to_user'] = user.id

    await context.bot.send_message(
        chat_id=ADMIN_ID,
        text=f"📩 پیام #{msg_id}\n\n{msg}"
    )
    await context.bot.send_message(
        chat_id=ADMIN_ID,
        text=(
            f"⚙️ عملیات روی #{msg_id}:\n\n"
            f"👤 دیدن آیدی: /who {msg_id}\n"
            f"🚫 بلاک کاربر: /block {user.id}"
        )
    )
    await update.message.reply_text("✓ فرستاده شد.")

async def who_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        return
    if not context.args:
        await update.message.reply_text("نحوه استفاده: /who 1")
        return
    storage = load_storage()
    data = storage.get(context.args[0])
    if not data:
        await update.message.reply_text("پیدا نشد.")
        return
    await update.message.reply_text(
        f"🔍 فرستنده #{context.args[0]}:\n\n"
        f"ID: {data['user_id']}\n"
        f"Username: @{data['username']}\n\n"
        f"بلاک: /block {data['user_id']}"
    )

async def block_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        return
    if not context.args:
        await update.message.reply_text("نحوه استفاده: /block 123456789")
        return
    try:
        user_id = int(context.args[0])
    except:
        await update.message.reply_text("آیدی نامعتبره.")
        return
    blocked = load_blocked()
    if user_id in blocked:
        await update.message.reply_text("از قبل بلاکه.")
        return
    blocked.append(user_id)
    save_blocked(blocked)
    await update.message.reply_text(f"✓ بلاک شد: {user_id}")

async def unblock_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        return
    if not context.args:
        await update.message.reply_text("نحوه استفاده: /unblock 123456789")
        return
    try:
        user_id = int(context.args[0])
    except:
        await update.message.reply_text("آیدی نامعتبره.")
        return
    blocked = load_blocked()
    if user_id not in blocked:
        await update.message.reply_text("بلاک نیست.")
        return
    blocked.remove(user_id)
    save_blocked(blocked)
    await update.message.reply_text(f"✓ آنبلاک شد: {user_id}")

def main():
    app = Application.builder().token(os.environ.get("BOT_TOKEN")).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("newlink", newlink_command))
    app.add_handler(CommandHandler("who", who_command))
    app.add_handler(CommandHandler("block", block_command))
    app.add_handler(CommandHandler("unblock", unblock_command))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    app.run_polling()

if __name__ == "__main__":
    main()
