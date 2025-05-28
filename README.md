# 🚀Multi-Account Broadcast Bot

A Telegram bot that allows you to log in up to 10 personal Telegram accounts, store their sessions, and broadcast a message to all groups and DMs from each account — all triggered via a single /broadcast command.


---

# ⚙️ Features

🔐 Secure login via API ID + Hash + Phone + OTP

💾 Persistent session storage (up to 10 accounts per user)

📤 Broadcast to all DMs and groups from all logged-in accounts

⏳ Sends message with delay to avoid rate limits

✅ Reports broadcast completion time



---

# 🛠 Setup

1. Install dependencies

pip install -r requirements.txt


2. Set bot token

In bot.py:

BOT_TOKEN = "YOUR_BOT_TOKEN"


3. Run the bot

python bot.py




---

# 📌 How It Works

1. /start → Log in accounts (API ID → Hash → Phone → OTP)


2. Repeat up to 10 accounts


3. Send any message


4. Run /broadcast → Message is sent from all logged-in accounts


5. Get confirmation with total messages sent & time taken




---

# 📂 Project Structure

├── bot.py                # Telegram bot logic
├── telethon_manager.py   # Telethon login + broadcast handler
├── sessions/             # Stores session files per user
├── requirements.txt
└── README.md


---

# 🔒 Notes

2FA not supported

Session files saved locally

Telegram API rate limits apply