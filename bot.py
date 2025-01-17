import logging
from aiogram import Bot, Dispatcher, types
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.filters import Command
from datetime import datetime
import sqlite3

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
    date TEXT,
    drank INTEGER DEFAULT 0,
    smoked INTEGER DEFAULT 0,
    PRIMARY KEY (user_id, date)
)
''')
conn.commit()

# Создание клавиатуры с кнопками
def create_markup():
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
            InlineKeyboardButton(text="📅 Календарь", callback_data="calendar")
        ]
    ])
    return markup

# Команда /start
@dp.message(Command("start"))
async def send_welcome(message: types.Message):
    markup = create_markup()
    await message.reply("Привет! Я бот для отслеживания твоих привычек. Выбери действие:", reply_markup=markup)

# Обработка нажатий на кнопки
@dp.callback_query()
async def process_callback(callback_query: types.CallbackQuery):
    user_id = callback_query.from_user.id
    date = datetime.now().strftime('%Y-%m-%d')
    action = callback_query.data

    if action == "drink":
        cursor.execute('INSERT OR REPLACE INTO habits (user_id, date, drank) VALUES (?, ?, ?)', (user_id, date, 1))
        conn.commit()
        await bot.answer_callback_query(callback_query.id, "Отметил, что ты пил сегодня!")
    elif action == "smoke":
        cursor.execute('INSERT OR REPLACE INTO habits (user_id, date, smoked) VALUES (?, ?, ?)', (user_id, date, 1))
        conn.commit()
        await bot.answer_callback_query(callback_query.id, "Отметил, что ты курил сегодня!")
    elif action == "both":
        cursor.execute('INSERT OR REPLACE INTO habits (user_id, date, drank, smoked) VALUES (?, ?, ?, ?)', (user_id, date, 1, 1))
        conn.commit()
        await bot.answer_callback_query(callback_query.id, "Отметил, что ты пил и курил сегодня!")
    elif action == "none":
        cursor.execute('INSERT OR REPLACE INTO habits (user_id, date, drank, smoked) VALUES (?, ?, ?, ?)', (user_id, date, 0, 0))
        conn.commit()
        await bot.answer_callback_query(callback_query.id, "Отметил, что ты ничего не делал сегодня!")
    elif action == "calendar":
        await show_calendar(callback_query)

# Функция для отображения календаря
async def show_calendar(callback_query: types.CallbackQuery):
    user_id = callback_query.from_user.id
    cursor.execute('SELECT date, drank, smoked FROM habits WHERE user_id = ?', (user_id,))
    records = cursor.fetchall()

    calendar = {}
    for record in records:
        date, drank, smoked = record
        if drank and smoked:
            calendar[date] = '🔴'  # И пил, и курил
        elif drank:
            calendar[date] = '🔵'  # Пил
        elif smoked:
            calendar[date] = '🟢'  # Курил
        else:
            calendar[date] = '⚪️'  # Ничего

    response = "Твой календарь:\n"
    for date, emoji in calendar.items():
        response += f"{date}: {emoji}\n"

    await bot.send_message(callback_query.from_user.id, response)

# Запуск бота
if __name__ == '__main__':
    dp.run_polling(bot)