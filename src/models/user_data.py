import os
import json
import logging
from typing import Dict, Any, Optional
from config import USERS_DATA_DIR

logger = logging.getLogger(__name__)

class UserDataManager:
    """Менеджер пользовательских данных"""
    
    @staticmethod
    def load_user_data(chat_id: int) -> Dict[str, Any]:
        """Загрузка данных пользователя"""
        try:
            # Создаем директорию, если её нет
            os.makedirs(USERS_DATA_DIR, exist_ok=True)
            
            # Путь к файлу с данными пользователя
            user_file = os.path.join(USERS_DATA_DIR, f"{chat_id}.json")
            
            # Если файл существует, загружаем данные
            if os.path.exists(user_file):
                with open(user_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            
            # Если файла нет, создаем новую структуру данных
            default_data = {
                'categories': {}  # Пустой словарь для категорий пользователя
            }
            
            # Сохраняем новую структуру
            with open(user_file, 'w', encoding='utf-8') as f:
                json.dump(default_data, f, ensure_ascii=False, indent=2)
            
            return default_data
            
        except Exception as e:
            logger.error(f"Ошибка при загрузке данных пользователя {chat_id}: {e}")
            return {'categories': {}}
    
    @staticmethod
    def save_user_data(chat_id: int, data: Dict[str, Any]) -> bool:
        """Сохранение данных пользователя"""
        try:
            # Создаем директорию, если её нет
            os.makedirs(USERS_DATA_DIR, exist_ok=True)
            
            # Путь к файлу с данными пользователя
            user_file = os.path.join(USERS_DATA_DIR, f"{chat_id}.json")
            
            # Сохраняем данные
            with open(user_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            
            return True
            
        except Exception as e:
            logger.error(f"Ошибка при сохранении данных пользователя {chat_id}: {e}")
            return False 