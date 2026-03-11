# ================= PROXYFXC ULTIMATE BOT =================
# DEVELOPER: @proxyfxc
# VERSION: 4.0 (OSINT + SMS BOMBER + BLACKBOX AI)
# =========================================================

import requests
import json
import sqlite3
import re
import asyncio
import os
import threading
import time
from datetime import datetime
from typing import Dict, Optional, Tuple
from io import BytesIO

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application, CommandHandler,
    CallbackQueryHandler, MessageHandler,
    ContextTypes, filters
)
from telegram.error import TelegramError

# ================= FLASK IMPORTS =================
from flask import Flask, jsonify

# ================= CONFIGURATION =================

BOT_TOKEN = os.environ.get("BOT_TOKEN", "8787228179:AAGy9p-BBOCO29IyWisnjWZIqzwCDH3mtdo")
ADMIN_ID = int(os.environ.get("ADMIN_ID", "8554863978"))
DEVELOPER = "@proxyfxc"

# ================= ALL WORKING APIS =================

# ABBAS APIS (Working)
ABBAS_APIS = {
    "number": "https://abbas-apis.vercel.app/api/num-name?number={}",
    "instagram": "https://abbas-apis.vercel.app/api/instagram?username={}",
    "github": "https://abbas-apis.vercel.app/api/github?username={}",
    "ip": "https://abbas-apis.vercel.app/api/ip?ip={}",
    "pakistan": "https://abbas-apis.vercel.app/api/pakistan?number={}",
    "pan": "https://abbas-apis.vercel.app/api/pan?pan={}",
    "ff_info": "https://abbas-apis.vercel.app/api/ff-info?uid={}",
    "phone": "https://abbas-apis.vercel.app/api/phone?number={}",
    "email": "https://abbas-apis.vercel.app/api/email?mail={}",
    "ff_ban": "https://abbas-apis.vercel.app/api/ff-ban?uid={}",
    "ifsc": "https://abbas-apis.vercel.app/api/ifsc?ifsc={}",
}

# RIYA AI APIS (Working)
RIYA_APIS = {
    "riya_chat": "https://nexeoxgf.vercel.app/apiv1/chat?text={}",
    "riya_info": "https://nexeoxgf.vercel.app/apiv1/info",
    "riya_mood": "https://nexeoxgf.vercel.app/apiv1/mood",
    "riya_love": "https://nexeoxgf.vercel.app/apiv1/love",
}

# BLACKBOX AI APIS (Working)
BLACKBOX_APIS = {
    "bb_text_get": "https://nexeoblackboxai.vercel.app/api/v2/chat?txt={}",
    "bb_text_post": "https://nexeoblackboxai.vercel.app/api/v2/chat",
    "bb_image": "https://nexeoblackboxai.vercel.app/api/v2/image?txt={}",
    "bb_status": "https://nexeoblackboxai.vercel.app/api/v2/status",
}

# COMBINED APIS
ALL_APIS = {**ABBAS_APIS, **RIYA_APIS, **BLACKBOX_APIS}

# SMS Bomber API (Working)
BOMBER_API = "https://greatonlinetools.com/smsbomber/endpoints/api/receive_number.php"
BOMBER_CSRF = "d1a98ebd3fa1cbc6fab5f65bc22e7689b0e0541d3e116d7d2e2af7d0b37fd8db"

# ================= DATABASE =================
DB_FILE = "proxyfxc_users.db"

def init_database():
    conn = sqlite3.connect(DB_FILE, check_same_thread=False)
    cur = conn.cursor()
    
    cur.execute("""
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY,
        username TEXT,
        first_name TEXT,
        joined_date TEXT,
        total_searches INTEGER DEFAULT 0,
        total_bombs INTEGER DEFAULT 0,
        is_admin INTEGER DEFAULT 0
    )
    """)
    
    cur.execute("""
    CREATE TABLE IF NOT EXISTS search_logs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        search_type TEXT,
        query TEXT,
        search_time TEXT
    )
    """)
    
    cur.execute("""
    CREATE TABLE IF NOT EXISTS bomber_logs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        phone TEXT,
        count INTEGER,
        success INTEGER,
        failed INTEGER,
        bomber_time TEXT
    )
    """)
    
    conn.commit()
    return conn, cur

DB, CUR = init_database()

# ================= LOGGING FUNCTIONS =================

def log_user(user_id: int, username: str, first_name: str):
    CUR.execute("""
        INSERT OR IGNORE INTO users (id, username, first_name, joined_date)
        VALUES (?, ?, ?, ?)
    """, (user_id, username, first_name, datetime.now().isoformat()))
    DB.commit()

def log_search(user_id: int, search_type: str, query: str):
    CUR.execute("""
        INSERT INTO search_logs (user_id, search_type, query, search_time)
        VALUES (?, ?, ?, ?)
    """, (user_id, search_type, query, datetime.now().isoformat()))
    
    CUR.execute("UPDATE users SET total_searches = total_searches + 1 WHERE id=?", (user_id,))
    DB.commit()

def log_bomber(user_id: int, phone: str, count: int, success: int, failed: int):
    CUR.execute("""
        INSERT INTO bomber_logs (user_id, phone, count, success, failed, bomber_time)
        VALUES (?, ?, ?, ?, ?, ?)
    """, (user_id, phone, count, success, failed, datetime.now().isoformat()))
    
    CUR.execute("UPDATE users SET total_bombs = total_bombs + 1 WHERE id=?", (user_id,))
    DB.commit()

# ================= API FUNCTIONS =================

def call_abbas_api(api_type: str, query: str) -> Optional[Dict]:
    """Call Abbas APIs"""
    if api_type not in ABBAS_APIS:
        return None
    
    url = ABBAS_APIS[api_type].format(query)
    
    try:
        response = requests.get(url, timeout=15)
        if response.status_code == 200:
            return response.json()
        return {"error": f"HTTP {response.status_code}", "success": False}
    except Exception as e:
        return {"error": str(e), "success": False}

def call_riya_api(api_type: str, query: str = None) -> Optional[Dict]:
    """Call Riya AI APIs"""
    if api_type not in RIYA_APIS:
        return None
    
    if query:
        url = RIYA_APIS[api_type].format(query)
    else:
        url = RIYA_APIS[api_type]
    
    try:
        response = requests.get(url, timeout=15)
        if response.status_code == 200:
            return response.json()
        return {"error": f"HTTP {response.status_code}", "success": False}
    except Exception as e:
        return {"error": str(e), "success": False}

def call_blackbox_api(api_type: str, query: str = None) -> Optional[Dict]:
    """Call Blackbox AI APIs"""
    if api_type == "bb_text_post" and query:
        # POST method
        url = BLACKBOX_APIS["bb_text_post"]
        try:
            payload = {"message": query}
            response = requests.post(url, json=payload, timeout=15)
            if response.status_code == 200:
                return response.json()
            return {"error": f"HTTP {response.status_code}", "success": False}
        except Exception as e:
            return {"error": str(e), "success": False}
    
    elif api_type in BLACKBOX_APIS and query:
        # GET method
        url = BLACKBOX_APIS[api_type].format(query)
        try:
            response = requests.get(url, timeout=15)
            if response.status_code == 200:
                return response.json()
            return {"error": f"HTTP {response.status_code}", "success": False}
        except Exception as e:
            return {"error": str(e), "success": False}
    
    elif api_type in BLACKBOX_APIS:
        # No query needed
        url = BLACKBOX_APIS[api_type]
        try:
            response = requests.get(url, timeout=15)
            if response.status_code == 200:
                return response.json()
            return {"error": f"HTTP {response.status_code}", "success": False}
        except Exception as e:
            return {"error": str(e), "success": False}
    
    return None

# ================= SMS BOMBER FUNCTION =================

def send_otp_bomber(phone_number: str, total_otps: int) -> Tuple[int, int]:
    """
    Send OTP bombs to phone number
    Returns: (success_count, failed_count)
    """
    sent_count = 0
    failed_count = 0
    
    for current_count in range(1, total_otps + 1):
        payload = {
            "mobile": phone_number,
            "count": total_otps,
            "country_code": "91",
            "curr_count": current_count,
            "csrf_token": BOMBER_CSRF,
            "request_type": "sms_bomber"
        }
        
        headers = {
            'User-Agent': "Mozilla/5.0 (Linux; Android 15; 23076RN4BI Build/AQ3A.240912.001) AppleWebKit/537.36",
            'Content-Type': "application/json",
            'origin': "https://greatonlinetools.com",
            'referer': "https://greatonlinetools.com/smsbomber/",
        }
        
        try:
            response = requests.post(BOMBER_API, data=json.dumps(payload), headers=headers, timeout=10)
            if response.status_code == 200:
                sent_count += 1
            else:
                failed_count += 1
        except:
            failed_count += 1
        
        if current_count < total_otps:
            time.sleep(2)
    
    return sent_count, failed_count

# ================= FORMAT RESPONSE =================

def format_response(api_name: str, data: Dict, query: str) -> str:
    """Format API response with developer credit"""
    
    header = f"""
╔══════════════════════════════════════╗
║     🔥 PROXYFXC ULTIMATE BOT 🔥     ║
║           BY {DEVELOPER}              ║
╚══════════════════════════════════════╝

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
"""
    
    footer = f"""
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
⏱️ {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
💻 DEVELOPER: {DEVELOPER}
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
"""
    
    if not data or "error" in data:
        error_msg = data.get("error", "Unknown error") if data else "No response"
        return f"{header}❌ ERROR: {error_msg}\n\nQuery: `{query}`{footer}"
    
    # Extract data properly
    if isinstance(data, dict) and "data" in data:
        result = data["data"]
    else:
        result = data
    
    # Format based on API
    info = f"📌 **{api_name.upper()} RESULT**\n"
    info += f"🔍 **Query:** `{query}`\n\n"
    
    if isinstance(result, dict):
        for key, value in result.items():
            if value and str(value).strip() and str(value) != "None":
                clean_key = key.replace("_", " ").title()
                info += f"• **{clean_key}:** `{value}`\n"
    elif isinstance(result, str):
        info += f"{result}\n"
    else:
        info += f"```json\n{json.dumps(result, indent=2)[:500]}\n```"
    
    return f"{header}{info}{footer}"

def format_bomber_result(phone: str, count: int, sent: int, failed: int) -> str:
    """Format SMS bomber result"""
    
    header = f"""
╔══════════════════════════════════════╗
║     💣 PROXYFXC SMS BOMBER 💣       ║
║           BY {DEVELOPER}              ║
╚══════════════════════════════════════╝

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
"""
    
    status = "✅ SUCCESS" if failed == 0 else "⚠️ PARTIAL" if sent > 0 else "❌ FAILED"
    
    result = f"""
📱 **TARGET:** `{phone}`
🔢 **REQUESTED:** `{count}` OTPs
✅ **SENT:** `{sent}` OTPs
❌ **FAILED:** `{failed}` OTPs
📊 **STATUS:** {status}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
⚠️ **NOTE:** Use responsibly!
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
"""
    
    footer = f"""
⏱️ {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
💻 DEVELOPER: {DEVELOPER}
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
"""
    
    return f"{header}{result}{footer}"

def format_blackbox_response(data: Dict) -> str:
    """Format Blackbox AI response specially"""
    
    header = f"""
╔══════════════════════════════════════╗
║     🚀 BLACKBOX AI INTEGRATION 🚀   ║
║           BY {DEVELOPER}              ║
╚══════════════════════════════════════╝

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
"""
    
    footer = f"""
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
⏱️ {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
💻 DEVELOPER: {DEVELOPER}
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
"""
    
    if not data or "error" in data:
        return f"{header}❌ ERROR: {data.get('error', 'Unknown error')}{footer}"
    
    # Extract Blackbox response
    if data.get("success"):
        result_data = data.get("data", {})
        
        info = f"""
📌 **RESPONSE DETAILS:**
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
📝 **Type:** {result_data.get('type', 'N/A')}
📨 **Method:** {result_data.get('method', 'N/A')}
📥 **Input:** `{result_data.get('input', 'N/A')}`

💬 **RESPONSE:**
{result_data.get('response', 'N/A')}

📊 **Length:** {result_data.get('length', 'N/A')}
"""
        
        # For image generation
        if 'image_url' in result_data:
            info += f"\n🖼️ **Image URL:**\n`{result_data.get('image_url')}`"
        
        return f"{header}{info}{footer}"
    
    return f"{header}{json.dumps(data, indent=2)}{footer}"

# ================= KEYBOARDS =================

def main_keyboard():
    buttons = [
        [InlineKeyboardButton("📱 Phone Number", callback_data="menu_number"),
         InlineKeyboardButton("📸 Instagram", callback_data="menu_instagram")],
        [InlineKeyboardButton("🌐 IP Address", callback_data="menu_ip"),
         InlineKeyboardButton("🐙 GitHub", callback_data="menu_github")],
        [InlineKeyboardButton("🇵🇰 Pakistan", callback_data="menu_pakistan"),
         InlineKeyboardButton("📧 Email", callback_data="menu_email")],
        [InlineKeyboardButton("🆔 PAN Card", callback_data="menu_pan"),
         InlineKeyboardButton("🏦 IFSC", callback_data="menu_ifsc")],
        [InlineKeyboardButton("🎮 Free Fire", callback_data="menu_ff_info"),
         InlineKeyboardButton("💖 Riya AI", callback_data="menu_riya")],
        [InlineKeyboardButton("🚀 Blackbox AI", callback_data="menu_blackbox"),
         InlineKeyboardButton("🎨 Generate Image", callback_data="menu_bb_image")],
        [InlineKeyboardButton("💣 SMS BOMBER", callback_data="menu_bomber"),
         InlineKeyboardButton("📊 My Stats", callback_data="stats")],
        [InlineKeyboardButton("❓ Help", callback_data="help"),
         InlineKeyboardButton("ℹ️ About", callback_data="about")]
    ]
    return InlineKeyboardMarkup(buttons)

def blackbox_keyboard():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("💬 Chat (GET)", callback_data="bb_get"),
         InlineKeyboardButton("💬 Chat (POST)", callback_data="bb_post")],
        [InlineKeyboardButton("🎨 Generate Image", callback_data="bb_img"),
         InlineKeyboardButton("📊 Status", callback_data="bb_status")],
        [InlineKeyboardButton("🔙 Main Menu", callback_data="menu")]
    ])

def bomber_keyboard():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("5 OTPs", callback_data="bomber_5"),
         InlineKeyboardButton("10 OTPs", callback_data="bomber_10"),
         InlineKeyboardButton("15 OTPs", callback_data="bomber_15")],
        [InlineKeyboardButton("20 OTPs", callback_data="bomber_20"),
         InlineKeyboardButton("25 OTPs", callback_data="bomber_25"),
         InlineKeyboardButton("30 OTPs", callback_data="bomber_30")],
        [InlineKeyboardButton("🔙 Main Menu", callback_data="menu")]
    ])

def back_button():
    return InlineKeyboardMarkup([[
        InlineKeyboardButton("🔙 Main Menu", callback_data="menu")
    ]])

# ================= HANDLERS =================

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    log_user(user.id, user.username, user.first_name)
    
    welcome = f"""
╔══════════════════════════════════════╗
║     🔥 PROXYFXC ULTIMATE BOT 🔥     ║
║   OSINT + BOMBER + BLACKBOX AI      ║
║           BY {DEVELOPER}              ║
╚══════════════════════════════════════╝

👋 **Welcome {user.first_name}!**

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
🔍 **OSINT TOOLS:**
• 📱 Phone Number Lookup
• 📸 Instagram Profile
• 🌐 IP Address Details
• 🐙 GitHub Profile
• 🇵🇰 Pakistan Number
• 📧 Email Investigation
• 🆔 PAN Card Details
• 🏦 IFSC Code Info
• 🎮 Free Fire Info

💖 **RIYA AI:**
• Romantic AI girlfriend chat

🚀 **BLACKBOX AI:**
• 💬 AI Chat (GET/POST)
• 🎨 Image Generation
• 📊 API Status

💣 **SMS BOMBER:**
• Send 5-30 OTPs to any number

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
💻 DEVELOPER: {DEVELOPER}
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

👇 **Select a tool:**
"""
    await update.message.reply_text(welcome, parse_mode='Markdown', reply_markup=main_keyboard())

async def button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    user = query.from_user
    await query.answer()
    
    if query.data == "menu":
        await query.message.edit_text("🔍 **Main Menu**", parse_mode='Markdown', reply_markup=main_keyboard())
    
    elif query.data == "about":
        about_text = f"""
ℹ️ **ABOUT THIS BOT**
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
🤖 **Name:** PROXYFXC ULTIMATE BOT
👑 **Developer:** {DEVELOPER}
📌 **Version:** 4.0
⚡ **Features:**
• 11+ OSINT Tools
• Riya AI Integration
• Blackbox AI Integration
• SMS Bomber
• Stats Tracking

📚 **APIs Used:**
• Abbas APIs
• Riya AI (@HYPERXLEAKER)
• Blackbox AI (@Nexeodev)
• Great Online Tools

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
💻 {DEVELOPER}
"""
        await query.message.edit_text(about_text, parse_mode='Markdown', reply_markup=back_button())
    
    elif query.data == "stats":
        CUR.execute("SELECT total_searches, total_bombs FROM users WHERE id=?", (user.id,))
        result = CUR.fetchone()
        searches = result[0] if result else 0
        bombs = result[1] if result else 0
        
        stats_text = f"""
📊 **YOUR STATS**
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
🆔 **User ID:** `{user.id}`
👤 **Username:** @{user.username or 'N/A'}
📈 **OSINT Searches:** {searches}
💣 **Bomber Uses:** {bombs}
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
💻 {DEVELOPER}
"""
        await query.message.edit_text(stats_text, parse_mode='Markdown', reply_markup=back_button())
    
    elif query.data == "help":
        help_text = f"""
❓ **HOW TO USE**
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
🔍 **OSINT TOOLS:**
• Click tool → Send query → Get results

💖 **RIYA AI:**
• Click "Riya AI" → Send message

🚀 **BLACKBOX AI:**
• Choose method (GET/POST)
• Send message for chat
• Send prompt for image

💣 **SMS BOMBER:**
• Click "SMS BOMBER"
• Choose OTP count
• Send phone number

📱 **FORMATS:**
• Phone: `919876543210`
• Instagram: `username`
• IP: `8.8.8.8`
• Email: `example@gmail.com`
• PAN: `ABCDE1234F`
• IFSC: `SBIN0001234`

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
⚠️ **Use responsibly!**
💻 {DEVELOPER}
"""
        await query.message.edit_text(help_text, parse_mode='Markdown', reply_markup=back_button())
    
    elif query.data == "menu_blackbox":
        await query.message.edit_text(
            "🚀 **BLACKBOX AI OPTIONS**\n\nChoose a method:",
            reply_markup=blackbox_keyboard()
        )
    
    elif query.data.startswith("bb_"):
        bb_type = query.data
        context.user_data['api_type'] = bb_type
        
        prompts = {
            "bb_get": "💬 **Blackbox Chat (GET)**\n\nSend your message:",
            "bb_post": "💬 **Blackbox Chat (POST)**\n\nSend your message:",
            "bb_img": "🎨 **Blackbox Image Generation**\n\nSend your image prompt:\nExample: `cat on moon`",
            "bb_status": "📊 **Checking Blackbox API Status...**"
        }
        
        if bb_type == "bb_status":
            result = call_blackbox_api("bb_status")
            response = format_blackbox_response(result)
            await query.message.edit_text(response, parse_mode='Markdown', reply_markup=blackbox_keyboard())
        else:
            await query.message.edit_text(
                prompts.get(bb_type, "Send your query:"),
                parse_mode='Markdown',
                reply_markup=back_button()
            )
    
    elif query.data.startswith("menu_"):
        api_type = query.data.replace("menu_", "")
        context.user_data['api_type'] = api_type
        
        prompts = {
            "number": "📱 **Phone Number Lookup**\n\nSend phone number:\nExample: `919876543210`",
            "instagram": "📸 **Instagram Profile**\n\nSend username:\nExample: `cristiano`",
            "ip": "🌐 **IP Address Lookup**\n\nSend IP address:\nExample: `8.8.8.8`",
            "github": "🐙 **GitHub Profile**\n\nSend username:\nExample: `octocat`",
            "pakistan": "🇵🇰 **Pakistan Number**\n\nSend number:\nExample: `3359736848`",
            "pan": "🆔 **PAN Card Lookup**\n\nSend PAN number:\nExample: `ABCDE1234F`",
            "ff_info": "🎮 **Free Fire Info**\n\nSend UID:\nExample: `2819649271`",
            "phone": "📱 **Phone Number Info**\n\nSend number:\nExample: `919087654321`",
            "email": "📧 **Email Investigation**\n\nSend email:\nExample: `example@gmail.com`",
            "ifsc": "🏦 **IFSC Code Info**\n\nSend IFSC code:\nExample: `SBIN0001234`",
            "riya": "💖 **Riya AI Chat**\n\nSend your message:",
            "bomber": "💣 **SMS BOMBER**\n\nSelect OTP count:"
        }
        
        if api_type == "bomber":
            await query.message.edit_text(
                "💣 **SMS BOMBER**\n\nSelect number of OTPs:",
                reply_markup=bomber_keyboard()
            )
        else:
            await query.message.edit_text(
                prompts.get(api_type, f"Send your query for {api_type}:"),
                parse_mode='Markdown',
                reply_markup=back_button()
            )
    
    elif query.data.startswith("bomber_"):
        count = int(query.data.replace("bomber_", ""))
        context.user_data['bomber_count'] = count
        context.user_data['api_type'] = 'bomber'
        
        await query.message.edit_text(
            f"💣 **SMS BOMBER**\n\nSelected: **{count} OTPs**\n\n📱 Send phone number:\nExample: `919876543210`",
            parse_mode='Markdown',
            reply_markup=back_button()
        )

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    text = update.message.text.strip()
    
    if 'api_type' not in context.user_data:
        await update.message.reply_text("❌ Please select a tool first!", reply_markup=main_keyboard())
        return
    
    api_type = context.user_data['api_type']
    
    # Handle SMS Bomber
    if api_type == "bomber":
        if 'bomber_count' not in context.user_data:
            await update.message.reply_text("❌ Please select OTP count first!", reply_markup=bomber_keyboard())
            return
        
        # Validate phone number
        phone = re.sub(r'\D', '', text)
        if len(phone) < 10 or len(phone) > 12:
            await update.message.reply_text("❌ Invalid phone number! Use 10-12 digits.\nExample: `919876543210`", parse_mode='Markdown')
            return
        
        count = context.user_data['bomber_count']
        
        status_msg = await update.message.reply_text(f"💣 Starting bomber for {phone}...\nSending {count} OTPs...")
        
        # Run bomber
        sent, failed = send_otp_bomber(phone, count)
        
        # Log result
        log_bomber(user.id, phone, count, sent, failed)
        
        # Format result
        result = format_bomber_result(phone, count, sent, failed)
        
        await status_msg.edit_text(result, parse_mode='Markdown', reply_markup=main_keyboard())
        
        # Clear context
        context.user_data['api_type'] = None
        context.user_data['bomber_count'] = None
        
        return
    
    # Handle Blackbox AI
    if api_type.startswith("bb_"):
        status_msg = await update.message.reply_text(f"🚀 Processing Blackbox AI request...")
        
        if api_type == "bb_get":
            result = call_blackbox_api("bb_text_get", text)
        elif api_type == "bb_post":
            result = call_blackbox_api("bb_text_post", text)
        elif api_type == "bb_img":
            result = call_blackbox_api("bb_image", text)
        else:
            result = {"error": "Invalid API type"}
        
        log_search(user.id, api_type, text)
        response = format_blackbox_response(result)
        
        await status_msg.edit_text(response, parse_mode='Markdown', reply_markup=main_keyboard())
        context.user_data['api_type'] = None
        return
    
    # Handle Riya AI
    if api_type == "riya":
        status_msg = await update.message.reply_text(f"💖 Riya is thinking...")
        result = call_riya_api("riya_chat", text)
        log_search(user.id, api_type, text)
        response = format_response("Riya AI", result, text)
        await status_msg.edit_text(response, parse_mode='Markdown', reply_markup=main_keyboard())
        context.user_data['api_type'] = None
        return
    
    # Handle Abbas OSINT APIs
    if api_type in ABBAS_APIS:
        status_msg = await update.message.reply_text(f"🔍 Searching...")
        result = call_abbas_api(api_type, text)
        log_search(user.id, api_type, text)
        response = format_response(api_type, result, text)
        await status_msg.edit_text(response, parse_mode='Markdown', reply_markup=main_keyboard())
        context.user_data['api_type'] = None
        return
    
    # Default response
    await update.message.reply_text("❌ Something went wrong!", reply_markup=main_keyboard())
    context.user_data['api_type'] = None

# ================= FLASK SERVER =================

flask_app = Flask(__name__)

@flask_app.route('/')
def home():
    return jsonify({
        "status": "online",
        "bot": "PROXYFXC ULTIMATE BOT",
        "developer": DEVELOPER,
        "version": "4.0",
        "features": {
            "osint": list(ABBAS_APIS.keys()),
            "riya_ai": list(RIYA_APIS.keys()),
            "blackbox_ai": list(BLACKBOX_APIS.keys()),
            "bomber": "active"
        },
        "time": datetime.now().isoformat()
    })

@flask_app.route('/health')
def health():
    return jsonify({"status": "healthy", "developer": DEVELOPER})

@flask_app.route('/stats')
def stats():
    CUR.execute("SELECT COUNT(*) FROM users")
    total_users = CUR.fetchone()[0]
    CUR.execute("SELECT SUM(total_searches) FROM users")
    total_searches = CUR.fetchone()[0] or 0
    CUR.execute("SELECT SUM(total_bombs) FROM users")
    total_bombs = CUR.fetchone()[0] or 0
    
    return jsonify({
        "total_users": total_users,
        "total_searches": total_searches,
        "total_bombs": total_bombs,
        "developer": DEVELOPER
    })

# ================= BOT SETUP =================

async def run_bot():
    app = Application.builder().token(BOT_TOKEN).build()
    
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(button_callback))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    
    print(f"✅ PROXYFXC ULTIMATE BOT STARTED!")
    print(f"👑 Developer: {DEVELOPER}")
    print(f"🔍 OSINT Tools: {len(ABBAS_APIS)}")
    print(f"💖 Riya AI: {len(RIYA_APIS)}")
    print(f"🚀 Blackbox AI: {len(BLACKBOX_APIS)}")
    print(f"💣 SMS Bomber: Active")
    
    await app.initialize()
    await app.start()
    await app.updater.start_polling()
    
    while True:
        await asyncio.sleep(1)

def start_bot():
    asyncio.run(run_bot())

# ================= MAIN =================

if __name__ == "__main__":
    print("=" * 60)
    print("🔥 PROXYFXC ULTIMATE BOT 🔥")
    print(f"👑 Developer: {DEVELOPER}")
    print("=" * 60)
    
    # Start bot in background thread
    bot_thread = threading.Thread(target=start_bot, daemon=True)
    bot_thread.start()
    
    # Start Flask server
    port = int(os.environ.get("PORT", 8080))
    flask_app.run(host="0.0.0.0", port=port)
