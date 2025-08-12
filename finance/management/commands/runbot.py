import django
import os
from django.core.management.base import BaseCommand
import asyncio

# 1. Установите переменную окружения
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'fincontrol.settings')

# 2. Запустите Django
django.setup()

# 3. Только после setup() импортируйте bot.py
from finance.telegram.bot import start_bot


class Command(BaseCommand):
    help = 'Запускает Telegram-бота'

    def handle(self, *args, **options):
        asyncio.run(start_bot())