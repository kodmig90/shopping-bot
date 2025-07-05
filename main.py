import logging
import os
from aiogram import Bot, Dispatcher, types, executor
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
from dotenv import load_dotenv
from supabase import create_client, Client

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher(bot)

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

kb = ReplyKeyboardMarkup(resize_keyboard=True)
kb.add(KeyboardButton("➕ Добавить товар"), KeyboardButton("🗑 Удалить товар"))
kb.add(KeyboardButton("📋 Показать список"))

# Команда /start
@dp.message_handler(commands=['start'])
async def cmd_start(message: types.Message):
    await message.answer("Привет! Я бот для списка покупок.\n\nВыберите действие:", reply_markup=kb)

# Обработка кнопок
@dp.message_handler(lambda message: message.text == "📋 Показать список")
async def show_list(message: types.Message):
    user_id = message.from_user.id
    response = supabase.table("shopping_list").select("*").eq("telegram_id", user_id).order("added_at", desc=False).execute()
    items = response.data

    if not items:
        await message.answer("🛒 Список покупок пуст.")
    else:
        text = "🛍 *Ваш список покупок:*\n\n"
        for i, item in enumerate(items, 1):
            qty = item['quantity']
            line = f"{i}. {item['item']}"
            if qty:
                line += f" — {qty}"
            text += line + "\n"
        await message.answer(text, parse_mode="Markdown")

@dp.message_handler(lambda message: message.text == "➕ Добавить товар")
async def add_item_prompt(message: types.Message):
    await message.answer("Напишите товар и (при необходимости) количество. Пример:\n\n`Хлеб 2`", parse_mode="Markdown")

@dp.message_handler(lambda message: message.text == "🗑 Удалить товар")
async def delete_item_prompt(message: types.Message):
    await message.answer("Напишите *точное* название товара, который нужно удалить.", parse_mode="Markdown")

@dp.message_handler(lambda message: message.text not in ["➕ Добавить товар", "🗑 Удалить товар", "📋 Показать список"])
async def handle_text(message: types.Message):
    user_id = message.from_user.id
    text = message.text.strip()

    if text.startswith("Удалить ") or message.reply_to_message and message.reply_to_message.text == "Напишите *точное* название товара, который нужно удалить.":
        item_to_delete = text.replace("Удалить", "").strip()
        response = supabase.table("shopping_list").delete().eq("telegram_id", user_id).eq("item", item_to_delete).execute()
        if response.count > 0:
            await message.answer(f"✅ Удалено: {item_to_delete}")
        else:
            await message.answer("❌ Такой товар не найден.")
        return

    parts = text.split(" ", 1)
    item = parts[0]
    quantity = parts[1] if len(parts) > 1 else ""

    supabase.table("shopping_list").insert({
        "telegram_id": user_id,
        "item": item,
        "quantity": quantity
    }).execute()
    await message.answer(f"✅ Добавлено: {item} {quantity}".strip())

if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    executor.start_polling(dp, skip_updates=True)
