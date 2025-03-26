import json
import os
from typing import Dict, List, Optional, Any
from datetime import datetime
import logging
from threading import Lock

logger = logging.getLogger(__name__)

class SubscriptionManager:
    def __init__(self, data_dir: str = 'data'):
        """Инициализация менеджера абонементов"""
        self.data_dir = data_dir
        # Создаем директорию с абсолютным путем
        if not os.path.isabs(data_dir):
            self.data_dir = os.path.abspath(data_dir)
        
        # Создаем директорию с правильными правами доступа
        os.makedirs(self.data_dir, mode=0o700, exist_ok=True)
        # Устанавливаем права доступа даже если директория уже существует
        os.chmod(self.data_dir, 0o700)
        
        # Инициализация кэша и блокировки
        self._cache: Dict[int, Dict[str, Any]] = {}
        self._cache_lock = Lock()
        
        logger.info(f"Инициализация SubscriptionManager: data_dir={self.data_dir}")
    
    def _get_user_file(self, chat_id: int) -> str:
        """Получение пути к файлу пользователя"""
        # Проверяем, что chat_id является положительным числом
        if not isinstance(chat_id, int) or chat_id <= 0:
            raise ValueError(f"Некорректный chat_id: {chat_id}")
        
        # Создаем безопасный путь к файлу
        safe_filename = f'{chat_id}.json'
        if '..' in safe_filename or '/' in safe_filename:
            raise ValueError(f"Некорректное имя файла: {safe_filename}")
        
        file_path = os.path.join(self.data_dir, safe_filename)
        # Проверяем, что путь не вышел за пределы data_dir
        if not os.path.abspath(file_path).startswith(os.path.abspath(self.data_dir)):
            raise ValueError(f"Попытка доступа к файлу вне разрешенной директории: {file_path}")
        
        return file_path
    
    def _load_user_data(self, chat_id: int) -> Dict[str, Any]:
        """Загрузка данных пользователя"""
        try:
            # Проверяем кэш
            with self._cache_lock:
                if chat_id in self._cache:
                    return self._cache[chat_id]
            
            file_path = self._get_user_file(chat_id)
            logger.info(f"Загрузка данных пользователя: chat_id={chat_id}, file_path={file_path}")
            
            if os.path.exists(file_path):
                # Проверяем права доступа к файлу
                stat = os.stat(file_path)
                if stat.st_mode & 0o777 != 0o600:
                    # Если права неправильные, исправляем их
                    os.chmod(file_path, 0o600)
                
                with open(file_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    logger.info(f"Загружены данные для chat_id={chat_id}")
                    # Сохраняем в кэш
                    with self._cache_lock:
                        self._cache[chat_id] = data
                    return data
            else:
                # Создаем пустой файл с правильными правами
                logger.info(f"Создаем новый файл данных: {file_path}")
                empty_data = {}
                self._save_user_data(chat_id, empty_data)
                # Сохраняем в кэш
                with self._cache_lock:
                    self._cache[chat_id] = empty_data
                return empty_data
            
        except Exception as e:
            logger.error(f"Ошибка при загрузке данных пользователя: {e}, chat_id={chat_id}")
            return {}
    
    def _save_user_data(self, chat_id: int, data: Dict[str, Any]) -> bool:
        """Сохранение данных пользователя"""
        try:
            file_path = self._get_user_file(chat_id)
            logger.info(f"Сохранение данных пользователя: chat_id={chat_id}, file_path={file_path}")
            
            # Создаем директорию, если её нет
            os.makedirs(os.path.dirname(file_path), mode=0o700, exist_ok=True)
            
            # Сначала сохраняем во временный файл
            temp_file = f"{file_path}.tmp"
            with open(temp_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            
            # Устанавливаем права доступа только для владельца
            os.chmod(temp_file, 0o600)
            
            # Затем переименовываем временный файл в целевой
            os.replace(temp_file, file_path)
            
            # Устанавливаем права доступа для целевого файла
            os.chmod(file_path, 0o600)
            
            # Обновляем кэш
            with self._cache_lock:
                self._cache[chat_id] = data
            
            logger.info(f"Данные успешно сохранены: {file_path}")
            return True
        except Exception as e:
            logger.error(f"Ошибка при сохранении данных пользователя: {e}, chat_id={chat_id}, file_path={file_path}")
            if os.path.exists(temp_file):
                try:
                    os.remove(temp_file)
                except:
                    pass
            return False
    
    def add_subscription(self, chat_id: int, category: str, name: str, days: int) -> bool:
        """Добавление нового абонемента"""
        try:
            logger.info(f"Добавление абонемента: chat_id={chat_id}, category={category}, name={name}, days={days}")
            
            # Загружаем или создаем данные пользователя
            data = self._load_user_data(chat_id)
            logger.info(f"Текущие данные пользователя: {data}")
            
            # Создаем категорию, если её нет
            if category not in data:
                logger.info(f"Создание новой категории: {category}")
                data[category] = []
            
            # Создаем новый абонемент
            subscription = {
                'name': name,
                'total_lessons': days,
                'used_lessons': {},
                'created_at': datetime.now().isoformat()
            }
            logger.info(f"Новый абонемент: {subscription}")
            
            # Добавляем абонемент в список
            data[category].append(subscription)
            
            # Сохраняем обновленные данные
            success = self._save_user_data(chat_id, data)
            if success:
                logger.info(f"Абонемент успешно добавлен: chat_id={chat_id}, category={category}")
            else:
                logger.error(f"Не удалось сохранить данные для chat_id={chat_id}, category={category}")
            return success
            
        except Exception as e:
            logger.error(f"Ошибка при добавлении абонемента: {e}, chat_id={chat_id}, category={category}")
            return False
    
    def get_subscriptions(self, chat_id: int, category: str) -> List[Dict[str, Any]]:
        """Получение списка абонементов в категории"""
        data = self._load_user_data(chat_id)
        return data.get(category, [])
    
    def get_subscription(self, chat_id: int, category: str, index: int) -> Optional[Dict[str, Any]]:
        """Получение абонемента по индексу"""
        subscriptions = self.get_subscriptions(chat_id, category)
        if 0 <= index < len(subscriptions):
            return subscriptions[index]
        return None
    
    def mark_lesson(self, chat_id: int, category: str, sub_index: int, lesson_num: int) -> bool:
        """Отметка занятия"""
        try:
            data = self._load_user_data(chat_id)
            subscription = data[category][sub_index]
            
            # Если занятие уже отмечено, снимаем отметку
            if str(lesson_num) in subscription['used_lessons']:
                del subscription['used_lessons'][str(lesson_num)]
            else:
                # Проверяем, не превышено ли количество занятий
                if len(subscription['used_lessons']) >= subscription['total_lessons']:
                    return False
                
                # Отмечаем занятие
                subscription['used_lessons'][str(lesson_num)] = datetime.now().strftime('%d.%m')
            
            return self._save_user_data(chat_id, data)
        except Exception:
            return False
    
    def delete_subscription(self, chat_id: int, category: str, sub_index: int) -> bool:
        """Удаление абонемента"""
        try:
            data = self._load_user_data(chat_id)
            if category in data and 0 <= sub_index < len(data[category]):
                data[category].pop(sub_index)
                return self._save_user_data(chat_id, data)
        except Exception:
            pass
        return False
    
    def save_subscriptions(self, chat_id: int, category: str, subscriptions: List[Dict[str, Any]]) -> bool:
        """Сохранение списка абонементов"""
        try:
            data = self._load_user_data(chat_id)
            data[category] = subscriptions
            return self._save_user_data(chat_id, data)
        except Exception as e:
            logger.error(f"Ошибка при сохранении абонементов: {e}")
            return False 