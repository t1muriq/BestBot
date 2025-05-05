from models import init_db
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def run_migrations():
    """Запуск миграций базы данных"""
    try:
        logger.info('Начало миграции базы данных...')
        init_db()
        logger.info('Миграция базы данных успешно завершена')
    except Exception as e:
        logger.error(f'Ошибка при миграции базы данных: {e}')
        raise

if __name__ == '__main__':
    run_migrations()