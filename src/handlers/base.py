import logging
from typing import Dict, Any
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, ParseMode
from telegram.ext import CallbackContext, ConversationHandler
from models.user_data import UserDataManager
from utils.subscription_manager import SubscriptionManager
from utils.formatting import format_subscription_info
from config import ADMIN_IDS

logger = logging.getLogger(__name__)

def is_admin(chat_id: int) -> bool:
    """Проверка прав администратора"""
    return chat_id in ADMIN_IDS

class BaseHandler:
    """Базовый обработчик команд"""
    
    def __init__(self, subscription_manager: SubscriptionManager = None):
        """Инициализация обработчика"""
        self.user_data_manager = UserDataManager()
        self.subscription_manager = subscription_manager
    
    def start(self, update: Update, context: CallbackContext):
        """Обработка команды /start"""
        if not update.message:
            return
        
        chat_id = update.effective_chat.id
        user_data = self.user_data_manager.load_user_data(chat_id)
        
        # Создаем клавиатуру с категориями
        keyboard = []
        current_row = []
        
        for category_id, category_data in DEFAULT_CATEGORIES.items():
            button = InlineKeyboardButton(
                category_data['name'],
                callback_data=category_id
            )
            current_row.append(button)
            
            if len(current_row) == 2:
                keyboard.append(current_row)
                current_row = []
        
        if current_row:
            keyboard.append(current_row)
        
        # Отправляем приветственное сообщение
        update.message.reply_text(
            "Привет! Я помогу тебе управлять абонементами.\n"
            "Выбери направление:",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
    
    def help(self, update: Update, context: CallbackContext):
        """Обработка команды /help"""
        if not update.message:
            return
        
        update.message.reply_text(
            "Доступные команды:\n"
            "/start - Начать работу с ботом\n"
            "/help - Показать это сообщение\n"
            "/cancel - Отменить текущее действие"
        )
    
    def cancel(self, update: Update, context: CallbackContext):
        """Обработка команды /cancel"""
        if not update.message:
            return
        
        context.user_data.clear()
        update.message.reply_text(
            "Действие отменено. Используйте /start, чтобы начать заново."
        )
        return ConversationHandler.END
    
    def error_handler(self, update: Update, context: CallbackContext):
        """Обработчик ошибок"""
        try:
            logger.error(f"Ошибка: {context.error}")
            if update:
                if update.effective_message:
                    update.effective_message.reply_text(
                        "Произошла ошибка. Пожалуйста, попробуйте позже или используйте /start для перезапуска.",
                        reply_markup=None
                    )
        except Exception as e:
            logger.error(f"Ошибка в обработчике ошибок: {e}")
    
    def send_error_message(self, update: Update, text: str = None):
        """Отправка сообщения об ошибке"""
        default_text = "Произошла ошибка. Пожалуйста, попробуйте еще раз или используйте /start."
        message = text or default_text
        
        if update.callback_query:
            update.callback_query.message.reply_text(message)
        elif update.message:
            update.message.reply_text(message)
    
    def get_category_keyboard(self, chat_id: int, category: str, show_list: bool = True) -> tuple[str, InlineKeyboardMarkup]:
        """Создание клавиатуры для категории"""
        # Формируем текст
        text = f"Направление: {format_category_name(category)}\n\n"
        
        # Получаем абонементы
        subscriptions = self.subscription_manager.get_subscriptions(chat_id, category)
        
        # Создаем клавиатуру
        keyboard = []
        
        # Сначала добавляем список абонементов как кнопки
        if subscriptions:
            text += "📋 Ваши абонементы:\n"
            for i, sub in enumerate(subscriptions, 1):
                used = len(sub.get('used_lessons', {}))
                total = sub['lessons']
                keyboard.append([
                    InlineKeyboardButton(
                        format_subscription_info(sub, show_lessons=True),
                        callback_data=f"lesson_{category}_{i-1}_0"
                    )
                ])
            text += "\n"
        else:
            text += "У вас пока нет абонементов в этом направлении.\n\n"
        
        # Добавляем разделитель
        text += "\nВыберите действие:"
        
        # Добавляем кнопки создания абонементов
        subscription_types = DEFAULT_CATEGORIES.get(category, {}).get('subscription_types', [])
        if subscription_types:
            for sub_type in subscription_types:
                keyboard.append([
                    InlineKeyboardButton(
                        f"➕ Создать абонемент на {sub_type['lessons']} занятий",
                        callback_data=f"create_{category}_{sub_type['lessons']}"
                    )
                ])
        
        # Добавляем кнопку "Назад"
        keyboard.append([
            InlineKeyboardButton("↩️ К списку направлений", callback_data="back_to_main")
        ])
        
        return text, InlineKeyboardMarkup(keyboard) 