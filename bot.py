import logging
from aiogram import Bot, Dispatcher, types
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.filters import Command
from datetime import datetime
import sqlite3
from calendar import monthcalendar

# Настройка логирования
logging.basicConfig(level=logging.INFO)

# Инициализация бота и диспетчера
API_TOKEN = '7600398699:AAGlzLpkKLrQ-OmG3tyaGN0uyss6rdxJAgM'  # Замените на ваш токен
bot = Bot(token=API_TOKEN)
dp = Dispatcher()

# Подключение к базе данных SQLite
conn = sqlite3.connect('habits.db')
cursor = conn.cursor()

# Создание таблицы для хранения данных
cursor.execute('''
CREATE TABLE IF NOT EXISTS habits (
    user_id INTEGER,
    username TEXT,
    date TEXT,
    drank INTEGER DEFAULT 0,
    smoked INTEGER DEFAULT 0,
    PRIMARY KEY (user_id, date)
)
''')
conn.commit()

# Создание клавиатуры с кнопками
def create_main_keyboard():
    markup = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="🔵 Пил", callback_data="drink"),
            InlineKeyboardButton(text="🟢 Курил", callback_data="smoke")
        ],
        [
            InlineKeyboardButton(text="🔴 Пил и курил", callback_data="both"),
            InlineKeyboardButton(text="⚪️ Ничего", callback_data="none")
        ],
        [
            InlineKeyboardButton(text="📅 Мой календарь", callback_data="my_calendar"),
            InlineKeyboardButton(text="📅 Календарь группы", callback_data="group_calendar")
        ]
    ])
    return markup

# Команда /start
@dp.message(Command("start"))
async def send_welcome(message: types.Message):
    markup = create_main_keyboard()
    await message.reply("Привет! Я бот для отслеживания привычек. Выбери действие:", reply_markup=markup)

# Обработка нажатий на кнопки
@dp.callback_query()
async def process_callback(callback_query: types.CallbackQuery):
    user_id = callback_query.from_user.id
    username = callback_query.from_user.username
    date = datetime.now().strftime('%Y-%m-%d')
    action = callback_query.data

    if action == "drink":
        cursor.execute('INSERT OR REPLACE INTO habits (user_id, username, date, drank) VALUES (?, ?, ?, ?)', (user_id, username, date, 1))
        conn.commit()
        await bot.answer_callback_query(callback_query.id, "Отметил, что ты пил сегодня!")
    elif action == "smoke":
        cursor.execute('INSERT OR REPLACE INTO habits (user_id, username, date, smoked) VALUES (?, ?, ?, ?)', (user_id, username, date, 1))
        conn.commit()
        await bot.answer_callback_query(callback_query.id, "Отметил, что ты курил сегодня!")
    elif action == "both":
        cursor.execute('INSERT OR REPLACE INTO habits (user_id, username, date, drank, smoked) VALUES (?, ?, ?, ?, ?)', (user_id, username, date, 1, 1))
        conn.commit()
        await bot.answer_callback_query(callback_query.id, "Отметил, что ты пил и курил сегодня!")
    elif action == "none":
        cursor.execute('INSERT OR REPLACE INTO habits (user_id, username, date, drank, smoked) VALUES (?, ?, ?, ?, ?)', (user_id, username, date, 0, 0))
        conn.commit()
        await bot.answer_callback_query(callback_query.id, "Отметил, что ты ничего не делал сегодня!")
    elif action == "my_calendar":
        await show_calendar(callback_query)
    elif action == "group_calendar":
        await show_group_calendar(callback_query)

# Функция для создания календаря
def create_calendar(year, month, records):
    cal = monthcalendar(year, month)
    calendar_str = "Пн Вт Ср Чт Пт Сб Вс\n"
    for week in cal:
        week_str = ""
        for day in week:
            if day == 0:
                week_str += "   "  # Пустое место для дней вне текущего месяца
            else:
                date = f"{year}-{month:02d}-{day:02d}"
                if date in records:
                    if records[date]['drank'] and records[date]['smoked']:
                        week_str += f"🔴{day:2d} "  # Пил и курил
                    elif records[date]['drank']:
                        week_str += f"🔵{day:2d} "  # Пил
                    elif records[date]['smoked']:
                        week_str += f"🟢{day:2d} "  # Курил
                    else:
                        week_str += f"⚪️{day:2d} "  # Ничего
                else:
                    week_str += f"{day:2d} "  # Нет данных
        calendar_str += week_str + "\n"
    return calendar_str

# Показать календарь пользователя
async def show_calendar(callback_query: types.CallbackQuery):
    user_id = callback_query.from_user.id
    username = callback_query.from_user.username
    cursor.execute('SELECT date, drank, smoked FROM habits WHERE user_id = ?', (user_id,))
    records = {row[0]: {'drank': row[1], 'smoked': row[2]} for row in cursor.fetchall()}

    now = datetime.now()
    calendar_str = create_calendar(now.year, now.month, records)
    response = f"Календарь @{username} за {now.strftime('%B %Y')}:\n```\n{calendar_str}\n```"

    await bot.send_message(callback_query.from_user.id, response, parse_mode="Markdown")

# Показать календарь группы
async def show_group_calendar(callback_query: types.CallbackQuery):
    cursor.execute('SELECT DISTINCT user_id, username FROM habits')
    users = cursor.fetchall()

    now = datetime.now()
    response = f"Календари всех участников за {now.strftime('%B %Y')}:\n\n"

    for user in users:
        user_id, username = user
        cursor.execute('SELECT date, drank, smoked FROM habits WHERE user_id = ?', (user_id,))
        records = {row[0]: {'drank': row[1], 'smoked': row[2]} for row in cursor.fetchall()}

        calendar_str = create_calendar(now.year, now.month, records)
        response += f"@{username}:\n```\n{calendar_str}\n```\n"

    await bot.send_message(callback_query.from_user.id, response, parse_mode="Markdown")

# Запуск бота
if __name__ == '__main__':
    dp.start_polling(bot)