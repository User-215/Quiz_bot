import aiosqlite
from aiogram import types
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram import types
from questions import quiz_data
from time import strftime, gmtime 

# Зададём имя базы данных
DB_NAME = 'quiz_bot.db'

def current_time() -> str:
    return strftime("%d.%m.%Y %H:%M:%S", gmtime())

async def create_table() -> None:
    # Создаем соединение с базой данных (если она не существует, она будет создана)
    async with aiosqlite.connect(DB_NAME) as db:
        # Создаем таблицу
        await db.execute('''CREATE TABLE IF NOT EXISTS quiz_state (user_id INTEGER PRIMARY KEY, user_name TEXT, question_index INTEGER, score INTEGER, last_score INTEGER, message_id INTEGER)''')
        # # Сохраняем изменения
        await db.commit()

async def get_quiz_index(user_id: int) -> int:
     # Подключаемся к базе данных
     async with aiosqlite.connect(DB_NAME) as db:
        # Получаем запись для заданного пользователя
        async with db.execute('SELECT question_index FROM quiz_state WHERE user_id = (?)', (user_id, )) as cursor:
            # Возвращаем результат
            result = await cursor.fetchone()
            return result[0] if result is not None else 0

async def update_quiz_index(user_id: int, index: int) -> None:
    # Создаем соединение с базой данных (если она не существует, она будет создана)
    async with aiosqlite.connect(DB_NAME) as db:
        # Обновляем запись
        await db.execute(f'UPDATE quiz_state SET question_index = {index} WHERE user_id = {user_id}')
        # Сохраняем изменения
        await db.commit()

async def get_score(user_id: int) -> int:
     # Подключаемся к базе данных
     async with aiosqlite.connect(DB_NAME) as db:
        # Получаем запись для заданного пользователя
        async with db.execute('SELECT score FROM quiz_state WHERE user_id = (?)', (user_id, )) as cursor:
            # Возвращаем результат
            result = await cursor.fetchone()
            return result[0] if result is not None else 0

async def update_score(user_id: int, score: int) -> None:
    # Создаем соединение с базой данных (если она не существует, она будет создана)
    async with aiosqlite.connect(DB_NAME) as db:
        # Обновляем запись
        await db.execute('UPDATE quiz_state SET score = (?) WHERE user_id = (?)', (score, user_id))
        # Сохраняем изменения
        await db.commit()

async def update_last_score(user_id: int, score: int) -> None:
    # Создаем соединение с базой данных (если она не существует, она будет создана)
    async with aiosqlite.connect(DB_NAME) as db:
        # Обновляем запись
        await db.execute(f'UPDATE quiz_state SET last_score = {score} WHERE user_id = {user_id}')
        # Сохраняем изменения
        await db.commit()

def generate_options_keyboard(answer_options: tuple) -> types.InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()

    for i, option in enumerate(answer_options):
        builder.add(
            types.InlineKeyboardButton(
                text=option,
                callback_data=str(i)
            )
        )

    builder.adjust(1)
    return builder.as_markup()

async def get_question(message: types.Message, user_id: int) -> None:
    # Получение текущего вопроса из словаря состояний пользователя
    current_question_index = await get_quiz_index(user_id)
    print(current_time(), user_id, 'Текущий вопрос', current_question_index)
    opts = quiz_data[current_question_index]['options']
    kb = generate_options_keyboard(opts)
    current_message = await message.answer(f"Вопрос {current_question_index + 1} из {len(quiz_data)}\n{quiz_data[current_question_index]['question']}", reply_markup=kb)
    # Создаем соединение с базой данных (если она не существует, она будет создана)
    async with aiosqlite.connect(DB_NAME) as db:
        # Обновляем запись
        await db.execute(f'UPDATE quiz_state SET message_id = {current_message.message_id} WHERE user_id = {user_id}')
        # Сохраняем изменения
        await db.commit()

async def new_quiz(message: types.Message) -> None:
    user_id = message.from_user.id
    user_name = message.from_user.username
    print(current_time(), user_id, 'Начало нового квиза.')
    current_question_index = 0
    current_score = 0
    async with aiosqlite.connect(DB_NAME) as db:
        # Вставляем новую запись, если запись с данным user_id не существует
        await db.execute('INSERT OR IGNORE INTO quiz_state (user_id, user_name, last_score) VALUES (?, ?, ?)', (user_id, user_name, 0))
        # Сохраняем изменения
        await db.commit()
        # Получаем запись с id последнего сообщения с вопросом для заданного пользователя
        async with db.execute('SELECT message_id FROM quiz_state WHERE user_id = (?)', (user_id, )) as cursor:
            # Возвращаем результат
            result = await cursor.fetchone()
            last_message_id = result[0] if result is not None else None
    # Пробуем удалить клавиатуру из последнего сообщения с вопросом
    try:
        await message.bot.edit_message_reply_markup(
            chat_id=user_id,
            message_id=last_message_id,
            reply_markup=None
        )
        print(current_time(), user_id, 'Удалена клавиатура предыдущего квиза.')
    except Exception as E:
        print(current_time(), user_id, 'Ошибка удаления клавиатуры предыдущего квиза:', E)
 
    await update_quiz_index(user_id, current_question_index)
    await update_score(user_id, current_score)
    await get_question(message, user_id)
 
async def check_answer(callback: types.CallbackQuery) -> None:
   # Получение текущего вопроса из словаря состояний пользователя.
    current_question_index = await get_quiz_index(callback.from_user.id)
    correct_option = quiz_data[current_question_index]['correct_option']
    # Выводим сообщение с ответом пользователя.
    await callback.message.answer(quiz_data[current_question_index]['options'][int(callback.data)])
    # Если номер ответа совпадает с номером правильного ответа.
    if callback.data == str(correct_option):
         # Получаем текущий счёт пользователя, увеливичаем его на единицу и выводим сообщение о правильности ответа.
         score = await get_score(callback.from_user.id)
         score += 1
         await update_score(callback.from_user.id, score)
         await callback.message.answer(f"{'\U00002705'} Верно!!! {'\U0001F600'}")
    else:
        # Иначе выводим сообщение о неправильности ответа и правильный ответ.
        await callback.message.answer(f"{'\U0000274C'} Неправильно. {'\U0001F61E'}\nПравильный ответ:\n{quiz_data[current_question_index]['options'][correct_option]}")
 
    # Обновляем номера текущего вопроса в базе данных.
    current_question_index += 1
    await update_quiz_index(callback.from_user.id, current_question_index)
    # Если текущий вопрос не был последним, то задаём следующий вопрос.
    if current_question_index < len(quiz_data):
        await get_question(callback.message, callback.from_user.id)
    else:
        # Иначе запоминаем результат квиза и выводим сообщение об окончании квиза и его результатх.
        score = await get_score(callback.from_user.id)
        await update_last_score(callback.from_user.id, score)
        await callback.message.answer(f"Это был последний вопрос.\nКоличество правильных ответов: {score}\nКвиз завершён!")
    # Удаляем клавиатуру последнего сообщения с вопросом.
    await callback.bot.edit_message_reply_markup(
        chat_id=callback.from_user.id,
        message_id=callback.message.message_id,
        reply_markup=None
    )

async def statistic() -> list:
     # Подключаемся к базе данных
     async with aiosqlite.connect(DB_NAME) as db:
        # Получаем все записи с id пользователя, его именем и последним результатом квиза.
        async with db.execute('SELECT user_id, user_name, last_score FROM quiz_state') as cursor:
            # Возвращаем результат
            results = await cursor.fetchall()
            return results if results is not None else [(0, None, 0)]
