import os
import logging
from fastapi import FastAPI
from dotenv import load_dotenv
import uvicorn
from supabase import create_client, Client
from aiogram import Bot, Dispatcher, types, executor

# Загрузка .env
load_dotenv()

# Настройки
API_TOKEN = os.getenv("BOT_TOKEN")
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

# FastAPI
app = FastAPI()

# Supabase
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

# Bot
bot = Bot(token=API_TOKEN)
dp = Dispatcher(bot)

# Telegram Handlers
@dp.message_handler(commands=['start'])
async def start(message: types.Message):
    await message.answer("Привет! Отправь продукт, и я добавлю его в список.")

@dp.message_handler()
async def add_item(message: types.Message):
    data = {
        "telegram_id": str(message.from_user.id),
        "item": message.text,
    }
    supabase.table("shopping_list").insert(data).execute()
    await message.answer(f"Добавлено: {message.text}")

# FastAPI endpoints
@app.get("/")
def read_root():
    return {"status": "ok"}

@app.on_event("startup")
async def on_startup():
    logging.warning("Запуск бота...")
    from threading import Thread
    Thread(target=lambda: executor.start_polling(dp, skip_updates=True)).start()

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run("main:app", host="0.0.0.0", port=port)
