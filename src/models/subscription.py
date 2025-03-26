import logging
from datetime import datetime
from typing import Dict, Optional, List
from .user_data import UserDataManager

logger = logging.getLogger(__name__)

class SubscriptionManager:
    """Менеджер абонементов"""
    
    def __init__(self):
        """Инициализация менеджера"""
        self.user_data_manager = UserDataManager()
    
    def create_subscription(self, chat_id: int, category: str, name: str, surname: str, lessons: int) -> bool:
        """Создание нового абонемента"""
        try:
            user_data = self.user_data_manager.load_user_data(chat_id)
            
            # Создаем категорию, если её нет
            if category not in user_data:
                user_data[category] = []
            
            # Создаем новый абонемент
            subscription = {
                'name': name,
                'surname': surname,
                'lessons': lessons,
                'type': category,
                'used_lessons': {},
                'created_at': datetime.now().isoformat()
            }
            
            # Добавляем абонемент в список
            user_data[category].append(subscription)
            
            # Сохраняем обновленные данные
            return self.user_data_manager.save_user_data(chat_id, user_data)
            
        except Exception as e:
            logger.error(f"Ошибка при создании абонемента: {e}")
            return False
    
    def mark_lesson(self, chat_id: int, category: str, sub_index: int, lesson_num: int) -> bool:
        """Отметка занятия как использованного/неиспользованного"""
        try:
            user_data = self.user_data_manager.load_user_data(chat_id)
            
            # Проверяем существование категории и абонемента
            if category not in user_data:
                logger.error(f"Категория {category} не найдена в данных пользователя {chat_id}")
                return False
            
            subscriptions = user_data[category]
            if not 0 <= sub_index < len(subscriptions):
                logger.error(f"Индекс абонемента {sub_index} выходит за пределы списка")
                return False
            
            subscription = subscriptions[sub_index]
            lesson = str(lesson_num)
            
            # Отмечаем или снимаем отметку с занятия
            if lesson in subscription['used_lessons']:
                del subscription['used_lessons'][lesson]
            else:
                subscription['used_lessons'][lesson] = datetime.now().strftime("%d.%m")
            
            # Сохраняем обновленные данные
            return self.user_data_manager.save_user_data(chat_id, user_data)
            
        except Exception as e:
            logger.error(f"Ошибка при отметке занятия: {e}")
            return False
    
    def delete_subscription(self, chat_id: int, category: str, sub_index: int) -> bool:
        """Удаление абонемента"""
        try:
            user_data = self.user_data_manager.load_user_data(chat_id)
            
            # Проверяем существование категории и абонемента
            if category not in user_data:
                logger.error(f"Категория {category} не найдена в данных пользователя {chat_id}")
                return False
            
            subscriptions = user_data[category]
            if not 0 <= sub_index < len(subscriptions):
                logger.error(f"Индекс абонемента {sub_index} выходит за пределы списка")
                return False
            
            # Удаляем абонемент
            user_data[category].pop(sub_index)
            
            # Сохраняем обновленные данные
            return self.user_data_manager.save_user_data(chat_id, user_data)
            
        except Exception as e:
            logger.error(f"Ошибка при удалении абонемента: {e}")
            return False
    
    def get_subscription(self, chat_id: int, category: str, sub_index: int) -> Optional[Dict]:
        """Получение информации об абонементе"""
        try:
            user_data = self.user_data_manager.load_user_data(chat_id)
            
            # Проверяем существование категории и абонемента
            if category not in user_data:
                logger.error(f"Категория {category} не найдена в данных пользователя {chat_id}")
                return None
            
            subscriptions = user_data[category]
            if not 0 <= sub_index < len(subscriptions):
                logger.error(f"Индекс абонемента {sub_index} выходит за пределы списка")
                return None
            
            return subscriptions[sub_index]
            
        except Exception as e:
            logger.error(f"Ошибка при получении информации об абонементе: {e}")
            return None
    
    def get_category_subscriptions(self, chat_id: int, category: str) -> List[Dict]:
        """Получение списка абонементов в категории"""
        try:
            user_data = self.user_data_manager.load_user_data(chat_id)
            
            # Проверяем существование категории
            if category not in user_data:
                logger.error(f"Категория {category} не найдена в данных пользователя {chat_id}")
                return []
            
            return user_data[category]
            
        except Exception as e:
            logger.error(f"Ошибка при получении списка абонементов: {e}")
            return [] 