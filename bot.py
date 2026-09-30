import os
import time
from threading import Thread
from flask import Flask
import telebot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
import firebase_admin
from firebase_admin import credentials, firestore

app = Flask(__name__)

@app.route('/')
def home():
    return "Rapido Bot Running 24/7 Free on Render!"

def run_flask():
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)

BOT_TOKEN = "8784908427:AAF1dkzSXxFWGK67oQ3EuInKW1QdR_WjejM"
ADMIN_TELEGRAM_ID = 1133405803
YOUR_UPI_ID = "ahm5646@ptyes"

try:
    if os.path.exists("firebase-key.json"):
        cred = credentials.Certificate("firebase-key.json")
        firebase_admin.initialize_app(cred)
        db = firestore.client()
        print("Firebase Connected!")
    else:
        db = None
except Exception as e:
    db = None

bot = telebot.TeleBot(BOT_TOKEN)

PLAN_DETAILS = {
    "BUY_7DAYS": {"name": "7 Days Plan", "price": 150, "days": 7},
    "BUY_15DAYS": {"name": "15 Days Pass", "price": 250, "days": 15},
    "BUY_30DAYS": {"name": "1 Month Plan (30 Days)", "price": 450, "days": 30},
    "BUY_LIFETIME": {"name": "Lifetime VIP Access", "price": 4500, "days": -1}
}

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
                    msg = f"🚖 *RAPIDO AUTO ACCEPTOR BOT*\n\n" \
                          f"📌 *Selected Plan:* {plan['name']}\n" \
                          f"💰 *Amount to Pay:* ₹{plan['price']}\n" \
                          f"📱 *Device ID:* `{device_id}`\n\n" \
                          f"💳 *UPI ID:* `{YOUR_UPI_ID}`\n\n" \
                          f"👇 *Next Steps:*\n" \
                          f"1. Is QR Code / UPI ID par ₹{plan['price']} pay karein.\n" \
                          f"2. Payment Screenshot yahan bhej dein!\n\n" \
                          f"_Payment verify hote hi 5 second me aapka plan active ho jayega!_"

                    qr_file_path = "qr.png" if os.path.exists("qr.png") else ("qr.jpg" if os.path.exists("qr.jpg") else None)
                    if qr_file_path:
                        with open(qr_file_path, "rb") as qr_img:
                            bot.send_photo(message.chat.id, qr_img, caption=msg, parse_mode="Markdown")
                    else:
                        bot.send_message(message.chat.id, msg, parse_mode="Markdown")

                    admin_msg = f"🚨 *NEW BUY ORDER RECEIVED!*\n\n" \
                                f"👤 *User:* @{message.from_user.username or 'NoUsername'} (ID: {message.from_user.id})\n" \
                                f"📦 *Plan:* {plan['name']} (₹{plan['price']})\n" \
                                f"📱 *Device ID:* `{device_id}`"

                    markup = InlineKeyboardMarkup()
                    markup.add(InlineKeyboardButton(f"✅ Approve {plan['name']}", callback_data=f"approve_{parts[1]}_{device_id}_{message.chat.id}"))

                    try:
                        bot.send_message(ADMIN_TELEGRAM_ID, admin_msg, parse_mode="Markdown", reply_markup=markup)
                    except Exception:
                        pass
                    return

        bot.send_message(
            message.chat.id, 
            "🚖 *Welcome to Rapido Auto Acceptor Bot!*\n\nApp me *Membership Plans* par jaakar plan select karein to buy subscription.",
            parse_mode="Markdown"
        )
    except Exception as e:
        print(f"Start Error: {e}")

@bot.message_handler(content_types=['photo', 'document'])
def handle_payment_screenshot(message):
    user_info = f"📸 *NEW PAYMENT SCREENSHOT RECEIVED!*\n\n" \
                f"👤 *From User:* @{message.from_user.username or 'NoUsername'} (ID: {message.from_user.id})\n" \
                f"💬 *Caption/Text:* {message.caption or 'No caption'}"
    try:
        if message.photo:
            file_id = message.photo[-1].file_id
            bot.send_photo(ADMIN_TELEGRAM_ID, file_id, caption=user_info, parse_mode="Markdown")
        elif message.document:
            file_id = message.document.file_id
            bot.send_document(ADMIN_TELEGRAM_ID, file_id, caption=user_info, parse_mode="Markdown")

        bot.reply_to(message, "✅ *Payment Screenshot Received!*\nAdmin is verifying your payment. Your plan will be activated within 5 minutes!")
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

        if db:
            user_ref = db.collection("users").document(device_id)
            user_ref.set({
                "isActive": True,
                "expiryTimestamp": expiry_ts,
                "planName": plan_code
            }, merge=True)

            bot.edit_message_text(
                f"✅ *APPROVED & ACTIVATED IN FIREBASE!*\n\n"
                f"📱 *Device ID:* `{device_id}`\n"
                f"📦 *Plan:* {plan['name']}",
                call.message.chat.id,
                call.message.message_id,
                parse_mode="Markdown"
            )
            bot.answer_callback_query(call.id, "Subscription Activated in Firebase!")

            bot.send_message(
                user_chat_id,
                f"🎉 *CONGRATULATIONS!*\n\n"
                f"Aapka *{plan['name']}* 100% Activate ho gaya hai!\n"
                f"App open karein aur Rapido Auto Acceptor chalu karein. Happy Riding! 🚖⚡",
                parse_mode="Markdown"
            )
    except Exception as e:
        print(f"Approval Error: {e}")

if __name__ == '__main__':
    try:
        bot.remove_webhook()
        print("Webhook cleared successfully!")
    except Exception as ex:
        print(f"Webhook clear error: {ex}")

    Thread(target=run_flask).start()
    print("Bot is running on Render 24/7 $0 Free Plan...")
    bot.infinity_polling()
