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
    bot.reply_to(message, f"👤 Your Telegram User ID: {message.from_user.id}")

# --- ADMIN COMMAND: INSTANT LIFETIME VIP GRANT ---
@bot.message_handler(commands=['lifetime'])
def handle_grant_lifetime(message):
    args = message.text.split()
    if len(args) < 2:
        bot.reply_to(message, "⚠️ Usage: /lifetime <DEVICE_ID>\nExample: /lifetime 815e3ed1ce8d80a8")
        return
    device_id = args[1].strip()
    success, msg = update_user_subscription(device_id, "LIFETIME", -1)
    if success:
        bot.reply_to(
            message, 
            f"👑 LIFETIME VIP ACCESS GRANTED!\n\n"
            f"📱 Device ID: {device_id}\n"
            f"♾️ Expiry: Permanent Lifetime Access (No Expiry)\n\n"
            f"Customer app open karega to VIP Lifetime status active ho jayega!"
        )
    else:
        bot.reply_to(message, f"❌ Error: {msg}")

# --- ADMIN COMMAND: INSTANT CUSTOM DAYS GRANT ---
@bot.message_handler(commands=['days'])
def handle_grant_days(message):
    args = message.text.split()
    if len(args) < 3:
        bot.reply_to(message, "⚠️ Usage: /days <DEVICE_ID> <NUM_DAYS>\nExample: /days 815e3ed1ce8d80a8 30")
        return
    device_id = args[1].strip()
    try:
        num_days = int(args[2].strip())
    except ValueError:
        bot.reply_to(message, "⚠️ Invalid number of days!")
        return

    current_time_ms = int(time.time() * 1000)
    expiry_ts = current_time_ms + (num_days * 24 * 60 * 60 * 1000)
    plan_code = "30DAYS" if num_days >= 28 else ("15DAYS" if num_days >= 14 else "7DAYS")

    success, msg = update_user_subscription(device_id, plan_code, expiry_ts)
    if success:
        bot.reply_to(
            message, 
            f"✅ {num_days}-DAYS SUBSCRIPTION GRANTED!\n\n"
            f"📱 Device ID: {device_id}\n"
            f"⏳ Expiry: {num_days} Days from current moment"
        )
    else:
        bot.reply_to(message, f"❌ Error: {msg}")

# --- ADMIN COMMAND: INSTANT EXPIRE / LOCK DEVICE ---
@bot.message_handler(commands=['expire'])
def handle_expire_device(message):
    args = message.text.split()
    if len(args) < 2:
        bot.reply_to(message, "⚠️ Usage: /expire <DEVICE_ID>\nExample: /expire 815e3ed1ce8d80a8")
        return
    device_id = args[1].strip()
    current_time_ms = int(time.time() * 1000) - 1000 # Expired in past

    success, msg = update_user_subscription(device_id, "1_DAY_FREE_TRIAL", current_time_ms)
    if success:
        bot.reply_to(
            message, 
            f"🔴 DEVICE EXPIRED & LOCKED!\n\n"
            f"📱 Device ID: {device_id}\n"
            f"🔒 Status: Expired / Inactive"
        )
    else:
        bot.reply_to(message, f"❌ Error: {msg}")

# --- ADMIN COMMAND: INSTANT 24-HOUR DEMO GRANT ---
@bot.message_handler(commands=['demo'])
def handle_grant_demo(message):
    try:
        args = message.text.split()
        if len(args) < 2:
            bot.reply_to(message, "⚠️ Usage: /demo <DEVICE_ID>\nExample: /demo 815e3ed1ce8d80a8")
            return

        device_id = args[1].strip()
        current_time_ms = int(time.time() * 1000)
        demo_expiry_ts = current_time_ms + (24 * 60 * 60 * 1000)

        success, msg = update_user_subscription(device_id, "1_DAY_FREE_TRIAL", demo_expiry_ts)
        if success:
            bot.reply_to(
                message, 
                f"✅ 24-HOUR EXTRA DEMO GRANTED!\n\n"
                f"📱 Device ID: {device_id}\n"
                f"⏳ Expiry: 24 Hours from current moment\n\n"
                f"Customer app open karega to 24h countdown live start ho jayega!"
            )
        else:
            bot.reply_to(message, f"❌ Error updating Firestore: {msg}")
    except Exception as ex:
        bot.reply_to(message, f"❌ Demo Error: {ex}")

@bot.message_handler(commands=['start'])
def handle_start(message):
    try:
        args = message.text.split()
        if len(args) > 1:
            param = args[1]
            parts = param.split('_')
            if len(parts) >= 3:
                plan_key = f"{parts[0]}_{parts[1]}"
                device_id = parts[2]
                if plan_key in PLAN_DETAILS:
                    plan = PLAN_DETAILS[plan_key]
                    msg = f"🚖 RAPIDO AUTO ACCEPTOR BOT\n\n" \
                          f"📌 Selected Plan: {plan['name']}\n" \
                          f"💰 Amount to Pay: ₹{plan['price']}\n" \
                          f"📱 Device ID: {device_id}\n\n" \
                          f"💳 UPI ID: {YOUR_UPI_ID}\n\n" \
                          f"👇 Next Steps:\n" \
                          f"1. Is QR Code / UPI ID par ₹{plan['price']} pay karein.\n" \
                          f"2. Payment Screenshot yahan bhej dein!\n\n" \
                          f"Payment verify hote hi 5 second me aapka plan active ho jayega!"

                    qr_file_path = "qr.png" if os.path.exists("qr.png") else ("qr.jpg" if os.path.exists("qr.jpg") else None)
                    if qr_file_path:
                        with open(qr_file_path, "rb") as qr_img:
                            bot.send_photo(message.chat.id, qr_img, caption=msg)
                    else:
                        bot.send_message(message.chat.id, msg)

                    admin_msg = f"🚨 NEW BUY ORDER RECEIVED!\n\n" \
                                f"👤 User: @{message.from_user.username or 'NoUsername'} (ID: {message.from_user.id})\n" \
                                f"📦 Plan: {plan['name']} (₹{plan['price']})\n" \
                                f"📱 Device ID: {device_id}"

                    markup = InlineKeyboardMarkup()
                    markup.add(InlineKeyboardButton(f"✅ Approve {plan['name']}", callback_data=f"approve_{parts[1]}_{device_id}_{message.chat.id}"))

                    try:
                        bot.send_message(ADMIN_TELEGRAM_ID, admin_msg, reply_markup=markup)
                    except Exception:
                        pass
                    return

        bot.send_message(
            message.chat.id, 
            "🚖 Welcome to Rapido Auto Acceptor Bot!\n\nApp me Membership Plans par jaakar plan select karein to buy subscription."
        )
    except Exception as e:
        print(f"Start Error: {e}")

@bot.message_handler(content_types=['photo', 'document'])
def handle_payment_screenshot(message):
    user_info = f"📸 NEW PAYMENT SCREENSHOT RECEIVED!\n\n" \
                f"👤 From User: @{message.from_user.username or 'NoUsername'} (ID: {message.from_user.id})\n" \
                f"💬 Caption/Text: {message.caption or 'No caption'}"
    try:
        if message.photo:
            file_id = message.photo[-1].file_id
            bot.send_photo(ADMIN_TELEGRAM_ID, file_id, caption=user_info)
        elif message.document:
            file_id = message.document.file_id
            bot.send_document(ADMIN_TELEGRAM_ID, file_id, caption=user_info)

        bot.reply_to(message, "✅ Payment Screenshot Received!\nAdmin is verifying your payment. Your plan will be activated within 5 minutes!")
    except Exception:
        pass

@bot.callback_query_handler(func=lambda call: call.data.startswith("approve_"))
def handle_approval(call):
    try:
        parts = call.data.split('_')
        plan_code = parts[1]
        device_id = parts[2]
        user_chat_id = parts[3]

        plan_key = f"BUY_{plan_code}"
        plan = PLAN_DETAILS.get(plan_key)

        if not plan:
            bot.answer_callback_query(call.id, "Invalid Plan!")
            return

        current_time_ms = int(time.time() * 1000)
        expiry_ts = -1 if plan["days"] == -1 else current_time_ms + (plan["days"] * 24 * 60 * 60 * 1000)

        success, msg = update_user_subscription(device_id, plan_code, expiry_ts)
        if success:
            bot.edit_message_text(
                f"✅ APPROVED & ACTIVATED IN FIREBASE!\n\n"
                f"📱 Device ID: {device_id}\n"
                f"📦 Plan: {plan['name']}",
                call.message.chat.id,
                call.message.message_id
            )
            bot.answer_callback_query(call.id, "Subscription Activated in Firebase!")

            bot.send_message(
                user_chat_id,
                f"🎉 CONGRATULATIONS!\n\n"
                f"Aapka {plan['name']} 100% Activate ho gaya hai!\n"
                f"App open karein aur Rapido Auto Acceptor chalu karein. Happy Riding! 🚖⚡"
            )
        else:
            bot.answer_callback_query(call.id, f"Error updating Firestore: {msg}")
    except Exception as e:
        print(f"Approval Error: {e}")

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
