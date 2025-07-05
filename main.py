import os
from dotenv import load_dotenv
from aiogram import Bot, Dispatcher, types
from aiogram.types import ParseMode
from aiogram.dispatcher.webhook import get_new_configured_app
from fastapi import FastAPI
from supabase import create_client

# Загрузка переменных из .env
load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
WEBHOOK_PATH = f"/webhook/{BOT_TOKEN}"
WEBHOOK_URL = f"{os.getenv('RENDER_EXTERNAL_URL')}{WEBHOOK_PATH}"

bot = Bot(token=BOT_TOKEN, parse_mode=ParseMode.HTML)
dp = Dispatcher(bot)
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

@dp.message_handler(commands=["start"])
async def start_handler(message: types.Message):
    await message.answer("Привет! Отправь товар, чтобы добавить в список 🛒")

@dp.message_handler(content_types=types.ContentType.TEXT)
async def add_item(message: types.Message):
    user_id = message.from_user.id
    item = message.text.strip()

    supabase.table("shopping_list").insert({
        "telegram_id": user_id,
        "item": item,
        "quantity": 1
    }).execute()

    await message.answer(f"✅ Добавлено: <b>{item}</b>")

@dp.message_handler(commands=["list"])
async def list_items(message: types.Message):
    user_id = message.from_user.id
    res = supabase.table("shopping_list").select("*").eq("telegram_id", user_id).execute()
    data = res.data

    if not data:
        await message.answer("📭 Список пуст.")
        return

    response = "📝 <b>Твой список:</b>\n"
    for idx, entry in enumerate(data, start=1):
        response += f"{idx}. {entry['item']} (x{entry['quantity']})\n"

    await message.answer(response)

@dp.message_handler(commands=["clear"])
async def clear_list(message: types.Message):
    user_id = message.from_user.id
    supabase.table("shopping_list").delete().eq("telegram_id", user_id).execute()
    await message.answer("🗑 Список очищен.")

# FastAPI + webhook
app = FastAPI()

@app.on_event("startup")
async def on_startup():
    await bot.set_webhook(WEBHOOK_URL)

@app.on_event("shutdown")
async def on_shutdown():
    await bot.delete_webhook()

app.mount(WEBHOOK_PATH, get_new_configured_app(dispatcher=dp, path=WEBHOOK_PATH))
