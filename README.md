# FinControl — Сервис учёта личных финансов

FinControl — это веб-сервис с Telegram-ботом для учёта личных финансов, аналитики и получения рекомендаций.

## 📱 Функционал

- Учёт доходов и расходов
- Категоризация операций
- Визуальная аналитика (графики и диаграммы)
- Персонализированные рекомендации
- Интеграция с Telegram-ботом
- Планирование бюджета
- Ежедневные отчёты

🚀 Быстрый старт
- Предварительные требования
- Python 3.10+
- pip
- Git

## 🚀 Установка

### 1. Клонируйте репозиторий

git clone https://github.com/ваш-ник/fincontrol.git
cd fincontrol

### 2. Создайте и активируйте виртуальное окружение

python -m venv venv
source venv/bin/activate  # Linux/MacOS
venv\Scripts\activate    # Windows

### 3. Установите зависимости

pip install -r requirements.txt

### 4. Настройте Telegram-бота (создайте файл .env)

echo "TELEGRAM_BOT_TOKEN=ваш_токен_от_BotFather" > .env

### 5. Примените миграции

python manage.py migrate

### 6. Создайте суперпользователя (опционально)

python manage.py createsuperuser

### 7. Запустите сервер

python manage.py runserver

### 8. В отдельном терминале запустите бота

python manage.py runbot

## ⚙️ Настройка

Конфигурация Telegram-бота
Создайте бота через @BotFather
Получите токен и добавьте его в файл .env

## 📄 Лицензия

Этот проект распространяется под лицензией MIT

---

### `LICENSE`
Создайте файл `LICENSE` с содержимым MIT-лицензии:

```text
MIT License

Copyright (c) 2025 Ваше Имя

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.


  🙌 Благодарности

Спасибо за использование FinControl! Если вам нравится проект, пожалуйста, поставьте звезду ⭐ на GitHub.