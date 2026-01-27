# SMK Mutiara Rini Telegram Bot
# This version supports AI answers in English and Malay

import openai, asyncio
from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes, MessageHandler, filters
from apscheduler.schedulers.background import BackgroundScheduler

# ===== CONFIG =====

import os

OPENAI_API_KEY = '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'
TELEGRAM_BOT_TOKEN = '8466417809:AAHQE7aV0pZH0Si-I_h_Zc28bKbihL82u2A'
REGISTRATION_CODE = "SMKMR2026"
ADMIN_REG_CODE = "ADMIN2026"
ADMIN_IDS = []  # multiple admins

openai.api_key = OPENAI_API_KEY

# ===== LOAD SCHOOL DATA =====
with open("history.txt", "r", encoding="utf-8") as f: history = f.read()
with open("teachers.txt", "r", encoding="utf-8") as f: teachers = f.read()
with open("rules.txt", "r", encoding="utf-8") as f: rules = f.read()
with open("faq.txt", "r", encoding="utf-8") as f: faq = f.read()
school_knowledge = f"{history}\n{teachers}\n{rules}\n{faq}"

# ===== LOAD USERS =====
try:
    with open("authorized_users.txt", "r") as f: authorized_ids = [int(line.strip()) for line in f.readlines()]
except: authorized_ids = []

try:
    with open("subscribers.txt", "r") as f: subscribers = [int(line.strip()) for line in f.readlines()]
except: subscribers = []

# ===== /start COMMAND =====
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.message.chat_id
    first_name = update.effective_user.first_name

    if chat_id in authorized_ids:
        welcome_text = f"👋 Hi {first_name}! Welcome back to SMK Mutiara Rini Bot!"
        if chat_id not in subscribers:
            subscribers.append(chat_id)
            with open("subscribers.txt", "a") as f: f.write(str(chat_id)+"\n")
    else:
        welcome_text = f"👋 Hi {first_name}! Welcome! Please enter the registration code to get access."

    buttons = [["School History", "Teachers"], ["Rules", "FAQs"], ["Announcements"]]
    reply_markup = ReplyKeyboardMarkup(buttons, resize_keyboard=True)

    await update.message.reply_text(welcome_text, reply_markup=reply_markup)

# ===== AI & MESSAGE HANDLER =====
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.message.chat_id
    user_message = update.message.text.strip()

    # ===== STUDENT REGISTRATION =====
    if chat_id not in authorized_ids:
        if user_message == REGISTRATION_CODE:
            authorized_ids.append(chat_id)
            with open("authorized_users.txt", "a") as f: f.write(str(chat_id)+"\n")
            if chat_id not in subscribers:
                subscribers.append(chat_id)
                with open("subscribers.txt", "a") as f: f.write(str(chat_id)+"\n")
            await update.message.reply_text(f"✅ Access granted! Welcome to SMK Mutiara Rini Bot, {update.effective_user.first_name}!")
        elif user_message == ADMIN_REG_CODE:
            if chat_id not in ADMIN_IDS:
                ADMIN_IDS.append(chat_id)
                await update.message.reply_text("✅ You are now an admin! You can send announcements using /announcement.")
        else:
            await update.message.reply_text("❌ Please enter the registration code to access this bot.")
        return

    # Add subscriber if new
    if chat_id not in subscribers:
        subscribers.append(chat_id)
        with open("subscribers.txt", "a") as f: f.write(str(chat_id)+"\n")

    # ===== MENU BUTTONS =====
    if user_message.lower() == "school history":
        await update.message.reply_text(history)
        return
    elif user_message.lower() == "teachers":
        await update.message.reply_text(teachers)
        return
    elif user_message.lower() == "rules":
        await update.message.reply_text(rules)
        return
    elif user_message.lower() == "faqs":
        await update.message.reply_text(faq)
        return
    elif user_message.lower() == "announcements":
        await update.message.reply_text("Check /announcement for latest updates (admin only).")
        return

    # ===== AI RESPONSE (English & Malay) =====
    prompt = f"""
You are SMK Mutiara Rini Assistant AI.
#Answer questions based ONLY on the following information:
{school_knowledge}
Answer politely, clearly, simply, in English if the question is in English, in Malay if the question is in Malay. If unrelated, reply: 'I can only answer questions about SMK Mutiara Rini.'
User question: {user_message}
"""
    response = openai.Completion.create(engine="text-davinci-003", prompt=prompt, max_tokens=200)
    await update.message.reply_text(response.choices[0].text.strip())

# ===== /announcement COMMAND =====
async def announcement(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.message.chat_id
    if chat_id not in ADMIN_IDS:
        await update.message.reply_text("❌ You are not authorized to send announcements.")
        return
    message_text = " ".join(context.args)
    if not message_text:
        await update.message.reply_text("❌ Please provide a message after the command.")
        return
    for cid in subscribers:
        try: await context.bot.send_message(chat_id=int(cid), text=f"📢 Announcement:\n{message_text}")
        except: pass
    await update.message.reply_text("✅ Announcement sent to all subscribers.")

# ===== SCHEDULED ANNOUNCEMENTS =====
async def scheduled_announcement(message_text):
    for cid in subscribers:
        try: await app.bot.send_message(chat_id=int(cid), text=f"📢 Scheduled Announcement:\n{message_text}")
        except: pass

def scheduler_job():
    asyncio.run(scheduled_announcement("📢 Weekly reminder: submit your homework by Friday!"))

scheduler = BackgroundScheduler()
scheduler.add_job(scheduler_job, 'cron', day_of_week='mon', hour=7, minute=0)
scheduler.start()

# ===== MAIN =====
app = ApplicationBuilder().token(TELEGRAM_BOT_TOKEN).build()
app.add_handler(CommandHandler("start", start))
app.add_handler(CommandHandler("announcement", announcement))
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

print("Bot is running...")
app.run_polling()