#!/usr/bin/env python3
import asyncio
import logging
import json
import os
import aiohttp
from http.cookies import SimpleCookie
from typing import Optional
from aiogram import Bot, Dispatcher, F
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.filters import CommandStart, Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.storage.memory import MemoryStorage

logging.basicConfig(level=logging.INFO)
BOT_TOKEN = "8565430862:AAEKjNqGjNKOpamnlqanPfJdUbmNY6Cu86k"
ADMIN_ID = 7399101034

# ------------------- TEXTS (qisqartirilgan, ammo to‘liq ishlaydi) -------------------
TEXTS = {
    "en": {
        "add_account": "➕ Add Account", "back": "◀️ Back", "cancel": "❌ Cancel",
        "send_email": "📧 Send email:", "send_password": "🔑 Send password:",
        "cookies_required": "🍪 Send cookies (F12 console > document.cookie):",
        "ua_required": "🌐 Send User-Agent (navigator.userAgent):",
        "account_added": "✅ Account added!", "main_menu": "🏠 Main Menu",
        "api_key_not_set": "❌ API key not set in Settings.",
        "api_key_prompt": "🔑 Send your Xevil API key:",
        "balance": "💰 Balance", "subscription": "💳 Subscription", "invite_friend": "🎁 Invite Friend",
        "settings": "⚙️ Settings", "refresh": "🔄",
        "active_accounts": "ACTIVE ACCOUNTS", "no_accounts": "No accounts",
        "control_panel": "Control Panel", "claims": "claims",
        "select_language": "Select language:", "language_changed": "Language changed!",
        "no_active_sub": "No active subscription", "accounts_count": "Accounts: 0", "claims_count": "Claims: 0",
        "available_plans": "Available plans:", "monthly": "Monthly $15", "claim_pack": "Claim pack $1",
        "pay_with_crypto": "Pay with Crypto", "select_crypto": "Select coin",
        "wallet_address": "Wallet address:", "amounts": "Amount USD:", "send_exact": "Send exact amount",
        "submit_txid_button": "Submit screenshot", "enter_amount": "Enter amount (0.1-100):",
        "enter_txid": "Send payment screenshot:", "txid_received": "Screenshot received!",
        "deposit_approved": "Deposit ${amount} approved!", "deposit_rejected": "Deposit rejected.",
        "referral_title": "Referral system", "your_link": "Your link:", "share_text": "Share with friends",
        "friends_joined": "Friends: {count}", "bonus_earned": "Bonus: {bonus}", "share_button": "Share",
        "balance_title": "My Balance", "current_balance": "Balance: ${balance}",
        "total_deposited": "Deposited: ${deposited}", "total_spent": "Spent: ${spent}",
        "spent_note": "\nEach claim costs $0.01", "cancelled": "Cancelled.",
        "updated": "Updated!", "not_found": "Not found!", "admin_only": "Admin only.",
        "invalid_amount": "Invalid amount", "user_not_found": "User not found",
        "only_photo": "Send a photo, not text.",
    },
    "uz": {
        "add_account": "➕ Hisob qo'shish", "back": "◀️ Orqaga", "cancel": "❌ Bekor",
        "send_email": "📧 Emailni yuboring:", "send_password": "🔑 Parolni yuboring:",
        "cookies_required": "🍪 Cookies yuboring (F12 > Konsol > document.cookie):",
        "ua_required": "🌐 User-Agent yuboring (navigator.userAgent):",
        "account_added": "✅ Hisob qo'shildi!", "main_menu": "🏠 Bosh menyu",
        "api_key_not_set": "❌ API kalit o'rnatilmagan.",
        "api_key_prompt": "🔑 Xevil API kalitingizni yuboring:",
        "balance": "💰 Balans", "subscription": "💳 Obuna", "invite_friend": "🎁 Do'st taklif",
        "settings": "⚙️ Sozlamalar", "refresh": "🔄",
        "active_accounts": "FAOL HISOBLAR", "no_accounts": "Hisob yo'q",
        "control_panel": "Boshqaruv paneli", "claims": "claim",
        "select_language": "Tilni tanlang:", "language_changed": "Til o'zgartirildi!",
        "no_active_sub": "Faol obuna yo'q", "accounts_count": "Hisoblar: 0", "claims_count": "Claimlar: 0",
        "available_plans": "Mavjud rejalar:", "monthly": "Oylik $15", "claim_pack": "Claim paketi $1",
        "pay_with_crypto": "Kripto to'lov", "select_crypto": "Tangani tanlang",
        "wallet_address": "Hamyon manzili:", "amounts": "Miqdor USD:", "send_exact": "Aynan shu miqdorni yuboring",
        "submit_txid_button": "Screenshot yuborish", "enter_amount": "Miqdorni kiriting (0.1-100):",
        "enter_txid": "To'lov skrinshotini yuboring:", "txid_received": "Screenshot qabul qilindi!",
        "deposit_approved": "${amount} to'lov tasdiqlandi!", "deposit_rejected": "To'lov rad etildi.",
        "referral_title": "Referal tizimi", "your_link": "Sizning link:", "share_text": "Do'stlarga ulashing",
        "friends_joined": "Do'stlar: {count}", "bonus_earned": "Bonus: {bonus}", "share_button": "Ulashish",
        "balance_title": "Mening balansim", "current_balance": "Balans: ${balance}",
        "total_deposited": "To'ldirilgan: ${deposited}", "total_spent": "Sarflangan: ${spent}",
        "spent_note": "\nHar bir claim $0.01 turadi", "cancelled": "Bekor qilindi.",
        "updated": "Yangilandi!", "not_found": "Topilmadi!", "admin_only": "Faqat admin.",
        "invalid_amount": "Noto'g'ri miqdor", "user_not_found": "Foydalanuvchi topilmadi",
        "only_photo": "Rasm yuboring, matn emas.",
    }
}

def get_text(user_id: int, key: str, **kwargs) -> str:
    lang = USER_SETTINGS.get(user_id, {}).get("language", "en")
    text = TEXTS.get(lang, TEXTS["en"]).get(key, key)
    if kwargs:
        try:
            return text.format(**kwargs)
        except:
            return text
    return text

# ------------------- PERSISTENT STORAGE -------------------
DATA_DIR = "data"
USER_SETTINGS_FILE = os.path.join(DATA_DIR, "user_settings.json")
CRANES_FILE = os.path.join(DATA_DIR, "cranes.json")

def ensure_data_dir():
    os.makedirs(DATA_DIR, exist_ok=True)

def load_user_settings():
    ensure_data_dir()
    if os.path.exists(USER_SETTINGS_FILE):
        with open(USER_SETTINGS_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}

def save_user_settings():
    ensure_data_dir()
    with open(USER_SETTINGS_FILE, "w", encoding="utf-8") as f:
        json.dump(USER_SETTINGS, f, indent=2, ensure_ascii=False)

def load_cranes():
    ensure_data_dir()
    if os.path.exists(CRANES_FILE):
        with open(CRANES_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return [
        {"name": "TronPick", "emoji": "🔴", "active": False, "claims": 0, "accounts": []},
        {"name": "LitePick", "emoji": "🌕", "active": False, "claims": 0, "accounts": []},
        {"name": "DogePick", "emoji": "🐕", "active": False, "claims": 0, "accounts": []},
        {"name": "PolPick",  "emoji": "🪙", "active": False, "claims": 0, "accounts": []},
        {"name": "BnbPick",  "emoji": "🟡", "active": False, "claims": 0, "accounts": []},
        {"name": "SolPick",  "emoji": "☀️", "active": False, "claims": 0, "accounts": []},
        {"name": "SuiPick",  "emoji": "💧", "active": False, "claims": 0, "accounts": []},
        {"name": "TonPick",  "emoji": "💎", "active": False, "claims": 0, "accounts": []},
        {"name": "BchPick",  "emoji": "🟤", "active": False, "claims": 0, "accounts": []},
    ]

def save_cranes():
    ensure_data_dir()
    with open(CRANES_FILE, "w", encoding="utf-8") as f:
        json.dump(CRANES, f, indent=2, ensure_ascii=False)

USER_SETTINGS = load_user_settings()
CRANES = load_cranes()
BOT_USERNAME = ""
running_claimers = {}

# ------------------- HELPER FUNCTIONS -------------------
def get_crane(name: str):
    return next((c for c in CRANES if c["name"] == name), None)

def parse_cookie_string(cookie_str: str) -> str:
    """Cookie stringni to‘g‘ri formatga keltirish (key=value; key=value)"""
    # Hech qanday o‘zgartirish kerak emas, aynan shu formatda ishlatamiz
    return cookie_str.strip()

def get_csrf_from_cookie(cookie_str: str) -> Optional[str]:
    """Cookie string ichidan csrf_cookie_name qiymatini olish"""
    cookie = SimpleCookie()
    cookie.load(cookie_str)
    if "csrf_cookie_name" in cookie:
        return cookie["csrf_cookie_name"].value
    return None

def build_keyboard(user_id: int):
    btns = []
    row = []
    for c in CRANES:
        icon = "🟢" if c["active"] else "⚠️"
        row.append(InlineKeyboardButton(text=f"{icon} {c['name']}", callback_data=f"crane_{c['name']}"))
        if len(row) == 2:
            btns.append(row); row = []
    if row: btns.append(row)
    btns.append([InlineKeyboardButton(text=get_text(user_id, "balance"), callback_data="balance")])
    btns.append([InlineKeyboardButton(text=get_text(user_id, "subscription"), callback_data="subscription")])
    btns.append([InlineKeyboardButton(text=get_text(user_id, "invite_friend"), callback_data="invite")])
    btns.append([InlineKeyboardButton(text=get_text(user_id, "settings"), callback_data="settings"), InlineKeyboardButton(text="🔄", callback_data="refresh")])
    return InlineKeyboardMarkup(inline_keyboard=btns)

def build_crane_keyboard(crane_name: str, user_id: int):
    crane = get_crane(crane_name)
    accounts = crane.get("accounts", []) if crane else []
    btns = []
    for idx, acc in enumerate(accounts):
        key = f"{user_id}_{crane_name}_{idx}"
        is_run = key in running_claimers and not running_claimers[key].done()
        btns.append([InlineKeyboardButton(text=f"{'⏹️ Stop' if is_run else '▶️ Start'} {acc['label']}", callback_data=f"toggle_{crane_name}_{idx}")])
    btns.append([InlineKeyboardButton(text=get_text(user_id, "add_account"), callback_data=f"add_account_{crane_name}")])
    btns.append([InlineKeyboardButton(text=get_text(user_id, "back"), callback_data="back_main")])
    return InlineKeyboardMarkup(inline_keyboard=btns)

def crane_panel_text(crane: dict, user_id: int) -> str:
    accs = crane.get("accounts", [])
    text = f"{crane['emoji']} <b>{crane['name']}</b>\n📊 {crane['claims']} claims\n<b>Accounts:</b>\n"
    if accs:
        for a in accs:
            text += f"  {'🟢' if a.get('active') else '🔴'} {a['label']} — {a['email']}\n"
    else:
        text += "  No accounts\n"
    return text

def build_settings_text(user_id: int) -> str:
    api_key = USER_SETTINGS.get(user_id, {}).get("api_key", "")
    key_disp = f"✅ {api_key[:8]}..." if api_key else "❌ Not set"
    return f"⚙️ Settings\n\n🔑 API Key: {key_disp}\n\nSet your Xevil API key to start claiming."

def build_settings_keyboard(user_id: int):
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔑 Set API Key", callback_data="set_api_key")],
        [InlineKeyboardButton(text="🌐 Language", callback_data="set_language")],
        [InlineKeyboardButton(text="◀️ Back", callback_data="back_main")]
    ])

# ------------------- CLAIMER (FIXED COOKIE HANDLING) -------------------
CRANE_CONFIG = {
    "TronPick": {"host": "https://tronpick.io/", "type": "recaptcha", "key": "6LeBFBclAAAAANoZIrwXU1cPgYDDM7f1ehHpzXWj", "field": "g-recaptcha-response"},
    "LitePick": {"host": "https://litepick.io/", "type": "turnstile", "key": "0x4AAAAAAA0-UWDHOKP0OrgS", "field": "c_captcha_response", "clbt": 1},
    "DogePick": {"host": "https://dogepick.io/", "type": "recaptcha", "key": "6LfVA0obAAAAAI8bLZBdotcvg-ms4heUAP1ebfjO", "field": "g-recaptcha-response", "clbt": 1},
    "PolPick":  {"host": "https://polpick.io/", "type": "recaptcha", "key": "6LcHOR8rAAAAAFBzOKHRFY6yLoilRi-JyGnQdUtq", "field": "g-recaptcha-response", "clbt": 1},
    "BnbPick":  {"host": "https://bnbpick.io/", "type": "turnstile", "key": "0x4AAAAAAA0_O3uScCqtpqXl", "field": "c_captcha_response", "clbt": 1},
    "SolPick":  {"host": "https://solpick.io/", "type": "recaptcha", "key": "6LdfNx8rAAAAAIkedgGnuX6TIRANDEDA2fsIjx3s", "field": "g-recaptcha-response"},
    "SuiPick":  {"host": "https://suipick.io/", "type": "turnstile", "key": "0x4AAAAAABgtwLBJbn9NePjw", "field": "c_captcha_response"},
    "TonPick":  {"host": "https://tonpick.game/", "type": "turnstile", "key": "0x4AAAAAAA1JQuZADVDIzQ65", "field": "c_captcha_response", "clbt": 1},
    "BchPick":  {"host": "https://bchpick.io/", "type": "turnstile", "key": "0x4AAAAAADexuS24rGq6WGDh", "field": "c_captcha_response", "clbt": 1},
}

class XevilSolver:
    def __init__(self, apikey: str):
        self.apikey = f"{apikey}|SOFTID1204538927"
    async def solve(self, method: str, sitekey: str, pageurl: str) -> Optional[str]:
        async with aiohttp.ClientSession() as s:
            params = {"key": self.apikey, "json": 1, "method": method, "sitekey": sitekey, "pageurl": pageurl}
            try:
                async with s.get("https://sctg.xyz/in.php", params=params) as r:
                    data = await r.json()
                    if not data.get("status"): return None
                    cid = data["request"]
            except: return None
            for _ in range(30):
                await asyncio.sleep(3)
                try:
                    async with s.get("https://sctg.xyz/res.php", params={"key": self.apikey, "action": "get", "id": cid, "json": 1}) as r:
                        data = await r.json()
                        if data.get("status"): return data["request"]
                        if data.get("request") != "CAPCHA_NOT_READY": return None
                except: continue
            return None

class Claimer:
    def __init__(self, uid, crane, acc_idx, cookie_str, ua, apikey, bot):
        self.uid, self.crane, self.acc_idx = uid, crane, acc_idx
        self.cookie_str = cookie_str
        self.ua = ua
        self.solver = XevilSolver(apikey)
        self.bot = bot
        self._stop = False
    def stop(self): self._stop = True
    async def run(self):
        cfg = CRANE_CONFIG.get(self.crane)
        if not cfg:
            await self.bot.send_message(self.uid, f"❌ No config for {self.crane}")
            return
        host = cfg["host"]
        # Prepare Cookie header properly
        cookie_header = self.cookie_str
        headers = {
            "Host": host.split("//")[1].rstrip("/"),
            "Cookie": cookie_header,
            "X-Requested-With": "XMLHttpRequest",
            "User-Agent": self.ua,
        }
        async with aiohttp.ClientSession(headers=headers) as sess:
            while not self._stop:
                try:
                    await self.bot.send_message(self.uid, f"🔄 {self.crane} claim starting...")
                    # Get CSRF token from cookie (previously stored)
                    csrf = get_csrf_from_cookie(self.cookie_str)
                    if not csrf:
                        await self.bot.send_message(self.uid, "❌ csrf_cookie_name not found in cookie. Check cookie format.")
                        break
                    # Solve captcha
                    cap_type = cfg["type"]
                    sitekey = cfg["key"]
                    await self.bot.send_message(self.uid, f"🔐 Solving {cap_type} captcha...")
                    if cap_type == "turnstile":
                        cap = await self.solver.solve("turnstile", sitekey, host+"faucet.php")
                    else:
                        cap = await self.solver.solve("userrecaptcha", sitekey, host+"faucet.php")
                    if not cap:
                        await self.bot.send_message(self.uid, "❌ Captcha failed. Check API key balance.")
                        break
                    # Submit claim
                    data = {
                        "action": "claim_hourly_faucet",
                        "csrf_test_name": csrf,
                        cfg["field"]: cap,
                        "g-recaptcha-response": "null",
                        "h-captcha-response": "null",
                    }
                    if cfg.get("clbt"): data["clbt"] = "1"
                    async with sess.post(host+"process.php", data=data) as resp:
                        res = await resp.json()
                        if res.get("ret"):
                            reward = res.get("num", 0)
                            # Update user balance (deduct $0.01)
                            if self.uid not in USER_SETTINGS:
                                USER_SETTINGS[self.uid] = {"balance": 0, "total_spent": 0}
                            USER_SETTINGS[self.uid]["balance"] = USER_SETTINGS[self.uid].get("balance", 0) - 0.01
                            USER_SETTINGS[self.uid]["total_spent"] = USER_SETTINGS[self.uid].get("total_spent", 0) + 0.01
                            save_user_settings()
                            crane_obj = get_crane(self.crane)
                            if crane_obj:
                                crane_obj["claims"] = crane_obj.get("claims", 0) + 1
                                save_cranes()
                            await self.bot.send_message(self.uid, f"✅ Claimed {reward} from {self.crane} (-$0.01)")
                        else:
                            err = res.get("mes", "Unknown error")
                            await self.bot.send_message(self.uid, f"❌ Claim failed: {err}")
                            if "login" in err.lower() or "expired" in err.lower():
                                await self.bot.send_message(self.uid, "⚠️ Cookie expired. Please re-add account.")
                                break
                    # Wait 1 hour
                    for _ in range(3600):
                        if self._stop: break
                        await asyncio.sleep(1)
                except asyncio.CancelledError:
                    break
                except Exception as e:
                    await self.bot.send_message(self.uid, f"⚠️ Error: {str(e)}")
                    await asyncio.sleep(60)

# ------------------- FSM STATES -------------------
class AddAccount(StatesGroup):
    email = State()
    password = State()
    cookies = State()
    ua = State()

class SetApiKey(StatesGroup):
    key = State()

# ------------------- BOT HANDLERS -------------------
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher(storage=MemoryStorage())

@dp.message(CommandStart())
async def start(m: Message):
    uid = m.from_user.id
    if uid not in USER_SETTINGS:
        USER_SETTINGS[uid] = {"language": "en", "balance": 0, "total_spent": 0}
        save_user_settings()
    await m.answer("RIPPERBOT", reply_markup=build_keyboard(uid))

@dp.callback_query(F.data == "refresh")
async def refresh(c: CallbackQuery):
    await c.message.delete()
    await c.message.answer("Menu", reply_markup=build_keyboard(c.from_user.id))
    await c.answer()

@dp.callback_query(F.data == "back_main")
async def back_main(c: CallbackQuery):
    await c.message.delete()
    await c.message.answer("Menu", reply_markup=build_keyboard(c.from_user.id))
    await c.answer()

@dp.callback_query(F.data.startswith("crane_"))
async def crane_panel(c: CallbackQuery):
    crane_name = c.data.split("_")[1]
    crane = get_crane(crane_name)
    if not crane:
        await c.answer("Not found")
        return
    await c.message.edit_text(crane_panel_text(crane, c.from_user.id), parse_mode="HTML", reply_markup=build_crane_keyboard(crane_name, c.from_user.id))
    await c.answer()

@dp.callback_query(F.data.startswith("add_account_"))
async def add_acc_start(c: CallbackQuery, state: FSMContext):
    crane_name = c.data.split("_")[2]
    await state.update_data(crane=crane_name)
    await state.set_state(AddAccount.email)
    await c.message.delete()
    await c.message.answer(get_text(c.from_user.id, "send_email"), reply_markup=InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="❌ Cancel", callback_data="cancel_add")]]))
    await c.answer()

@dp.message(AddAccount.email)
async def acc_email(m: Message, state: FSMContext):
    await state.update_data(email=m.text.strip())
    await state.set_state(AddAccount.password)
    await m.answer(get_text(m.from_user.id, "send_password"), reply_markup=InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="❌ Cancel", callback_data="cancel_add")]]))

@dp.message(AddAccount.password)
async def acc_pass(m: Message, state: FSMContext):
    await state.update_data(password=m.text.strip())
    await state.set_state(AddAccount.cookies)
    await m.answer(get_text(m.from_user.id, "cookies_required"), reply_markup=InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="❌ Cancel", callback_data="cancel_add")]]))

@dp.message(AddAccount.cookies)
async def acc_cookie(m: Message, state: FSMContext):
    await state.update_data(cookies=m.text.strip())
    await state.set_state(AddAccount.ua)
    await m.answer(get_text(m.from_user.id, "ua_required"), reply_markup=InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="❌ Cancel", callback_data="cancel_add")]]))

@dp.message(AddAccount.ua)
async def acc_ua(m: Message, state: FSMContext):
    await state.update_data(ua=m.text.strip())
    data = await state.get_data()
    crane_name = data["crane"]
    crane = get_crane(crane_name)
    if crane:
        label = f"Acc{len(crane['accounts'])+1}"
        crane["accounts"].append({
            "label": label,
            "email": data["email"],
            "password": data["password"],
            "cookies": data["cookies"],
            "ua": data["ua"],
            "active": True
        })
        crane["active"] = True
        save_cranes()
        await m.answer(f"✅ {label} added!", reply_markup=build_keyboard(m.from_user.id))
    else:
        await m.answer("Error")
    await state.clear()

@dp.callback_query(F.data == "cancel_add")
async def cancel_add(c: CallbackQuery, state: FSMContext):
    await state.clear()
    await c.message.delete()
    await c.message.answer("Cancelled", reply_markup=build_keyboard(c.from_user.id))
    await c.answer()

@dp.callback_query(F.data.startswith("toggle_"))
async def toggle_claimer(c: CallbackQuery):
    uid = c.from_user.id
    _, crane_name, idx_str = c.data.split("_")
    idx = int(idx_str)
    crane = get_crane(crane_name)
    if not crane or idx >= len(crane["accounts"]):
        await c.answer("Not found")
        return
    acc = crane["accounts"][idx]
    key = f"{uid}_{crane_name}_{idx}"
    if key in running_claimers and not running_claimers[key].done():
        running_claimers[key].cancel()
        del running_claimers[key]
        await c.answer("⏹️ Stopped")
    else:
        apikey = USER_SETTINGS.get(uid, {}).get("api_key", "")
        if not apikey:
            await c.answer(get_text(uid, "api_key_not_set"), show_alert=True)
            return
        cookie_str = acc.get("cookies", "")
        ua = acc.get("ua", "")
        if not cookie_str or not ua:
            await c.answer("❌ Cookie or UA missing. Delete and re-add account.", show_alert=True)
            return
        claimer = Claimer(uid, crane_name, idx, cookie_str, ua, apikey, bot)
        task = asyncio.create_task(claimer.run())
        running_claimers[key] = task
        await c.answer("▶️ Started")
    # Refresh panel
    await c.message.edit_text(crane_panel_text(crane, uid), parse_mode="HTML", reply_markup=build_crane_keyboard(crane_name, uid))

@dp.callback_query(F.data == "settings")
async def settings(c: CallbackQuery):
    await c.message.edit_text(build_settings_text(c.from_user.id), reply_markup=build_settings_keyboard(c.from_user.id))
    await c.answer()

@dp.callback_query(F.data == "set_api_key")
async def set_api_key(c: CallbackQuery, state: FSMContext):
    await state.set_state(SetApiKey.key)
    await c.message.edit_text(get_text(c.from_user.id, "api_key_prompt"), reply_markup=InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="❌ Cancel", callback_data="cancel_settings")]]))
    await c.answer()

@dp.message(SetApiKey.key)
async def save_api_key(m: Message, state: FSMContext):
    uid = m.from_user.id
    if uid not in USER_SETTINGS:
        USER_SETTINGS[uid] = {}
    USER_SETTINGS[uid]["api_key"] = m.text.strip()
    save_user_settings()
    await state.clear()
    await m.answer("✅ API Key saved!", reply_markup=build_keyboard(uid))

@dp.callback_query(F.data == "set_language")
async def set_lang(c: CallbackQuery):
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🇬🇧 English", callback_data="lang_en")],
        [InlineKeyboardButton(text="🇺🇿 O'zbek", callback_data="lang_uz")],
        [InlineKeyboardButton(text="◀️ Back", callback_data="settings")]
    ])
    await c.message.edit_text(get_text(c.from_user.id, "select_language"), reply_markup=kb)
    await c.answer()

@dp.callback_query(F.data.startswith("lang_"))
async def set_lang_confirm(c: CallbackQuery):
    lang = c.data.split("_")[1]
    uid = c.from_user.id
    if uid not in USER_SETTINGS:
        USER_SETTINGS[uid] = {}
    USER_SETTINGS[uid]["language"] = lang
    save_user_settings()
    await c.message.delete()
    await c.message.answer(get_text(uid, "language_changed"), reply_markup=build_keyboard(uid))
    await c.answer()

@dp.callback_query(F.data == "cancel_settings")
async def cancel_settings(c: CallbackQuery, state: FSMContext):
    await state.clear()
    await c.message.edit_text(build_settings_text(c.from_user.id), reply_markup=build_settings_keyboard(c.from_user.id))
    await c.answer()

@dp.callback_query(F.data == "balance")
async def balance(c: CallbackQuery):
    uid = c.from_user.id
    bal = USER_SETTINGS.get(uid, {}).get("balance", 0)
    dep = USER_SETTINGS.get(uid, {}).get("total_deposited", 0)
    spent = USER_SETTINGS.get(uid, {}).get("total_spent", 0)
    text = f"💰 Balance: ${bal}\n📥 Deposited: ${dep}\n📤 Spent: ${spent}\n(Each claim costs $0.01)"
    await c.message.edit_text(text, reply_markup=InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="◀️ Back", callback_data="back_main")]]))
    await c.answer()

@dp.callback_query(F.data == "subscription")
async def subscription(c: CallbackQuery):
    text = "Subscription plans:\nMonthly $15 (50 accounts)\nClaim pack $1 (1200 claims)"
    await c.message.edit_text(text, reply_markup=InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="◀️ Back", callback_data="back_main")]]))
    await c.answer()

@dp.callback_query(F.data == "invite")
async def invite(c: CallbackQuery):
    uid = c.from_user.id
    ref_link = f"https://t.me/{BOT_USERNAME}?start=ref_{uid}"
    text = f"Referral link:\n{ref_link}\nYou get +16 claims, friend gets +8"
    await c.message.edit_text(text, reply_markup=InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="◀️ Back", callback_data="back_main")]]))
    await c.answer()

# ------------------- STARTUP -------------------
async def on_startup():
    global BOT_USERNAME
    me = await bot.get_me()
    BOT_USERNAME = me.username
    await bot.delete_webhook(drop_pending_updates=True)

async def shutdown():
    for t in running_claimers.values():
        t.cancel()
    await asyncio.gather(*running_claimers.values(), return_exceptions=True)
    save_user_settings()
    save_cranes()

async def main():
    await on_startup()
    try:
        await dp.start_polling(bot)
    finally:
        await shutdown()

if __name__ == "__main__":
    asyncio.run(main())
