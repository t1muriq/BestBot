from sqlalchemy import create_engine, Column, Integer, String, DateTime, BigInteger, inspect, text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import os
import logging
from datetime import datetime

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
#ТИМУР ПЕРЕПЕШИ ПАРОЛЬ В .env!! как нить потом
# Получаем URL подключения к базе данных из переменной окружения
DATABASE_URL = os.getenv('DATABASE_URL', 'postgresql://postgres:123@postgres:5432/weather_bot')

# Создаем движок SQLAlchemy
engine = create_engine(DATABASE_URL)

# Создаем базовый класс для моделей
Base = declarative_base()

# Создаем сессию
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

class User(Base):
    """Модель для хранения информации о пользователях бота WW"""
    __tablename__ = 'users'

    id = Column(BigInteger, primary_key=True)  # Telegram user ID
    username = Column(String, nullable=True)   # Telegram username
    first_name = Column(String, nullable=True) # Имя пользователя
    last_name = Column(String, nullable=True)  # Фамилия пользователя
    registration_date = Column(DateTime, default=datetime.utcnow) # Дата регистрации
    last_activity = Column(DateTime, default=datetime.utcnow)    # Последняя активность

def init_db():
    """Инициализация базы данных"""
    try:
        # Проверяем подключение к базе данных
        with engine.connect() as connection:
            connection.execute(text("SELECT 1"))
            logger.info("Успешное подключение к базе данных")
        
        # Создаем все таблицы
        Base.metadata.create_all(bind=engine)
        logger.info("Таблицы успешно созданы")
        
        # Проверяем, что таблицы действительно созданы
        inspector = inspect(engine)
        tables = inspector.get_table_names()
        logger.info(f"Существующие таблицы: {tables}")
        
    except Exception as e:
        logger.error(f"Ошибка при инициализации базы данных: {e}")
        raise

def get_db():
    """Получение сессии базы данных"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()