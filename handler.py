from aiogram import F, Router #фильтр
from aiogram.types import Message
from aiogram.filters import CommandStart #фильтр события start
from aiogram.fsm.state import State, StatesGroup # сщстояния и антифлуд
from aiogram.fsm.context import FSMContext

from ai import ai_generating

router = Router()

class Gen(StatesGroup): #класс на ожидание при запросе
    wait = State()

@router.message(CommandStart()) # обработка команды start
async def start_hell(message: Message):
  await message.answer('Привет, запрос говори свой ')

@router.message(Gen.wait)
async def stop_spam(message: Message):
  await message.answer('Ожидайте, ваш запрос выполняется сучка')

@router.message() # принятие любых запросов
async def generate(message: Message, state: FSMContext): #передача запроса к ии
  await state.set_state(Gen.wait)
  response = await ai_generating(message.text) # передача запроса от пользователя
  await message.answer(response) # ответ ии
  await state.clear()
