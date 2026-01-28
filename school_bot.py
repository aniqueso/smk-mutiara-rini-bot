# SMK Mutiara Rini Telegram Bot
# This version supports AI answers in English and Malay

import openai, asyncio
from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes, MessageHandler, filters
from apscheduler.schedulers.background import BackgroundScheduler


# ===== CONFIG =====
INFO_KEYWORDS = [
    "teacher", "cikgu", "sejarah", "math", "add math",
    "principal", "pengetua", "history", "rules",
    "school", "smk", "form", "kelas"
]


import json
import os

MEMORY_FILE = "user_memory.json"

def load_memory():
    if not os.path.exists(MEMORY_FILE):
        return {}
    with open(MEMORY_FILE, "r", encoding="utf-8") as f:
        return json.load(f)

def save_memory(memory):
    with open(MEMORY_FILE, "w", encoding="utf-8") as f:
        json.dump(memory, f, indent=4)

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
user_id = str(update.message.from_user.id)
user_name = update.message.from_user.first_name

memory = load_memory()

if user_id not in memory:
    memory[user_id] = {
        "name": user_name,
        "form": None,
        "language": "en"
    }
    save_memory(memory)

if memory[user_id]["form"] is None:
    reply = (
        f"Hey {memory[user_id]['name']} 👋\n"
        "Quick one — you’re Form what?"
    )
    update.message.reply_text(reply)
   

text = update.message.text.lower()

if "form" in text:
    for f in ["1", "2", "3", "4", "5"]:
        if f in text:
            memory[user_id]["form"] = f
            save_memory(memory)
            update.message.reply_text(
                f"Got it 👍 Form {f}. I’ll remember that."
            )
         

text = update.message.text.lower()

is_info = any(keyword in text for keyword in INFO_KEYWORDS)

if not is_info:
    name = memory[user_id]["name"]

    casual_replies = [
        f"Haha yeah 😄 what’s up, {name}?",
        f"Oi {name}, what you thinking about?",
        f"That sounds random 😂 wanna ask about school or just chatting?",
        f"Relatable ngl. School vibes ah?"
    ]

    update.message.reply_text(random.choice(casual_replies))
  

if not is_info and len(text.split()) > 20:
    update.message.reply_text(
        "Haha 😄 I’m here mainly for school stuff, but what’s up?"
    )
    return

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
    SYSTEM_PROMPT = """
You are a friendly senior student from SMK Mutiara Rini.
You have been around the school for years and know the routines, subjects, teachers, and student life.

You speak casually, like a real student helping a junior.
You are supportive, chill, and sometimes humorous, but always respectful.
You explain things clearly without sounding like a textbook.

You never say you are an AI.
You never say you are an official school representative.
You stay within school-related topics.

You naturally ask follow-up questions.
You sound human, not robotic.
If they asks you a question in Malay, answer in Malay, if they ask you in English, answer in English
"""
messages = [
    {"role": "system", "content": SYSTEM_PROMPT},
    {"role": "user", "content": user_message}
]


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


def load_teachers():
    teachers = {}
    with open("teachers.txt", "r", encoding="utf-8") as f:
        for line in f:
            subject, name, forms = line.strip().split("|")
            subject = subject.strip().lower()
            form_list = forms.replace("Forms", "").strip().split(",")

            if subject not in teachers:
                teachers[subject] = []

            teachers[subject].append({
                "name": name.strip(),
                "forms": [f.strip() for f in form_list]
            })
    return teachers
