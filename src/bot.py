import os
import logging
from telegram import Update
from telegram.ext import (
    Updater, CommandHandler, CallbackQueryHandler,
    MessageHandler, Filters, ConversationHandler
)
from telegram.error import TelegramError

from models.user_data import UserDataManager
from utils.subscription_manager import SubscriptionManager
from handlers.base import BaseHandler
from config import BOT_TOKEN, CHOOSING_NAME_SURNAME, ENTERING_LESSONS_COUNT, CHOOSING_CATEGORY_NAME
from src.handlers.category_manager import CategoryManager
from src.handlers.subscription import SubscriptionHandler

# Настройка логирования
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

class DanceBot:
    """Основной класс бота для управления абонементами"""
    
    def __init__(self):
        """Инициализация бота"""
        self.updater = Updater(BOT_TOKEN)
        self.dp = self.updater.dispatcher
        
        # Инициализация менеджеров
        self.subscription_manager = SubscriptionManager()
        
        # Инициализация обработчиков
        self.subscription_handler = SubscriptionHandler(self.subscription_manager)
        self.category_manager = CategoryManager()
        
        # Регистрация обработчиков
        self._setup_handlers()
    
    def _setup_handlers(self):
        """Настройка обработчиков команд"""
        # Обработчик команды /start
        self.dp.add_handler(CommandHandler('start', self.subscription_handler.start))
        
        # Обработчик создания абонемента
        subscription_conv_handler = ConversationHandler(
            entry_points=[
                CallbackQueryHandler(
                    self.subscription_handler.process_name_surname,
                    pattern='^create_.*'
                )
            ],
            states={
                CHOOSING_NAME_SURNAME: [
                    MessageHandler(
                        Filters.text & ~Filters.command,
                        self.subscription_handler.process_name_surname
                    )
                ],
                ENTERING_LESSONS_COUNT: [
                    MessageHandler(
                        Filters.text & ~Filters.command,
                        self.subscription_handler.process_name_surname
                    )
                ]
            },
            fallbacks=[
                CallbackQueryHandler(
                    self.subscription_handler.button,
                    pattern='^category_.*'
                ),
                CallbackQueryHandler(
                    self.subscription_handler.button,
                    pattern='^back_to_main$'
                ),
                CommandHandler('start', self.subscription_handler.start)
            ],
            per_message=False,
            name="subscription_conversation"
        )
        self.dp.add_handler(subscription_conv_handler)
        
        # Обработчик создания категории
        category_conv_handler = ConversationHandler(
            entry_points=[
                CallbackQueryHandler(
                    self.category_manager.handle_add_category_callback,
                    pattern='^add_category$'
                )
            ],
            states={
                CHOOSING_CATEGORY_NAME: [
                    MessageHandler(
                        Filters.text & ~Filters.command,
                        self.category_manager.handle_category_name_input
                    )
                ]
            },
            fallbacks=[
                CallbackQueryHandler(
                    self.category_manager.handle_settings_callback,
                    pattern='^settings$'
                ),
                CallbackQueryHandler(
                    self.category_manager.back_to_main_menu_callback,
                    pattern='^back_to_main$'
                ),
                CommandHandler('start', self.subscription_handler.start)
            ],
            per_message=False,
            name="category_conversation"
        )
        self.dp.add_handler(category_conv_handler)
        
        # Регистрация обработчиков категорий
        for command in self.category_manager.commands:
            self.dp.add_handler(command)
        for callback in self.category_manager.callbacks:
            self.dp.add_handler(callback)
        for handler in self.category_manager.handlers:
            self.dp.add_handler(handler)
        
        # Регистрация специфичных обработчиков подписок
        for callback in self.subscription_handler.callbacks:
            self.dp.add_handler(callback)
        
        # Общий обработчик кнопок регистрируем в последнюю очередь
        self.dp.add_handler(CallbackQueryHandler(self.subscription_handler.button))
        
        # Обработчик ошибок
        self.dp.add_error_handler(self.error_handler)
    
    def error_handler(self, update: Update, context):
        """Обработка ошибок"""
        try:
            raise context.error
        except TelegramError as e:
            # Игнорируем ошибку о неизмененном сообщении
            if "Message is not modified" in str(e):
                return
            logger.error(f"Telegram Error: {e}")
        except Exception as e:
            logger.error(f"General Error: {e}")
    
    def run(self):
        """Запуск бота"""
        self.updater.start_polling()
        print("Бот запущен")
        self.updater.idle()

def main():
    bot = DanceBot()
    bot.run()

if __name__ == '__main__':
    main() 