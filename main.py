import logging
from aiogram import Bot, Dispatcher, types
from aiogram.types import ParseMode
from aiogram.utils import executor
from supabase import create_client
import os

# Инициализация
BOT_TOKEN = os.getenv("BOT_TOKEN")
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

bot = Bot(token=BOT_TOKEN, parse_mode=ParseMode.HTML)
dp = Dispatcher(bot)
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

# Включаем логирование
logging.basicConfig(level=logging.INFO)

@dp.message_handler(commands=["start"])
async def cmd_start(message: types.Message):
    await message.answer(
        "Привет! Я — бот-список покупок 🛒\n\n"
        "Команды:\n"
        "/add — добавить товар\n"
        "/list — показать список\n"
        "/delete — удалить товар\n"
        "/ping — проверка связи"
    )

@dp.message_handler(commands=["ping"])
async def cmd_ping(message: types.Message):
    await message.answer("✅ Бот работает")

@dp.message_handler(commands=["add"])
async def cmd_add(message: types.Message):
    telegram_id = message.from_user.id
    args = message.get_args()
    logging.info(f"/add от {telegram_id}: {args}")
    if not args:
        await message.answer("❗ Укажите товар. Пример:\n<code>/add Хлеб</code>")
        return

    # Можно разбивать на товар и количество, например: "Яблоки 2шт"
    supabase.table("shopping_list").insert({
        "telegram_id": telegram_id,
        "item": args,
        "quantity": 1
    }).execute()

    await message.answer(f"✅ Добавлено: {args}")

@dp.message_handler(commands=["list"])
async def cmd_list(message: types.Message):
    telegram_id = message.from_user.id
    logging.info(f"/list для {telegram_id}")
    response = supabase.table("shopping_list").select("*").eq("telegram_id", telegram_id).execute()
    items = response.data

    if not items:
        await message.answer("🛒 Список пуст")
        return

    text = "📋 Ваш список покупок:\n"
    for item in items:
        text += f"• {item['item']} (x{item.get('quantity', 1)})\n"
    await message.answer(text)

@dp.message_handler(commands=["delete"])
async def cmd_delete(message: types.Message):
    telegram_id = message.from_user.id
    args = message.get_args()
    if not args:
        await message.answer("❗ Укажите товар для удаления. Пример:\n<code>/delete Хлеб</code>")
        return

    supabase.table("shopping_list").delete().eq("telegram_id", telegram_id).eq("item", args).execute()
    await message.answer(f"🗑️ Удалено: {args}")

# Команда запуска — НЕ использовать если у тебя вебхук
# if __name__ == "__main__":
#     executor.start_polling(dp, skip_updates=True)
