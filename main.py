import logging
import os
from aiogram import Bot, Dispatcher, types
from aiogram.utils.executor import start_webhook
from supabase import create_client, Client
from dotenv import load_dotenv
from aiohttp import web

load_dotenv()

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Переменные окружения
TOKEN = os.getenv("BOT_TOKEN")
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
WEBHOOK_HOST = os.getenv("WEBHOOK_HOST")
WEBHOOK_PATH = f"/webhook/{TOKEN}"
WEBHOOK_URL = f"{WEBHOOK_HOST}{WEBHOOK_PATH}"

bot = Bot(token=TOKEN)
dp = Dispatcher(bot)

# Инициализация Supabase
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

# Хэндлер для аптайм-чеков
async def handle_uptime(request):
    return web.Response(text="Bot is alive!")

# Стартовая команда
@dp.message_handler(commands=["start"])
async def cmd_start(message: types.Message):
    user_id = message.from_user.id

    # Проверка, есть ли пользователь уже
    response = supabase.table("users").select("telegram_id").eq("telegram_id", user_id).execute()
    if not response.data:
        supabase.table("users").insert({"telegram_id": user_id}).execute()

    text = (
        "👋 Привет! Это бот для списка покупок.\n\n"
        "Доступные команды:\n"
        "/add — добавить товар\n"
        "/list — показать список\n"
        "/delete — удалить товар"
    )
    await message.answer(text)

# Команда добавления
@dp.message_handler(commands=["add"])
async def cmd_add(message: types.Message):
    try:
        args = message.get_args()
        if not args:
            await message.reply("❗ Пожалуйста, укажи товар после команды /add.")
            return

        user_id = message.from_user.id
        supabase.table("shopping_list").insert({
            "telegram_id": user_id,
            "item": args,
        }).execute()

        await message.reply(f"✅ Добавлено: {args}")
    except Exception as e:
        logger.error(f"❌ Ошибка при добавлении товара: {e}")
        await message.reply("⚠️ Не удалось добавить товар.")

# Команда списка
@dp.message_handler(commands=["list"])
async def cmd_list(message: types.Message):
    try:
        user_id = message.from_user.id
        response = supabase.table("shopping_list").select("id", "item").eq("telegram_id", user_id).execute()
        items = response.data

        if not items:
            await message.reply("🛒 Список пуст.")
            return

        text = "📝 Твой список покупок:\n" + "\n".join(
            [f"{item['id']}. {item['item']}" for item in items]
        )
        await message.reply(text)
    except Exception as e:
        logger.error(f"❌ Ошибка при получении списка: {e}")
        await message.reply("⚠️ Не удалось получить список.")

# Команда удаления
@dp.message_handler(commands=["delete"])
async def cmd_delete(message: types.Message):
    try:
        args = message.get_args()
        if not args or not args.isdigit():
            await message.reply("❗ Укажи ID товара, который нужно удалить. Например: /delete 3")
            return

        item_id = int(args)
        user_id = message.from_user.id

        response = supabase.table("shopping_list").delete().eq("id", item_id).eq("telegram_id", user_id).execute()

        if response.count == 0:
            await message.reply("⚠️ Товар не найден или не принадлежит тебе.")
        else:
            await message.reply("🗑️ Удалено.")
    except Exception as e:
        logger.error(f"❌ Ошибка при удалении товара: {e}")
        await message.reply("⚠️ Не удалось удалить товар.")

# Настройки вебхука
async def on_startup(dp: Dispatcher):
    await bot.set_webhook(WEBHOOK_URL)
    logger.info(f"✅ Webhook установлен: {WEBHOOK_URL}")

async def on_shutdown(dp: Dispatcher):
    logger.info("⛔ Отключение...")
    await bot.delete_webhook()

# Приложение aiohttp
app = web.Application()
app.router.add_get("/", handle_uptime)  # Корневой маршрут для аптайма
app.router.add_post(WEBHOOK_PATH, lambda request: dp.start_polling())  # Вебхук Telegram

# Запуск сервера
if __name__ == "__main__":
    web.run_app(app, host="0.0.0.0", port=int(os.environ.get("PORT", 10000)))
