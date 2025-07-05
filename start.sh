#!/bin/bash

# Запуск Telegram-бота
python3 main.py &

# Запуск аптайм-сервера
python3 uptime.py &
