import os
import time
import json
import requests
from flask import Flask, request
import telebot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton

app = Flask(__name__)
BOT_TOKEN = "8784908427:AAF4j1GIIDzIFDmXpQ74zXyQIIF9lJeircw"
ADMIN_TELEGRAM_ID = 1133405803
YOUR_UPI_ID = "ahm5646@ptyes"
PROJECT_ID = "autoacceptorapp"

bot = telebot.TeleBot(BOT_TOKEN)

# --- DIRECT GOOGLE FIRESTORE REST API ENGINE (0 JWT / 0 TIME SYNC DEPENDENCY!) ---
def update_user_subscription(device_id, plan_code, expiry_ts):
    try:
        # Direct HTTP PATCH to Google Cloud Firestore REST API v1
        url = f"https://firestore.googleapis.com/v1/projects/{PROJECT_ID}/databases/(default)/documents/users/{device_id}?updateMask.fieldPaths=isActive&updateMask.fieldPaths=expiryTimestamp&updateMask.fieldPaths=planName"
        payload = {
            "fields": {
                "isActive": {"booleanValue": True},
                "expiryTimestamp": {"integerValue": str(expiry_ts)},
                "planName": {"stringValue": str(plan_code)}
            }
        }
        resp = requests.patch(url, json=payload, timeout=10)
        print(f"Firestore REST API PATCH Response: {resp.status_code} - {resp.text}")

        if resp.status_code in [200, 201]:
            return True, "Success"

        # Fallback Overwrite
        url_no_mask = f"https://firestore.googleapis.com/v1/projects/{PROJECT_ID}/databases/(default)/documents/users/{device_id}"
        resp2 = requests.post(url_no_mask, json=payload, timeout=10)
        if resp2.status_code in [200, 201]:
            return True, "Success"

        return False, f"HTTP {resp.status_code}: {resp.text}"
    except Exception as ex:
        print(f"REST Exception: {ex}")
        return False, f"REST Exception: {ex}"

PLAN_DETAILS = {
    "BUY_7DAYS": {"name": "7 Days Plan", "price": 150, "days": 7},
    "BUY_15DAYS": {"name": "15 Days Pass", "price": 250, "days": 15},
    "BUY_30DAYS": {"name": "1 Month Plan (30 Days)", "price": 450, "days": 30},
    "BUY_LIFETIME": {"name": "Lifetime VIP Access", "price": 4500, "days": -1}
}

# --- WEBHOOK ROUTE FOR RENDER ---
@app.route('/webhook', methods=['POST'])
def webhook():
    try:
        if request.headers.get('content-type') == 'application/json':
            json_string = request.get_data().decode('utf-8')
            update = telebot.types.Update.de_json(json_string)
            bot.process_new_updates([update])
    except Exception as e:
        print(f"Webhook error: {e}")
    return 'OK', 200

@app.route('/')
def home():
    try:
        render_url = os.environ.get("RENDER_EXTERNAL_URL", "https://rapido-bot.onrender.com")
        bot.set_webhook(url=f"{render_url}/webhook")
        return f"Rapido Bot Webhook Active on {render_url}!"
    except Exception as e:
        return f"Render Bot Running! Webhook error: {e}"

@bot.message_handler(commands=['myid'])
def handle_myid(message):
    bot.reply_to(message, f"👤
