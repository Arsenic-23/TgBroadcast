import os
import asyncio
from telethon import TelegramClient
from telethon.errors import SessionPasswordNeededError
from telethon.tl.types import User, Chat, Channel

SESSIONS_DIR = "sessions"
os.makedirs(SESSIONS_DIR, exist_ok=True)

MAX_ACCOUNTS = 10

user_accounts = {}  # {telegram_user_id: [session_names]}

def get_session_name(bot_user_id: int, account_index: int):
    return os.path.join(SESSIONS_DIR, f"{bot_user_id}_acc{account_index}")

async def login_account(bot_user_id: int, account_index: int, api_id: int, api_hash: str, phone: str, send_code, get_otp):
    session_name = get_session_name(bot_user_id, account_index)
    client = TelegramClient(session_name, api_id, api_hash)

    await client.connect()

    if not await client.is_user_authorized():
        await client.send_code_request(phone)
        await send_code()

        code = await get_otp()
        try:
            await client.sign_in(phone, code)
        except SessionPasswordNeededError:
            return False, "2FA password is enabled, which is not supported in this version."
    await client.disconnect()

    user_accounts.setdefault(bot_user_id, []).append(session_name)
    return True, f"✅ Account {account_index+1} logged in successfully."

async def broadcast_message(bot_user_id: int, message: str, delay: int = 5):
    session_names = user_accounts.get(bot_user_id, [])
    if not session_names:
        return False, "No accounts logged in."

    total_sent = 0
    for session_name in session_names:
        try:
            client = TelegramClient(session_name, 0, "")  # api_id and api_hash are embedded in session
            await client.start()
            async for dialog in client.iter_dialogs():
                entity = dialog.entity
                try:
                    if isinstance(entity, User):
                        if entity.bot or entity.deleted or entity.is_self:
                            continue
                    await client.send_message(entity.id, message)
                    total_sent += 1
                    await asyncio.sleep(delay)
                except Exception as e:
                    print(f"[!] Error sending to {entity.id}: {e}")
            await client.disconnect()
        except Exception as e:
            print(f"[!] Failed with session {session_name}: {e}")

    return True, f"✅ Broadcast complete. Total messages sent: {total_sent}"