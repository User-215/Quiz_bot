import asyncio
import logging
import os
from aiogram import Bot, Dispatcher, types
from aiogram.filters.command import Command
from aiogram.utils.keyboard import ReplyKeyboardBuilder
from aiogram import F
from handlers import create_table, new_quiz, check_answer, statistic
from dotenv import load_dotenv

# Включаем логирование, чтобы не пропустить важные сообщения
logging.basicConfig(level=logging.INFO)

# Загружем токен бота из файла .env
load_dotenv('token.env')

# Объект бота
bot = Bot(token=os.getenv("API_TOKEN"))

# Диспетчер
dp = Dispatcher()

# Хэндлер на коллбек клавиатуры с вариантами ответов
@dp.callback_query()
async def tap_answer(callback: types.CallbackQuery) -> None:
    await check_answer(callback)

# Хэндлер на команду /start
@dp.message(Command("start"))
async def cmd_start(message: types.Message) -> None:
    builder = ReplyKeyboardBuilder()
    builder.add(types.KeyboardButton(text="Начать игру"))
    builder.add(types.KeyboardButton(text="Статистика"))
    builder.add(types.KeyboardButton(text="Помощь"))
    await message.answer("Добро пожаловать в квиз!", reply_markup=builder.as_markup(resize_keyboard=True))

# Хэндлер на команду /quiz
@dp.message(F.text=="Начать игру")
@dp.message(Command("quiz"))
async def cmd_quiz(message: types.Message) -> None:
    await message.answer("Давайте начнём квиз!")
    await new_quiz(message)

# Хэндлер на команду /statistic
@dp.message(F.text=="Статистика")
@dp.message(Command("statistic"))
async def cmd_statistic(message: types.Message) -> None:
    current_user_id = message.from_user.id
    last_scores = await statistic()
    result = [f'{user_id} \\- {user_name} \\- {last_score}' if user_id != current_user_id else f'_*__{user_id} \\- {user_name} \\- {last_score}__*_' for user_id, user_name, last_score in last_scores]
    await message.answer('\n'.join(['ID \\- Name \\- Score'] + result), parse_mode='MarkdownV2')

# Хэндлер на команду /help
@dp.message(F.text=="Помощь")
@dp.message(Command("help"))
async def cmd_help(message: types.Message) -> None:
    try:
        # Читаем содержимое файла
        with open('help.md2') as file:
            readme_content = file.read()
        # Отправляем содержимое файла как сообщение с Markdown-разметкой
        await message.answer(readme_content, parse_mode='MarkdownV2')
    except FileNotFoundError:
        await message.answer("Файл help.md не найден.")
    except Exception as e:
        await message.answer(f"Возникла ошибка: {e}")

async def main() -> None:

    # Запускаем создание таблицы базы данных
    await create_table()

    # Запуск процесса поллинга новых апдейтов
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())