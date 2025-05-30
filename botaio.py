import asyncio
import logging
import sys
from os import getenv
import boto3
import random

from aiogram import Bot, Dispatcher, html
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.filters import CommandStart
from aiogram.types import Message

def random_Z(string: str) -> str:
  random_words = string.split()
  random.shuffle(random_words)
  return " ".join(random_words)

TOKEN = "8097160235:AAF0_dJuMn_jxRmZJDsMxUVIpsOGj6-MHRc"

# Все обработчики должны быть подключены к маршрутизатору (или диспетчеру)

dp = Dispatcher()


@dp.message(CommandStart())
async def command_start_handler(message: Message) -> None:
    await message.answer(f"Hello, {message.from_user.full_name}!")


@dp.message()
async def echo_handler(message: Message):
    try:
        await message.answer(random_Z(message.text))
    except TypeError:
        await message.answer("ЕРОР ОШИБКА")


async def main() -> None:
    # Инициализируйте экземпляр бота свойствами бота по умолчанию, которые будут передаваться во все вызовы API
    bot = Bot(token=TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))

    # И диспетчеризация событий запуска
    await dp.start_polling(bot)


logging.basicConfig(level=logging.INFO, stream=sys.stdout)
asyncio.run(main())
#   h a k - z v u k 2 . 0  
 