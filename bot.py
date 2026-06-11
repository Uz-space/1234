import asyncio
import logging
from aiogram import Bot, Dispatcher, F
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.filters import CommandStart, Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.storage.memory import MemoryStorage

logging.basicConfig(level=logging.INFO)

BOT_TOKEN = "8565430862:AAFjLLyuK2peW_AAQactpVOI5LyeFSpY4XM"

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

# { user_id: { "api_key": ..., "api_host": ... } }
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


def cancel_keyboard():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="❌ Cancel", callback_data="cancel_add")]
    ])


def skip_cookies_keyboard():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="❌ Cancel", callback_data="cancel_add")],
        [InlineKeyboardButton(text="⏭️ Skip Cookies", callback_data="skip_cookies")],
    ])


def skip_ua_keyboard():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="❌ Cancel", callback_data="cancel_add")],
        [InlineKeyboardButton(text="⏭️ Skip UA", callback_data="skip_ua")],
    ])


# ─── Main menu ───────────────────────────────────────────────────────────────
def build_message_text() -> str:
    lines = []
    for c in CRANES:
        name_upper = c["name"].upper()
        if c["active"]:
            mult = f" | 🟢 {c['multiplier']}" if c["multiplier"] else ""
            line = f"{c['emoji']} {name_upper} ✅ [∞]{mult} ({c['claims']}/{c['max_claims']})"
        else:
            line = f"{c['emoji']} {name_upper} ⚠️ [∞] | ▫️ (0/{c['max_claims']})"
        lines.append(line)

    text = "\n".join(lines)
    text += "\n\n"

    api_icon = "✅" if API_STATE["connected"] else "❌"
    text += f"🔑 API: {api_icon} ({API_STATE['domain']})\n"

    if API_STATE["connected"] and API_STATE["accounts"] != 0:
        acc_str    = "∞" if API_STATE["accounts"] == -1 else str(API_STATE["accounts"])
        claims_str = str(API_STATE["total_claims"]) if API_STATE["total_claims"] > 0 else "0"
        text += f"📓 {API_STATE['plan']} | {acc_str} accounts | {claims_str} claims\n"

    text += "\n📡 LIVE LOG\n"
    text += "────────────────\n"

    if LIVE_LOG["log_text"]:
        text += f"{LIVE_LOG['crane_emoji']} {LIVE_LOG['crane_name'].upper()}\n"
        text += LIVE_LOG["log_text"]
    else:
        text += "⏳ No claims yet..."

    return text


def build_keyboard() -> InlineKeyboardMarkup:
    buttons = []
    row = []
    for c in CRANES:
        icon = "🟢" if c["active"] else "⚠️"
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

    buttons.append([InlineKeyboardButton(text="🌐 Proxies", callback_data="proxies")])
    buttons.append([InlineKeyboardButton(text="📊 Stats & Balance", callback_data="stats")])
    buttons.append([InlineKeyboardButton(text="💳 Subscription", callback_data="subscription")])
    buttons.append([InlineKeyboardButton(text="🎁 Invite Friend", callback_data="invite")])
    buttons.append([
        InlineKeyboardButton(text="⚙️ Settings", callback_data="settings"),
        InlineKeyboardButton(text="🔄", callback_data="refresh"),
    ])
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def build_crane_keyboard(crane_name: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="➕ Add Account", callback_data=f"add_account_{crane_name}")],
        [InlineKeyboardButton(text="◀️ Back", callback_data="back_main")],
    ])


def crane_panel_text(crane: dict) -> str:
    accounts     = crane.get("accounts", [])
    acc_count    = len(accounts)
    active_count = sum(1 for a in accounts if a.get("active", False))

    text = (
        f"{crane['emoji']} <b>{crane['name']} — Control Panel</b>\n"
        f"📊 {crane['claims']} claims | 💰 {crane['balance']}\n"
        f"▶️ <b>ACTIVE ACCOUNTS ({active_count}/{acc_count}):</b>\n"
    )
    if accounts:
        for acc in accounts:
            status = "🟢" if acc.get("active") else "🔴"
            text += f"  {status} {acc['label']} — {acc['email']}\n"
    else:
        text += "<i>No active accounts — + to add</i>"
    return text


# ─── Settings ────────────────────────────────────────────────────────────────
def build_settings_text(user_id: int) -> str:
    s        = USER_SETTINGS.get(user_id, {})
    api_key  = s.get("api_key", "")
    api_host = s.get("api_host", "sctg.xyz")

    if api_key:
        key_display = f"✅ {api_key[:8]}..."
    else:
        key_display = "❌ Not set"

    return (
        "⚙️ <b>Settings</b>\n\n"
        f"🔑 API Key: {key_display}\n"
        f"🌐 API Host: <a href='http://{api_host}'>{api_host}</a>\n\n"
        "<i>Each user has their own API key.</i>"
    )


def build_settings_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔑 XEvil API Key", callback_data="set_api_key")],
        [InlineKeyboardButton(text="🌐 API Host", callback_data="set_api_host")],
        [InlineKeyboardButton(text="🌐 Language", callback_data="set_language")],
        [InlineKeyboardButton(text="◀️ Back", callback_data="back_main")],
    ])


# ─── Bot va Dispatcher ───────────────────────────────────────────────────────
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher(storage=MemoryStorage())


# ─── /start ──────────────────────────────────────────────────────────────────
@dp.message(CommandStart())
async def cmd_start(message: Message, state: FSMContext):
    await state.clear()
    await message.answer(
        text=build_message_text(),
        reply_markup=build_keyboard(),
        parse_mode="HTML"
    )


# ─── /cancel ─────────────────────────────────────────────────────────────────
@dp.message(Command("cancel"))
async def cmd_cancel(message: Message, state: FSMContext):
    data = await state.get_data()
    crane_name = data.get("crane_name", "")
    await state.clear()
    if crane_name:
        crane = get_crane(crane_name)
        if crane:
            await message.answer(
                text=crane_panel_text(crane),
                reply_markup=build_crane_keyboard(crane_name),
                parse_mode="HTML"
            )
            return
    await message.answer(
        text=build_message_text(),
        reply_markup=build_keyboard(),
        parse_mode="HTML"
    )


# ─── Refresh ─────────────────────────────────────────────────────────────────
@dp.callback_query(F.data == "refresh")
async def cb_refresh(call: CallbackQuery, state: FSMContext):
    await state.clear()
    await call.message.delete()
    await call.message.answer(
        text=build_message_text(),
        reply_markup=build_keyboard(),
        parse_mode="HTML"
    )
    await call.answer("♻️ Updated!")


# ─── Back to main ────────────────────────────────────────────────────────────
@dp.callback_query(F.data == "back_main")
async def cb_back_main(call: CallbackQuery, state: FSMContext):
    await state.clear()
    await call.message.delete()
    await call.message.answer(
        text=build_message_text(),
        reply_markup=build_keyboard(),
        parse_mode="HTML"
    )
    await call.answer()


# ─── Crane panel ─────────────────────────────────────────────────────────────
@dp.callback_query(F.data.startswith("crane_"))
async def cb_crane(call: CallbackQuery):
    crane_name = call.data.replace("crane_", "")
    crane = get_crane(crane_name)
    if not crane:
        await call.answer("Not found!", show_alert=True)
        return
    await call.message.delete()
    await call.message.answer(
        text=crane_panel_text(crane),
        reply_markup=build_crane_keyboard(crane_name),
        parse_mode="HTML"
    )
    await call.answer()


# ─── Add Account Step 1: Email ───────────────────────────────────────────────
@dp.callback_query(F.data.startswith("add_account_"))
async def cb_add_account(call: CallbackQuery, state: FSMContext):
    crane_name = call.data.replace("add_account_", "")
    crane = get_crane(crane_name)
    if not crane:
        await call.answer("Not found!", show_alert=True)
        return

    acc_num = len(crane["accounts"]) + 1
    label = f"Account {acc_num}"

    await state.set_state(AddAccount.email)
    await state.update_data(crane_name=crane_name, label=label)

    await call.message.delete()
    await call.message.answer(
        text=(
            f"{crane['emoji']} <b>Add Account — {crane_name}</b>\n\n"
            f"🏷️ Label: <b>{label}</b>\n\n"
            "📧 Send the account email:\n\n"
            "/cancel to abort."
        ),
        reply_markup=cancel_keyboard(),
        parse_mode="HTML"
    )
    await call.answer()


# ─── Step 2: Password ────────────────────────────────────────────────────────
@dp.message(AddAccount.email)
async def fsm_email(message: Message, state: FSMContext):
    email = message.text.strip()
    await state.update_data(email=email)
    await state.set_state(AddAccount.password)
    await message.answer(
        text=(
            f"📧 Email: <code>{email}</code>\n\n"
            "🔑 Now send the password:\n\n"
            "/cancel to abort."
        ),
        reply_markup=cancel_keyboard(),
        parse_mode="HTML"
    )


# ─── Step 3: Cookies ─────────────────────────────────────────────────────────
@dp.message(AddAccount.password)
async def fsm_password(message: Message, state: FSMContext):
    password = message.text.strip()
    await state.update_data(password=password)
    await state.set_state(AddAccount.cookies)
    await message.answer(
        text=(
            "🔑 Password: ✅\n\n"
            "🍪 Cookies (optional — send cookies or tap Skip):\n\n"
            "F12 > Console > <code>document.cookie</code>\n\n"
            "/cancel to abort."
        ),
        reply_markup=skip_cookies_keyboard(),
        parse_mode="HTML"
    )


# ─── Skip Cookies ────────────────────────────────────────────────────────────
@dp.callback_query(F.data == "skip_cookies")
async def cb_skip_cookies(call: CallbackQuery, state: FSMContext):
    await state.update_data(cookies=None)
    await state.set_state(AddAccount.ua)
    await call.message.edit_text(
        text=(
            "🍪 Cookies: ⏭️ Skipped\n\n"
            "🌐 User-Agent (optional — send UA or tap Skip):\n\n"
            "F12 > Console > <code>navigator.userAgent</code>\n\n"
            "/cancel to abort."
        ),
        reply_markup=skip_ua_keyboard(),
        parse_mode="HTML"
    )
    await call.answer()


# ─── Cookies kiritildi ───────────────────────────────────────────────────────
@dp.message(AddAccount.cookies)
async def fsm_cookies(message: Message, state: FSMContext):
    cookies = message.text.strip()
    await state.update_data(cookies=cookies)
    await state.set_state(AddAccount.ua)
    await message.answer(
        text=(
            f"🍪 Cookies: ✅ ({len(cookies)} chars)\n\n"
            "🌐 User-Agent (optional — send UA or tap Skip):\n\n"
            "F12 > Console > <code>navigator.userAgent</code>\n\n"
            "/cancel to abort."
        ),
        reply_markup=skip_ua_keyboard(),
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
            f"✅ <b>Account added!</b>\n\n"
            f"{crane['emoji']} {crane_name} #{len(crane['accounts'])}\n"
            f"📝 {label}\n"
            f"📧 <code>{email}</code>\n"
            f"🔑 ✅\n"
            f"🍪 {'✅' if cookies else '⏭️'}\n"
            f"🌐 UA: {'✅' if ua else '⏭️'}"
        ),
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text=f"◀️ {crane_name}", callback_data=f"crane_{crane_name}")],
            [InlineKeyboardButton(text="🏠 Main Menu", callback_data="back_main")],
        ]),
        parse_mode="HTML"
    )


# ─── Cancel add ──────────────────────────────────────────────────────────────
@dp.callback_query(F.data == "cancel_add")
async def cb_cancel_add(call: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    crane_name = data.get("crane_name", "")
    await state.clear()
    crane = get_crane(crane_name)
    await call.message.delete()
    if crane:
        await call.message.answer(
            text=crane_panel_text(crane),
            reply_markup=build_crane_keyboard(crane_name),
            parse_mode="HTML"
        )
    else:
        await call.message.answer(
            text=build_message_text(),
            reply_markup=build_keyboard(),
            parse_mode="HTML"
        )
    await call.answer("❌ Cancelled.")


# ─── Settings ────────────────────────────────────────────────────────────────
@dp.callback_query(F.data == "settings")
async def cb_settings(call: CallbackQuery):
    await call.message.delete()
    await call.message.answer(
        text=build_settings_text(call.from_user.id),
        reply_markup=build_settings_keyboard(),
        parse_mode="HTML"
    )
    await call.answer()


@dp.callback_query(F.data == "set_api_key")
async def cb_set_api_key(call: CallbackQuery, state: FSMContext):
    await state.set_state(SettingsState.api_key)
    await call.message.edit_text(
        text=(
            "🔑 <b>XEvil API Key</b>\n\n"
            "Send your API key:\n\n"
            "/cancel to abort."
        ),
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="❌ Cancel", callback_data="cancel_settings")]
        ]),
        parse_mode="HTML"
    )
    await call.answer()


@dp.callback_query(F.data == "set_api_host")
async def cb_set_api_host(call: CallbackQuery, state: FSMContext):
    await state.set_state(SettingsState.api_host)
    await call.message.edit_text(
        text=(
            "🌐 <b>API Host</b>\n\n"
            "Send the API host (e.g. <code>sctg.xyz</code>):\n\n"
            "/cancel to abort."
        ),
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="❌ Cancel", callback_data="cancel_settings")]
        ]),
        parse_mode="HTML"
    )
    await call.answer()


@dp.callback_query(F.data == "set_language")
async def cb_language(call: CallbackQuery):
    await call.answer("🌐 Language (coming soon...)", show_alert=True)


@dp.callback_query(F.data == "cancel_settings")
async def cb_cancel_settings(call: CallbackQuery, state: FSMContext):
    await state.clear()
    await call.message.edit_text(
        text=build_settings_text(call.from_user.id),
        reply_markup=build_settings_keyboard(),
        parse_mode="HTML"
    )
    await call.answer("❌ Cancelled.")


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
        reply_markup=build_settings_keyboard(),
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
        reply_markup=build_settings_keyboard(),
        parse_mode="HTML"
    )


# ─── Proxies ─────────────────────────────────────────────────────────────────
@dp.callback_query(F.data == "proxies")
async def cb_proxies(call: CallbackQuery):
    await call.answer("🌐 Proxies (coming soon...)", show_alert=False)


# ─── Stats ───────────────────────────────────────────────────────────────────
@dp.callback_query(F.data == "stats")
async def cb_stats(call: CallbackQuery):
    await call.answer("📊 Stats & Balance (coming soon...)", show_alert=False)


# ─── Subscription ────────────────────────────────────────────────────────────
@dp.callback_query(F.data == "subscription")
async def cb_subscription(call: CallbackQuery):
    text = (
        "💳 <b>Subscription</b>\n\n"
        "❌ No active subscription\n\n"
        "📊 Accounts: 0\n"
        "📊 Claims: 0\n\n"
        "✅ <b>Available plans:</b>\n\n"
        "📆 <b>Monthly</b> – $15/month\n"
        "├ 50 accounts (any site)\n"
        "└ Unlimited claims\n\n"
        "🎫 <b>Claim Pack</b> – $1/1200 claims\n"
        "├ Unlimited accounts\n"
        "└ 1200 claims per pack\n\n"
        "━━━━━━━━━━━━━━━━━━━━━━━━\n"
    )

    await call.message.delete()
    await call.message.answer(
        text=text,
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="💎 Pay with Crypto", callback_data="pay_crypto")],
            [InlineKeyboardButton(text="◀️ Back", callback_data="back_main")],
        ]),
        parse_mode="HTML"
    )
    await call.answer()


# ─── Pay with Crypto ─────────────────────────────────────────────────────────
@dp.callback_query(F.data == "pay_crypto")
async def cb_pay_crypto(call: CallbackQuery):
    text = "💎 <b>Select Cryptocurrency</b>\n\nChoose your preferred coin:"

    await call.message.delete()
    await call.message.answer(
        text=text,
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="🟡 BNB (BEP-20)", callback_data="pay_bnb")],
            [InlineKeyboardButton(text="🟠 SOL", callback_data="pay_sol")],
            [InlineKeyboardButton(text="⚪ LTC", callback_data="pay_ltc")],
            [InlineKeyboardButton(text="💎 TON", callback_data="pay_ton")],
            [InlineKeyboardButton(text="🔴 TRX (TRC-20)", callback_data="pay_trx")],
            [InlineKeyboardButton(text="🐕 DOGE", callback_data="pay_doge")],
            [InlineKeyboardButton(text="◀️ Back", callback_data="subscription")],
        ]),
        parse_mode="HTML"
    )
    await call.answer()


@dp.callback_query(F.data == "pay_bnb")
async def cb_pay_bnb(call: CallbackQuery):
    text = (
        "🟡 <b>BNB (BEP-20)</b>\n\n"
        "📍 <b>Wallet Address:</b>\n"
        "<code>0x...BNB_ADDRESS_HERE...</code>\n\n"
        "💰 <b>Amounts:</b>\n"
        "• Monthly — $15\n"
        "• Claim Pack — $1\n\n"
        "⚠️ Send exactly the amount\n"
        "📝 After payment, tap Submit TXID"
    )
    await call.message.delete()
    await call.message.answer(
        text=text,
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="📝 Submit TXID", callback_data="submit_txid")],
            [InlineKeyboardButton(text="◀️ Back", callback_data="pay_crypto")],
        ]),
        parse_mode="HTML"
    )
    await call.answer()


@dp.callback_query(F.data == "pay_sol")
async def cb_pay_sol(call: CallbackQuery):
    text = (
        "🟠 <b>SOL</b>\n\n"
        "📍 <b>Wallet Address:</b>\n"
        "<code>...SOL_ADDRESS_HERE...</code>\n\n"
        "💰 <b>Amounts:</b>\n"
        "• Monthly — $15\n"
        "• Claim Pack — $1\n\n"
        "⚠️ Send exactly the amount\n"
        "📝 After payment, tap Submit TXID"
    )
    await call.message.delete()
    await call.message.answer(
        text=text,
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="📝 Submit TXID", callback_data="submit_txid")],
            [InlineKeyboardButton(text="◀️ Back", callback_data="pay_crypto")],
        ]),
        parse_mode="HTML"
    )
    await call.answer()


@dp.callback_query(F.data == "pay_ltc")
async def cb_pay_ltc(call: CallbackQuery):
    text = (
        "⚪ <b>LTC</b>\n\n"
        "📍 <b>Wallet Address:</b>\n"
        "<code>...LTC_ADDRESS_HERE...</code>\n\n"
        "💰 <b>Amounts:</b>\n"
        "• Monthly — $15\n"
        "• Claim Pack — $1\n\n"
        "⚠️ Send exactly the amount\n"
        "📝 After payment, tap Submit TXID"
    )
    await call.message.delete()
    await call.message.answer(
        text=text,
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="📝 Submit TXID", callback_data="submit_txid")],
            [InlineKeyboardButton(text="◀️ Back", callback_data="pay_crypto")],
        ]),
        parse_mode="HTML"
    )
    await call.answer()


@dp.callback_query(F.data == "pay_ton")
async def cb_pay_ton(call: CallbackQuery):
    text = (
        "💎 <b>TON</b>\n\n"
        "📍 <b>Wallet Address:</b>\n"
        "<code>...TON_ADDRESS_HERE...</code>\n\n"
        "💰 <b>Amounts:</b>\n"
        "• Monthly — $15\n"
        "• Claim Pack — $1\n\n"
        "⚠️ Send exactly the amount\n"
        "📝 After payment, tap Submit TXID"
    )
    await call.message.delete()
    await call.message.answer(
        text=text,
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="📝 Submit TXID", callback_data="submit_txid")],
            [InlineKeyboardButton(text="◀️ Back", callback_data="pay_crypto")],
        ]),
        parse_mode="HTML"
    )
    await call.answer()


@dp.callback_query(F.data == "pay_trx")
async def cb_pay_trx(call: CallbackQuery):
    text = (
        "🔴 <b>TRX (TRC-20)</b>\n\n"
        "📍 <b>Wallet Address:</b>\n"
        "<code>TXiU2U73Ei9ewcMYu6H1eht5jDGBCUUu1F</code>\n\n"
        "💰 <b>Amounts:</b>\n"
        "• Monthly — $15\n"
        "• Claim Pack — $1\n\n"
        "⚠️ Send exactly the amount\n"
        "📝 After payment, tap Submit TXID"
    )
    await call.message.delete()
    await call.message.answer(
        text=text,
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="📝 Submit TXID", callback_data="submit_txid")],
            [InlineKeyboardButton(text="◀️ Back", callback_data="pay_crypto")],
        ]),
        parse_mode="HTML"
    )
    await call.answer()


@dp.callback_query(F.data == "pay_doge")
async def cb_pay_doge(call: CallbackQuery):
    text = (
        "🐕 <b>DOGE</b>\n\n"
        "📍 <b>Wallet Address:</b>\n"
        "<code>...DOGE_ADDRESS_HERE...</code>\n\n"
        "💰 <b>Amounts:</b>\n"
        "• Monthly — $15\n"
        "• Claim Pack — $1\n\n"
        "⚠️ Send exactly the amount\n"
        "📝 After payment, tap Submit TXID"
    )
    await call.message.delete()
    await call.message.answer(
        text=text,
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="📝 Submit TXID", callback_data="submit_txid")],
            [InlineKeyboardButton(text="◀️ Back", callback_data="pay_crypto")],
        ]),
        parse_mode="HTML"
    )
    await call.answer()


@dp.callback_query(F.data == "submit_txid")
async def cb_submit_txid(call: CallbackQuery):
    await call.answer("📝 Send your TXID in chat...", show_alert=True)


# ─── Invite Friend ───────────────────────────────────────────────────────────
@dp.callback_query(F.data == "invite")
async def cb_invite(call: CallbackQuery):
    user = call.from_user
    ref_code = f"ref_{user.id}"
    ref_link = f"https://t.me/{BOT_USERNAME}?start={ref_code}"

    text = (
        "🎁🎁 <b>Referral System</b>\n"
        "━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
        "🔗 <b>Your referral link:</b>\n"
        f"<code>{ref_link}</code>\n\n"
        "📢 <b>Share this link with your friends!</b>\n"
        "├ You get: <b>+16 claims</b>\n"
        "└ Your friend gets: <b>+8 claims</b>\n\n"
        "👥 <b>Friends joined:</b> 0\n"
        "📊 <b>Bonus claims earned:</b> 0"
    )

    await call.message.delete()
    await call.message.answer(
        text=text,
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="📨 Share with Friend", url=f"https://t.me/share/url?url={ref_link}&text=Join+me%21")],
            [InlineKeyboardButton(text="◀️ Back", callback_data="back_main")],
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
