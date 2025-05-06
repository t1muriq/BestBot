#Жесткий солид короче пуляем бд постгрес в бот

from models import init_db
import logging

#это типо уровень логов
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def run_migrations():
    """WW Запускаем миграцию бдхи"""
    try:
        logger.info('Начало миграции базы данных...')
        init_db()
        logger.info('Миграция базы данных успешно завершена')
    except Exception as e:
        logger.error(f'Ошибка при миграции базы данных: {e}')
        raise

if __name__ == '__main__':
    run_migrations()