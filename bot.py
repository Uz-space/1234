import asyncio
import logging
import re
import time
import requests
from typing import Optional, Dict

import cloudscraper
from aiogram import Bot, Dispatcher, F
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.filters import CommandStart, Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.storage.memory import MemoryStorage

logging.basicConfig(level=logging.INFO)

BOT_TOKEN = "8952550187:AAH87AXq35FuN8AoAkp1IEuT4uqWnpJgNug"  # O'z tokeningizni qo'ying

# ─── Tillar (faqat o'zbek) ──────────────────────────────────────────────────
TEXTS = {
    "uz": {
        "main_title": "LITEPICK & TRONPICK BOT",
        "api_connected": "✅",
        "api_disconnected": "❌",
        "live_log": "📡 JONLI LOG",
        "no_claims": "⏳ Hali hech qanday claim yo‘q...",
        "crane_active": "✅",
        "crane_inactive": "⚠️",
        "add_account": "➕ Hisob qo‘shish",
        "claim_now": "▶️ Claimni boshlash",
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
        "settings_note": "API kalit va hostni sozlang.",
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
        "cookies_optional": "🍪 Cookies (ixtiyoriy):",
        "cookies_instruction": "F12 > Konsol > <code>document.cookie</code>",
        "cookies_skipped": "🍪 Cookies: ⏭️ O‘tkazib yuborildi",
        "ua_optional": "🌐 User-Agent (ixtiyoriy):",
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
        "api_key_prompt": "🔑 <b>API kaliti</b>\n\nAPI kalitingizni yuboring:\n\n/cancel bekor qilish.",
        "api_host_prompt": "🌐 <b>API host</b>\n\nAPI hostni yuboring (masalan <code>sctg.xyz</code>):",
        "claim_started": "⏳ Claim boshlandi...",
        "claim_success": "✅ Claim muvaffaqiyatli!",
        "claim_failed": "❌ Claim muvaffaqiyatsiz",
        "no_active_accounts": "⚠️ Claim qilish uchun faol hisob yo‘q.",
        "claim_log": "📌 Claim logi:\n{log}",
        "auto_claim_started": "🔄 24/7 avtomatik claim ishga tushdi!",
        "auto_claim_stopped": "⏹ 24/7 avtomatik claim to‘xtatildi.",
        "toggle_auto": "🔄 24/7 yoqish/o‘chirish",
        "auto_on": "✅ 24/7 yoqilgan",
        "auto_off": "❌ 24/7 o‘chirilgan",
    }
}

LANG = "uz"

def get_text(key: str, **kwargs) -> str:
    text = TEXTS[LANG].get(key, key)
    if kwargs:
        return text.format(**kwargs)
    return text

# ─── Kranlar (LitePick va TronPick) ────────────────────────────────────────
CRANES = [
    {
        "name": "LitePick",
        "emoji": "🌕",
        "host": "https://litepick.io/",
        "captcha_type": "turnstile",
        "sitekey": "0x4AAAAAAA0-UWDHOKP0OrgS",
        "active": False,
        "claims": 0,
        "max_claims": "∞",
        "balance": "0",
        "accounts": []
    },
    {
        "name": "TronPick",
        "emoji": "🔴",
        "host": "https://tronpick.io/",
        "captcha_type": "recaptcha",
        "sitekey": "6LeBFBclAAAAANoZIrwXU1cPgYDDM7f1ehHpzXWj",
        "active": False,
        "claims": 0,
        "max_claims": "∞",
        "balance": "0",
        "accounts": []
    }
]

API_STATE = {
    "connected": False,
    "domain": "sctg.xyz",
    "plan": "Trial",
    "accounts": 0,
    "total_claims": 0,
}

LIVE_LOG = {"crane_emoji": "", "crane_name": "", "log_text": ""}
MY_SETTINGS = {"api_key": "", "api_host": "sctg.xyz"}

# 24/7 holati
AUTO_CLAIM = {
    "enabled": False,
    "task": None,
}

# ─── FSM States ──────────────────────────────────────────────────────────────
class AddAccount(StatesGroup):
    email    = State()
    password = State()
    cookies  = State()
    ua       = State()

class SettingsState(StatesGroup):
    api_key  = State()
    api_host = State()

# ─── Helperlar ───────────────────────────────────────────────────────────────
def get_crane(name: str):
    return next((c for c in CRANES if c["name"] == name), None)

def cancel_keyboard():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=get_text("cancel"), callback_data="cancel_add")]
    ])

def skip_cookies_keyboard():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=get_text("cancel"), callback_data="cancel_add")],
        [InlineKeyboardButton(text=get_text("skip_cookies"), callback_data="skip_cookies")],
    ])

def skip_ua_keyboard():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=get_text("cancel"), callback_data="cancel_add")],
        [InlineKeyboardButton(text=get_text("skip_ua"), callback_data="skip_ua")],
    ])

# ─── PICK CLIENT (LitePick va TronPick uchun) ─────────────────────────────
class PickClient:
    def __init__(self, host: str, cookie: str, user_agent: str,
                 captcha_type: str, sitekey: str,
                 api_key: str = "", api_host: str = "sctg.xyz"):
        self.host = host.rstrip('/')
        self.cookie = cookie
        self.user_agent = user_agent
        self.captcha_type = captcha_type   # 'turnstile' yoki 'recaptcha'
        self.sitekey = sitekey
        self.api_key = api_key
        self.api_host = api_host

        self.scraper = cloudscraper.create_scraper()
        self.scraper.headers.update({
            "User-Agent": user_agent,
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.5",
            "Accept-Encoding": "gzip, deflate, br",
            "Connection": "keep-alive",
            "Upgrade-Insecure-Requests": "1",
        })
        self.scraper.cookies.update(self._parse_cookie(cookie))

    def _parse_cookie(self, cookie_str: str) -> Dict:
        cookies = {}
        for item in cookie_str.split(';'):
            item = item.strip()
            if '=' in item:
                key, val = item.split('=', 1)
                cookies[key] = val
        return cookies

    def _headers(self) -> Dict:
        return {
            "Host": self.host.replace('https://', ''),
            "Cookie": self.cookie,
            "X-Requested-With": "XMLHttpRequest",
            "User-Agent": self.user_agent,
        }

    def _get_csrf(self) -> str:
        for item in self.cookie.split(';'):
            item = item.strip()
            if item.startswith("csrf_cookie_name="):
                return item.split('=', 1)[1]
        return ""

    def dashboard(self) -> Dict:
        url = f"{self.host}/"
        resp = self.scraper.get(url, headers=self._headers())
        html = resp.text

        data = {
            "cloudflare": 1 if "Just a moment..." in html else 0,
            "Login": 1 if "login_button" not in html else 0
        }
        match = re.search(r'&username=([^&]+)', html)
        data["Username"] = match.group(1) if match else "Unknown"
        match = re.search(r'class="drop_down_header_text user_balance">([^<]+)<', html)
        data["Balance"] = match.group(1).strip() if match else "0"
        match = re.search(r'Your level is  <b>([^<]+)</b>', html)
        level = match.group(1) if match else "0"
        match2 = re.search(r'aria-valuemax="100">([^<]+)<', html)
        progress = match2.group(1).strip() if match2 else "0%"
        data["Level"] = f"{level} {progress}"
        matches = re.findall(r'<b id="(total_wagered|wagering_target)">([^<]+)</b>', html)
        w_data = {k: v for k, v in matches}
        data["Total Wagered"] = w_data.get("total_wagered", "0")
        data["Wagering Target"] = w_data.get("wagering_target", "0")
        return data

    def _solve_captcha(self, pageurl: str) -> Optional[str]:
        if not self.api_key:
            return None
        # Provider: multibot yoki xevil
        if "multibot" in self.api_host.lower():
            base_in = "http://api.multibot.in/in.php"
            base_res = "http://api.multibot.in/res.php"
            key = self.api_key
        else:
            base_in = f"https://{self.api_host}/in.php"
            base_res = f"https://{self.api_host}/res.php"
            key = f"{self.api_key}|SOFTID1204538927"

        # Metodni aniqlash
        method_map = {
            "turnstile": "turnstile",
            "recaptcha": "userrecaptcha",
            "hcaptcha": "hcaptcha"
        }
        method = method_map.get(self.captcha_type, "turnstile")

        params = {
            "key": key,
            "method": method,
            "pageurl": pageurl,
            "sitekey": self.sitekey,
            "json": 1
        }
        try:
            resp = requests.get(base_in, params=params, timeout=30)
            data = resp.json()
        except Exception as e:
            logging.error(f"Captcha in_api error: {e}")
            return None

        if not data.get("status"):
            logging.error(f"Captcha error: {data}")
            return None

        captcha_id = data.get("request")
        if not captcha_id:
            return None

        for _ in range(30):
            time.sleep(3)
            res_params = {"key": key, "action": "get", "id": captcha_id, "json": 1}
            try:
                resp2 = requests.get(base_res, params=res_params, timeout=30)
                res_data = resp2.json()
            except Exception as e:
                logging.error(f"Captcha res error: {e}")
                continue

            if res_data.get("status"):
                return res_data.get("request")
            if res_data.get("request") == "CAPCHA_NOT_READY":
                continue
            else:
                logging.error(f"Captcha final error: {res_data}")
                return None
        return None

    def claim_hourly(self) -> Dict:
        url = f"{self.host}/faucet.php"
        resp = self.scraper.get(url, headers=self._headers())
        html = resp.text

        if "Just a moment..." in html:
            return {"success": False, "msg": "Cloudflare detected"}

        if "select_hourly_faucet" in html:
            tmr_match = re.search(r'select_hourly_faucet\|([^|]+)\|', html)
            if tmr_match:
                return {"success": False, "msg": f"Kuting {tmr_match.group(1)} soniya"}

        csrf = self._get_csrf()

        # Captcha yechish
        cap_token = None
        if self.captcha_type in ("turnstile", "recaptcha", "hcaptcha"):
            cap_token = self._solve_captcha(url)

        if not cap_token:
            return {"success": False, "msg": "Captcha yechilmadi"}

        # POST ma'lumotlarini tayyorlash
        data = {
            "action": "claim_hourly_faucet",
            "csrf_test_name": csrf,
        }
        if self.captcha_type == "hcaptcha":
            data["h-captcha-response"] = cap_token
            data["g-recaptcha-response"] = "null"
        elif self.captcha_type == "recaptcha":
            data["g-recaptcha-response"] = cap_token
            data["h-captcha-response"] = "null"
        elif self.captcha_type == "turnstile":
            data["c_captcha_response"] = cap_token
            data["clbt"] = "1"
            data["g-recaptcha-response"] = "null"
            data["h-captcha-response"] = "null"
        else:
            data["g-recaptcha-response"] = "null"
            data["h-captcha-response"] = "null"

        post_headers = self._headers()
        post_headers["Content-Type"] = "application/x-www-form-urlencoded"

        process_url = f"{self.host}/process.php"
        resp2 = self.scraper.post(process_url, data=data, headers=post_headers)
        try:
            result = resp2.json()
        except:
            return {"success": False, "msg": "Noto'g'ri javob"}

        if result.get("ret"):
            return {"success": True, "msg": result.get("mes", "Claim qilindi"), "num": result.get("num")}
        else:
            return {"success": False, "msg": result.get("mes", "Noma'lum xato")}

    def claim_bonus(self) -> Dict:
        url = f"{self.host}/faucet.php"
        resp = self.scraper.get(url, headers=self._headers())
        html = resp.text

        if "Just a moment..." in html:
            return {"success": False, "msg": "Cloudflare detected"}

        bonus_match = re.search(r'<span id="free_spins">([^<]+)</span>', html)
        if not bonus_match or bonus_match.group(1).strip() == "0":
            return {"success": False, "msg": "Bonus mavjud emas"}

        csrf = self._get_csrf()
        data = {"action": "claim_bonus_faucet", "csrf_test_name": csrf}
        post_headers = self._headers()
        post_headers["Content-Type"] = "application/x-www-form-urlencoded"

        process_url = f"{self.host}/process.php"
        resp2 = self.scraper.post(process_url, data=data, headers=post_headers)
        try:
            result = resp2.json()
        except:
            return {"success": False, "msg": "Noto'g'ri javob"}

        if result.get("ret"):
            return {"success": True, "msg": result.get("mes", "Bonus olindi"), "num": result.get("num")}
        else:
            return {"success": False, "msg": result.get("mes", "Noma'lum xato")}

# ─── UI / Menyu ──────────────────────────────────────────────────────────────
def build_message_text() -> str:
    lines = []
    for c in CRANES:
        name_upper = c["name"].upper()
        if c["active"]:
            active_mark = get_text("crane_active")
            line = f"{c['emoji']} {name_upper} {active_mark} [∞] ({c['claims']}/{c['max_claims']})"
        else:
            inactive_mark = get_text("crane_inactive")
            line = f"{c['emoji']} {name_upper} {inactive_mark} [∞] (0/{c['max_claims']})"
        lines.append(line)

    text = "\n".join(lines)
    text += "\n\n"

    api_icon = get_text("api_connected") if API_STATE["connected"] else get_text("api_disconnected")
    text += f"🔑 API: {api_icon} ({API_STATE['domain']})\n"

    if API_STATE["connected"] and API_STATE["accounts"] != 0:
        acc_str = "∞" if API_STATE["accounts"] == -1 else str(API_STATE["accounts"])
        claims_str = str(API_STATE["total_claims"]) if API_STATE["total_claims"] > 0 else "0"
        text += f"📓 {API_STATE['plan']} | {acc_str} accounts | {claims_str} claims\n"

    auto_status = get_text("auto_on") if AUTO_CLAIM["enabled"] else get_text("auto_off")
    text += f"\n🔄 24/7: {auto_status}\n"

    text += f"\n{get_text('live_log')}\n────────────────\n"
    if LIVE_LOG["log_text"]:
        text += f"{LIVE_LOG['crane_emoji']} {LIVE_LOG['crane_name'].upper()}\n"
        text += LIVE_LOG["log_text"]
    else:
        text += get_text("no_claims")

    return text

def build_keyboard() -> InlineKeyboardMarkup:
    buttons = []
    row = []
    for c in CRANES:
        icon = get_text("crane_active") if c["active"] else get_text("crane_inactive")
        btn = InlineKeyboardButton(text=f"{icon} {c['name']}", callback_data=f"crane_{c['name']}")
        row.append(btn)
        if len(row) == 2:
            buttons.append(row)
            row = []
    if row:
        buttons.append(row)

    buttons.append([InlineKeyboardButton(text=get_text("balance"), callback_data="balance")])
    buttons.append([InlineKeyboardButton(text=get_text("subscription"), callback_data="subscription")])
    buttons.append([InlineKeyboardButton(text=get_text("invite_friend"), callback_data="invite")])
    buttons.append([
        InlineKeyboardButton(text=get_text("settings"), callback_data="settings"),
        InlineKeyboardButton(text=get_text("refresh"), callback_data="refresh"),
    ])
    buttons.append([InlineKeyboardButton(text=get_text("toggle_auto"), callback_data="toggle_auto")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)

def build_crane_keyboard(crane_name: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=get_text("add_account"), callback_data=f"add_account_{crane_name}")],
        [InlineKeyboardButton(text=get_text("claim_now"), callback_data=f"claim_crane_{crane_name}")],
        [InlineKeyboardButton(text=get_text("back"), callback_data="back_main")],
    ])

def crane_panel_text(crane: dict) -> str:
    accounts = crane.get("accounts", [])
    acc_count = len(accounts)
    active_count = sum(1 for a in accounts if a.get("active", False))

    text = (
        f"{crane['emoji']} <b>{crane['name']} — {get_text('control_panel')}</b>\n"
        f"📊 {crane['claims']} {get_text('claims')} | 💰 {crane['balance']}\n"
        f"▶️ <b>{get_text('active_accounts')} ({active_count}/{acc_count}):</b>\n"
    )
    if accounts:
        for acc in accounts:
            status = "🟢" if acc.get("active") else "🔴"
            text += f"  {status} {acc['label']} — {acc['email']}\n"
    else:
        text += f"<i>{get_text('no_accounts')}</i>"
    return text

def build_settings_text() -> str:
    api_key = MY_SETTINGS.get("api_key", "")
    api_host = MY_SETTINGS.get("api_host", "sctg.xyz")

    if api_key:
        key_display = f"{get_text('api_key_set')} {api_key[:8]}..."
    else:
        key_display = get_text("api_key_not_set")

    return (
        f"{get_text('settings_title')}\n\n"
        f"{get_text('api_key_label')}: {key_display}\n"
        f"{get_text('api_host_label')}: <a href='http://{api_host}'>{api_host}</a>\n\n"
        f"<i>{get_text('settings_note')}</i>"
    )

def build_settings_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=get_text("api_key_label"), callback_data="set_api_key")],
        [InlineKeyboardButton(text=get_text("api_host_label"), callback_data="set_api_host")],
        [InlineKeyboardButton(text=get_text("back"), callback_data="back_main")],
    ])

# ─── Bot va Dispatcher ───────────────────────────────────────────────────────
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher(storage=MemoryStorage())

# ─── 24/7 avtomatik claim ──────────────────────────────────────────────────
async def auto_claim_loop():
    """Har bir kran uchun har soatda claim qiladi"""
    while AUTO_CLAIM["enabled"]:
        for crane in CRANES:
            if not crane["accounts"]:
                continue
            active_accounts = [acc for acc in crane["accounts"] if acc.get("active")]
            if not active_accounts:
                continue

            api_key = MY_SETTINGS.get("api_key", "")
            api_host = MY_SETTINGS.get("api_host", "sctg.xyz")

            log_lines = []
            for acc in active_accounts:
                email = acc.get("email")
                cookies = acc.get("cookies")
                ua = acc.get("ua")
                if not cookies or not ua:
                    log_lines.append(f"❌ {email}: cookies/ua yo'q")
                    continue

                client = PickClient(
                    host=crane["host"],
                    cookie=cookies,
                    user_agent=ua,
                    captcha_type=crane["captcha_type"],
                    sitekey=crane["sitekey"],
                    api_key=api_key,
                    api_host=api_host
                )

                # Hourly claim
                result = await asyncio.to_thread(client.claim_hourly)
                if result.get("success"):
                    num = result.get("num", "?")
                    msg = result.get("msg", "Claim qilindi")
                    log_lines.append(f"✅ {email}: {msg} (num: {num})")
                    crane["claims"] += 1
                    try:
                        dash = await asyncio.to_thread(client.dashboard)
                        crane["balance"] = dash.get("Balance", "0")
                    except:
                        pass
                else:
                    log_lines.append(f"❌ {email}: {result.get('msg', 'failed')}")

                # Bonus
                bonus_result = await asyncio.to_thread(client.claim_bonus)
                if bonus_result.get("success"):
                    log_lines.append(f"🎁 {email}: bonus {bonus_result.get('msg', '')}")
                    crane["claims"] += 1

                await asyncio.sleep(2)

            if log_lines:
                LIVE_LOG["crane_emoji"] = crane["emoji"]
                LIVE_LOG["crane_name"] = crane["name"]
                LIVE_LOG["log_text"] = "\n".join(log_lines[-5:])
                crane["active"] = True

        await asyncio.sleep(3600)  # 1 soat

# ─── Handlers ────────────────────────────────────────────────────────────────
@dp.message(CommandStart())
async def cmd_start(message: Message, state: FSMContext):
    await state.clear()
    await message.answer(text=build_message_text(), reply_markup=build_keyboard(), parse_mode="HTML")

@dp.message(Command("cancel"))
async def cmd_cancel(message: Message, state: FSMContext):
    data = await state.get_data()
    crane_name = data.get("crane_name", "")
    await state.clear()
    if crane_name:
        crane = get_crane(crane_name)
        if crane:
            await message.answer(text=crane_panel_text(crane), reply_markup=build_crane_keyboard(crane_name), parse_mode="HTML")
            return
    await message.answer(text=build_message_text(), reply_markup=build_keyboard(), parse_mode="HTML")

@dp.callback_query(F.data == "refresh")
async def cb_refresh(call: CallbackQuery, state: FSMContext):
    await state.clear()
    await call.message.delete()
    await call.message.answer(text=build_message_text(), reply_markup=build_keyboard(), parse_mode="HTML")
    await call.answer(get_text("updated"))

@dp.callback_query(F.data == "back_main")
async def cb_back_main(call: CallbackQuery, state: FSMContext):
    await state.clear()
    await call.message.delete()
    await call.message.answer(text=build_message_text(), reply_markup=build_keyboard(), parse_mode="HTML")
    await call.answer()

@dp.callback_query(F.data.startswith("crane_"))
async def cb_crane(call: CallbackQuery):
    crane_name = call.data.replace("crane_", "")
    crane = get_crane(crane_name)
    if not crane:
        await call.answer(get_text("not_found"), show_alert=True)
        return
    await call.message.delete()
    await call.message.answer(text=crane_panel_text(crane), reply_markup=build_crane_keyboard(crane_name), parse_mode="HTML")
    await call.answer()

# ─── Toggle 24/7 ────────────────────────────────────────────────────────────
@dp.callback_query(F.data == "toggle_auto")
async def cb_toggle_auto(call: CallbackQuery):
    global AUTO_CLAIM
    if AUTO_CLAIM["enabled"]:
        AUTO_CLAIM["enabled"] = False
        if AUTO_CLAIM["task"]:
            AUTO_CLAIM["task"].cancel()
            try:
                await AUTO_CLAIM["task"]
            except asyncio.CancelledError:
                pass
            AUTO_CLAIM["task"] = None
        await call.answer(get_text("auto_claim_stopped"))
    else:
        AUTO_CLAIM["enabled"] = True
        AUTO_CLAIM["task"] = asyncio.create_task(auto_claim_loop())
        await call.answer(get_text("auto_claim_started"))

    await call.message.delete()
    await call.message.answer(text=build_message_text(), reply_markup=build_keyboard(), parse_mode="HTML")

# ─── Claim (bir martalik) ──────────────────────────────────────────────────
@dp.callback_query(F.data.startswith("claim_crane_"))
async def cb_claim_crane(call: CallbackQuery, state: FSMContext):
    crane_name = call.data.replace("claim_crane_", "")
    crane = get_crane(crane_name)
    if not crane:
        await call.answer(get_text("not_found"), show_alert=True)
        return

    active_accounts = [acc for acc in crane["accounts"] if acc.get("active")]
    if not active_accounts:
        await call.answer(get_text("no_active_accounts"), show_alert=True)
        return

    await call.answer(get_text("claim_started"))

    api_key = MY_SETTINGS.get("api_key", "")
    api_host = MY_SETTINGS.get("api_host", "sctg.xyz")

    log_lines = []
    for acc in active_accounts:
        email = acc.get("email")
        cookies = acc.get("cookies")
        ua = acc.get("ua")
        if not cookies or not ua:
            log_lines.append(f"❌ {email}: cookies/ua yo'q")
            continue

        client = PickClient(
            host=crane["host"],
            cookie=cookies,
            user_agent=ua,
            captcha_type=crane["captcha_type"],
            sitekey=crane["sitekey"],
            api_key=api_key,
            api_host=api_host
        )

        result = await asyncio.to_thread(client.claim_hourly)
        if result.get("success"):
            num = result.get("num", "?")
            msg = result.get("msg", "Claim qilindi")
            log_lines.append(f"✅ {email}: {msg} (num: {num})")
            crane["claims"] += 1
            try:
                dash = await asyncio.to_thread(client.dashboard)
                crane["balance"] = dash.get("Balance", "0")
            except:
                pass
        else:
            log_lines.append(f"❌ {email}: {result.get('msg', 'failed')}")

        bonus_result = await asyncio.to_thread(client.claim_bonus)
        if bonus_result.get("success"):
            log_lines.append(f"🎁 {email}: bonus {bonus_result.get('msg', '')}")
            crane["claims"] += 1

        await asyncio.sleep(2)

    LIVE_LOG["crane_emoji"] = crane["emoji"]
    LIVE_LOG["crane_name"] = crane["name"]
    LIVE_LOG["log_text"] = "\n".join(log_lines[-5:])
    if active_accounts:
        crane["active"] = True

    result_text = get_text("claim_log", log="\n".join(log_lines))
    await call.message.delete()
    await call.message.answer(
        text=result_text,
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text=f"◀️ {crane_name}", callback_data=f"crane_{crane_name}")],
            [InlineKeyboardButton(text=get_text("main_menu"), callback_data="back_main")],
        ]),
        parse_mode="HTML"
    )

# ─── Add Account (FSM) ──────────────────────────────────────────────────────
@dp.callback_query(F.data.startswith("add_account_"))
async def cb_add_account(call: CallbackQuery, state: FSMContext):
    crane_name = call.data.replace("add_account_", "")
    crane = get_crane(crane_name)
    if not crane:
        await call.answer(get_text("not_found"), show_alert=True)
        return

    acc_num = len(crane["accounts"]) + 1
    label = f"Account {acc_num}"
    await state.set_state(AddAccount.email)
    await state.update_data(crane_name=crane_name, label=label)

    await call.message.delete()
    await call.message.answer(
        text=(
            f"{crane['emoji']} <b>{get_text('add_account_title', crane=crane_name)}</b>\n\n"
            f"{get_text('label', label=label)}\n\n"
            f"{get_text('send_email')}\n\n"
            f"{get_text('cancel_abort')}"
        ),
        reply_markup=cancel_keyboard(),
        parse_mode="HTML"
    )
    await call.answer()

@dp.message(AddAccount.email)
async def fsm_email(message: Message, state: FSMContext):
    email = message.text.strip()
    await state.update_data(email=email)
    await state.set_state(AddAccount.password)
    await message.answer(
        text=(
            f"{get_text('email_received', email=email)}\n\n"
            f"{get_text('send_password')}\n\n"
            f"{get_text('cancel_abort')}"
        ),
        reply_markup=cancel_keyboard(),
        parse_mode="HTML"
    )

@dp.message(AddAccount.password)
async def fsm_password(message: Message, state: FSMContext):
    password = message.text.strip()
    await state.update_data(password=password)
    await state.set_state(AddAccount.cookies)
    await message.answer(
        text=(
            f"{get_text('password_ok')}\n\n"
            f"{get_text('cookies_optional')}\n\n"
            f"{get_text('cookies_instruction')}\n\n"
            f"{get_text('cancel_abort')}"
        ),
        reply_markup=skip_cookies_keyboard(),
        parse_mode="HTML"
    )

@dp.callback_query(F.data == "skip_cookies")
async def cb_skip_cookies(call: CallbackQuery, state: FSMContext):
    await state.update_data(cookies=None)
    await state.set_state(AddAccount.ua)
    await call.message.edit_text(
        text=(
            f"{get_text('cookies_skipped')}\n\n"
            f"{get_text('ua_optional')}\n\n"
            f"{get_text('ua_instruction')}\n\n"
            f"{get_text('cancel_abort')}"
        ),
        reply_markup=skip_ua_keyboard(),
        parse_mode="HTML"
    )
    await call.answer()

@dp.message(AddAccount.cookies)
async def fsm_cookies(message: Message, state: FSMContext):
    cookies = message.text.strip()
    await state.update_data(cookies=cookies)
    await state.set_state(AddAccount.ua)
    await message.answer(
        text=(
            f"{get_text('cookies_received', len=len(cookies))}\n\n"
            f"{get_text('ua_optional')}\n\n"
            f"{get_text('ua_instruction')}\n\n"
            f"{get_text('cancel_abort')}"
        ),
        reply_markup=skip_ua_keyboard(),
        parse_mode="HTML"
    )

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
            f"{get_text('account_added')}\n\n"
            f"{crane['emoji']} {get_text('account_num', crane=crane_name, num=len(crane['accounts']))}\n"
            f"📝 {label}\n"
            f"📧 <code>{email}</code>\n"
            f"🔑 ✅\n"
            f"{get_text('cookies_status', status='✅' if cookies else '⏭️')}\n"
            f"{get_text('ua_status', status='✅' if ua else '⏭️')}"
        ),
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text=f"◀️ {crane_name}", callback_data=f"crane_{crane_name}")],
            [InlineKeyboardButton(text=get_text("main_menu"), callback_data="back_main")],
        ]),
        parse_mode="HTML"
    )

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
    await call.answer(get_text("cancelled"))

# ─── Settings ────────────────────────────────────────────────────────────────
@dp.callback_query(F.data == "settings")
async def cb_settings(call: CallbackQuery):
    await call.message.delete()
    await call.message.answer(
        text=build_settings_text(),
        reply_markup=build_settings_keyboard(),
        parse_mode="HTML"
    )
    await call.answer()

@dp.callback_query(F.data == "set_api_key")
async def cb_set_api_key(call: CallbackQuery, state: FSMContext):
    await state.set_state(SettingsState.api_key)
    await call.message.edit_text(
        text=get_text("api_key_prompt"),
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text=get_text("cancel"), callback_data="cancel_settings")]
        ]),
        parse_mode="HTML"
    )
    await call.answer()

@dp.callback_query(F.data == "set_api_host")
async def cb_set_api_host(call: CallbackQuery, state: FSMContext):
    await state.set_state(SettingsState.api_host)
    await call.message.edit_text(
        text=get_text("api_host_prompt"),
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text=get_text("cancel"), callback_data="cancel_settings")]
        ]),
        parse_mode="HTML"
    )
    await call.answer()

@dp.callback_query(F.data == "cancel_settings")
async def cb_cancel_settings(call: CallbackQuery, state: FSMContext):
    await state.clear()
    await call.message.edit_text(
        text=build_settings_text(),
        reply_markup=build_settings_keyboard(),
        parse_mode="HTML"
    )
    await call.answer(get_text("cancelled"))

@dp.message(SettingsState.api_key)
async def fsm_api_key(message: Message, state: FSMContext):
    api_key = message.text.strip()
    MY_SETTINGS["api_key"] = api_key
    API_STATE["connected"] = True
    await state.clear()
    await message.answer(
        text=build_settings_text(),
        reply_markup=build_settings_keyboard(),
        parse_mode="HTML"
    )

@dp.message(SettingsState.api_host)
async def fsm_api_host(message: Message, state: FSMContext):
    api_host = message.text.strip()
    MY_SETTINGS["api_host"] = api_host
    API_STATE["domain"] = api_host
    await state.clear()
    await message.answer(
        text=build_settings_text(),
        reply_markup=build_settings_keyboard(),
        parse_mode="HTML"
    )

# ─── Boshqa tugmalar (placeholder) ──────────────────────────────────────────
@dp.callback_query(F.data == "balance")
async def cb_balance(call: CallbackQuery):
    await call.answer("Balans ma'lumotlari tez orada.", show_alert=False)

@dp.callback_query(F.data == "subscription")
async def cb_subscription(call: CallbackQuery):
    await call.answer("Obuna tizimi hozircha ishlamaydi.", show_alert=True)

@dp.callback_query(F.data == "invite")
async def cb_invite(call: CallbackQuery):
    await call.answer("Referal tizimi hozircha ishlamaydi.", show_alert=True)

# ─── Ishga tushirish ─────────────────────────────────────────────────────────
async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
