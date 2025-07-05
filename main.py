import logging
import os

from aiogram import Bot, Dispatcher, types
from aiogram.utils.executor import start_webhook
from dotenv import load_dotenv
from supabase import create_client, Client
from aiohttp import web

# Загрузка переменных
load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
WEBHOOK_HOST = os.getenv("WEBHOOK_URL")
WEBHOOK_PATH = f"/webhook/{BOT_TOKEN}"
WEBHOOK_URL = f"{WEBHOOK_HOST}{WEBHOOK_PATH}" if WEBHOOK_HOST else None
WEBAPP_HOST = "0.0.0.0"
WEBAPP_PORT = int(os.getenv("PORT", 8000))

# Логирование
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Инициализация
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher(bot)

# Команды
@dp.message_handler(commands=["start"])
async def cmd_start(message: types.Message):
    logger.info(f"/start от {message.from_user.id}")
    await message.answer("Привет! Я бот для списка покупок 🛒\n\n"
                         "Доступные команды:\n"
                         "/add [товар] — добавить товар\n"
                         "/list — посмотреть список\n"
                         "/delete [номер] — удалить товар")

@dp.message_handler(commands=["add"])
async def cmd_add(message: types.Message):
    item = message.get_args()
    if not item:
        await message.reply("Укажи товар после команды /add")
        return
    try:
        supabase.table("shopping_list").insert({
            "telegram_id": message.from_user.id,
            "item": item,
        }).execute()
        await message.answer(f"✅ Товар «{item}» добавлен")
    except Exception as e:
        logger.exception("Ошибка при добавлении")
        await message.reply("Ошибка при добавлении товара")

@dp.message_handler(commands=["list"])
async def cmd_list(message: types.Message):
    try:
        response = supabase.table("shopping_list").select("id, item") \
            .eq("telegram_id", message.from_user.id).execute()
        items = response.data
        if not items:
            await message.answer("Список пуст.")
        else:
            text = "📝 Список покупок:\n\n"
            for i, entry in enumerate(items, start=1):
                text += f"{i}. {entry['item']}\n"
            await message.answer(text)
    except Exception as e:
        logger.exception("Ошибка при получении списка")
        await message.reply("Ошибка при получении списка")

@dp.message_handler(commands=["delete"])
async def cmd_delete(message: types.Message):
    arg = message.get_args()
    if not arg or not arg.isdigit():
        await message.reply("Укажи номер товара для удаления, например /delete 2")
        return
    index = int(arg) - 1
    try:
        response = supabase.table("shopping_list").select("id, item") \
            .eq("telegram_id", message.from_user.id).execute()
        items = response.data
        if index < 0 or index >= len(items):
            await message.reply("Неверный номер товара")
            return
        item_id = items[index]['id']
        supabase.table("shopping_list").delete().eq("id", item_id).execute()
        await message.answer(f"🗑️ Удалён: {items[index]['item']}")
    except Exception as e:
        logger.exception("Ошибка при удалении")
        await message.reply("Ошибка при удалении товара")

# Аптайм-эндпоинт
async def handle_uptime(request):
    return web.Response(text="✅ Uptime OK")

# Webhook lifecycle
async def on_startup(dp):
    if not WEBHOOK_URL:
        logger.warning("WEBHOOK_URL не задан")
    else:
        await bot.set_webhook(WEBHOOK_URL)
        logger.info(f"Webhook установлен: {WEBHOOK_URL}")

async def on_shutdown(dp):
    logger.info("Удаление webhook...")
    await bot.delete_webhook()

# Запуск
if __name__ == "__main__":
    if not BOT_TOKEN:
        logger.critical("BOT_TOKEN не установлен!")
        exit(1)

    app = web.Application()
    app.router.add_get("/", handle_uptime)
    app.router.add_get("/uptime", handle_uptime)

    logger.info("🚀 Запуск...")

    start_webhook(
        dispatcher=dp,
        webhook_path=WEBHOOK_PATH,
        on_startup=on_startup,
        on_shutdown=on_shutdown,
        skip_updates=True,
        host=WEBAPP_HOST,
        port=WEBAPP_PORT,
        web_app=app,
    )
