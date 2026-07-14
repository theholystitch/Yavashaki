import os
import json
import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, filters, ContextTypes

FIXED_LINK_CODE = "shahab"
ADMIN_ID = int(os.environ.get("ADMIN_ID", "0"))
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
        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("📎 کپی لینک", callback_data="copy_link")],
            [InlineKeyboardButton("🚫 لیست بلاک‌شده‌ها", callback_data="list_blocked")],
            [InlineKeyboardButton("♻️ ریست پیام‌ها", callback_data="reset_msgs")]
        ])
        await update.message.reply_text(
            "👋 *سلام ادمین عزیز*\n\n"
            "به پنل مدیریت خوش اومدی ✨\n"
            "از دکمه‌های زیر استفاده کن:",
            reply_markup=keyboard,
            parse_mode="Markdown"
        )
    else:
        if context.args and context.args[0] == FIXED_LINK_CODE:
            context.user_data['verified'] = True
            await update.message.reply_text(
                "✅ *تایید شدی!*\n\n"
                "از این لحظه می‌تونی پیام ناشناس بفرستی 📨\n"
                "پیامت رو همینجا بنویس.",
                parse_mode="Markdown"
            )
        else:
            await update.message.reply_text(
                "🚫 *دسترسی نداری*\n\n"
                "برای استفاده از ربات به لینک ناشناس نیاز داری.",
                parse_mode="Markdown"
            )

# ---------- دکمه‌های ادمین ----------
async def admin_buttons(update, context):
    query = update.callback_query
    await query.answer()
    if query.from_user.id != ADMIN_ID:
        return

    if query.data == "copy_link":
        bot = await context.bot.get_me()
        link = f"https://t.me/{bot.username}?start={FIXED_LINK_CODE}"
        await query.message.edit_text(
            f"🔗 *لینک ناشناس تو:*\n\n"
            f"`{link}`\n\n"
            f"📋 روی لینک بزن تا کپی شه.",
            parse_mode="Markdown"
        )

    elif query.data == "list_blocked":
        blocked = load_blocked()
        if not blocked:
            text = "✨ *لیست بلاک‌شده‌ها خالیه*\n\nکسی بلاک نیست."
        else:
            text = "🚫 *لیست بلاک‌شده‌ها:*\n\n"
            for i, uid in enumerate(blocked, 1):
                text += f"`{i}.` `{uid}`\n"
            text += f"\n🔓 برای رفع بلاک: `/unblock آیدی`"
        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("↩️ برگشت", callback_data="back_admin")]
        ])
        await query.message.edit_text(text, reply_markup=keyboard, parse_mode="Markdown")

    elif query.data == "reset_msgs":
        save_storage({})
        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("↩️ برگشت", callback_data="back_admin")]
        ])
        await query.message.edit_text(
            "♻️ *پیام‌ها ریست شد*",
            reply_markup=keyboard,
            parse_mode="Markdown"
        )

    elif query.data == "back_admin":
        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("📎 کپی لینک", callback_data="copy_link")],
            [InlineKeyboardButton("🚫 لیست بلاک‌شده‌ها", callback_data="list_blocked")],
            [InlineKeyboardButton("♻️ ریست پیام‌ها", callback_data="reset_msgs")]
        ])
        await query.message.edit_text(
            "👋 *سلام ادمین عزیز*\n\n"
            "به پنل مدیریت خوش اومدی ✨\n"
            "از دکمه‌های زیر استفاده کن:",
            reply_markup=keyboard,
            parse_mode="Markdown"
        )

# ---------- دکمه زیر پیام ناشناس ----------
async def msg_buttons(update, context):
    query = update.callback_query
    await query.answer()
    if query.from_user.id != ADMIN_ID:
        return

    msg_id = query.data.split(":")[1]
    storage = load_storage()
    target = storage.get(msg_id, {})

    if query.data.startswith("id:"):
        if target:
            await query.message.reply_text(
                f"🔍 *اطلاعات فرستنده:*\n\n"
                f"👤 آیدی: `{target.get('user_id')}`\n"
                f"📛 یوزرنیم: @{target.get('username', 'ندارد')}\n\n"
                f"🔓 رفع بلاک: `/unblock {target.get('user_id')}`",
                parse_mode="Markdown"
            )

    elif query.data.startswith("block:"):
        if target:
            user_id = target.get('user_id')
            blocked = load_blocked()
            if user_id not in blocked:
                blocked.append(user_id)
                save_blocked(blocked)
                try:
                    await context.bot.send_message(
                        chat_id=user_id,
                        text="🚫 *بلاک شدی!*\n\nدیگه نمی‌تونی پیام بفرستی.",
                        parse_mode="Markdown"
                    )
                except:
                    pass
                await query.message.reply_text(f"✓ طرف بلاک شد: `{user_id}`", parse_mode="Markdown")
            else:
                await query.message.reply_text("⚠️ از قبل بلاک بود.")

# ---------- پیام‌ها ----------
async def handle_message(update, context):
    user = update.effective_user
    msg = update.message.text

    blocked = load_blocked()
    if user.id in blocked:
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

    keyboard = InlineKeyboardMarkup([
        [
            InlineKeyboardButton("🔍 آیدی", callback_data=f"id:{msg_id}"),
            InlineKeyboardButton("🚫 بلاک", callback_data=f"block:{msg_id}")
        ]
    ])

    await context.bot.send_message(
        chat_id=ADMIN_ID,
        text="❤️ *ناشناس جدید اومده*",
        reply_markup=keyboard,
        parse_mode="Markdown"
    )
    await update.message.reply_text(
        "✅ *فرستاده شد!*\n\n"
        "پیامت به دست ادمین رسید ✨",
        parse_mode="Markdown"
    )

# ---------- رفع بلاک ----------
async def unblock_command(update, context):
    if update.effective_user.id != ADMIN_ID:
        return
    if not context.args:
        await update.message.reply_text(
            "📝 *نحوه استفاده:*\n\n`/unblock 123456789`",
            parse_mode="Markdown"
        )
        return
    try:
        user_id = int(context.args[0])
    except:
        await update.message.reply_text("❌ آیدی نامعتبره.")
        return
    blocked = load_blocked()
    if user_id not in blocked:
        await update.message.reply_text("⚠️ این کاربر بلاک نیست.")
        return
    blocked.remove(user_id)
    save_blocked(blocked)
    await update.message.reply_text(f"✅ کاربر `{user_id}` آنبلاک شد ✨", parse_mode="Markdown")

# ---------- ران ----------
def main():
    app = Application.builder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("unblock", unblock_command))
    app.add_handler(CallbackQueryHandler(admin_buttons, pattern="^(copy_link|list_blocked|reset_msgs|back_admin)$"))
    app.add_handler(CallbackQueryHandler(msg_buttons, pattern="^(id|block):"))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    app.run_polling()

if __name__ == "__main__":
    main()
