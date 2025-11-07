from keep_alive import keep_alive
keep_alive()

import telebot
import os
from telebot import types

# === SOZLAMALAR ===
BOT_TOKEN = os.getenv("BOT_TOKEN", "8425489641:AAFOKW3K-A88inkVxBguqqBQTqr2y-f9Cb0")
ADMIN_ID = os.getenv("ADMIN_ID", "5851585402")
ADMIN_USERNAME = os.getenv("ADMIN_USERNAME", "@Mominjon_gofurov")

# ==========================================
bot = telebot.TeleBot(BOT_TOKEN)

user_data = {}  # Foydalanuvchi ma'lumotlarini vaqtinchalik saqlash

# --- Asosiy menyu ---
@bot.message_handler(commands=['start'])
def send_welcome(message):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=False)
    btn1 = types.KeyboardButton("💳 Hisobni to'ldirish")
    btn2 = types.KeyboardButton("📤 Hisobdan yechish")
    btn3 = types.KeyboardButton("📞 Admin bilan aloqa")
    markup.add(btn1, btn2, btn3)
    bot.send_message(message.chat.id, "Salom! 1Win agent botiga xush kelibsiz.", reply_markup=markup)

# --- Menyu tugmalariga javob ---
@bot.message_handler(func=lambda message: message.text == "💳 Hisobni to'ldirish")
def top_up_menu(message):
    markup = types.InlineKeyboardMarkup()
    btn1 = types.InlineKeyboardButton("Naqd pulda", callback_data="topup_cash")
    btn2 = types.InlineKeyboardButton("Karta orqali", callback_data="topup_card")
    markup.add(btn1, btn2)
    bot.send_message(message.chat.id, "To'lov usulini tanlang:", reply_markup=markup)

@bot.message_handler(func=lambda message: message.text == "📤 Hisobdan yechish")
def withdraw_start(message):
    msg = bot.send_message(message.chat.id, "Iltimos, 1Win hisobingizni (login yoki ID) kiriting:")
    bot.register_next_step_handler(msg, get_withdraw_id)

@bot.message_handler(func=lambda message: message.text == "📞 Admin bilan aloqa")
def contact_admin(message):
    bot.send_message(message.chat.id, f"Admin bilan bog'lanish: {ADMIN_USERNAME}")

# --- Callback tugmalar (to'ldirish) ---
@bot.callback_query_handler(func=lambda call: call.data == "topup_cash")
def topup_cash(call):
    bot.answer_callback_query(call.id)
    bot.send_message(call.message.chat.id, "Iltimos, lokatsiyangizni yuboring:", reply_markup=types.ReplyKeyboardMarkup(resize_keyboard=True).add(types.KeyboardButton("📍 Lokatsiyani yuborish", request_location=True)))
    bot.register_next_step_handler_by_chat_id(call.message.chat.id, get_location)

@bot.callback_query_handler(func=lambda call: call.data == "topup_card")
def topup_card(call):
    bot.answer_callback_query(call.id)
    msg = bot.send_message(call.message.chat.id, "Iltimos, 1Win hisobingizni (login yoki ID) kiriting:")
    bot.register_next_step_handler(msg, get_card_id)

# --- Naqd to'lov: lokatsiya → telefon → xabar admin uchun ---
def get_location(message):
    if message.location:
        lat = message.location.latitude
        lon = message.location.longitude
        user_data[message.chat.id] = {'location': (lat, lon)}
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
        markup.add(types.KeyboardButton("📞 Telefon raqamni yuborish", request_contact=True))
        bot.send_message(message.chat.id, "Endi telefon raqamingizni yuboring:", reply_markup=markup)
        bot.register_next_step_handler_by_chat_id(message.chat.id, get_phone)
    else:
        bot.send_message(message.chat.id, "Iltimos, lokatsiyani yuboring (📍 tugmasini bosing).")
        bot.register_next_step_handler_by_chat_id(message.chat.id, get_location)

def get_phone(message):
    if message.contact:
        phone = message.contact.phone_number
    else:
        phone = message.text.strip()

    data = user_data.get(message.chat.id, {})
    location = data.get('location')
    if location:
        lat, lon = location
        maps_link = f"https://www.google.com/maps?q={lat},{lon}"
        admin_msg = (
            f"🔔 Yangi NAQD to'lov so'rovi:\n"
            f"Foydalanuvchi: @{message.from_user.username or 'N/A'} (ID: {message.chat.id})\n"
            f"Lokatsiya: {maps_link}\n"
            f"Telefon: {phone}"
        )
        bot.send_message(ADMIN_ID, admin_msg)
        bot.send_message(message.chat.id, "Muroja'atingiz qabul qilindi! Tez orada siz bilan aloqaga chiqamiz.", reply_markup=types.ReplyKeyboardRemove())
    else:
        bot.send_message(message.chat.id, "Xatolik yuz berdi. /start buyrug'ini yuboring.")

# --- Karta orqali to'ldirish ---
def get_card_id(message):
    user_data[message.chat.id] = {'1win_id': message.text.strip()}
    msg = bot.send_message(message.chat.id, "To'ldirmoqchi bo'lgan summani kiriting (so'mda, faqat raqam):")
    bot.register_next_step_handler(msg, get_card_amount)

def get_card_amount(message):
    try:
        amount = int(message.text.strip())
        real_amount = amount + 19
        user_data[message.chat.id]['amount'] = amount
        user_data[message.chat.id]['real_amount'] = real_amount

        karta = "9860350144850400"

        bot.send_message(
            message.chat.id,
            f"💳 Iltimos, quyidagi karta raqamiga **{real_amount} UZS** o'tkazing:\n\n"
            f"`{karta}`\n\n"
            f"O'tkazma chekini (screenshot) yuboring:",
            parse_mode="Markdown"
        )
        bot.register_next_step_handler_by_chat_id(message.chat.id, get_receipt)
    except ValueError:
        bot.send_message(message.chat.id, "Faqat raqam kiriting. Qayta urinib ko'ring.")
        bot.register_next_step_handler_by_chat_id(message.chat.id, get_card_amount)

def get_receipt(message):
    if message.photo:
        photo = message.photo[-1].file_id
        data = user_data.get(message.chat.id, {})
        admin_msg = (
            f"🔔 Yangi KARTA orqali to'lov:\n"
            f"Foydalanuvchi: @{message.from_user.username or 'N/A'} (ID: {message.chat.id})\n"
            f"1Win ID: {data.get('1win_id')}\n"
            f"So'ralgan: {data.get('amount')} → Haqiqiy: {data.get('real_amount')} UZS\n"
            f"Chek:"
        )
        bot.send_message(ADMIN_ID, admin_msg)
        bot.send_photo(ADMIN_ID, photo)
        bot.send_message(message.chat.id, "Chek qabul qilindi! Tez orada hisobingiz to'ldiriladi.")
    else:
        bot.send_message(message.chat.id, "Iltimos, chekni rasm sifatida yuboring.")
        bot.register_next_step_handler_by_chat_id(message.chat.id, get_receipt)

# --- Pul yechish ---
def get_withdraw_id(message):
    user_data[message.chat.id] = {'1win_id': message.text.strip()}
    msg = bot.send_message(message.chat.id, "1Win tomonidan berilgan pul yechish kodini kiriting:")
    bot.register_next_step_handler(msg, get_withdraw_code)

def get_withdraw_code(message):
    data = user_data.get(message.chat.id, {})
    admin_msg = (
        f"📤 Yangi PUL YECHISH so'rovi:\n"
        f"Foydalanuvchi: @{message.from_user.username or 'N/A'} (ID: {message.chat.id})\n"
        f"1Win ID: {data.get('1win_id')}\n"
        f"Yechish kodi: {message.text.strip()}"
    )
    bot.send_message(ADMIN_ID, admin_msg)
    bot.send_message(message.chat.id, "So'rov qabul qilindi! Pul tez orada yetkaziladi.")

# --- Botni ishga tushirish ---
if __name__ == "__main__":
    print("Bot ishga tushdi...")
    bot.polling(none_stop=True)
