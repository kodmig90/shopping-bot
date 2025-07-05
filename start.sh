#!/bin/bash

# Запуск Telegram-бота (в фоне)
python3 main.py &

# Запуск аптайм-сервера (в foreground)
python3 uptime.py
