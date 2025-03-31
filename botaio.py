import asyncio
import logging
import sys
import random
import requests
import json

from aiogram import Bot, Dispatcher, html
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.filters import CommandStart
from aiogram.types import Message

from handler import router

dp = Dispatcher()

TOKEN = "8097160235:AAF0_dJuMn_jxRmZJDsMxUVIpsOGj6-MHRc"
OPENROUTER_API_KEY = "sk-a757607aa0694b669f703c7bf7c9db55"
MODEL = "deepseek/deepseek-chat"

@dp.message(CommandStart())
async def command_start_handler(message: Message) -> None:
    await message.answer(f"Hello, {html.bold(message.from_user.full_name)}! Спроси меня о чем то cum.")

async def main() -> None:
    bot = Bot(token=TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
    dp.include_router(router)
    await dp.start_polling(bot)

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, stream=sys.stdout)
    asyncio.run(main())
