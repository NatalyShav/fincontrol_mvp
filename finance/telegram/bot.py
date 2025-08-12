
from aiogram import Bot, Dispatcher, types
from django.conf import settings
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from asgiref.sync import sync_to_async
from finance.telegram.handlers import router
from finance.telegram.services import prepare_daily_reports

# Инициализация бота
bot = Bot(token=settings.TELEGRAM_BOT_TOKEN)
dp = Dispatcher()

# Планировщик
scheduler = AsyncIOScheduler()


async def send_daily_report():
    try:
        # Получаем данные в синхронной функции
        reports = await sync_to_async(prepare_daily_reports)()

        # Отправляем отчёты
        for chat_id, text in reports:
            try:
                await bot.send_message(
                    chat_id=chat_id,
                    text=text
                )
            except Exception as e:
                print(f"❌ Не удалось отправить отчёт {chat_id}: {e}")
    except Exception as e:
        print(f"❌ Ошибка при отправке отчётов: {e}")


def start_scheduler():
    scheduler.add_job(send_daily_report, 'cron', hour=9, minute=0)
    scheduler.start()


async def start_bot():
    # Регистрируем маршрутизатор с обработчиками
    dp.include_router(router)

    # Устанавливаем список команд в интерфейсе Telegram
    await bot.set_my_commands([
        types.BotCommand(command="/today", description="Отчёт за сегодня"),
        types.BotCommand(command="/week", description="Отчёт за неделю"),
        types.BotCommand(command="/add", description="Добавить операцию"),
        types.BotCommand(command="/help", description="Справка"),
        types.BotCommand(command="/menu", description="Показать меню")
    ])

    # Запускаем планировщик
    start_scheduler()

    # Запускаем бота
    print("✅ Telegram-бот запущен...")
    await dp.start_polling(bot)