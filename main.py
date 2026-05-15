import logging
import sqlite3
import google.generativeai as genai

from telegram import ReplyKeyboardMarkup, ReplyKeyboardRemove, Update, KeyboardButton, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application, CommandHandler, ContextTypes, ConversationHandler, MessageHandler, CallbackQueryHandler, filters
)

import config
import database

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
NAME, PHONE_NUMBER, AI_CONSULTANT, SERVICE_TYPE, DIMENSIONS, MATERIAL, DESIGN_STATUS, INSTALLATION_LOCATION, DEADLINE, CONFIRM_ORDER = range(10)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    user = update.effective_user
    database.init_db()
    db_user = database.get_user(user.id)

    welcome_message = (
        "Assalomu alaykum, hurmatli mijoz! 👋\n\n"
        "Sizni **Oson Reklama** agentligining buyurtmalarni qabul qilish botida ko'rib turganimizdan mamnunmiz! ✨\n\n"
        "Bizning agentligimiz sizning biznesingiz uchun eng zamonaviy va samarali tashqi reklama yechimlarini taqdim etadi. Keling, birgalikda brendingizni yorqinroq qilamiz! 🚀\n\n"
    )

    if db_user:
        await update.message.reply_html(
            f"{welcome_message}Sizga qanday turdagi reklama xizmati kerak yoki qanday muammoni hal qilmoqchisiz?"
        )
        return AI_CONSULTANT
    else:
        await update.message.reply_html(
            f"{welcome_message}Iltimos, avval ismingizni kiriting."
        )
        return NAME

async def get_name(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    user_name = update.message.text
    context.user_data["name"] = user_name
    
    contact_button = KeyboardButton(text="📞 Telefon raqamni yuborish", request_contact=True)
    reply_markup = ReplyKeyboardMarkup([[contact_button]], one_time_keyboard=True, resize_keyboard=True)

    await update.message.reply_html(
        f"Rahmat, **{user_name}**! Endi iltimos, telefon raqamingizni yuboring. Bu bizga siz bilan tezkor bog'lanishga yordam beradi. 👇",
        reply_markup=reply_markup,
    )
    return PHONE_NUMBER

async def get_phone_number(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    user = update.effective_user
    phone_number = update.message.contact.phone_number if update.message.contact else update.message.text
    context.user_data["phone_number"] = phone_number

    database.add_user(user.id, context.user_data["name"], phone_number)

    await update.message.reply_html(
        "Ajoyib! Ma'lumotlaringiz muvaffaqiyatli saqlandi. ✅\n\n" 
        "Endi sizga qanday turdagi reklama xizmati kerakligini yoki qanday muammoni hal qilmoqchi ekanligingizni qisqacha ta'riflab bering. Bizning AI konsultantimiz sizga eng mos yechimni topishga yordam beradi. 🤖",
        reply_markup=ReplyKeyboardRemove(),
    )
    return AI_CONSULTANT

async def ai_consultant(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    user_id = update.effective_user.id
    user_input = update.message.text
    
    # Save user message to history
    database.add_chat_message(user_id, "user", user_input)
    
    # Get chat history
    history = database.get_chat_history(user_id)
    
    # Prepare prompt for Gemini
    prompt = "You are an AI assistant for Oson Reklama agency. Analyze the user's request and identify the most suitable advertising service type from: Banner, Bo'rtma harflar, Flayer / Vizitka, Layt-boks, Boshqa / Maxsus loyiha. Respond ONLY with the identified service type, or 'Boshqa / Maxsus loyiha' if unsure. Keep the response short and concise.\n\n"
    for role, content in history:
        prompt += f"{role}: {content}\n"
    prompt += "assistant:"

    try:
        response = model.generate_content(prompt)
        service_type = response.text.strip()
        # Save AI response to history
        database.add_chat_message(user_id, "assistant", service_type)
    except Exception as e:
        logger.error(f"Gemini API error: {e}")
        service_type = "Boshqa / Maxsus loyiha" # Fallback

    context.user_data["service_type"] = service_type

    # Dynamic menu based on AI analysis
    keyboard = [
        [InlineKeyboardButton("🖼 Premium Banner", callback_data="Banner")],
        [InlineKeyboardButton("✨ Bo'rtma Harflar", callback_data="Bo'rtma harflar")],
        [InlineKeyboardButton("📄 Flayer & Vizitka", callback_data="Flayer / Vizitka")],
        [InlineKeyboardButton("💡 Layt-boks", callback_data="Layt-boks")],
        [InlineKeyboardButton("🏗 Maxsus Loyiha", callback_data="Boshqa / Maxsus loyiha")],
        [InlineKeyboardButton("📞 Biz bilan bog'laning", url="https://t.me/osonreklama_admin")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await update.message.reply_html(
        f"Tushunarli! Bizning AI konsultantimiz sizning so'rovingizga asosan **{service_type}** xizmatini taklif qiladi. \n\n" 
        "Iltimos, quyidagi variantlardan birini tanlang yoki agar boshqa xizmat kerak bo'lsa, uni yozib yuboring: 👇",
        reply_markup=reply_markup,
    )
    return SERVICE_TYPE

async def select_service_type(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    if query:
        await query.answer()
        selected_service = query.data
        await query.edit_message_text(
            text=f"Siz **{selected_service}** xizmatini tanladingiz. Ajoyib tanlov!",
            parse_mode="HTML"
        )
    else:
        selected_service = update.message.text
        await update.message.reply_html(f"Siz **{selected_service}** xizmatini tanladingiz. Ajoyib tanlov!")

    context.user_data["service_type"] = selected_service

    await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text="Endi buyurtmangizning asosiy o'lchamlarini kiriting. \n\n" 
             "**Misol**: `100x200 sm` (eni x bo'yi) yoki `A4` format. \n" 
             "Iltimos, aniq ma'lumot bering. 📏",
        parse_mode="HTML",
        reply_markup=ReplyKeyboardRemove(),
    )
    return DIMENSIONS

async def get_dimensions(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.user_data["dimensions"] = update.message.text
    keyboard = [
        [InlineKeyboardButton("💎 Premium Sifat", callback_data="Premium Sifat")],
        [InlineKeyboardButton("💰 Budjet Variant", callback_data="Budjet Variant")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_html(
        "Material turini tanlang: \n\n" 
        "**💎 Premium Sifat**: Uzoq muddatli, ob-havoga chidamli va estetik jihatdan yuqori materiallar. \n" 
        "**💰 Budjet Variant**: Iqtisodiy jihatdan qulay, ammo sifatli yechimlar. \n\n" 
        "Qaysi biri sizga ma'qul?",
        reply_markup=reply_markup,
    )
    return MATERIAL

async def get_material(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    if query:
        await query.answer()
        context.user_data["material"] = query.data
        await query.edit_message_text(
            text=f"Siz **{query.data}** material turini tanladingiz. Rahmat!",
            parse_mode="HTML"
        )
    else:
        context.user_data["material"] = update.message.text
        await update.message.reply_html(f"Siz **{update.message.text}** material turini tanladingiz. Rahmat!")

    keyboard = [
        [InlineKeyboardButton("✅ Tayyor maketim bor", callback_data="Tayyor maketim bor")],
        [InlineKeyboardButton("🎨 Dizayner kerak", callback_data="Dizayner kerak")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text="Dizayn holatini aniqlaymiz: \n\n" 
             "**✅ Tayyor maketingiz bormi**? Unda bizga yuborishingiz mumkin. \n" 
             "**🎨 Dizayner kerakmi**? Bizning professional dizaynerlar jamoasi sizga yordam beradi. \n\n" 
             "Iltimos, tanlang:",
        parse_mode="HTML",
        reply_markup=reply_markup,
    )
    return DESIGN_STATUS

async def get_design_status(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    if query:
        await query.answer()
        context.user_data["design_status"] = query.data
        await query.edit_message_text(
            text=f"Siz **{query.data}** ni tanladingiz. Tushunarli!",
            parse_mode="HTML"
        )
    else:
        context.user_data["design_status"] = update.message.text
        await update.message.reply_html(f"Siz **{update.message.text}** ni tanladingiz. Tushunarli!")

    await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text="Reklama qayerga o'rnatiladi? \n\n" 
             "**Misol**: `Do'kon peshtoqiga`, `Bino fasadiga`, `Ichki makonga`. \n" 
             "Iltimos, montaj joyini aniq ko'rsating. 📍",
        parse_mode="HTML",
        reply_markup=ReplyKeyboardRemove(),
    )
    return INSTALLATION_LOCATION

async def get_installation_location(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.user_data["installation_location"] = update.message.text
    await update.message.reply_html(
        "Buyurtma qachongacha tayyor bo'lishi kerak? \n\n" 
        "**Misol**: `1 hafta ichida`, `2026-06-01 gacha`, `Shoshilinch`. \n" 
        "Iltimos, muddatni kiriting. ⏳"
    )
    return DEADLINE

async def get_deadline(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.user_data["deadline"] = update.message.text

    summary = (
        """━━━━━━━━━━━━━━━
📋 **BUYURTMA XULOSASI**
━━━━━━━━━━━━━━━

**Xizmat turi**: {service_type}
**O'lchamlari**: {dimensions}
**Material**: {material}
**Dizayn holati**: {design_status}
**Montaj joyi**: {installation_location}
**Muddat**: {deadline}

Ma'lumotlar to'g'rimi? Iltimos, tasdiqlang yoki tahrirlang. 👇""".format(
            service_type=context.user_data.get("service_type"),
            dimensions=context.user_data.get("dimensions"),
            material=context.user_data.get("material"),
            design_status=context.user_data.get("design_status"),
            installation_location=context.user_data.get("installation_location"),
            deadline=context.user_data.get("deadline")
        )
    )
    keyboard = [
        [InlineKeyboardButton("✅ Tasdiqlash", callback_data="Tasdiqlash")],
        [InlineKeyboardButton("✏️ Tahrirlash", callback_data="Tahrirlash")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await update.message.reply_html(summary, reply_markup=reply_markup)
    return CONFIRM_ORDER

async def confirm_order(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    response = query.data

    if response == "Tasdiqlash":
        user = update.effective_user
        database.add_user(user.id, context.user_data.get("name"), context.user_data.get("phone_number"))
        order_id = database.add_order(
            user.id,
            context.user_data.get("service_type"),
            context.user_data.get("dimensions"),
            context.user_data.get("material"),
            context.user_data.get("design_status"),
            context.user_data.get("installation_location"),
            context.user_data.get("deadline"),
            "Kutilmoqda"
        )

        admin_message = (
            """🆕 **YANGI BUYURTMA** #{order_id}

━━━━━━━━━━━━━━━
👤 **Mijoz ma'lumotlari**:
━━━━━━━━━━━━━━━
**Ismi**: {name}
**Telefon raqami**: {phone_number}
**Telegram profili**: @{username} (ID: `{user_id}`)

━━━━━━━━━━━━━━━
📝 **Texnik vazifa**:
━━━━━━━━━━━━━━━
**1. Xizmat turi**: {service_type}
**2. O'lchamlari**: {dimensions}
**3. Material**: {material}
**4. Dizayn holati**: {design_status}
**5. Montaj joyi**: {installation_location}
**6. Muddat**: {deadline}

**Status**: ⏳ Kutilmoqda""".format(
                order_id=order_id,
                name=context.user_data.get("name"),
                phone_number=context.user_data.get("phone_number"),
                username=user.username,
                user_id=user.id,
                service_type=context.user_data.get("service_type"),
                dimensions=context.user_data.get("dimensions"),
                material=context.user_data.get("material"),
                design_status=context.user_data.get("design_status"),
                installation_location=context.user_data.get("installation_location"),
                deadline=context.user_data.get("deadline")
            )
        )

        admin_keyboard = [
            [InlineKeyboardButton("✅ Qabul qildim", callback_data=f"admin_accept_{order_id}")],
            [InlineKeyboardButton("🔄 Jarayonda", callback_data=f"admin_process_{order_id}")]
        ]
        admin_reply_markup = InlineKeyboardMarkup(admin_keyboard)

        if config.ADMIN_CHAT_ID:
            await context.bot.send_message(chat_id=config.ADMIN_CHAT_ID, text=admin_message, parse_mode="HTML", reply_markup=admin_reply_markup)

        await query.edit_message_text("Buyurtmangiz muvaffaqiyatli qabul qilindi! 🎉 Tez orada siz bilan bog'lanamiz. Ishonchingiz uchun rahmat! 🙏", parse_mode="HTML")
        return ConversationHandler.END
    elif response == "Tahrirlash":
        await query.edit_message_text("Iltimos, xizmat turini qaytadan tanlang yoki yozing: 👇", parse_mode="HTML")
        return AI_CONSULTANT
    return CONFIRM_ORDER

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    await update.message.reply_text("Muloqot yakunlandi. Xizmatlarimiz kerak bo'lsa, yana bog'laning! 😊", reply_markup=ReplyKeyboardRemove())
    return ConversationHandler.END

def main() -> None:
    application = Application.builder().token(config.BOT_TOKEN).build()

    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={
            NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_name)],
            PHONE_NUMBER: [MessageHandler(filters.CONTACT | filters.TEXT, get_phone_number)],
            AI_CONSULTANT: [MessageHandler(filters.TEXT & ~filters.COMMAND, ai_consultant)],
            SERVICE_TYPE: [CallbackQueryHandler(select_service_type), MessageHandler(filters.TEXT & ~filters.COMMAND, select_service_type)],
            DIMENSIONS: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_dimensions)],
            MATERIAL: [CallbackQueryHandler(get_material), MessageHandler(filters.TEXT & ~filters.COMMAND, get_material)],
            DESIGN_STATUS: [CallbackQueryHandler(get_design_status), MessageHandler(filters.TEXT & ~filters.COMMAND, get_design_status)],
            INSTALLATION_LOCATION: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_installation_location)],
            DEADLINE: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_deadline)],
            CONFIRM_ORDER: [CallbackQueryHandler(confirm_order)],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
    )

    application.add_handler(conv_handler)
    application.run_polling()

if __name__ == "__main__":
    main()
