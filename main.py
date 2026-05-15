import logging
import os
import threading
import asyncio
from flask import Flask

from telegram import ReplyKeyboardMarkup, ReplyKeyboardRemove, Update, KeyboardButton, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application, CommandHandler, ContextTypes, ConversationHandler, MessageHandler, CallbackQueryHandler, filters
)

import config
import database
import google.generativeai as genai

# Flask app for health checks
app = Flask(__name__)

@app.route('/')
def health():
    return 'OK', 200

def run_flask():
    port = int(os.environ.get('PORT', 8000))
    app.run(host='0.0.0.0', port=port)

# Enable logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logging.getLogger("httpx").setLevel(logging.WARNING)
logger = logging.getLogger(__name__)

# Gemini API initialization
genai.configure(api_key=config.GEMINI_API_KEY)
model = genai.GenerativeModel('gemini-1.5-flash')

# Conversation states
LANG, NAME, PHONE, AI_CONSULT, SERVICE, DIMENSIONS, LOCATION, FINAL_INPUT, CONFIRM = range(9)

# Translations
STRINGS = {
    'uz': {
        'welcome': "Assalomu alaykum! <b>Oson Reklama</b> botiga xush kelibsiz. ✨\nBiznesingiz uchun eng yorqin reklama yechimlarini taqdim etamiz.",
        'choose_lang': "Iltimos, muloqot tilini tanlang:",
        'get_name': "Tanishganimizdan xursandmiz! Ismingizni yozib yuboring:",
        'get_phone': "Rahmat! Endi telefon raqamingizni yuboring (tugmani bosing yoki yozing):",
        'phone_btn': "📞 Raqamni yuborish",
        'ai_consult': "Sizga qanday reklama kerak? Masalan: 'Menga do'konim uchun chiroyli yonadigan harflar kerak' deb yozishingiz yoki ovozli xabar yuborishingiz mumkin. 🎤",
        'service_suggest': "AI konsultantimiz sizga <b>{service}</b> xizmatini taklif qiladi. Ma'qulmi?",
        'get_dims': "O'lchamlarni kiriting (masalan: 2x3 metr yoki A4):",
        'get_loc': "Reklama o'rnatiladigan joy lokatsiyasini yuboring (ixtiyoriy):",
        'loc_btn': "📍 Lokatsiya yuborish",
        'skip_btn': "➡️ O'tkazib yuborish",
        'get_final': "Qo'shimcha ma'lumot bormi? Matn yozing yoki ovozli xabar yuboring:",
        'confirm': "Buyurtma ma'lumotlari to'g'rimi?",
        'done': "Rahmat! Buyurtmangiz qabul qilindi. Tez orada bog'lanamiz. ✅",
        'portfolio': "Bizning ishlarimiz: https://t.me/osonreklamaishlar",
        'yes': "✅ Ha",
        'no': "❌ Yo'q / Tahrirlash",
        'admin_new_order': "🆕 <b>YANGI BUYURTMA</b>",
    },
    'ru': { # Using Cyrillic Uzbek as 'ru' key for simplicity in logic
        'welcome': "Ассалому алайкум! <b>Oson Reklama</b> ботига хуш келибсиз. ✨\nБизнесингиз учун энг ёрқин реклама ечимларини тақдим этамиз.",
        'choose_lang': "Илтимос, мулоқот тилини танланг:",
        'get_name': "Танишганимиздан хурсандмиз! Исмингизни ёзиб юборинг:",
        'get_phone': "Раҳмат! Энди телефон рақамингизни юборинг (тугмани босинг ёки ёзинг):",
        'phone_btn': "📞 Рақамни юбориш",
        'ai_consult': "Сизга қандай реклама керак? Масалан: 'Менга дўконим учун чиройли ёнадиган ҳарфлар керак' деб ёзишингиз ёки овозли хабар юборишингиз мумкин. 🎤",
        'service_suggest': "AI консултантимиз сизга <b>{service}</b> хизматини таклиф қилади. Маъқулми?",
        'get_dims': "Ўлчамларни киритинг (масалан: 2х3 метр ёки А4):",
        'get_loc': "Реклама ўрнатиладиган жой локациясини юборинг (ихтиёрий):",
        'loc_btn': "📍 Локация юбориш",
        'skip_btn': "➡️ Ўтказиб юбориш",
        'get_final': "Қўшимча маълумот борми? Матн ёзинг ёки овозли хабар юборинг:",
        'confirm': "Буюртма маълумотлари тўғрими?",
        'done': "Раҳмат! Буюртмангиз қабул қилинди. Тез орада боғланамиз. ✅",
        'portfolio': "Бизнинг ишларимиз: https://t.me/osonreklamaishlar",
        'yes': "✅ Ҳа",
        'no': "❌ Йўқ / Таҳрирлаш",
        'admin_new_order': "🆕 <b>ЯНГИ БУЮРТМА</b>",
    }
}

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    database.init_db()
    keyboard = [
        [InlineKeyboardButton("O'zbek (Lotin)", callback_data='lang_uz')],
        [InlineKeyboardButton("Ўзбек (Кирилл)", callback_data='lang_ru')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text(
        "Assalomu alaykum! Iltimos, tilni tanlang / Илтимос, тилни танланг:",
        reply_markup=reply_markup
    )
    return LANG

async def set_lang(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    lang = query.data.split('_')[1]
    context.user_data['lang'] = lang
    
    s = STRINGS[lang]
    await query.edit_message_text(f"{s['welcome']}\n\n{s['get_name']}", parse_mode='HTML')
    return NAME

async def get_name(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.user_data['name'] = update.message.text
    lang = context.user_data['lang']
    s = STRINGS[lang]
    
    btn = [[KeyboardButton(s['phone_btn'], request_contact=True)]]
    await update.message.reply_text(s['get_phone'], reply_markup=ReplyKeyboardMarkup(btn, resize_keyboard=True, one_time_keyboard=True), parse_mode='HTML')
    return PHONE

async def get_phone(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    phone = update.message.contact.phone_number if update.message.contact else update.message.text
    context.user_data['phone'] = phone
    lang = context.user_data['lang']
    s = STRINGS[lang]
    
    await update.message.reply_text(f"{s['portfolio']}\n\n{s['ai_consult']}", reply_markup=ReplyKeyboardRemove(), parse_mode='HTML')
    return AI_CONSULT

async def ai_consult(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    lang = context.user_data['lang']
    s = STRINGS[lang]
    
    if update.message.voice:
        context.user_data['voice_file_id'] = update.message.voice.file_id
        user_input = "[Ovozli xabar yuborildi]"
    else:
        user_input = update.message.text
    
    context.user_data['initial_desc'] = user_input
    
    # AI classification only here
    prompt = f"Analyze this advertising request: '{user_input}'. Classify it into one of: Banner, Bo'rtma harflar, Laytboks, Vizitka/Flayer, Boshqa. Respond with ONLY the category name."
    try:
        response = model.generate_content(prompt)
        service = response.text.strip()
    except:
        service = "Boshqa"
    
    context.user_data['service'] = service
    
    keyboard = [[InlineKeyboardButton(s['yes'], callback_data='confirm_service'), InlineKeyboardButton(s['no'], callback_data='edit_service')]]
    await update.message.reply_text(s['service_suggest'].format(service=service), reply_markup=InlineKeyboardMarkup(keyboard), parse_mode='HTML')
    return SERVICE

async def get_dims(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    if query: await query.answer()
    
    lang = context.user_data['lang']
    s = STRINGS[lang]
    
    msg = s['get_dims']
    if query:
        await query.edit_message_text(msg, parse_mode='HTML')
    else:
        await update.message.reply_text(msg, parse_mode='HTML')
    return DIMENSIONS

async def get_loc(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.user_data['dims'] = update.message.text
    lang = context.user_data['lang']
    s = STRINGS[lang]
    
    btn = [[KeyboardButton(s['loc_btn'], request_location=True)], [KeyboardButton(s['skip_btn'])]]
    await update.message.reply_text(s['get_loc'], reply_markup=ReplyKeyboardMarkup(btn, resize_keyboard=True, one_time_keyboard=True), parse_mode='HTML')
    return LOCATION

async def get_final(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    if update.message.location:
        context.user_data['lat'] = update.message.location.latitude
        context.user_data['lon'] = update.message.location.longitude
    
    lang = context.user_data['lang']
    s = STRINGS[lang]
    
    await update.message.reply_text(s['get_final'], reply_markup=ReplyKeyboardRemove(), parse_mode='HTML')
    return FINAL_INPUT

async def pre_confirm(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    lang = context.user_data['lang']
    s = STRINGS[lang]
    
    if update.message.voice:
        context.user_data['final_voice_id'] = update.message.voice.file_id
        context.user_data['final_desc'] = "[Ovozli xabar]"
    else:
        context.user_data['final_desc'] = update.message.text
    
    summary = f"📋 <b>{s['confirm']}</b>\n\n👤 {context.user_data['name']}\n📞 {context.user_data['phone']}\n🛠 {context.user_data['service']}\n📏 {context.user_data['dims']}"
    
    keyboard = [[InlineKeyboardButton(s['yes'], callback_data='final_yes'), InlineKeyboardButton(s['no'], callback_data='final_no')]]
    await update.message.reply_text(summary, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode='HTML')
    return CONFIRM

async def final_done(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    lang = context.user_data['lang']
    s = STRINGS[lang]
    
    if query.data == 'final_yes':
        # Save to DB
        order_id = database.add_order(
            update.effective_user.id,
            context.user_data['service'],
            context.user_data['dims'],
            context.user_data.get('lat'),
            context.user_data.get('lon'),
            context.user_data.get('final_voice_id') or context.user_data.get('voice_file_id'),
            context.user_data['final_desc']
        )
        
        # Send to Admin Group
        admin_msg = f"🚀 <b>{s['admin_new_order']} #{order_id}</b>\n\n" \
                    f"👤 Mijoz: {context.user_data['name']}\n" \
                    f"📞 Tel: {context.user_data['phone']}\n" \
                    f"🛠 Xizmat: {context.user_data['service']}\n" \
                    f"📏 O'lcham: {context.user_data['dims']}\n" \
                    f"📝 Izoh: {context.user_data['final_desc']}"
        
        await context.bot.send_message(config.ADMIN_CHAT_ID, admin_msg, parse_mode='HTML')
        
        # Send Location if exists
        if 'lat' in context.user_data:
            await context.bot.send_location(config.ADMIN_CHAT_ID, context.user_data['lat'], context.user_data['lon'])
            
        # Forward Voice if exists
        voice_id = context.user_data.get('final_voice_id') or context.user_data.get('voice_file_id')
        if voice_id:
            await context.bot.send_voice(config.ADMIN_CHAT_ID, voice_id)
            
        await query.edit_message_text(s['done'], parse_mode='HTML')
        return ConversationHandler.END
    else:
        await query.edit_message_text(s['ai_consult'], parse_mode='HTML')
        return AI_CONSULT

def main():
    threading.Thread(target=run_flask, daemon=True).start()
    
    app_tg = Application.builder().token(config.BOT_TOKEN).build()
    
    conv = ConversationHandler(
        entry_points=[CommandHandler('start', start)],
        states={
            LANG: [CallbackQueryHandler(set_lang, pattern='^lang_')],
            NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_name)],
            PHONE: [MessageHandler((filters.TEXT | filters.CONTACT) & ~filters.COMMAND, get_phone)],
            AI_CONSULT: [MessageHandler((filters.TEXT | filters.VOICE) & ~filters.COMMAND, ai_consult)],
            SERVICE: [CallbackQueryHandler(get_dims, pattern='confirm_service'), CallbackQueryHandler(ai_consult, pattern='edit_service')],
            DIMENSIONS: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_loc)],
            LOCATION: [MessageHandler((filters.LOCATION | filters.TEXT) & ~filters.COMMAND, get_final)],
            FINAL_INPUT: [MessageHandler((filters.TEXT | filters.VOICE) & ~filters.COMMAND, pre_confirm)],
            CONFIRM: [CallbackQueryHandler(final_done, pattern='^final_')],
        },
        fallbacks=[CommandHandler('start', start)]
    )
    
    app_tg.add_handler(conv)
    app_tg.run_polling()

if __name__ == '__main__':
    main()
