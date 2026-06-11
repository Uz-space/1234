import asyncio
import logging
from aiogram import Bot, Dispatcher, F
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.filters import CommandStart, Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.storage.memory import MemoryStorage

logging.basicConfig(level=logging.INFO)

BOT_TOKEN = "YOUR_BOT_TOKEN_HERE"

# ─── Til tarjimalari ─────────────────────────────────────────────────────────
TEXTS = {
    "en": {
        "main_title": "RIPPERBOT",
        "api_connected": "✅",
        "api_disconnected": "❌",
        "live_log": "📡 LIVE LOG",
        "no_claims": "⏳ No claims yet...",
        "crane_active_indicator": "✅",
        "crane_inactive_indicator": "⚠️",
        "add_account": "➕ Add Account",
        "back": "◀️ Back",
        "control_panel": "Control Panel",
        "claims": "claims",
        "balance": "💰 Balance",
        "subscription": "💳 Subscription",
        "invite_friend": "🎁 Invite Friend",
        "settings": "⚙️ Settings",
        "refresh": "🔄",
        "active_accounts": "ACTIVE ACCOUNTS",
        "no_accounts": "No active accounts — + to add",
        "settings_title": "⚙️ Settings",
        "api_key_label": "🔑 API Key",
        "api_host_label": "🌐 API Host",
        "api_key_not_set": "❌ Not set",
        "api_key_set": "✅",
        "settings_note": "Each user has their own API key.",
        "language": "🌐 Language",
        "select_language": "🌐 Select your language:",
        "language_changed": "✅ Language changed!",
        "subscription_title": "💳 Subscription",
        "no_active_sub": "❌ No active subscription",
        "accounts_count": "📊 Accounts: 0",
        "claims_count": "📊 Claims: 0",
        "available_plans": "✅ Available plans:",
        "monthly": "📆 Monthly – $15/month",
        "monthly_desc": "├ 50 accounts (any site)\n└ Unlimited claims",
        "claim_pack": "🎫 Claim Pack – $1/1200 claims",
        "claim_pack_desc": "├ Unlimited accounts\n└ 1200 claims per pack",
        "pay_with_crypto": "💎 Pay with Crypto",
        "select_crypto": "💎 Select Cryptocurrency\n\nChoose your preferred coin:",
        "bnb": "🟡 BNB (BEP-20)",
        "sol": "🟠 SOL",
        "ltc": "⚪ LTC",
        "ton": "💎 TON",
        "trx": "🔴 TRX (TRC-20)",
        "doge": "🐕 DOGE",
        "wallet_address": "📍 Wallet Address:",
        "amounts": "💰 Amounts:",
        "monthly_amount": "• Monthly — $15",
        "pack_amount": "• Claim Pack — $1",
        "send_exact": "⚠️ Send exactly the amount",
        "submit_txid": "📝 After payment, tap Submit TXID",
        "submit_txid_button": "📝 Submit TXID",
        "submit_txid_prompt": "📝 Send your TXID in chat...",
        "cancel": "❌ Cancel",
        "skip_cookies": "⏭️ Skip Cookies",
        "skip_ua": "⏭️ Skip UA",
        "add_account_title": "Add Account — {crane}",
        "label": "🏷️ Label: {label}",
        "send_email": "📧 Send the account email:",
        "cancel_abort": "/cancel to abort.",
        "email_received": "📧 Email: <code>{email}</code>",
        "send_password": "🔑 Now send the password:",
        "password_ok": "🔑 Password: ✅",
        "cookies_optional": "🍪 Cookies (optional — send cookies or tap Skip):",
        "cookies_instruction": "F12 > Console > <code>document.cookie</code>",
        "cookies_skipped": "🍪 Cookies: ⏭️ Skipped",
        "ua_optional": "🌐 User-Agent (optional — send UA or tap Skip):",
        "ua_instruction": "F12 > Console > <code>navigator.userAgent</code>",
        "cookies_received": "🍪 Cookies: ✅ ({len} chars)",
        "account_added": "✅ <b>Account added!</b>",
        "account_num": "{crane} #{num}",
        "cookies_status": "🍪 {status}",
        "ua_status": "🌐 UA: {status}",
        "main_menu": "🏠 Main Menu",
        "cancelled": "❌ Cancelled.",
        "updated": "♻️ Updated!",
        "not_found": "Not found!",
        "api_key_prompt": "🔑 <b>XEvil API Key</b>\n\nSend your API key:\n\n/cancel to abort.",
        "api_host_prompt": "🌐 <b>API Host</b>\n\nSend the API host (e.g. <code>sctg.xyz</code>):\n\n/cancel to abort.",
        "referral_title": "🎁🎁 <b>Referral System</b>",
        "your_link": "🔗 <b>Your referral link:</b>",
        "share_text": "📢 <b>Share this link with your friends!</b>\n├ You get: <b>+16 claims</b>\n└ Your friend gets: <b>+8 claims</b>",
        "friends_joined": "👥 <b>Friends joined:</b> 0",
        "bonus_earned": "📊 <b>Bonus claims earned:</b> 0",
        "share_button": "📨 Share with Friend",
    },
    "uz": {
        "main_title": "RIPPERBOT",
        "api_connected": "✅",
        "api_disconnected": "❌",
        "live_log": "📡 JONLI LOG",
        "no_claims": "⏳ Hali hech qanday claim yo‘q...",
        "crane_active_indicator": "✅",
        "crane_inactive_indicator": "⚠️",
        "add_account": "➕ Hisob qo‘shish",
        "back": "◀️ Orqaga",
        "control_panel": "Boshqaruv paneli",
        "claims": "claim",
        "balance": "💰 Balans",
        "subscription": "💳 Obuna",
        "invite_friend": "🎁 Do‘st taklif qilish",
        "settings": "⚙️ Sozlamalar",
        "refresh": "🔄",
        "active_accounts": "FAOL HISOBLAR",
        "no_accounts": "Faol hisoblar yo‘q — + qo‘shish",
        "settings_title": "⚙️ Sozlamalar",
        "api_key_label": "🔑 API kalit",
        "api_host_label": "🌐 API host",
        "api_key_not_set": "❌ O‘rnatilmagan",
        "api_key_set": "✅",
        "settings_note": "Har bir foydalanuvchi o‘z API kalitiga ega.",
        "language": "🌐 Til",
        "select_language": "🌐 Tilni tanlang:",
        "language_changed": "✅ Til o‘zgartirildi!",
        "subscription_title": "💳 Obuna",
        "no_active_sub": "❌ Faol obuna yo‘q",
        "accounts_count": "📊 Hisoblar: 0",
        "claims_count": "📊 Claimlar: 0",
        "available_plans": "✅ Mavjud rejalar:",
        "monthly": "📆 Oylik – $15/oy",
        "monthly_desc": "├ 50 ta hisob (istalgan sayt)\n└ Cheksiz claim",
        "claim_pack": "🎫 Claim paketi – $1/1200 claim",
        "claim_pack_desc": "├ Cheksiz hisob\n└ 1200 claim",
        "pay_with_crypto": "💎 Kripto bilan to‘lash",
        "select_crypto": "💎 Kriptovalyutani tanlang\n\nO‘zingizga qulay tangani belgilang:",
        "bnb": "🟡 BNB (BEP-20)",
        "sol": "🟠 SOL",
        "ltc": "⚪ LTC",
        "ton": "💎 TON",
        "trx": "🔴 TRX (TRC-20)",
        "doge": "🐕 DOGE",
        "wallet_address": "📍 Hamyon manzili:",
        "amounts": "💰 Miqdorlar:",
        "monthly_amount": "• Oylik — $15",
        "pack_amount": "• Claim paketi — $1",
        "send_exact": "⚠️ Aynan shu miqdorni yuboring",
        "submit_txid": "📝 To‘lovdan so‘ng TXID yuboring",
        "submit_txid_button": "📝 TXID yuborish",
        "submit_txid_prompt": "📝 TXID ni chatga yozing...",
        "cancel": "❌ Bekor qilish",
        "skip_cookies": "⏭️ Cookies o‘tkazib yuborish",
        "skip_ua": "⏭️ UA o‘tkazib yuborish",
        "add_account_title": "Hisob qo‘shish — {crane}",
        "label": "🏷️ Label: {label}",
        "send_email": "📧 Hisob emailini yuboring:",
        "cancel_abort": "/cancel bekor qilish.",
        "email_received": "📧 Email: <code>{email}</code>",
        "send_password": "🔑 Endi parolni yuboring:",
        "password_ok": "🔑 Parol: ✅",
        "cookies_optional": "🍪 Cookies (ixtiyoriy — cookies yuboring yoki Skip bosing):",
        "cookies_instruction": "F12 > Konsol > <code>document.cookie</code>",
        "cookies_skipped": "🍪 Cookies: ⏭️ O‘tkazib yuborildi",
        "ua_optional": "🌐 User-Agent (ixtiyoriy — UA yuboring yoki Skip bosing):",
        "ua_instruction": "F12 > Konsol > <code>navigator.userAgent</code>",
        "cookies_received": "🍪 Cookies: ✅ ({len} belgi)",
        "account_added": "✅ <b>Hisob qo‘shildi!</b>",
        "account_num": "{crane} #{num}",
        "cookies_status": "🍪 {status}",
        "ua_status": "🌐 UA: {status}",
        "main_menu": "🏠 Bosh menyu",
        "cancelled": "❌ Bekor qilindi.",
        "updated": "♻️ Yangilandi!",
        "not_found": "Topilmadi!",
        "api_key_prompt": "🔑 <b>XEvil API kaliti</b>\n\nAPI kalitingizni yuboring:\n\n/cancel bekor qilish.",
        "api_host_prompt": "🌐 <b>API host</b>\n\nAPI hostni yuboring (masalan <code>sctg.xyz</code>):\n\n/cancel bekor qilish.",
        "referral_title": "🎁🎁 <b>Referal tizimi</b>",
        "your_link": "🔗 <b>Sizning referal linkingiz:</b>",
        "share_text": "📢 <b>Do‘stlaringizga ulashing!</b>\n├ Siz: <b>+16 claim</b>\n├ Do‘stingiz: <b>+8 claim</b>",
        "friends_joined": "👥 <b>Qo‘shilgan do‘stlar:</b> 0",
        "bonus_earned": "📊 <b>Bonus claimlar:</b> 0",
        "share_button": "📨 Do‘stga ulashish",
    },
    "ru": {
        "main_title": "RIPPERBOT",
        "api_connected": "✅",
        "api_disconnected": "❌",
        "live_log": "📡 ЖИВОЙ ЛОГ",
        "no_claims": "⏳ Пока нет клеймов...",
        "crane_active_indicator": "✅",
        "crane_inactive_indicator": "⚠️",
        "add_account": "➕ Добавить аккаунт",
        "back": "◀️ Назад",
        "control_panel": "Панель управления",
        "claims": "клеймы",
        "balance": "💰 Баланс",
        "subscription": "💳 Подписка",
        "invite_friend": "🎁 Пригласить друга",
        "settings": "⚙️ Настройки",
        "refresh": "🔄",
        "active_accounts": "АКТИВНЫЕ АККАУНТЫ",
        "no_accounts": "Нет активных аккаунтов — + добавить",
        "settings_title": "⚙️ Настройки",
        "api_key_label": "🔑 API ключ",
        "api_host_label": "🌐 API хост",
        "api_key_not_set": "❌ Не установлен",
        "api_key_set": "✅",
        "settings_note": "У каждого пользователя свой API ключ.",
        "language": "🌐 Язык",
        "select_language": "🌐 Выберите язык:",
        "language_changed": "✅ Язык изменён!",
        "subscription_title": "💳 Подписка",
        "no_active_sub": "❌ Нет активной подписки",
        "accounts_count": "📊 Аккаунтов: 0",
        "claims_count": "📊 Клеймов: 0",
        "available_plans": "✅ Доступные планы:",
        "monthly": "📆 Месячный – $15/мес",
        "monthly_desc": "├ 50 аккаунтов (любой сайт)\n└ Безлимитные клеймы",
        "claim_pack": "🎫 Пакет клеймов – $1/1200 клеймов",
        "claim_pack_desc": "├ Безлимит аккаунтов\n└ 1200 клеймов",
        "pay_with_crypto": "💎 Оплатить криптой",
        "select_crypto": "💎 Выберите криптовалюту\n\nПредпочитаемая монета:",
        "bnb": "🟡 BNB (BEP-20)",
        "sol": "🟠 SOL",
        "ltc": "⚪ LTC",
        "ton": "💎 TON",
        "trx": "🔴 TRX (TRC-20)",
        "doge": "🐕 DOGE",
        "wallet_address": "📍 Адрес кошелька:",
        "amounts": "💰 Суммы:",
        "monthly_amount": "• Месячный — $15",
        "pack_amount": "• Пакет клеймов — $1",
        "send_exact": "⚠️ Отправьте точную сумму",
        "submit_txid": "📝 После оплаты нажмите Submit TXID",
        "submit_txid_button": "📝 Отправить TXID",
        "submit_txid_prompt": "📝 Напишите TXID в чат...",
        "cancel": "❌ Отмена",
        "skip_cookies": "⏭️ Пропустить Cookies",
        "skip_ua": "⏭️ Пропустить UA",
        "add_account_title": "Добавить аккаунт — {crane}",
        "label": "🏷️ Метка: {label}",
        "send_email": "📧 Отправьте email аккаунта:",
        "cancel_abort": "/cancel для отмены.",
        "email_received": "📧 Email: <code>{email}</code>",
        "send_password": "🔑 Теперь отправьте пароль:",
        "password_ok": "🔑 Пароль: ✅",
        "cookies_optional": "🍪 Cookies (опционально — отправьте cookies или нажмите Skip):",
        "cookies_instruction": "F12 > Консоль > <code>document.cookie</code>",
        "cookies_skipped": "🍪 Cookies: ⏭️ Пропущено",
        "ua_optional": "🌐 User-Agent (опционально — отправьте UA или нажмите Skip):",
        "ua_instruction": "F12 > Консоль > <code>navigator.userAgent</code>",
        "cookies_received": "🍪 Cookies: ✅ ({len} симв.)",
        "account_added": "✅ <b>Аккаунт добавлен!</b>",
        "account_num": "{crane} #{num}",
        "cookies_status": "🍪 {status}",
        "ua_status": "🌐 UA: {status}",
        "main_menu": "🏠 Главное меню",
        "cancelled": "❌ Отменено.",
        "updated": "♻️ Обновлено!",
        "not_found": "Не найдено!",
        "api_key_prompt": "🔑 <b>XEvil API ключ</b>\n\nОтправьте ваш API ключ:\n\n/cancel для отмены.",
        "api_host_prompt": "🌐 <b>API хост</b>\n\nОтправьте API хост (например <code>sctg.xyz</code>):\n\n/cancel для отмены.",
        "referral_title": "🎁🎁 <b>Реферальная система</b>",
        "your_link": "🔗 <b>Ваша реферальная ссылка:</b>",
        "share_text": "📢 <b>Поделитесь ссылкой с друзьями!</b>\n├ Вы получаете: <b>+16 клеймов</b>\n└ Друг получает: <b>+8 клеймов</b>",
        "friends_joined": "👥 <b>Присоединилось друзей:</b> 0",
        "bonus_earned": "📊 <b>Заработано бонусов:</b> 0",
        "share_button": "📨 Поделиться с другом",
    }
}

def get_text(user_id: int, key: str, **kwargs) -> str:
    lang = USER_SETTINGS.get(user_id, {}).get("language", "en")
    text = TEXTS.get(lang, TEXTS["en"]).get(key, key)
    if kwargs:
        return text.format(**kwargs)
    return text

# ─── Kran konfiguratsiyasi ───────────────────────────────────────────────────
CRANES = [
    {"name": "TronPick", "emoji": "🔴",  "active": False, "multiplier": None, "claims": 0, "max_claims": "∞", "balance": 0, "accounts": []},
    {"name": "LitePick", "emoji": "🌕",  "active": False, "multiplier": None, "claims": 0, "max_claims": "∞", "balance": 0, "accounts": []},
    {"name": "DogePick", "emoji": "🐕",  "active": False, "multiplier": None, "claims": 0, "max_claims": "∞", "balance": 0, "accounts": []},
    {"name": "PolPick",  "emoji": "🪙",  "active": False, "multiplier": None, "claims": 0, "max_claims": "∞", "balance": 0, "accounts": []},
    {"name": "BnbPick",  "emoji": "🟡",  "active": False, "multiplier": None, "claims": 0, "max_claims": "∞", "balance": 0, "accounts": []},
    {"name": "SolPick",  "emoji": "☀️",  "active": False, "multiplier": None, "claims": 0, "max_claims": "∞", "balance": 0, "accounts": []},
    {"name": "SuiPick",  "emoji": "💧",  "active": False, "multiplier": None, "claims": 0, "max_claims": "∞", "balance": 0, "accounts": []},
    {"name": "UsdPick",  "emoji": "💵",  "active": False, "multiplier": None, "claims": 0, "max_claims": "∞", "balance": 0, "accounts": []},
    {"name": "TonPick",  "emoji": "💎",  "active": False, "multiplier": None, "claims": 0, "max_claims": "∞", "balance": 0, "accounts": []},
    {"name": "BchPick",  "emoji": "🟤",  "active": False, "multiplier": None, "claims": 0, "max_claims": "∞", "balance": 0, "accounts": []},
]

API_STATE = {
    "connected": False,
    "domain": "sctg.xyz",
    "plan": "Trial",
    "accounts": 0,
    "total_claims": 0,
}

LIVE_LOG = {
    "crane_emoji": "",
    "crane_name": "",
    "log_text": "",
}

# { user_id: { "api_key": ..., "api_host": ..., "language": "en" } }
USER_SETTINGS = {}

BOT_USERNAME = ""


# ─── FSM States ──────────────────────────────────────────────────────────────
class AddAccount(StatesGroup):
    email    = State()
    password = State()
    cookies  = State()
    ua       = State()


class SettingsState(StatesGroup):
    api_key  = State()
    api_host = State()


# ─── Helpers ─────────────────────────────────────────────────────────────────
def get_crane(name: str):
    return next((c for c in CRANES if c["name"] == name), None)


def cancel_keyboard(user_id: int):
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=get_text(user_id, "cancel"), callback_data="cancel_add")]
    ])


def skip_cookies_keyboard(user_id: int):
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=get_text(user_id, "cancel"), callback_data="cancel_add")],
        [InlineKeyboardButton(text=get_text(user_id, "skip_cookies"), callback_data="skip_cookies")],
    ])


def skip_ua_keyboard(user_id: int):
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=get_text(user_id, "cancel"), callback_data="cancel_add")],
        [InlineKeyboardButton(text=get_text(user_id, "skip_ua"), callback_data="skip_ua")],
    ])


# ─── Main menu ───────────────────────────────────────────────────────────────
def build_message_text(user_id: int) -> str:
    lines = []
    for c in CRANES:
        name_upper = c["name"].upper()
        if c["active"]:
            mult = f" | 🟢 {c['multiplier']}" if c["multiplier"] else ""
            active_mark = get_text(user_id, "crane_active_indicator")
            line = f"{c['emoji']} {name_upper} {active_mark} [∞]{mult} ({c['claims']}/{c['max_claims']})"
        else:
            inactive_mark = get_text(user_id, "crane_inactive_indicator")
            line = f"{c['emoji']} {name_upper} {inactive_mark} [∞] | ▫️ (0/{c['max_claims']})"
        lines.append(line)

    text = "\n".join(lines)
    text += "\n\n"

    api_icon = get_text(user_id, "api_connected") if API_STATE["connected"] else get_text(user_id, "api_disconnected")
    text += f"🔑 API: {api_icon} ({API_STATE['domain']})\n"

    if API_STATE["connected"] and API_STATE["accounts"] != 0:
        acc_str    = "∞" if API_STATE["accounts"] == -1 else str(API_STATE["accounts"])
        claims_str = str(API_STATE["total_claims"]) if API_STATE["total_claims"] > 0 else "0"
        text += f"📓 {API_STATE['plan']} | {acc_str} accounts | {claims_str} claims\n"

    text += f"\n{get_text(user_id, 'live_log')}\n"
    text += "────────────────\n"

    if LIVE_LOG["log_text"]:
        text += f"{LIVE_LOG['crane_emoji']} {LIVE_LOG['crane_name'].upper()}\n"
        text += LIVE_LOG["log_text"]
    else:
        text += get_text(user_id, "no_claims")

    return text


def build_keyboard(user_id: int) -> InlineKeyboardMarkup:
    buttons = []
    row = []
    for c in CRANES:
        icon = get_text(user_id, "crane_active_indicator") if c["active"] else get_text(user_id, "crane_inactive_indicator")
        btn = InlineKeyboardButton(
            text=f"{icon} {c['name']}",
            callback_data=f"crane_{c['name']}"
        )
        row.append(btn)
        if len(row) == 2:
            buttons.append(row)
            row = []
    if row:
        buttons.append(row)

    buttons.append([InlineKeyboardButton(text=get_text(user_id, "balance"), callback_data="balance")])
    buttons.append([InlineKeyboardButton(text=get_text(user_id, "subscription"), callback_data="subscription")])
    buttons.append([InlineKeyboardButton(text=get_text(user_id, "invite_friend"), callback_data="invite")])
    buttons.append([
        InlineKeyboardButton(text=get_text(user_id, "settings"), callback_data="settings"),
        InlineKeyboardButton(text=get_text(user_id, "refresh"), callback_data="refresh"),
    ])
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def build_crane_keyboard(crane_name: str, user_id: int) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=get_text(user_id, "add_account"), callback_data=f"add_account_{crane_name}")],
        [InlineKeyboardButton(text=get_text(user_id, "back"), callback_data="back_main")],
    ])


def crane_panel_text(crane: dict, user_id: int) -> str:
    accounts     = crane.get("accounts", [])
    acc_count    = len(accounts)
    active_count = sum(1 for a in accounts if a.get("active", False))

    text = (
        f"{crane['emoji']} <b>{crane['name']} — {get_text(user_id, 'control_panel')}</b>\n"
        f"📊 {crane['claims']} {get_text(user_id, 'claims')} | 💰 {crane['balance']}\n"
        f"▶️ <b>{get_text(user_id, 'active_accounts')} ({active_count}/{acc_count}):</b>\n"
    )
    if accounts:
        for acc in accounts:
            status = "🟢" if acc.get("active") else "🔴"
            text += f"  {status} {acc['label']} — {acc['email']}\n"
    else:
        text += f"<i>{get_text(user_id, 'no_accounts')}</i>"
    return text


# ─── Settings ────────────────────────────────────────────────────────────────
def build_settings_text(user_id: int) -> str:
    s        = USER_SETTINGS.get(user_id, {})
    api_key  = s.get("api_key", "")
    api_host = s.get("api_host", "sctg.xyz")

    if api_key:
        key_display = f"{get_text(user_id, 'api_key_set')} {api_key[:8]}..."
    else:
        key_display = get_text(user_id, "api_key_not_set")

    return (
        f"{get_text(user_id, 'settings_title')}\n\n"
        f"{get_text(user_id, 'api_key_label')}: {key_display}\n"
        f"{get_text(user_id, 'api_host_label')}: <a href='http://{api_host}'>{api_host}</a>\n\n"
        f"<i>{get_text(user_id, 'settings_note')}</i>"
    )


def build_settings_keyboard(user_id: int) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=get_text(user_id, "api_key_label"), callback_data="set_api_key")],
        [InlineKeyboardButton(text=get_text(user_id, "api_host_label"), callback_data="set_api_host")],
        [InlineKeyboardButton(text=get_text(user_id, "language"), callback_data="set_language")],
        [InlineKeyboardButton(text=get_text(user_id, "back"), callback_data="back_main")],
    ])


# ─── Bot va Dispatcher ───────────────────────────────────────────────────────
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher(storage=MemoryStorage())


# ─── /start ──────────────────────────────────────────────────────────────────
@dp.message(CommandStart())
async def cmd_start(message: Message, state: FSMContext):
    await state.clear()
    user_id = message.from_user.id
    if user_id not in USER_SETTINGS:
        USER_SETTINGS[user_id] = {"language": "en"}
    await message.answer(
        text=build_message_text(user_id),
        reply_markup=build_keyboard(user_id),
        parse_mode="HTML"
    )


# ─── /cancel ─────────────────────────────────────────────────────────────────
@dp.message(Command("cancel"))
async def cmd_cancel(message: Message, state: FSMContext):
    user_id = message.from_user.id
    data = await state.get_data()
    crane_name = data.get("crane_name", "")
    await state.clear()
    if crane_name:
        crane = get_crane(crane_name)
        if crane:
            await message.answer(
                text=crane_panel_text(crane, user_id),
                reply_markup=build_crane_keyboard(crane_name, user_id),
                parse_mode="HTML"
            )
            return
    await message.answer(
        text=build_message_text(user_id),
        reply_markup=build_keyboard(user_id),
        parse_mode="HTML"
    )


# ─── Refresh ─────────────────────────────────────────────────────────────────
@dp.callback_query(F.data == "refresh")
async def cb_refresh(call: CallbackQuery, state: FSMContext):
    user_id = call.from_user.id
    await state.clear()
    await call.message.delete()
    await call.message.answer(
        text=build_message_text(user_id),
        reply_markup=build_keyboard(user_id),
        parse_mode="HTML"
    )
    await call.answer(get_text(user_id, "updated"))


# ─── Back to main ────────────────────────────────────────────────────────────
@dp.callback_query(F.data == "back_main")
async def cb_back_main(call: CallbackQuery, state: FSMContext):
    user_id = call.from_user.id
    await state.clear()
    await call.message.delete()
    await call.message.answer(
        text=build_message_text(user_id),
        reply_markup=build_keyboard(user_id),
        parse_mode="HTML"
    )
    await call.answer()


# ─── Crane panel ─────────────────────────────────────────────────────────────
@dp.callback_query(F.data.startswith("crane_"))
async def cb_crane(call: CallbackQuery):
    user_id = call.from_user.id
    crane_name = call.data.replace("crane_", "")
    crane = get_crane(crane_name)
    if not crane:
        await call.answer(get_text(user_id, "not_found"), show_alert=True)
        return
    await call.message.delete()
    await call.message.answer(
        text=crane_panel_text(crane, user_id),
        reply_markup=build_crane_keyboard(crane_name, user_id),
        parse_mode="HTML"
    )
    await call.answer()


# ─── Add Account Step 1: Email ───────────────────────────────────────────────
@dp.callback_query(F.data.startswith("add_account_"))
async def cb_add_account(call: CallbackQuery, state: FSMContext):
    user_id = call.from_user.id
    crane_name = call.data.replace("add_account_", "")
    crane = get_crane(crane_name)
    if not crane:
        await call.answer(get_text(user_id, "not_found"), show_alert=True)
        return

    acc_num = len(crane["accounts"]) + 1
    label = f"Account {acc_num}"

    await state.set_state(AddAccount.email)
    await state.update_data(crane_name=crane_name, label=label)

    await call.message.delete()
    await call.message.answer(
        text=(
            f"{crane['emoji']} <b>{get_text(user_id, 'add_account_title', crane=crane_name)}</b>\n\n"
            f"{get_text(user_id, 'label', label=label)}\n\n"
            f"{get_text(user_id, 'send_email')}\n\n"
            f"{get_text(user_id, 'cancel_abort')}"
        ),
        reply_markup=cancel_keyboard(user_id),
        parse_mode="HTML"
    )
    await call.answer()


# ─── Step 2: Password ────────────────────────────────────────────────────────
@dp.message(AddAccount.email)
async def fsm_email(message: Message, state: FSMContext):
    user_id = message.from_user.id
    email = message.text.strip()
    await state.update_data(email=email)
    await state.set_state(AddAccount.password)
    await message.answer(
        text=(
            f"{get_text(user_id, 'email_received', email=email)}\n\n"
            f"{get_text(user_id, 'send_password')}\n\n"
            f"{get_text(user_id, 'cancel_abort')}"
        ),
        reply_markup=cancel_keyboard(user_id),
        parse_mode="HTML"
    )


# ─── Step 3: Cookies ─────────────────────────────────────────────────────────
@dp.message(AddAccount.password)
async def fsm_password(message: Message, state: FSMContext):
    user_id = message.from_user.id
    password = message.text.strip()
    await state.update_data(password=password)
    await state.set_state(AddAccount.cookies)
    await message.answer(
        text=(
            f"{get_text(user_id, 'password_ok')}\n\n"
            f"{get_text(user_id, 'cookies_optional')}\n\n"
            f"{get_text(user_id, 'cookies_instruction')}\n\n"
            f"{get_text(user_id, 'cancel_abort')}"
        ),
        reply_markup=skip_cookies_keyboard(user_id),
        parse_mode="HTML"
    )


# ─── Skip Cookies ────────────────────────────────────────────────────────────
@dp.callback_query(F.data == "skip_cookies")
async def cb_skip_cookies(call: CallbackQuery, state: FSMContext):
    user_id = call.from_user.id
    await state.update_data(cookies=None)
    await state.set_state(AddAccount.ua)
    await call.message.edit_text(
        text=(
            f"{get_text(user_id, 'cookies_skipped')}\n\n"
            f"{get_text(user_id, 'ua_optional')}\n\n"
            f"{get_text(user_id, 'ua_instruction')}\n\n"
            f"{get_text(user_id, 'cancel_abort')}"
        ),
        reply_markup=skip_ua_keyboard(user_id),
        parse_mode="HTML"
    )
    await call.answer()


# ─── Cookies kiritildi ───────────────────────────────────────────────────────
@dp.message(AddAccount.cookies)
async def fsm_cookies(message: Message, state: FSMContext):
    user_id = message.from_user.id
    cookies = message.text.strip()
    await state.update_data(cookies=cookies)
    await state.set_state(AddAccount.ua)
    await message.answer(
        text=(
            f"{get_text(user_id, 'cookies_received', len=len(cookies))}\n\n"
            f"{get_text(user_id, 'ua_optional')}\n\n"
            f"{get_text(user_id, 'ua_instruction')}\n\n"
            f"{get_text(user_id, 'cancel_abort')}"
        ),
        reply_markup=skip_ua_keyboard(user_id),
        parse_mode="HTML"
    )


# ─── Skip UA ─────────────────────────────────────────────────────────────────
@dp.callback_query(F.data == "skip_ua")
async def cb_skip_ua(call: CallbackQuery, state: FSMContext):
    await state.update_data(ua=None)
    await _finish_add_account(call.message, state)
    await call.answer()


# ─── UA kiritildi ────────────────────────────────────────────────────────────
@dp.message(AddAccount.ua)
async def fsm_ua(message: Message, state: FSMContext):
    await state.update_data(ua=message.text.strip())
    await _finish_add_account(message, state)


# ─── Finish ──────────────────────────────────────────────────────────────────
async def _finish_add_account(message: Message, state: FSMContext):
    user_id = message.from_user.id
    data = await state.get_data()
    crane_name = data["crane_name"]
    label = data["label"]
    email = data["email"]
    password = data["password"]
    cookies = data.get("cookies")
    ua = data.get("ua")

    crane = get_crane(crane_name)
    if crane is None:
        await state.clear()
        return

    crane["accounts"].append({
        "label": label,
        "email": email,
        "password": password,
        "cookies": cookies,
        "ua": ua,
        "active": True,
    })
    crane["active"] = True

    await state.clear()
    await message.answer(
        text=(
            f"{get_text(user_id, 'account_added')}\n\n"
            f"{crane['emoji']} {get_text(user_id, 'account_num', crane=crane_name, num=len(crane['accounts']))}\n"
            f"📝 {label}\n"
            f"📧 <code>{email}</code>\n"
            f"🔑 ✅\n"
            f"{get_text(user_id, 'cookies_status', status='✅' if cookies else '⏭️')}\n"
            f"{get_text(user_id, 'ua_status', status='✅' if ua else '⏭️')}"
        ),
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text=f"◀️ {crane_name}", callback_data=f"crane_{crane_name}")],
            [InlineKeyboardButton(text=get_text(user_id, "main_menu"), callback_data="back_main")],
        ]),
        parse_mode="HTML"
    )


# ─── Cancel add ──────────────────────────────────────────────────────────────
@dp.callback_query(F.data == "cancel_add")
async def cb_cancel_add(call: CallbackQuery, state: FSMContext):
    user_id = call.from_user.id
    data = await state.get_data()
    crane_name = data.get("crane_name", "")
    await state.clear()
    crane = get_crane(crane_name)
    await call.message.delete()
    if crane:
        await call.message.answer(
            text=crane_panel_text(crane, user_id),
            reply_markup=build_crane_keyboard(crane_name, user_id),
            parse_mode="HTML"
        )
    else:
        await call.message.answer(
            text=build_message_text(user_id),
            reply_markup=build_keyboard(user_id),
            parse_mode="HTML"
        )
    await call.answer(get_text(user_id, "cancelled"))


# ─── Settings ────────────────────────────────────────────────────────────────
@dp.callback_query(F.data == "settings")
async def cb_settings(call: CallbackQuery):
    user_id = call.from_user.id
    await call.message.delete()
    await call.message.answer(
        text=build_settings_text(user_id),
        reply_markup=build_settings_keyboard(user_id),
        parse_mode="HTML"
    )
    await call.answer()


@dp.callback_query(F.data == "set_api_key")
async def cb_set_api_key(call: CallbackQuery, state: FSMContext):
    user_id = call.from_user.id
    await state.set_state(SettingsState.api_key)
    await call.message.edit_text(
        text=get_text(user_id, "api_key_prompt"),
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text=get_text(user_id, "cancel"), callback_data="cancel_settings")]
        ]),
        parse_mode="HTML"
    )
    await call.answer()


@dp.callback_query(F.data == "set_api_host")
async def cb_set_api_host(call: CallbackQuery, state: FSMContext):
    user_id = call.from_user.id
    await state.set_state(SettingsState.api_host)
    await call.message.edit_text(
        text=get_text(user_id, "api_host_prompt"),
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text=get_text(user_id, "cancel"), callback_data="cancel_settings")]
        ]),
        parse_mode="HTML"
    )
    await call.answer()


@dp.callback_query(F.data == "set_language")
async def cb_set_language(call: CallbackQuery):
    user_id = call.from_user.id
    # Til tanlash menyusi
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🇬🇧 English", callback_data="lang_en")],
        [InlineKeyboardButton(text="🇺🇿 O'zbek", callback_data="lang_uz")],
        [InlineKeyboardButton(text="🇷🇺 Русский", callback_data="lang_ru")],
        [InlineKeyboardButton(text=get_text(user_id, "back"), callback_data="settings")],
    ])
    await call.message.edit_text(
        text=get_text(user_id, "select_language"),
        reply_markup=keyboard,
        parse_mode="HTML"
    )
    await call.answer()


@dp.callback_query(F.data.startswith("lang_"))
async def cb_language_selected(call: CallbackQuery):
    user_id = call.from_user.id
    lang_code = call.data.split("_")[1]  # en, uz, ru
    if user_id not in USER_SETTINGS:
        USER_SETTINGS[user_id] = {}
    USER_SETTINGS[user_id]["language"] = lang_code
    await call.message.delete()
    await call.message.answer(
        text=build_settings_text(user_id),
        reply_markup=build_settings_keyboard(user_id),
        parse_mode="HTML"
    )
    await call.answer(get_text(user_id, "language_changed"))


@dp.callback_query(F.data == "cancel_settings")
async def cb_cancel_settings(call: CallbackQuery, state: FSMContext):
    user_id = call.from_user.id
    await state.clear()
    await call.message.edit_text(
        text=build_settings_text(user_id),
        reply_markup=build_settings_keyboard(user_id),
        parse_mode="HTML"
    )
    await call.answer(get_text(user_id, "cancelled"))


@dp.message(SettingsState.api_key)
async def fsm_api_key(message: Message, state: FSMContext):
    user_id = message.from_user.id
    api_key = message.text.strip()
    if user_id not in USER_SETTINGS:
        USER_SETTINGS[user_id] = {}
    USER_SETTINGS[user_id]["api_key"] = api_key
    API_STATE["connected"] = True
    await state.clear()
    await message.answer(
        text=build_settings_text(user_id),
        reply_markup=build_settings_keyboard(user_id),
        parse_mode="HTML"
    )


@dp.message(SettingsState.api_host)
async def fsm_api_host(message: Message, state: FSMContext):
    user_id = message.from_user.id
    api_host = message.text.strip()
    if user_id not in USER_SETTINGS:
        USER_SETTINGS[user_id] = {}
    USER_SETTINGS[user_id]["api_host"] = api_host
    API_STATE["domain"] = api_host
    await state.clear()
    await message.answer(
        text=build_settings_text(user_id),
        reply_markup=build_settings_keyboard(user_id),
        parse_mode="HTML"
    )


# ─── Balance ─────────────────────────────────────────────────────────────────
@dp.callback_query(F.data == "balance")
async def cb_balance(call: CallbackQuery):
    user_id = call.from_user.id
    await call.answer(get_text(user_id, "balance") + " (coming soon...)", show_alert=False)


# ─── Subscription ────────────────────────────────────────────────────────────
@dp.callback_query(F.data == "subscription")
async def cb_subscription(call: CallbackQuery):
    user_id = call.from_user.id
    text = (
        f"{get_text(user_id, 'subscription_title')}\n\n"
        f"{get_text(user_id, 'no_active_sub')}\n\n"
        f"{get_text(user_id, 'accounts_count')}\n"
        f"{get_text(user_id, 'claims_count')}\n\n"
        f"{get_text(user_id, 'available_plans')}\n\n"
        f"{get_text(user_id, 'monthly')}\n"
        f"{get_text(user_id, 'monthly_desc')}\n\n"
        f"{get_text(user_id, 'claim_pack')}\n"
        f"{get_text(user_id, 'claim_pack_desc')}\n\n"
        "━━━━━━━━━━━━━━━━━━━━━━━━\n"
    )
    await call.message.delete()
    await call.message.answer(
        text=text,
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text=get_text(user_id, "pay_with_crypto"), callback_data="pay_crypto")],
            [InlineKeyboardButton(text=get_text(user_id, "back"), callback_data="back_main")],
        ]),
        parse_mode="HTML"
    )
    await call.answer()


# ─── Pay with Crypto ─────────────────────────────────────────────────────────
@dp.callback_query(F.data == "pay_crypto")
async def cb_pay_crypto(call: CallbackQuery):
    user_id = call.from_user.id
    text = get_text(user_id, "select_crypto")
    await call.message.delete()
    await call.message.answer(
        text=text,
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text=get_text(user_id, "bnb"), callback_data="pay_bnb")],
            [InlineKeyboardButton(text=get_text(user_id, "sol"), callback_data="pay_sol")],
            [InlineKeyboardButton(text=get_text(user_id, "ltc"), callback_data="pay_ltc")],
            [InlineKeyboardButton(text=get_text(user_id, "ton"), callback_data="pay_ton")],
            [InlineKeyboardButton(text=get_text(user_id, "trx"), callback_data="pay_trx")],
            [InlineKeyboardButton(text=get_text(user_id, "doge"), callback_data="pay_doge")],
            [InlineKeyboardButton(text=get_text(user_id, "back"), callback_data="subscription")],
        ]),
        parse_mode="HTML"
    )
    await call.answer()


@dp.callback_query(F.data == "pay_bnb")
async def cb_pay_bnb(call: CallbackQuery):
    user_id = call.from_user.id
    text = (
        f"🟡 <b>BNB (BEP-20)</b>\n\n"
        f"{get_text(user_id, 'wallet_address')}\n"
        f"<code>0x...BNB_ADDRESS_HERE...</code>\n\n"
        f"{get_text(user_id, 'amounts')}\n"
        f"{get_text(user_id, 'monthly_amount')}\n"
        f"{get_text(user_id, 'pack_amount')}\n\n"
        f"{get_text(user_id, 'send_exact')}\n"
        f"{get_text(user_id, 'submit_txid')}"
    )
    await call.message.delete()
    await call.message.answer(
        text=text,
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text=get_text(user_id, "submit_txid_button"), callback_data="submit_txid")],
            [InlineKeyboardButton(text=get_text(user_id, "back"), callback_data="pay_crypto")],
        ]),
        parse_mode="HTML"
    )
    await call.answer()


@dp.callback_query(F.data == "pay_sol")
async def cb_pay_sol(call: CallbackQuery):
    user_id = call.from_user.id
    text = (
        f"🟠 <b>SOL</b>\n\n"
        f"{get_text(user_id, 'wallet_address')}\n"
        f"<code>...SOL_ADDRESS_HERE...</code>\n\n"
        f"{get_text(user_id, 'amounts')}\n"
        f"{get_text(user_id, 'monthly_amount')}\n"
        f"{get_text(user_id, 'pack_amount')}\n\n"
        f"{get_text(user_id, 'send_exact')}\n"
        f"{get_text(user_id, 'submit_txid')}"
    )
    await call.message.delete()
    await call.message.answer(
        text=text,
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text=get_text(user_id, "submit_txid_button"), callback_data="submit_txid")],
            [InlineKeyboardButton(text=get_text(user_id, "back"), callback_data="pay_crypto")],
        ]),
        parse_mode="HTML"
    )
    await call.answer()


@dp.callback_query(F.data == "pay_ltc")
async def cb_pay_ltc(call: CallbackQuery):
    user_id = call.from_user.id
    text = (
        f"⚪ <b>LTC</b>\n\n"
        f"{get_text(user_id, 'wallet_address')}\n"
        f"<code>...LTC_ADDRESS_HERE...</code>\n\n"
        f"{get_text(user_id, 'amounts')}\n"
        f"{get_text(user_id, 'monthly_amount')}\n"
        f"{get_text(user_id, 'pack_amount')}\n\n"
        f"{get_text(user_id, 'send_exact')}\n"
        f"{get_text(user_id, 'submit_txid')}"
    )
    await call.message.delete()
    await call.message.answer(
        text=text,
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text=get_text(user_id, "submit_txid_button"), callback_data="submit_txid")],
            [InlineKeyboardButton(text=get_text(user_id, "back"), callback_data="pay_crypto")],
        ]),
        parse_mode="HTML"
    )
    await call.answer()


@dp.callback_query(F.data == "pay_ton")
async def cb_pay_ton(call: CallbackQuery):
    user_id = call.from_user.id
    text = (
        f"💎 <b>TON</b>\n\n"
        f"{get_text(user_id, 'wallet_address')}\n"
        f"<code>...TON_ADDRESS_HERE...</code>\n\n"
        f"{get_text(user_id, 'amounts')}\n"
        f"{get_text(user_id, 'monthly_amount')}\n"
        f"{get_text(user_id, 'pack_amount')}\n\n"
        f"{get_text(user_id, 'send_exact')}\n"
        f"{get_text(user_id, 'submit_txid')}"
    )
    await call.message.delete()
    await call.message.answer(
        text=text,
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text=get_text(user_id, "submit_txid_button"), callback_data="submit_txid")],
            [InlineKeyboardButton(text=get_text(user_id, "back"), callback_data="pay_crypto")],
        ]),
        parse_mode="HTML"
    )
    await call.answer()


@dp.callback_query(F.data == "pay_trx")
async def cb_pay_trx(call: CallbackQuery):
    user_id = call.from_user.id
    text = (
        f"🔴 <b>TRX (TRC-20)</b>\n\n"
        f"{get_text(user_id, 'wallet_address')}\n"
        f"<code>TXiU2U73Ei9ewcMYu6H1eht5jDGBCUUu1F</code>\n\n"
        f"{get_text(user_id, 'amounts')}\n"
        f"{get_text(user_id, 'monthly_amount')}\n"
        f"{get_text(user_id, 'pack_amount')}\n\n"
        f"{get_text(user_id, 'send_exact')}\n"
        f"{get_text(user_id, 'submit_txid')}"
    )
    await call.message.delete()
    await call.message.answer(
        text=text,
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text=get_text(user_id, "submit_txid_button"), callback_data="submit_txid")],
            [InlineKeyboardButton(text=get_text(user_id, "back"), callback_data="pay_crypto")],
        ]),
        parse_mode="HTML"
    )
    await call.answer()


@dp.callback_query(F.data == "pay_doge")
async def cb_pay_doge(call: CallbackQuery):
    user_id = call.from_user.id
    text = (
        f"🐕 <b>DOGE</b>\n\n"
        f"{get_text(user_id, 'wallet_address')}\n"
        f"<code>...DOGE_ADDRESS_HERE...</code>\n\n"
        f"{get_text(user_id, 'amounts')}\n"
        f"{get_text(user_id, 'monthly_amount')}\n"
        f"{get_text(user_id, 'pack_amount')}\n\n"
        f"{get_text(user_id, 'send_exact')}\n"
        f"{get_text(user_id, 'submit_txid')}"
    )
    await call.message.delete()
    await call.message.answer(
        text=text,
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text=get_text(user_id, "submit_txid_button"), callback_data="submit_txid")],
            [InlineKeyboardButton(text=get_text(user_id, "back"), callback_data="pay_crypto")],
        ]),
        parse_mode="HTML"
    )
    await call.answer()


@dp.callback_query(F.data == "submit_txid")
async def cb_submit_txid(call: CallbackQuery):
    user_id = call.from_user.id
    await call.answer(get_text(user_id, "submit_txid_prompt"), show_alert=True)


# ─── Invite Friend ───────────────────────────────────────────────────────────
@dp.callback_query(F.data == "invite")
async def cb_invite(call: CallbackQuery):
    user_id = call.from_user.id
    user = call.from_user
    ref_code = f"ref_{user.id}"
    ref_link = f"https://t.me/{BOT_USERNAME}?start={ref_code}"

    text = (
        f"{get_text(user_id, 'referral_title')}\n"
        "━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
        f"{get_text(user_id, 'your_link')}\n"
        f"<code>{ref_link}</code>\n\n"
        f"{get_text(user_id, 'share_text')}\n\n"
        f"{get_text(user_id, 'friends_joined')}\n"
        f"{get_text(user_id, 'bonus_earned')}"
    )

    await call.message.delete()
    await call.message.answer(
        text=text,
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text=get_text(user_id, "share_button"), url=f"https://t.me/share/url?url={ref_link}&text=Join+me%21")],
            [InlineKeyboardButton(text=get_text(user_id, "back"), callback_data="back_main")],
        ]),
        parse_mode="HTML"
    )
    await call.answer()


# ─── Startup ─────────────────────────────────────────────────────────────────
async def on_startup():
    global BOT_USERNAME
    me = await bot.get_me()
    BOT_USERNAME = me.username


async def main():
    await on_startup()
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
