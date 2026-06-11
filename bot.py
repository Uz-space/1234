import asyncio
import logging
from aiogram import Bot, Dispatcher, F
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.filters import CommandStart, Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.storage.memory import MemoryStorage
from texts import TEXTS

logging.basicConfig(level=logging.INFO)

BOT_TOKEN = "8565430862:AAGehtqqTWqvLS-H4BH-LyUE6VfSbVJy698"
ADMIN_ID = 7399101034 # O‘z Telegram ID ingizni yozing

# ─── Global ma'lumotlar ──────────────────────────────────────────────────────
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

API_STATE = {"connected": False, "domain": "sctg.xyz", "plan": "Trial", "accounts": 0, "total_claims": 0}
LIVE_LOG = {"crane_emoji": "", "crane_name": "", "log_text": ""}
USER_SETTINGS = {}
BOT_USERNAME = ""

# ─── FSM States ──────────────────────────────────────────────────────────────
class AddAccount(StatesGroup): email = State(); password = State(); cookies = State(); ua = State()
class SettingsState(StatesGroup): api_key = State(); api_host = State()
class DepositState(StatesGroup): amount = State(); txid = State()

def get_text(user_id: int, key: str, **kwargs) -> str:
    lang = USER_SETTINGS.get(user_id, {}).get("language", "en")
    text = TEXTS.get(lang, TEXTS["en"]).get(key, key)
    if kwargs:
        return text.format(**kwargs)
    return text

def get_crane(name: str): return next((c for c in CRANES if c["name"] == name), None)

def cancel_keyboard(user_id: int): return InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text=get_text(user_id, "cancel"), callback_data="cancel_add")]])
def skip_cookies_keyboard(user_id: int): return InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text=get_text(user_id, "cancel"), callback_data="cancel_add")], [InlineKeyboardButton(text=get_text(user_id, "skip_cookies"), callback_data="skip_cookies")]])
def skip_ua_keyboard(user_id: int): return InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text=get_text(user_id, "cancel"), callback_data="cancel_add")], [InlineKeyboardButton(text=get_text(user_id, "skip_ua"), callback_data="skip_ua")]])

def build_message_text(user_id: int) -> str:
    lines = []
    for c in CRANES:
        name_upper = c["name"].upper()
        if c["active"]:
            mult = f" | 🟢 {c['multiplier']}" if c["multiplier"] else ""
            line = f"{c['emoji']} {name_upper} ✅ [∞]{mult} ({c['claims']}/{c['max_claims']})"
        else:
            line = f"{c['emoji']} {name_upper} ⚠️ [∞] | ▫️ (0/{c['max_claims']})"
        lines.append(line)
    text = "\n".join(lines) + "\n\n"
    api_icon = get_text(user_id, "api_connected") if API_STATE["connected"] else get_text(user_id, "api_disconnected")
    text += f"🔑 API: {api_icon} ({API_STATE['domain']})\n"
    if API_STATE["connected"] and API_STATE["accounts"] != 0:
        acc_str = "∞" if API_STATE["accounts"] == -1 else str(API_STATE["accounts"])
        claims_str = str(API_STATE["total_claims"]) if API_STATE["total_claims"] > 0 else "0"
        text += f"📓 {API_STATE['plan']} | {acc_str} accounts | {claims_str} claims\n"
    text += f"\n{get_text(user_id, 'live_log')}\n────────────────\n"
    if LIVE_LOG["log_text"]:
        text += f"{LIVE_LOG['crane_emoji']} {LIVE_LOG['crane_name'].upper()}\n{LIVE_LOG['log_text']}"
    else:
        text += get_text(user_id, "no_claims")
    return text

def build_keyboard(user_id: int) -> InlineKeyboardMarkup:
    buttons = []
    row = []
    for c in CRANES:
        icon = "🟢" if c["active"] else "⚠️"
        btn = InlineKeyboardButton(text=f"{icon} {c['name']}", callback_data=f"crane_{c['name']}")
        row.append(btn)
        if len(row) == 2:
            buttons.append(row); row = []
    if row: buttons.append(row)
    buttons.append([InlineKeyboardButton(text=get_text(user_id, "balance"), callback_data="balance")])
    buttons.append([InlineKeyboardButton(text=get_text(user_id, "subscription"), callback_data="subscription")])
    buttons.append([InlineKeyboardButton(text=get_text(user_id, "invite_friend"), callback_data="invite")])
    buttons.append([InlineKeyboardButton(text=get_text(user_id, "settings"), callback_data="settings"), InlineKeyboardButton(text=get_text(user_id, "refresh"), callback_data="refresh")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)

def build_crane_keyboard(crane_name: str, user_id: int): 
    return InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text=get_text(user_id, "add_account"), callback_data=f"add_account_{crane_name}")], [InlineKeyboardButton(text=get_text(user_id, "back"), callback_data="back_main")]])

def crane_panel_text(crane: dict, user_id: int) -> str:
    accounts = crane.get("accounts", [])
    acc_count = len(accounts)
    active_count = sum(1 for a in accounts if a.get("active", False))
    text = f"{crane['emoji']} <b>{crane['name']} — {get_text(user_id, 'control_panel')}</b>\n📊 {crane['claims']} {get_text(user_id, 'claims')} | 💰 {crane['balance']}\n▶️ <b>{get_text(user_id, 'active_accounts')} ({active_count}/{acc_count}):</b>\n"
    if accounts:
        for acc in accounts:
            status = "🟢" if acc.get("active") else "🔴"
            text += f"  {status} {acc['label']} — {acc['email']}\n"
    else:
        text += f"<i>{get_text(user_id, 'no_accounts')}</i>"
    return text

def build_settings_text(user_id: int) -> str:
    s = USER_SETTINGS.get(user_id, {})
    api_key = s.get("api_key", "")
    api_host = s.get("api_host", "sctg.xyz")
    key_display = f"{get_text(user_id, 'api_key_set')} {api_key[:8]}..." if api_key else get_text(user_id, "api_key_not_set")
    return f"{get_text(user_id, 'settings_title')}\n\n{get_text(user_id, 'api_key_label')}: {key_display}\n{get_text(user_id, 'api_host_label')}: <a href='http://{api_host}'>{api_host}</a>\n\n<i>{get_text(user_id, 'settings_note')}</i>"

def build_settings_keyboard(user_id: int): 
    return InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text=get_text(user_id, "api_key_label"), callback_data="set_api_key")], [InlineKeyboardButton(text=get_text(user_id, "api_host_label"), callback_data="set_api_host")], [InlineKeyboardButton(text=get_text(user_id, "language"), callback_data="set_language")], [InlineKeyboardButton(text=get_text(user_id, "back"), callback_data="back_main")]])

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher(storage=MemoryStorage())

# ─── /start ──────────────────────────────────────────────────────────────────
@dp.message(CommandStart())
async def cmd_start(message: Message, state: FSMContext):
    await state.clear()
    user_id = message.from_user.id
    args = message.text.split()
    referrer_id = None
    if len(args) > 1 and args[1].startswith("ref_"):
        try:
            referrer_id = int(args[1].split("_")[1])
        except:
            pass

    if user_id not in USER_SETTINGS:
        USER_SETTINGS[user_id] = {
            "language": "en",
            "balance": 0.0,
            "total_deposited": 0.0,
            "total_spent": 0.0,
            "referrals": [],
            "referral_bonus": 0
        }
        if referrer_id and referrer_id in USER_SETTINGS and referrer_id != user_id:
            USER_SETTINGS[referrer_id]["balance"] = USER_SETTINGS[referrer_id].get("balance", 0.0) + 0.16
            USER_SETTINGS[referrer_id]["referral_bonus"] = USER_SETTINGS[referrer_id].get("referral_bonus", 0) + 16
            USER_SETTINGS[referrer_id]["referrals"].append(user_id)
            USER_SETTINGS[user_id]["balance"] = USER_SETTINGS[user_id].get("balance", 0.0) + 0.08
            USER_SETTINGS[user_id]["referral_bonus"] = USER_SETTINGS[user_id].get("referral_bonus", 0) + 8
            await bot.send_message(referrer_id, get_text(referrer_id, "referee_bonus"))
            await message.answer(get_text(user_id, "referral_bonus", ref_id=referrer_id))

    await message.answer(text=build_message_text(user_id), reply_markup=build_keyboard(user_id), parse_mode="HTML")

@dp.message(Command("cancel"))
async def cmd_cancel(message: Message, state: FSMContext):
    user_id = message.from_user.id
    data = await state.get_data()
    crane_name = data.get("crane_name", "")
    await state.clear()
    if crane_name:
        crane = get_crane(crane_name)
        if crane:
            await message.answer(text=crane_panel_text(crane, user_id), reply_markup=build_crane_keyboard(crane_name, user_id), parse_mode="HTML")
            return
    await message.answer(text=build_message_text(user_id), reply_markup=build_keyboard(user_id), parse_mode="HTML")

# ─── Admin commands ──────────────────────────────────────────────────────────
@dp.message(Command("add_balance"))
async def cmd_add_balance(message: Message):
    if message.from_user.id != ADMIN_ID:
        await message.reply(get_text(message.from_user.id, "admin_only"))
        return
    parts = message.text.split()
    if len(parts) != 3:
        await message.reply(get_text(ADMIN_ID, "add_balance_usage"))
        return
    try:
        user_id = int(parts[1]); amount = float(parts[2])
    except:
        await message.reply(get_text(ADMIN_ID, "invalid_amount"))
        return
    if user_id not in USER_SETTINGS:
        await message.reply(get_text(ADMIN_ID, "user_not_found"))
        return
    USER_SETTINGS[user_id]["balance"] = USER_SETTINGS[user_id].get("balance", 0.0) + amount
    USER_SETTINGS[user_id]["total_deposited"] = USER_SETTINGS[user_id].get("total_deposited", 0.0) + amount
    await message.reply(get_text(ADMIN_ID, "balance_updated", user_id=user_id, amount=amount, balance=USER_SETTINGS[user_id]["balance"]))

@dp.message(Command("add_spent"))
async def cmd_add_spent(message: Message):
    if message.from_user.id != ADMIN_ID:
        await message.reply(get_text(message.from_user.id, "admin_only"))
        return
    parts = message.text.split()
    if len(parts) != 3:
        await message.reply(get_text(ADMIN_ID, "add_spent_usage"))
        return
    try:
        user_id = int(parts[1]); amount = float(parts[2])
    except:
        await message.reply(get_text(ADMIN_ID, "invalid_amount"))
        return
    if user_id not in USER_SETTINGS:
        await message.reply(get_text(ADMIN_ID, "user_not_found"))
        return
    USER_SETTINGS[user_id]["total_spent"] = USER_SETTINGS[user_id].get("total_spent", 0.0) + amount
    await message.reply(get_text(ADMIN_ID, "spent_updated", user_id=user_id, amount=amount, spent=USER_SETTINGS[user_id]["total_spent"]))

# ─── Refresh, Back, Crane panel ──────────────────────────────────────────────
@dp.callback_query(F.data == "refresh")
async def cb_refresh(call: CallbackQuery, state: FSMContext):
    user_id = call.from_user.id
    await state.clear()
    await call.message.delete()
    await call.message.answer(text=build_message_text(user_id), reply_markup=build_keyboard(user_id), parse_mode="HTML")
    await call.answer(get_text(user_id, "updated"))

@dp.callback_query(F.data == "back_main")
async def cb_back_main(call: CallbackQuery, state: FSMContext):
    user_id = call.from_user.id
    await state.clear()
    await call.message.delete()
    await call.message.answer(text=build_message_text(user_id), reply_markup=build_keyboard(user_id), parse_mode="HTML")
    await call.answer()

@dp.callback_query(F.data.startswith("crane_"))
async def cb_crane(call: CallbackQuery):
    user_id = call.from_user.id
    crane_name = call.data.replace("crane_", "")
    crane = get_crane(crane_name)
    if not crane:
        await call.answer(get_text(user_id, "not_found"), show_alert=True)
        return
    await call.message.delete()
    await call.message.answer(text=crane_panel_text(crane, user_id), reply_markup=build_crane_keyboard(crane_name, user_id), parse_mode="HTML")
    await call.answer()

# ─── Add account flow ────────────────────────────────────────────────────────
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
    await call.message.answer(text=f"{crane['emoji']} <b>{get_text(user_id, 'add_account_title', crane=crane_name)}</b>\n\n{get_text(user_id, 'label', label=label)}\n\n{get_text(user_id, 'send_email')}\n\n{get_text(user_id, 'cancel_abort')}", reply_markup=cancel_keyboard(user_id), parse_mode="HTML")
    await call.answer()

@dp.message(AddAccount.email)
async def fsm_email(message: Message, state: FSMContext):
    user_id = message.from_user.id
    email = message.text.strip()
    await state.update_data(email=email)
    await state.set_state(AddAccount.password)
    await message.answer(text=f"{get_text(user_id, 'email_received', email=email)}\n\n{get_text(user_id, 'send_password')}\n\n{get_text(user_id, 'cancel_abort')}", reply_markup=cancel_keyboard(user_id), parse_mode="HTML")

@dp.message(AddAccount.password)
async def fsm_password(message: Message, state: FSMContext):
    user_id = message.from_user.id
    password = message.text.strip()
    await state.update_data(password=password)
    await state.set_state(AddAccount.cookies)
    await message.answer(text=f"{get_text(user_id, 'password_ok')}\n\n{get_text(user_id, 'cookies_optional')}\n\n{get_text(user_id, 'cookies_instruction')}\n\n{get_text(user_id, 'cancel_abort')}", reply_markup=skip_cookies_keyboard(user_id), parse_mode="HTML")

@dp.callback_query(F.data == "skip_cookies")
async def cb_skip_cookies(call: CallbackQuery, state: FSMContext):
    user_id = call.from_user.id
    await state.update_data(cookies=None)
    await state.set_state(AddAccount.ua)
    await call.message.edit_text(text=f"{get_text(user_id, 'cookies_skipped')}\n\n{get_text(user_id, 'ua_optional')}\n\n{get_text(user_id, 'ua_instruction')}\n\n{get_text(user_id, 'cancel_abort')}", reply_markup=skip_ua_keyboard(user_id), parse_mode="HTML")
    await call.answer()

@dp.message(AddAccount.cookies)
async def fsm_cookies(message: Message, state: FSMContext):
    user_id = message.from_user.id
    cookies = message.text.strip()
    await state.update_data(cookies=cookies)
    await state.set_state(AddAccount.ua)
    await message.answer(text=f"{get_text(user_id, 'cookies_received', len=len(cookies))}\n\n{get_text(user_id, 'ua_optional')}\n\n{get_text(user_id, 'ua_instruction')}\n\n{get_text(user_id, 'cancel_abort')}", reply_markup=skip_ua_keyboard(user_id), parse_mode="HTML")

@dp.callback_query(F.data == "skip_ua")
async def cb_skip_ua(call: CallbackQuery, state: FSMContext):
    await state.update_data(ua=None)
    await _finish_add_account(call.message, state)
    await call.answer()

@dp.message(AddAccount.ua)
async def fsm_ua(message: Message, state: FSMContext):
    await state.update_data(ua=message.text.strip())
    await _finish_add_account(message, state)

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
    crane["accounts"].append({"label": label, "email": email, "password": password, "cookies": cookies, "ua": ua, "active": True})
    crane["active"] = True
    await state.clear()
    await message.answer(text=f"{get_text(user_id, 'account_added')}\n\n{crane['emoji']} {get_text(user_id, 'account_num', crane=crane_name, num=len(crane['accounts']))}\n📝 {label}\n📧 <code>{email}</code>\n🔑 ✅\n{get_text(user_id, 'cookies_status', status='✅' if cookies else '⏭️')}\n{get_text(user_id, 'ua_status', status='✅' if ua else '⏭️')}", reply_markup=InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text=f"◀️ {crane_name}", callback_data=f"crane_{crane_name}")], [InlineKeyboardButton(text=get_text(user_id, "main_menu"), callback_data="back_main")]]), parse_mode="HTML")

@dp.callback_query(F.data == "cancel_add")
async def cb_cancel_add(call: CallbackQuery, state: FSMContext):
    user_id = call.from_user.id
    data = await state.get_data()
    crane_name = data.get("crane_name", "")
    await state.clear()
    crane = get_crane(crane_name)
    await call.message.delete()
    if crane:
        await call.message.answer(text=crane_panel_text(crane, user_id), reply_markup=build_crane_keyboard(crane_name, user_id), parse_mode="HTML")
    else:
        await call.message.answer(text=build_message_text(user_id), reply_markup=build_keyboard(user_id), parse_mode="HTML")
    await call.answer(get_text(user_id, "cancelled"))

# ─── Settings ────────────────────────────────────────────────────────────────
@dp.callback_query(F.data == "settings")
async def cb_settings(call: CallbackQuery):
    user_id = call.from_user.id
    await call.message.delete()
    await call.message.answer(text=build_settings_text(user_id), reply_markup=build_settings_keyboard(user_id), parse_mode="HTML")
    await call.answer()

@dp.callback_query(F.data == "set_api_key")
async def cb_set_api_key(call: CallbackQuery, state: FSMContext):
    user_id = call.from_user.id
    await state.set_state(SettingsState.api_key)
    await call.message.edit_text(text=get_text(user_id, "api_key_prompt"), reply_markup=InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text=get_text(user_id, "cancel"), callback_data="cancel_settings")]]), parse_mode="HTML")
    await call.answer()

@dp.callback_query(F.data == "set_api_host")
async def cb_set_api_host(call: CallbackQuery, state: FSMContext):
    user_id = call.from_user.id
    await state.set_state(SettingsState.api_host)
    await call.message.edit_text(text=get_text(user_id, "api_host_prompt"), reply_markup=InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text=get_text(user_id, "cancel"), callback_data="cancel_settings")]]), parse_mode="HTML")
    await call.answer()

@dp.callback_query(F.data == "set_language")
async def cb_set_language(call: CallbackQuery):
    user_id = call.from_user.id
    keyboard = InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="🇬🇧 English", callback_data="lang_en")], [InlineKeyboardButton(text="🇺🇿 O'zbek", callback_data="lang_uz")], [InlineKeyboardButton(text="🇷🇺 Русский", callback_data="lang_ru")], [InlineKeyboardButton(text=get_text(user_id, "back"), callback_data="settings")]])
    await call.message.edit_text(text=get_text(user_id, "select_language"), reply_markup=keyboard, parse_mode="HTML")
    await call.answer()

@dp.callback_query(F.data.startswith("lang_"))
async def cb_language_selected(call: CallbackQuery):
    user_id = call.from_user.id
    lang_code = call.data.split("_")[1]
    if user_id not in USER_SETTINGS: USER_SETTINGS[user_id] = {}
    USER_SETTINGS[user_id]["language"] = lang_code
    await call.message.delete()
    await call.message.answer(text=build_settings_text(user_id), reply_markup=build_settings_keyboard(user_id), parse_mode="HTML")
    await call.answer(get_text(user_id, "language_changed"))

@dp.callback_query(F.data == "cancel_settings")
async def cb_cancel_settings(call: CallbackQuery, state: FSMContext):
    user_id = call.from_user.id
    await state.clear()
    await call.message.edit_text(text=build_settings_text(user_id), reply_markup=build_settings_keyboard(user_id), parse_mode="HTML")
    await call.answer(get_text(user_id, "cancelled"))

@dp.message(SettingsState.api_key)
async def fsm_api_key(message: Message, state: FSMContext):
    user_id = message.from_user.id
    api_key = message.text.strip()
    if user_id not in USER_SETTINGS: USER_SETTINGS[user_id] = {}
    USER_SETTINGS[user_id]["api_key"] = api_key
    API_STATE["connected"] = True
    await state.clear()
    await message.answer(text=build_settings_text(user_id), reply_markup=build_settings_keyboard(user_id), parse_mode="HTML")

@dp.message(SettingsState.api_host)
async def fsm_api_host(message: Message, state: FSMContext):
    user_id = message.from_user.id
    api_host = message.text.strip()
    if user_id not in USER_SETTINGS: USER_SETTINGS[user_id] = {}
    USER_SETTINGS[user_id]["api_host"] = api_host
    API_STATE["domain"] = api_host
    await state.clear()
    await message.answer(text=build_settings_text(user_id), reply_markup=build_settings_keyboard(user_id), parse_mode="HTML")

# ─── Balance ─────────────────────────────────────────────────────────────────
@dp.callback_query(F.data == "balance")
async def cb_balance(call: CallbackQuery):
    user_id = call.from_user.id
    balance = USER_SETTINGS.get(user_id, {}).get("balance", 0.0)
    total_deposited = USER_SETTINGS.get(user_id, {}).get("total_deposited", 0.0)
    total_spent = USER_SETTINGS.get(user_id, {}).get("total_spent", 0.0)
    text = f"{get_text(user_id, 'balance_title')}\n\n{get_text(user_id, 'current_balance', balance=balance)}\n{get_text(user_id, 'total_deposited', deposited=total_deposited)}\n{get_text(user_id, 'total_spent', spent=total_spent)}\n{get_text(user_id, 'spent_note')}"
    await call.message.delete()
    await call.message.answer(text=text, reply_markup=InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text=get_text(user_id, "back"), callback_data="back_main")]]), parse_mode="HTML")
    await call.answer()

# ─── Subscription ────────────────────────────────────────────────────────────
@dp.callback_query(F.data == "subscription")
async def cb_subscription(call: CallbackQuery):
    user_id = call.from_user.id
    text = f"{get_text(user_id, 'subscription_title')}\n\n{get_text(user_id, 'no_active_sub')}\n\n{get_text(user_id, 'accounts_count')}\n{get_text(user_id, 'claims_count')}\n\n{get_text(user_id, 'available_plans')}\n\n{get_text(user_id, 'monthly')}\n{get_text(user_id, 'monthly_desc')}\n\n{get_text(user_id, 'claim_pack')}\n{get_text(user_id, 'claim_pack_desc')}\n\n━━━━━━━━━━━━━━━━━━━━━━━━\n"
    await call.message.delete()
    await call.message.answer(text=text, reply_markup=InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text=get_text(user_id, "pay_with_crypto"), callback_data="pay_crypto")], [InlineKeyboardButton(text=get_text(user_id, "back"), callback_data="back_main")]]), parse_mode="HTML")
    await call.answer()

# ─── Pay with Crypto ─────────────────────────────────────────────────────────
@dp.callback_query(F.data == "pay_crypto")
async def cb_pay_crypto(call: CallbackQuery):
    user_id = call.from_user.id
    text = get_text(user_id, "select_crypto")
    await call.message.delete()
    await call.message.answer(text=text, reply_markup=InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=get_text(user_id, "bnb"), callback_data="pay_bnb")],
        [InlineKeyboardButton(text=get_text(user_id, "sol"), callback_data="pay_sol")],
        [InlineKeyboardButton(text=get_text(user_id, "ltc"), callback_data="pay_ltc")],
        [InlineKeyboardButton(text=get_text(user_id, "ton"), callback_data="pay_ton")],
        [InlineKeyboardButton(text=get_text(user_id, "trx"), callback_data="pay_trx")],
        [InlineKeyboardButton(text=get_text(user_id, "doge"), callback_data="pay_doge")],
        [InlineKeyboardButton(text=get_text(user_id, "back"), callback_data="subscription")]
    ]), parse_mode="HTML")
    await call.answer()

@dp.callback_query(F.data.startswith("pay_"))
async def cb_pay_coin(call: CallbackQuery):
    user_id = call.from_user.id
    coin_map = {"bnb": "BNB (BEP-20)", "sol": "SOL", "ltc": "LTC", "ton": "TON", "trx": "TRX (TRC-20)", "doge": "DOGE"}
    coin_key = call.data.split("_")[1]
    coin_name = coin_map.get(coin_key, coin_key.upper())
    wallets = {"bnb": "0x...BNB_ADDRESS_HERE...", "sol": "...SOL_ADDRESS_HERE...", "ltc": "...LTC_ADDRESS_HERE...", "ton": "...TON_ADDRESS_HERE...", "trx": "TXiU2U73Ei9ewcMYu6H1eht5jDGBCUUu1F", "doge": "...DOGE_ADDRESS_HERE..."}
    address = wallets.get(coin_key, "Address not set")
    text = f"{coin_name}\n\n{get_text(user_id, 'wallet_address')}\n<code>{address}</code>\n\n{get_text(user_id, 'amounts')}\n{get_text(user_id, 'send_exact')}\n{get_text(user_id, 'submit_txid')}"
    await call.message.delete()
    await call.message.answer(text=text, reply_markup=InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text=get_text(user_id, "submit_txid_button"), callback_data="submit_txid")], [InlineKeyboardButton(text=get_text(user_id, "back"), callback_data="pay_crypto")]]), parse_mode="HTML")
    await call.answer()

# ─── Submit Screenshot (deposit flow) ────────────────────────────────────────
@dp.callback_query(F.data == "submit_txid")
async def cb_submit_txid(call: CallbackQuery, state: FSMContext):
    user_id = call.from_user.id
    await state.set_state(DepositState.amount)
    await call.message.answer(
        text=get_text(user_id, "enter_amount"),
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text=get_text(user_id, "cancel"), callback_data="cancel_deposit")]]),
        parse_mode="HTML"
    )
    await call.answer()

@dp.message(DepositState.amount)
async def fsm_deposit_amount(message: Message, state: FSMContext):
    user_id = message.from_user.id
    try:
        amount = float(message.text.strip())
        if amount < 0.1 or amount > 100:
            raise ValueError
    except:
        await message.answer(get_text(user_id, "invalid_amount"))
        return
    await state.update_data(amount=amount)
    await state.set_state(DepositState.txid)
    await message.answer(
        text=get_text(user_id, "enter_txid"),
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text=get_text(user_id, "cancel"), callback_data="cancel_deposit")]]),
        parse_mode="HTML"
    )

@dp.message(DepositState.txid)
async def fsm_deposit_photo(message: Message, state: FSMContext):
    user_id = message.from_user.id
    if not message.photo:
        await message.answer(get_text(user_id, "only_photo"))
        return

    photo = message.photo[-1]
    file_id = photo.file_id
    data = await state.get_data()
    amount = data.get("amount")
    if not amount:
        await state.clear()
        await message.answer("❌ Xatolik yuz berdi. Iltimos, qaytadan /start bilan boshlang.")
        return
    await state.clear()

    caption = get_text(ADMIN_ID, "deposit_request", user_id=user_id, amount=amount, txid="📸 Screenshot")
    approve_btn = InlineKeyboardButton(text=get_text(ADMIN_ID, "approve"), callback_data=f"approve_deposit_{user_id}_{amount}")
    reject_btn = InlineKeyboardButton(text=get_text(ADMIN_ID, "reject"), callback_data=f"reject_deposit_{user_id}")
    keyboard = InlineKeyboardMarkup(inline_keyboard=[[approve_btn, reject_btn]])

    try:
        await bot.send_photo(ADMIN_ID, photo=file_id, caption=caption, reply_markup=keyboard, parse_mode="HTML")
        await message.answer(get_text(user_id, "txid_received"))
    except Exception as e:
        await message.answer(f"❌ Xatolik: {e}. Iltimos, keyinroq qaytadan urinib ko‘ring.")

@dp.callback_query(F.data == "cancel_deposit")
async def cb_cancel_deposit(call: CallbackQuery, state: FSMContext):
    user_id = call.from_user.id
    await state.clear()
    await call.message.delete()
    await call.message.answer(text=get_text(user_id, "cancelled"), reply_markup=build_keyboard(user_id), parse_mode="HTML")
    await call.answer()

# ─── Admin approve/reject callbacks ──────────────────────────────────────────
@dp.callback_query(F.data.startswith("approve_deposit_"))
async def cb_approve_deposit(call: CallbackQuery):
    if call.from_user.id != ADMIN_ID:
        await call.answer("❌ Admin only.", show_alert=True)
        return
    parts = call.data.split("_")
    user_id = int(parts[2])
    amount = float(parts[3])
    if user_id not in USER_SETTINGS:
        await call.answer("User not found", show_alert=True)
        return
    USER_SETTINGS[user_id]["balance"] = USER_SETTINGS[user_id].get("balance", 0.0) + amount
    USER_SETTINGS[user_id]["total_deposited"] = USER_SETTINGS[user_id].get("total_deposited", 0.0) + amount
    await bot.send_message(user_id, get_text(user_id, "deposit_approved", amount=amount))
    await call.message.edit_text(call.message.text + "\n\n✅ APPROVED", reply_markup=None)
    await call.answer("Approved")

@dp.callback_query(F.data.startswith("reject_deposit_"))
async def cb_reject_deposit(call: CallbackQuery):
    if call.from_user.id != ADMIN_ID:
        await call.answer("❌ Admin only.", show_alert=True)
        return
    user_id = int(call.data.split("_")[2])
    await bot.send_message(user_id, get_text(user_id, "deposit_rejected"))
    await call.message.edit_text(call.message.text + "\n\n❌ REJECTED", reply_markup=None)
    await call.answer("Rejected")

# ─── Invite Friend (referal ko‘rsatkichlari bilan) ───────────────────────────
@dp.callback_query(F.data == "invite")
async def cb_invite(call: CallbackQuery):
    user_id = call.from_user.id
    ref_link = f"https://t.me/{BOT_USERNAME}?start=ref_{user_id}"
    friends_count = len(USER_SETTINGS.get(user_id, {}).get("referrals", []))
    bonus = USER_SETTINGS.get(user_id, {}).get("referral_bonus", 0)
    text = f"{get_text(user_id, 'referral_title')}\n━━━━━━━━━━━━━━━━━━━━━━━━\n\n{get_text(user_id, 'your_link')}\n<code>{ref_link}</code>\n\n{get_text(user_id, 'share_text')}\n\n{get_text(user_id, 'friends_joined', count=friends_count)}\n{get_text(user_id, 'bonus_earned', bonus=bonus)}"
    await call.message.delete()
    await call.message.answer(text=text, reply_markup=InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text=get_text(user_id, "share_button"), url=f"https://t.me/share/url?url={ref_link}&text=Join+me%21")], [InlineKeyboardButton(text=get_text(user_id, "back"), callback_data="back_main")]]), parse_mode="HTML")
    await call.answer()

async def on_startup():
    global BOT_USERNAME
    me = await bot.get_me()
    BOT_USERNAME = me.username

async def main():
    await on_startup()
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
