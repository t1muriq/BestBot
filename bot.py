# Проект нереальный короче
# Универсальный бот для всего на свете 

import redis
import json
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes, CallbackQueryHandler, MessageHandler, filters
import requests
import os
import logging
import sys
from datetime import datetime
from models import User, SessionLocal
from migrations import run_migrations
from models import init_db

#Вот эта тема для того, чтобы логи писались в разные файлы по заполняемости, Сейчас заменю ее на по датам лол
from logging.handlers import RotatingFileHandler
# По датам
from logging.handlers import TimedRotatingFileHandler

#Здесь мы короче инициализируем базу данных
init_db()

# Создаем путь к папке логов, я хз почему то иногда не разбивается на разные файлы
log_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'logs')
log_filename = os.path.join(log_dir, 'bot.log')

# Показываем как именно писать логи суета суета
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler(sys.stdout)]
)

#Сам экземпляр логгера
logger = logging.getLogger(__name__)

# Создаем директорию для логов
try:
    os.makedirs(log_dir, exist_ok=True)
    logger.info(f"Создана директория для логов: {log_dir}")

    # Создаем RotatingFileHandler 
    # file_handler = RotatingFileHandler(
    #     log_filename,
    #     maxBytes=10*1024*1024,  # Максимальный размер файла - 10MB
    #     backupCount=10,  # Хранить максимум 10 файлов
    #     encoding='utf-8'
    # )

    #Теперь по нормальному создадим по датам( ну я хоть попробовал)
    file_handler = TimedRotatingFileHandler(
        log_filename,
        when='midnight', #каждую ночь обновлять
        interval=1,
        backupCount=10,  # Хранить максимум 10 файлов
        encoding='utf-8'
    )
    file_handler.suffix = "%Y%m%d"


    # Настраиваем форматирование логов
    log_formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    file_handler.setFormatter(log_formatter)
    
    # Добавляем файловый обработчик к логгеру
    logger.addHandler(file_handler)
    
except Exception as e:
    logger.error(f"Ошибка при настройке логирования: {e}")
    sys.exit(1)

#Здесь я засунул эти токены в .env (туда пароль надо тоже засунуть)
TOKEN = os.getenv("API_TOKEN")
WEATHER_API_KEY = os.getenv("WEATHER_API_KEY")

# Redis конфигурация, короче кеш каждые 10 минут
REDIS_HOST = os.getenv('REDIS_HOST', 'localhost')
REDIS_PORT = int(os.getenv('REDIS_PORT', 6379))
CACHE_EXPIRATION = 600  # 10 minutes

# Инициализируем Redis 
redis_client = redis.Redis(host=REDIS_HOST, port=REDIS_PORT, decode_responses=True)

#это на будущее, но хз, мне кажется не будем юзать
PATH_TO_WEATHER_TABLE = "weather_result/weather_list.csv"

#Короче если пользователь не существует, то создаем его, если существует, то обновляем его
async def save_or_update_user(user):
    """Жестко юзаю тройные кавычки типо шарю WW"""
    db = SessionLocal()
    try:
        # Проверяем существование пользователя
        db_user = db.query(User).filter(User.id == user.id).first()
        logger.info(f"Пользователь {user.id} существует: {db_user is not None}")
        logger.info(f"Пользователь {user.id} {user.username} {user.first_name} {user.last_name}")
        logger.info(f"Все аттрибуты класса user {dir(user)}")
        if db_user is None:
            # Создаем нового пользователя
            logger.info(f"Создание нового пользователя с ID: {user.id}")
            db_user = User(
                id=user.id,
                username=user.username,
                first_name=user.first_name,
                last_name=user.last_name,
                registration_date=datetime.utcnow(),
                last_activity=datetime.utcnow()
            )
            db.add(db_user)
            try:
                db.flush()  # Проверяем успешность добавления
                logger.info(f"Новый пользователь успешно создан в БД: {user.id}")
            except Exception as e:
                logger.error(f"Ошибка при создании пользователя {user.id}: {e}")
                db.rollback()
                return
        else:
            # Обновляем существующего пользователя
            logger.info(f"Обновление данных пользователя: {user.id}")
            db_user.last_activity = datetime.utcnow()
            if user.username:
                db_user.username = user.username
            if user.first_name:
                db_user.first_name = user.first_name
            if user.last_name:
                db_user.last_name = user.last_name
        
        # Сохраняем изменения
        db.commit()
        logger.info(f"Операция с пользователем {user.id} успешно завершена11")
    except Exception as e:
        logger.error(f"Ошибка при сохранении пользователя: {e}")
        db.rollback()
    finally:
        db.close()

# функция при старте бота /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    logger.info(f"Пользователь {update.effective_user.id} запустил бота")
    await save_or_update_user(update.effective_user)
    keyboard = [
        [
            InlineKeyboardButton("🌤 Узнать погоду", callback_data='weather'),
            InlineKeyboardButton("ℹ️ Помощь", callback_data='help')
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text(
        "Привет! Я погодный бот 🌤\nВыбери действие:",
        reply_markup=reply_markup
    )


async def get_weather_data(city: str):
    logger.info(f"Запрос погоды для города: {city}")
    # Пробую взять из кеша
    cache_key = f"weather:{city.lower()}"
    cached_data = redis_client.get(cache_key)
    
    if cached_data:
        logger.info(f"Получены кэшированные данные для города {city}")
        return json.loads(cached_data)
    
    # Если в кеше нет такой суеты то в апи иду
    url = f"http://api.openweathermap.org/data/2.5/weather?q={city}&appid={WEATHER_API_KEY}&units=metric&lang=ru"
    response = requests.get(url)
    data = response.json()
    
    if data.get("cod") == 200:
        logger.info(f"Успешный запрос к API погоды для города {city}")
        # Cache the successful response
        redis_client.setex(cache_key, CACHE_EXPIRATION, json.dumps(data))
    else:
        logger.error(f"Ошибка при запросе погоды для города {city}: {data.get('message', 'Неизвестная ошибка')}")

    
    return data

async def weather(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("Пожалуйста, укажи город после команды. Пример: /weather Moscow")
        return

    city = ' '.join(context.args)
    data = await get_weather_data(city)

    if data.get("cod") != 200:
        await update.message.reply_text("Не удалось найти информацию о погоде для этого города.")
        return

    weather_desc = data["weather"][0]["description"]
    temp = data["main"]["temp"]
    feels_like = data["main"]["feels_like"]

    message = (
        f"🌍 Город: {city.title()}\n"
        f"🌡 Температура: {temp}°C\n"
        f"🤔 Ощущается как: {feels_like}°C\n"
        f"🌤 Погода: {weather_desc.capitalize()}\n"
        f"Timur Пахан суетной {data['weather'][0]['icon']}\n"
    )

    await update.message.reply_text(message)

async def button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    logger.info(f"Пользователь {query.from_user.id} нажал кнопку {query.data}")
    await query.answer()

    if query.data == 'weather':
        await query.message.reply_text("Напиши название города, чтобы узнать погоду.")
    elif query.data == 'help':
        await query.message.reply_text(
            "Доступные команды:\n"
            "/weather <город> - узнать погоду в указанном городе\n"
            "/start - показать главное меню"
        )

async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.text.startswith('/'):
        return
    
    logger.info(f"Пользователь {update.effective_user.id} отправил сообщение: {update.message.text}")
        
    city = update.message.text
    data = await get_weather_data(city)

    if data.get("cod") != 200:
        await update.message.reply_text("Не удалось найти информацию о погоде для этого города.")
        return

    weather_desc = data["weather"][0]["description"]
    temp = data["main"]["temp"]
    feels_like = data["main"]["feels_like"]

    message = (
        f"🌍 Город: {city.title()}\n"
        f"🌡 Температура: {temp}°C\n"
        f"🤔 Ощущается как: {feels_like}°C\n"
        f"🌤 Погода: {weather_desc.capitalize()}\n"
        f"Timur Пахан суетной {data['weather'][0]['icon']}\n"
    )

    await update.message.reply_text(message)

if __name__ == '__main__':
    logger.info("Запуск бота...")
    # Запускаем миграции при старте
    run_migrations()
    logger.info("Миграции выполнены успешно")
    
    app = ApplicationBuilder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("weather", weather))
    app.add_handler(CallbackQueryHandler(button_callback))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))
    app.run_polling()
