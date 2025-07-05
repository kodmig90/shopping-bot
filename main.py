import os
import asyncio
from aiogram import Bot, Dispatcher, types
from aiogram.types import Message
from aiogram.utils import executor
from aiohttp import web
from supabase import create_client, Client
from dotenv import load_dotenv

load_dotenv()

# ========== Настройки ==========

BOT_TOKEN = os.getenv("BOT_TOKEN")
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher(bot)
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

# ========== Хендлеры Telegram-команд ==========

@dp.message_handler(commands=["start"])
async def cmd_start(message: Message):
    await message.answer("Привет! Я — бот-список покупок 🛒\n\nКоманды:\n/add — добавить товар\n/list — показать список\n/delete — удалить товар\n/ping — проверка связи")

@dp.message_handler(commands=["ping"])
async def cmd_ping(message: Message):
    await message.answer("✅ Бот работает")

@dp.message_handler(commands=["add"])
async def cmd_add(message: Message):
    parts = message.text.split(maxsplit=1)
    if len(parts) < 2:
        await message.answer("❗ Укажите товар. Пример:\n`/add Хлеб`", parse_mode="Markdown")
        return
    item = parts[1]
    user_id = message.from_user.id
    supabase.table("shopping_list").insert({
        "telegram_id": user_id,
        "item": item
    }).execute()
    await message.answer(f"➕ Добавлено: {item}")

@dp.message_handler(commands=["list"])
async def cmd_list(message: Message):
    user_id = message.from_user.id
    result = supabase.table("shopping_list").select("id, item").eq("telegram_id", user_id).execute()
    items = result.data
    if not items:
        await message.answer("🧺 Список пуст")
        return
    text = "\n".join([f"{item['id']}. {item['item']}" for item in items])
    await message.answer(f"🛒 Ваш список:\n{text}")

@dp.message_handler(commands=["delete"])
async def cmd_delete(message: Message):
    parts = message.text.split(maxsplit=1)
    if len(parts) < 2 or not parts[1].isdigit():
        await message.answer("❗ Укажите номер товара из списка. Пример:\n`/delete 3`", parse_mode="Markdown")
        return
    item_id = int(parts[1])
    user_id = message.from_user.id
    response = supabase.table("shopping_list").delete().eq("telegram_id", user_id).eq("id", item_id).execute()
    if response.count == 0:
        await message.answer("⚠️ Товар с таким номером не найден.")
    else:
        await message.answer(f"🗑️ Удалено: {item_id}")

# ========== Аптайм-сервер ==========

async def handle_root(request):
    return web.Response(text="✅ Uptime OK — бот работает!")

async def handle_ping(request):
    return web.json_response({"status": "ok"})

async def run_uptime_server():
    app = web.Application()
    app.router.add_get("/", handle_root)
    app.router.add_get("/ping", handle_ping)
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, port=8000)
    await site.start()

# ========== Запуск ==========

async def main():
    await asyncio.gather(
        run_uptime_server(),
        dp.start_polling()
    )

if __name__ == "__main__":
    asyncio.run(main())
