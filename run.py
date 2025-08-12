# run.py
import os
import subprocess
import sys

if __name__ == "__main__":
    # Запуск сервера
    server = subprocess.Popen([sys.executable, "manage.py", "runserver"])
    # Запуск бота
    bot = subprocess.Popen([sys.executable, "manage.py", "runbot"])

    try:
        server.wait()
        bot.wait()
    except KeyboardInterrupt:
        server.terminate()
        bot.terminate()