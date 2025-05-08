import logging
import sqlite3
import requests
import os
from datetime import datetime, timedelta
from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    CallbackQueryHandler,
    ContextTypes,
)
from apscheduler.schedulers.background import BackgroundScheduler
from dotenv import load_dotenv

# Load environment variables
load_dotenv()
BOT_TOKEN = os.getenv("BOT_TOKEN")

# Database setup
def init_db():
    conn = sqlite3.connect("data.db")
    c = conn.cursor()
    
    # Users table
    c.execute('''CREATE TABLE IF NOT EXISTS users (
        user_id INTEGER PRIMARY KEY,
        streak INTEGER DEFAULT 0,
        ice INTEGER DEFAULT 0,
        last_done DATE,
        reminder_time TEXT DEFAULT '08:00',
        current_page INTEGER DEFAULT 1,
        language TEXT DEFAULT 'en'
    )''')
    
    # Bookmarks table
    c.execute('''CREATE TABLE IF NOT EXISTS bookmarks (
        user_id INTEGER,
        page INTEGER,
        created DATE,
        FOREIGN KEY(user_id) REFERENCES users(user_id)
    )''')
    
    conn.commit()
    conn.close()

# Database helper functions
def get_user(user_id):
    conn = sqlite3.connect("data.db")
    c = conn.cursor()
    c.execute("SELECT * FROM users WHERE user_id=?", (user_id,))
    user = c.fetchone()
    conn.close()
    return user

def update_streak(user_id, increment=True):
    conn = sqlite3.connect("data.db")
    c = conn.cursor()
    if increment:
        c.execute("UPDATE users SET streak = streak + 1, last_done = DATE('now') WHERE user_id=?", (user_id,))
    else:
        c.execute("UPDATE users SET streak = 0 WHERE user_id=?", (user_id,))
    conn.commit()
    conn.close()

class QuranAPI:
    @staticmethod
    def get_page(page, language='en'):
        valid_editions = {
            'en': 'en.asad',
            'ar': 'quran-uthmani'
        }
        edition = valid_editions.get(language, 'en.asad')
        url = f"https://api.alquran.cloud/v1/page/{page}/{edition}"
        
        try:
            response = requests.get(url, timeout=5)
            if response.status_code == 200:
                return response.json()
            return None
        except Exception as e:
            logging.error(f"Quran API Error: {str(e)}")
            return None

async def show_page(update: Update, page: int):
    user = get_user(update.effective_user.id)
    data = QuranAPI.get_page(page, user[6])  # user[6] is the language
    
    try:
        if data and 'data' in data:
            # Extract Arabic text from ayahs
            arabic_text = "\n".join([ayah['text'] for ayah in data['data']['ayahs']])
            
            # Extract translation text
            translation_text = data['data']['edition']['text']
            
            text = f"📖 Page {page}\n\n"
            text += f"{arabic_text}\n\n"
            text += f"Translation:\n{translation_text}"
            
            await update.callback_query.edit_message_text(
                text=text,
                reply_markup=InlineKeyboardMarkup([
                    [
                        InlineKeyboardButton("◀️", callback_data=f"page_{max(1, page-1)}"),
                        InlineKeyboardButton(f"{page}/604", callback_data="current"),
                        InlineKeyboardButton("▶️", callback_data=f"page_{min(604, page+1)}")
                    ],
                    [InlineKeyboardButton("🔖 Bookmark", callback_data=f"bookmark_{page}")],
                    [InlineKeyboardButton("🏠 Main Menu", callback_data="main")]
                ])
            )
        else:
            await update.callback_query.edit_message_text("Error loading page. Please try again.")
            
    except KeyError as e:
        logging.error(f"API Structure Error: {str(e)}")
        await update.callback_query.edit_message_text("⚠️ Error loading Quran content. Please try another page.")
# Bot setup
logging.basicConfig(level=logging.INFO)
scheduler = BackgroundScheduler()
init_db()

# Main menu buttons
# Main menu buttons
def get_main_buttons(user_id):
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("📖 Read Quran", callback_data="page_1")],
        [InlineKeyboardButton("✅ Mark Done", callback_data="done")],
        [
            InlineKeyboardButton("📊 My Progress", callback_data="progress"),
            InlineKeyboardButton("⏰ Set Reminder", callback_data="reminder")
        ],
        [InlineKeyboardButton("🔖 My Bookmarks", callback_data="bookmarks")]
    ])

# Command handlers
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if not get_user(user_id):
        conn = sqlite3.connect("data.db")
        c = conn.cursor()
        c.execute("INSERT INTO users (user_id) VALUES (?)", (user_id,))
        conn.commit()
        conn.close()
    
    await update.message.reply_text(
        "🕌 Welcome to Quran Reminder Bot!",
        reply_markup=get_main_buttons(user_id)
    )

async def show_page(update: Update, page: int):
    user = get_user(update.effective_user.id)
    data = QuranAPI.get_page(page, user[6])
    
    if data and 'data' in data:
        try:
            # Use correct API response structure
            text = f"📖 Page {page}\n\n"
            text += f"{data['data']['text']}\n\n"  # Direct text access
            text += f"Translation: {data['data']['translations'][0]['text']}"
            
        except KeyError as e:
            text = f"⚠️ Error parsing Quran data: {str(e)}"
    else:
        text = "Error loading page. Please try again."
    
    # ... keyboard markup code ...
        
    await update.callback_query.edit_message_text(
        text=text,
        reply_markup=InlineKeyboardMarkup([
            [  # First row
                InlineKeyboardButton("◀️", callback_data=f"page_{max(1, page-1)}"),
                InlineKeyboardButton(f"{page}/604", callback_data="current"),
                InlineKeyboardButton("▶️", callback_data=f"page_{min(604, page+1)}")
            ],
            [  # Second row
                InlineKeyboardButton("🔖 Bookmark", callback_data=f"bookmark_{page}")
            ],
            [  # Third row
                InlineKeyboardButton("🏠 Main Menu", callback_data="main")
            ]
        ])
    )

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    data = query.data
    
    if data.startswith("page_"):
        await show_page(update, int(data.split("_")[1]))
    elif data == "done":
        await mark_done(update)
    elif data.startswith("bookmark_"):
        await add_bookmark(update, int(data.split("_")[1]))
    elif data == "progress":
        await show_progress(update)
    elif data == "reminder":
        await show_reminder_options(update)
    elif data.startswith("setreminder_"):
        time_str = data.split('_')[1]
        user_id = query.from_user.id
        conn = sqlite3.connect("data.db")
        c = conn.cursor()
        c.execute("UPDATE users SET reminder_time = ? WHERE user_id = ?", (time_str, user_id))
        conn.commit()
        conn.close()
        await query.edit_message_text(f"⏰ Reminder set to {time_str}!", reply_markup=get_main_buttons(user_id))
    elif data == "main":
        await query.edit_message_text(
            "Main Menu:",
            reply_markup=get_main_buttons(query.from_user.id)
        )

async def add_bookmark(update: Update, page: int):
    query = update.callback_query
    user_id = query.from_user.id
    conn = sqlite3.connect("data.db")
    c = conn.cursor()
    
    # Check for existing bookmark
    c.execute("SELECT * FROM bookmarks WHERE user_id=? AND page=?", (user_id, page))
    if c.fetchone():
        await query.answer("⚠️ Bookmark already exists!")
    else:
        c.execute("INSERT INTO bookmarks (user_id, page, created) VALUES (?, ?, DATE('now'))", (user_id, page))
        conn.commit()
        await query.answer("🔖 Bookmark added!")
    conn.close()

async def show_progress(update: Update):
    query = update.callback_query
    user_id = query.from_user.id
    user = get_user(user_id)
    
    if user:
        progress_text = (
            f"📊 Your Progress:\n\n"
            f"🔥 Current Streak: {user[1]} days\n"
            f"❄️ Ice Points: {user[2]}\n"
            f"📅 Last Reading: {user[3] if user[3] else 'Never'}"
        )
        await query.edit_message_text(
            progress_text,
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🏠 Main Menu", callback_data="main")]])
        )
    else:
        await query.edit_message_text("User not found.")

async def show_reminder_options(update: Update):
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("8:00 AM", callback_data="setreminder_08:00"),
         InlineKeyboardButton("12:00 PM", callback_data="setreminder_12:00")],
        [InlineKeyboardButton("6:00 PM", callback_data="setreminder_18:00"),
         InlineKeyboardButton("8:00 PM", callback_data="setreminder_20:00")],
        [InlineKeyboardButton("Cancel", callback_data="main")]
    ])
    await update.callback_query.edit_message_text(
        "⏰ Choose your preferred reminder time:",
        reply_markup=keyboard
    )

async def mark_done(update: Update):
    query = update.callback_query
    user_id = query.from_user.id
    user = get_user(user_id)
    
    if user[3] == datetime.now().date().isoformat():
        await query.edit_message_text("✅ Already marked today!")
    else:
        update_streak(user_id)
        await query.edit_message_text(
            "✅ Quran reading recorded!",
            reply_markup=get_main_buttons(user_id)
        )

async def send_reminders(app):
    current_time = datetime.now().strftime("%H:%M")
    conn = sqlite3.connect("data.db")
    c = conn.cursor()
    c.execute("SELECT user_id FROM users WHERE reminder_time = ?", (current_time,))
    users = c.fetchall()
    
    for user in users:
        try:
            await app.bot.send_message(
                chat_id=user[0],
                text="📖 Don't forget to read Quran today!",
                reply_markup=get_main_buttons(user[0])
            )
        except Exception as e:
            logging.error(f"Reminder error for {user[0]}: {str(e)}")
    
    conn.close()

# Modify the scheduler job to properly handle async
def main():
    app = ApplicationBuilder().token(BOT_TOKEN).build()
    
    # Handlers
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(button_handler))
    
    # Create wrapper for async execution
    async def send_reminders_wrapper():
        await send_reminders(app)
    
    # Scheduler configuration
    scheduler.add_job(
        lambda: app.updater.bot._loop.create_task(send_reminders_wrapper()),
        'cron',
        minute='*',
        misfire_grace_time=60
    )
    
    scheduler.start()
    app.run_polling()
if __name__ == "__main__":
    main()