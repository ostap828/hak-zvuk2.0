import asyncio
import logging
from aiogram import Router, types, F, Bot
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.filters.command import Command
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup, Message, CallbackQuery
from sqlalchemy.ext.asyncio import async_session, AsyncSession
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.dispatcher.dispatcher import Dispatcher
from DB import User, History, create_tables as init_db, async_session as async_session_maker, create_history, get_user_history
from aiogram.dispatcher.middlewares.base import BaseMiddleware
from typing import Any, Awaitable, Callable, Dict
from sqlalchemy import select

# Создаем роутер
router = Router()


# Класс для состояний бота
class BotStates(StatesGroup):
    waiting_for_name = State()
    analytics_mode = State()
    chat_tz = State()


# Хранение истории анализов (в реальном проекте лучше использовать базу данных)
analyses = {}


# Клавиатуры
def get_analytics_keyboard():
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="Выход из режима аналитики", callback_data="exit_analytics"),
            InlineKeyboardButton(text="Чат по ТЗ", callback_data="chat_tz")
        ]
    ])
    return keyboard


def get_history_keyboard():
    buttons = []
    for analysis_id, analysis in analyses.items():
        buttons.append([InlineKeyboardButton(
            text=f"Анализ {analysis_id}",
            callback_data=f"analysis_{analysis_id}"
        )])
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def get_analysis_options_keyboard():
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="Режим аналитики", callback_data="start_analytics"),
            InlineKeyboardButton(text="Удаление анализа", callback_data="delete_analysis"),
            InlineKeyboardButton(text="Назад", callback_data="back_to_history")
        ]
    ])
    return keyboard


# Обработчики команд


@router.message(Command("start"))
@router.message(F.text.lower() == "регистрация")
async def register_user(message: Message, session: AsyncSession):
    """Регистрация пользователя в базе данных"""
    user_id = message.from_user.id
    username = message.from_user.full_name

    try:
        # Проверяем, есть ли пользователь уже в базе по users_id
        existing_user = await session.execute(select(User).where(User.users_id == user_id))
        existing_user = existing_user.scalar_one_or_none()
        
        if existing_user:
            await message.answer("🔄 Вы уже зарегистрированы!")
            return

        # Создаем нового пользователя
        new_user = User(
            users_id=user_id,
            users_name=username
        )

        session.add(new_user)
        await session.commit()

        await message.answer(
            "✅ Регистрация успешна!\n"
            f"ID: {user_id}\n"
            f"Имя: {username}"
        )

    except Exception as e:
        await session.rollback()
        await message.answer("❌ Ошибка при регистрации. Попробуйте позже.")
        print(f"Ошибка регистрации: {e}")


@router.message(BotStates.waiting_for_name)
async def process_name(message: types.Message, state: FSMContext, session: AsyncSession):
    user_name = message.text
    user_id = message.from_user.id

    if len(user_name) < 2:
        await message.reply("Имя должно содержать хотя бы 2 символа. Попробуйте еще раз:")
        return

    # Здесь исправляем поле на правильное имя из модели User
    new_user = User(
        users_id=user_id,  # Используйте правильное имя поля из вашей модели
        users_name=user_name
    )
    session.add(new_user)
    await session.commit()

    await message.reply(
        f"Отлично, {user_name}! Добро пожаловать! Используйте /help для получения списка команд."
    )
    await state.clear()


@router.message(Command("help"))
async def cmd_help(message: types.Message):
    help_text = """
    🤖 Описание работы сервиса:

    /upload_tech - Запуск режима аналитики
    /history - Просмотр предыдущих анализов
    /help - Показать это сообщение

    В режиме аналитики вы можете:
    - Общаться с ботом по ТЗ
    - Выйти из режима аналитики

    В истории анализов вы можете:
    - Просматривать прошлые анализы
    - Удалять анализы
    - Запускать режим аналитики для выбранного анализа
    """
    await message.reply(help_text)


@router.message(Command("upload_tech"))
async def cmd_upload_tech(message: types.Message, state: FSMContext, session: AsyncSession):
    user_id = message.from_user.id
    
    try:
        # Создаем запись в истории при загрузке ТЗ
        history_record = await create_history(
            session=session,
            users_id=user_id,
            path_to_tz="path/to/tz",  # Здесь нужно указать реальный путь к ТЗ
            path_to_analyze="path/to/analysis"  # Здесь нужно указать реальный путь к анализу
        )
        await session.commit()
        
        await state.set_state(BotStates.analytics_mode)
        await message.reply(
            "Режим аналитики активирован.",
            reply_markup=get_analytics_keyboard()
        )
    except Exception as e:
        await session.rollback()
        await message.reply(f"Ошибка при создании записи в истории: {e}")


@router.message(Command("history"))
async def cmd_history(message: types.Message, session: AsyncSession):
    user_id = message.from_user.id
    
    try:
        # Получаем историю пользователя из базы данных
        user_history = await get_user_history(session, users_id=user_id)
        
        if not user_history:
            await message.reply("История анализов пуста.")
            return

        # Создаем клавиатуру с историей
        buttons = []
        for history in user_history:
            buttons.append([InlineKeyboardButton(
                text=f"Анализ #{history.id}",
                callback_data=f"analysis_{history.id}"
            )])
        
        keyboard = InlineKeyboardMarkup(inline_keyboard=buttons)
        await message.reply("Предыдущие анализы:", reply_markup=keyboard)
        
    except Exception as e:
        await message.reply(f"Ошибка при получении истории: {e}")


# Обработчики callback'ов
@router.callback_query(F.data == "chat_tz")
async def process_chat_tz(callback_query: types.CallbackQuery, state: FSMContext):
    await state.set_state(BotStates.chat_tz)
    await callback_query.message.reply("Режим чата по ТЗ активирован. Напишите ваше сообщение.")
    await callback_query.answer()


@router.callback_query(F.data == "exit_analytics")
async def process_exit_analytics(callback_query: types.CallbackQuery, state: FSMContext):
    await state.clear()
    await callback_query.message.reply("Режим аналитики деактивирован.")
    await callback_query.answer()


@router.callback_query(F.data.startswith("analysis_"))
async def process_analysis_selection(callback_query: types.CallbackQuery):
    analysis_id = callback_query.data.split("_")[1]
    await callback_query.message.reply(
        f"Выбран анализ {analysis_id}",
        reply_markup=get_analysis_options_keyboard()
    )
    await callback_query.answer()


@router.callback_query(F.data == "start_analytics")
async def process_start_analytics(callback_query: types.CallbackQuery, state: FSMContext, session: AsyncSession):
    user_id = callback_query.from_user.id
    
    try:
        # Создаем запись в истории
        history_record = await create_history(
            session=session,
            users_id=user_id,
            path_to_tz="path/to/tz",  # Здесь нужно указать реальный путь к ТЗ
            path_to_analyze="path/to/analysis"  # Здесь нужно указать реальный путь к анализу
        )
        await session.commit()
        
        await state.set_state(BotStates.analytics_mode)
        await callback_query.message.reply(
            "Режим аналитики активирован.",
            reply_markup=get_analytics_keyboard()
        )
    except Exception as e:
        await session.rollback()
        await callback_query.message.reply(f"Ошибка при создании записи в истории: {e}")
    
    await callback_query.answer()


@router.callback_query(F.data == "delete_analysis")
async def process_delete_analysis(callback_query: types.CallbackQuery):
    analysis_id = callback_query.message.text.split()[-1]
    if analysis_id in analyses:
        del analyses[analysis_id]
        await callback_query.message.reply("Анализ удален.")
    await callback_query.message.reply(
        "Предыдущие анализы:",
        reply_markup=get_history_keyboard()
    )
    await callback_query.answer()


@router.callback_query(F.data == "back_to_history")
async def process_back_to_history(callback_query: types.CallbackQuery):
    await callback_query.message.reply(
        "Предыдущие анализы:",
        reply_markup=get_history_keyboard()
    )
    await callback_query.answer()


# Эхо-функция для режима чата по ТЗ
@router.message(BotStates.chat_tz)
async def echo_message(message: types.Message):
    await message.reply(message.text)


# Функция запуска бота
async def main():
    # Загружаем токен бота из переменной окружения или используем заданный
    BOT_TOKEN = "8097160235:AAF0_dJuMn_jxRmZJDsMxUVIpsOGj6-MHRc"  # Замените на ваш токен

    # Инициализируем базу данных
    await init_db()

    # Инициализируем бота и диспетчер
    bot = Bot(token=BOT_TOKEN)
    storage = MemoryStorage()
    dp = Dispatcher(storage=storage)

    # Регистрируем middleware
    dp.update.middleware(DatabaseMiddleware())

    # Регистрируем роутер
    dp.include_router(router)

    # Запускаем бота
    await dp.start_polling(bot)


class DatabaseMiddleware(BaseMiddleware):
    async def __call__(
        self,
        handler: Callable[[types.TelegramObject, Dict[str, Any]], Awaitable[Any]],
        event: types.TelegramObject,
        data: Dict[str, Any]
    ) -> Any:
        async with async_session_maker() as session:
            data["session"] = session
            result = await handler(event, data)
        return result


if __name__ == '__main__':
    asyncio.run(main())