# DressBot 👗

Telegram-бот для магазина одежды. Позволяет просматривать каталог платьев, фильтровать по цене/размеру/категории. Имеет панель администратора для управления товарами.

## Стек
- Python 3.13 + aiogram 3
- Supabase (база данных)

## Локальный запуск

1. Клонируй репозиторий:
   ```bash
   git clone https://github.com/YOUR_USERNAME/DressBot.git
   cd DressBot
   ```

2. Установи зависимости:
   ```bash
   pip install -r requirements.txt
   ```

3. Создай файл `.env` на основе `.env.example` и заполни своими данными:
   ```bash
   cp .env.example .env
   ```

4. Запусти бота:
   ```bash
   python bot.py
   ```
