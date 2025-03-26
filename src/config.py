import os
import calendar
from datetime import datetime
from typing import List, Dict

# Токен бота
BOT_TOKEN = "7698682045:AAHXlt2KxRtURYyMtUHyDD-1H3MmU9bORpM"

# ID администраторов
ADMIN_IDS: List[int] = [264524008]

# Настройки подключения
CONNECTION_SETTINGS = {
    'read_timeout': 15.0,
    'write_timeout': 15.0,
    'pool_timeout': 15.0,
    'connect_timeout': 15.0
}

# Директории для данных
WORKSPACE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(WORKSPACE_DIR, 'data')
USERS_DATA_DIR = os.path.join(DATA_DIR, 'users')

# Создаем директории при импорте конфига
os.makedirs(DATA_DIR, mode=0o700, exist_ok=True)
os.makedirs(USERS_DATA_DIR, mode=0o700, exist_ok=True)

# Эмодзи для случайного выбора
RANDOM_EMOJIS = ['💃', '🎭', '🌟', '✨', '🎪', '🎨', '🎬', '🎯', '🎵', '🎶', '🌈', '🦋', '🌺', '🌸', '🍀']

def count_weekdays_in_current_month(weekdays: List[int]) -> int:
    """Подсчет количества определенных дней недели в текущем месяце"""
    now = datetime.now()
    _, num_days = calendar.monthrange(now.year, now.month)
    count = 0
    for day in range(1, num_days + 1):
        if calendar.weekday(now.year, now.month, day) in weekdays:
            count += 1
    return count

# Состояния для разговора
ENTERING_LESSONS_COUNT = 1
CHOOSING_NAME_SURNAME = 2
CHOOSING_CATEGORY_NAME = 3
CHOOSING_SUBSCRIPTION_TYPE = 4 