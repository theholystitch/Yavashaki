**Deploy to Railway**

Fork this repository to your GitHub account
On Railway, click New Project, then Deploy from GitHub
Select your forked repo
Railway auto-detects Procfile.txt and installs requirements.txt
Go to Variables tab and add:
BOT_TOKEN — token from BotFather
ADMIN_ID — your numeric user ID
The channel ID is hardcoded in bot.py (line ~14). To use a different channel, update CHANNEL_ID and CHANNEL_USERNAME.
Important: add your bot as an administrator to your channel, otherwise the membership check will fail with "Chat not found".
Railway will deploy automatically. Check the Logs tab to confirm the application started.
Configuration

**Edit the top of bot.py:**
FIXED_LINK_CODE = "YOUR FAVOURITE"              # referral code for /start
CHANNEL_USERNAME = "@TELEGRAMCHANNEL"       # shown to users in the join prompt
CHANNEL_ID = -STATIC ID              # numeric channel ID (required for getChatMember)

**Bot Flow
User side**

User opens https://t.me/<your_bot>?start=YOUR FAVOURITE
Bot checks membership in @TELEGRAMCHANNEL
Not a member — shows join button + "I joined" check button
Member — marks user as verified, allows messaging
User sends any text — message is forwarded anonymously to admin with action buttons
Admin side
When admin receives an anonymous message:
❤️ ناشناس جدید برات اومده:

<user's message>

[🔍 آیدی]  [🚫 بلاک]
🔍 آیدی — reveals sender's ID and username in a reply
🚫 بلاک — blocks the user, sends them an auto-reply, stores in blocked.json
**Admin commands:**
/start — opens admin panel
/unblock <user_id> — removes user from blocklist
Project Structure
Yavashaki/
├── bot.py              # main application
├── requirements.txt    # python-telegram-bot
├── Procfile.txt        # Railway worker definition
├── runtime.txt         # Python version pin
├── messages.json       # generated at runtime (msg_id -> sender info)
└── blocked.json        # generated at runtime (list of blocked user_ids)
Testing Notes
Tested on Railway free tier with the following constraints:
Ephemeral filesystem — JSON storage is fine for short-term data, but not durable across full redeploys. For long-term persistence, migrate to Redis or a managed DB.
Worker dyno sleeps after 10 minutes of inactivity on the free plan — paid tier keeps it always-on.
No HTTPS webhook endpoint is exposed; uses Telegram's long polling (run_polling) which works out of the box on Railway workers.
Security Considerations
The bot does not store message content — only sender metadata (user_id, username) is persisted in messages.json. The actual anonymous message is forwarded to the admin in real time and is not retained.
ADMIN_ID is a single hardcoded value. For multi-admin setups, refactor to a list.
FIXED_LINK_CODE prevents public users from triggering /start without the referral link, but is not a real authentication mechanism. Pair with a CAPTCHA flow for production-grade abuse prevention.
License
MIT
Author
Built by @theholystitch — feel free to fork, star, and adapt.
