import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, ParseMode
from telegram.ext import CallbackContext, ConversationHandler, CallbackQueryHandler
from .base import BaseHandler
from utils.formatting import format_subscription_info
from config import CHOOSING_NAME_SURNAME, ENTERING_LESSONS_COUNT, USERS_DATA_DIR
from utils.subscription_manager import SubscriptionManager
import os
import json
from typing import Dict
from datetime import datetime

logger = logging.getLogger(__name__)

class SubscriptionHandler(BaseHandler):
    """Обработчик абонементов"""
    
    def __init__(self, subscription_manager: SubscriptionManager):
        super().__init__(subscription_manager)
        self.commands = []
        self.callbacks = [
            CallbackQueryHandler(self.handle_subscription_callback, pattern='^subscription_'),
            CallbackQueryHandler(self.handle_lesson_callback, pattern='^lesson_')
        ]
    
    def button(self, update: Update, context: CallbackContext):
        """Обработка нажатий на кнопки"""
        query = update.callback_query
        query.answer()
        
        try:
            chat_id = update.effective_chat.id
            data = query.data
            
            logger.info(f"Обработка callback: chat_id={chat_id}, data={data}")
            
            # Обработка команды start и возврата в главное меню
            if data == 'start' or data == 'back_to_main':
                self.start(update, context)
                return ConversationHandler.END
            
            # Обработка нажатия на категорию
            if data.startswith('category_'):
                category = data.replace('category_', '')
                user_data = self.user_data_manager.load_user_data(chat_id)
                if category not in user_data['categories']:
                    logger.error(f"Категория не найдена: {category}")
                    self.send_error_message(update, "Категория не найдена")
                    return ConversationHandler.END
                
                text, reply_markup = self.get_category_keyboard(chat_id, category)
                query.edit_message_text(
                    text=text,
                    reply_markup=reply_markup
                )
                return ConversationHandler.END
            
            # Обработка настроек
            if data == 'settings':
                keyboard = [
                    [InlineKeyboardButton("➕ Создать категорию", callback_data="add_category")],
                    [InlineKeyboardButton("❌ Удалить категорию", callback_data="delete_category_menu")],
                    [InlineKeyboardButton("🔙 В главное меню", callback_data="back_to_main")]
                ]
                query.edit_message_text(
                    "⚙️ Настройки\n\nВыберите действие:",
                    reply_markup=InlineKeyboardMarkup(keyboard)
                )
                return ConversationHandler.END
            
            logger.error(f"Неизвестный callback: {data}")
            return ConversationHandler.END
            
        except Exception as e:
            logger.error(f"Ошибка при обработке нажатия кнопки: {e}")
            self.send_error_message(update)
            return ConversationHandler.END
    
    def start(self, update: Update, context: CallbackContext):
        """Обработка команды /start"""
        if not update.message and not update.callback_query:
            return
        
        chat_id = update.effective_chat.id
        user_data = self.user_data_manager.load_user_data(chat_id)
        keyboard = []
        current_row = []
        
        # Создаем кнопки для каждой категории пользователя
        for category_id, category_data in user_data['categories'].items():
            button = InlineKeyboardButton(
                category_data.get('name', category_id),
                callback_data=f'category_{category_id}'
            )
            current_row.append(button)
            
            if len(current_row) == 2:
                keyboard.append(current_row)
                current_row = []
        
        if current_row:
            keyboard.append(current_row)
        
        # Добавляем кнопку настроек
        keyboard.append([
            InlineKeyboardButton("⚙️ Настройки", callback_data="settings")
        ])
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        message = "🏠 Главное меню\n\nВыберите категорию или перейдите в настройки:"
        
        if update.callback_query:
            update.callback_query.edit_message_text(
                text=message,
                reply_markup=reply_markup
            )
        else:
            update.message.reply_text(
                text=message,
                reply_markup=reply_markup
            )
    
    def get_category_keyboard(self, chat_id: int, category: str) -> tuple:
        """Получение клавиатуры для категории"""
        user_data = self.user_data_manager.load_user_data(chat_id)
        category_data = user_data['categories'].get(category, {})
        
        text = f"📁 Категория: {category_data.get('name', category)}\n\n"
        text += "Выберите действие:"
        
        keyboard = [
            [InlineKeyboardButton("➕ Создать абонемент", callback_data=f"create_{category}")],
            [InlineKeyboardButton("📋 Список абонементов", callback_data=f"subscription_list_{category}")],
            [InlineKeyboardButton("❌ Удалить абонемент", callback_data=f"subscription_delete_menu_{category}")],
            [InlineKeyboardButton("🔙 В главное меню", callback_data="back_to_main")]
        ]
        
        return text, InlineKeyboardMarkup(keyboard)

    def process_name_surname(self, update: Update, context: CallbackContext):
        """Обработка создания абонемента"""
        try:
            chat_id = update.effective_chat.id
            current_state = context.user_data.get('state', None)
            logger.info(f"process_name_surname вызван: chat_id={chat_id}, current_state={current_state}, user_data={context.user_data}")
            
            # Если это callback query (начало создания абонемента)
            if update.callback_query:
                query = update.callback_query
                query.answer()
                
                # Получаем категорию из callback_data
                category = query.data.replace('create_', '')
                context.user_data['category'] = category
                context.user_data['state'] = CHOOSING_NAME_SURNAME
                
                # Запрашиваем название абонемента
                keyboard = [[InlineKeyboardButton("🔙 Отмена", callback_data=f"category_{category}")]]
                query.edit_message_text(
                    "Введите название абонемента:",
                    reply_markup=InlineKeyboardMarkup(keyboard)
                )
                logger.info(f"Запрошено название абонемента для категории {category}, state={CHOOSING_NAME_SURNAME}")
                return CHOOSING_NAME_SURNAME
            
            # Если это сообщение (обработка введенных данных)
            if update.message:
                text = update.message.text.strip()
                logger.info(f"Получен текст: {text}, состояние: {context.user_data}")
                
                # Если это первый шаг (ввод названия абонемента)
                if current_state == CHOOSING_NAME_SURNAME:
                    context.user_data['subscription_name'] = text
                    context.user_data['state'] = ENTERING_LESSONS_COUNT
                    category = context.user_data.get('category')
                    
                    # Запрашиваем количество дней
                    keyboard = [[InlineKeyboardButton("🔙 Отмена", callback_data=f"category_{category}")]]
                    update.message.reply_text(
                        "Введите количество дней в абонементе (целое положительное число):",
                        reply_markup=InlineKeyboardMarkup(keyboard)
                    )
                    logger.info(f"Запрошено количество дней для абонемента {text}, state={ENTERING_LESSONS_COUNT}")
                    return ENTERING_LESSONS_COUNT
                
                # Обработка количества дней
                elif current_state == ENTERING_LESSONS_COUNT:
                    try:
                        days = int(text)
                        if days <= 0:
                            raise ValueError("Количество дней должно быть положительным числом")
                        
                        category = context.user_data.get('category')
                        subscription_name = context.user_data.get('subscription_name')
                        
                        if not category or not subscription_name:
                            logger.error(f"Отсутствуют необходимые данные в контексте: {context.user_data}")
                            update.message.reply_text(
                                "❌ Произошла ошибка. Пожалуйста, начните создание абонемента заново."
                            )
                            return ConversationHandler.END
                        
                        logger.info(f"Создание абонемента: категория={category}, название={subscription_name}, дней={days}")
                        
                        # Создаем новый абонемент
                        if not self.subscription_manager.add_subscription(chat_id, category, subscription_name, days):
                            logger.error(f"Ошибка при создании абонемента: chat_id={chat_id}, category={category}, name={subscription_name}, days={days}")
                            update.message.reply_text(
                                "❌ Не удалось создать абонемент. Пожалуйста, попробуйте еще раз."
                            )
                            return ConversationHandler.END
                        
                        # Отправляем подтверждение
                        keyboard = [
                            [InlineKeyboardButton("📋 Показать все абонементы", callback_data=f"subscription_list_{category}")],
                            [InlineKeyboardButton("🔙 К категории", callback_data=f"category_{category}")]
                        ]
                        
                        update.message.reply_text(
                            f"✅ Абонемент успешно создан!\n"
                            f"Название: {subscription_name}\n"
                            f"Количество дней: {days}",
                            reply_markup=InlineKeyboardMarkup(keyboard)
                        )
                        
                        logger.info(f"Абонемент успешно создан: {subscription_name}")
                        
                        # Очищаем данные контекста
                        context.user_data.clear()
                        return ConversationHandler.END
                        
                    except ValueError:
                        category = context.user_data.get('category')
                        keyboard = [[InlineKeyboardButton("🔙 Отмена", callback_data=f"category_{category}")]]
                        update.message.reply_text(
                            "❌ Пожалуйста, введите корректное количество дней (целое положительное число)",
                            reply_markup=InlineKeyboardMarkup(keyboard)
                        )
                        return ENTERING_LESSONS_COUNT
                
                else:
                    logger.error(f"Неожиданное состояние: {current_state}")
                    update.message.reply_text(
                        "❌ Произошла ошибка. Пожалуйста, начните создание абонемента заново.",
                        reply_markup=InlineKeyboardMarkup([[
                            InlineKeyboardButton("🔙 В главное меню", callback_data="back_to_main")
                        ]])
                    )
                    return ConversationHandler.END
            
            logger.error("Неожиданный тип обновления")
            return ConversationHandler.END
            
        except Exception as e:
            logger.error(f"Ошибка при обработке создания абонемента: {e}")
            if update.message:
                update.message.reply_text(
                    "❌ Произошла ошибка. Пожалуйста, попробуйте еще раз."
                )
            return ConversationHandler.END
    
    def handle_subscription_callback(self, update: Update, context: CallbackContext) -> None:
        query = update.callback_query
        chat_id = query.message.chat_id
        data = query.data
        
        if data.startswith('subscription_list_'):
            self.show_subscription_list(update, context)
        elif data.startswith('subscription_delete_menu_'):
            self.show_delete_subscription_menu(update, context)
        elif data.startswith('subscription_delete_'):
            self.handle_delete_subscription(update, context)

    def show_delete_subscription_menu(self, update: Update, context: CallbackContext) -> None:
        """Показ меню удаления абонементов"""
        query = update.callback_query
        chat_id = query.message.chat_id
        category = query.data.split('_')[3]
        
        # Получаем список абонементов
        subscriptions = self.subscription_manager.get_subscriptions(chat_id, category)
        keyboard = []
        
        if not subscriptions:
            query.edit_message_text(
                "❌ В этой категории нет абонементов для удаления.",
                reply_markup=InlineKeyboardMarkup([[
                    InlineKeyboardButton("🔙 Назад", callback_data=f"category_{category}")
                ]])
            )
            query.answer()
            return
        
        # Создаем кнопки для каждого абонемента
        for i, sub in enumerate(subscriptions):
            name = sub.get('name', '')
            used_lessons = sub.get('used_lessons', {})
            if not isinstance(used_lessons, dict):
                used_lessons = {}
            total = sub.get('total_lessons', 0)
            used_count = len(used_lessons)
            
            keyboard.append([
                InlineKeyboardButton(
                    f"❌ {name} ({used_count}/{total} дней)",
                    callback_data=f"subscription_delete_{category}_{i}"
                )
            ])
        
        keyboard.append([InlineKeyboardButton("🔙 Назад", callback_data=f"category_{category}")])
        
        query.edit_message_text(
            "❌ Удаление абонементов\n\n"
            "Выберите абонемент для удаления:",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
        query.answer()

    def handle_delete_subscription(self, update: Update, context: CallbackContext) -> None:
        query = update.callback_query
        chat_id = query.message.chat_id
        _, _, category, sub_index = query.data.split('_', 3)
        
        try:
            sub_index = int(sub_index)
            # Получаем список абонементов
            subscriptions = self.subscription_manager.get_subscriptions(chat_id, category)
            if not subscriptions or sub_index >= len(subscriptions):
                self.send_error_message(update, "Абонемент не найден. Пожалуйста, попробуйте еще раз.")
                return
            
            # Удаляем абонемент
            subscriptions.pop(sub_index)
            
            # Сохраняем обновленные данные
            self.subscription_manager.save_subscriptions(chat_id, category, subscriptions)
            
            # Возвращаемся к списку абонементов
            self.show_delete_subscription_menu(update, context)
            
        except (ValueError, IndexError) as e:
            logger.error(f"Ошибка при удалении абонемента: {e}")
            self.send_error_message(update, "Не удалось удалить абонемент. Пожалуйста, попробуйте еще раз.")

    def show_subscription_list(self, update: Update, context: CallbackContext) -> None:
        """Показ списка абонементов"""
        query = update.callback_query
        chat_id = query.message.chat_id
        category = query.data.split('_')[2]
        
        # Получаем список абонементов
        subscriptions = self.subscription_manager.get_subscriptions(chat_id, category)
        keyboard = []
        
        if not subscriptions:
            query.edit_message_text(
                "📋 В этой категории пока нет абонементов.",
                reply_markup=InlineKeyboardMarkup([[
                    InlineKeyboardButton("🔙 Назад", callback_data=f"category_{category}")
                ]])
            )
            query.answer()
            return
        
        text = "📋 Список абонементов:\n\n"
        
        # Создаем кнопки для каждого абонемента
        for i, sub in enumerate(subscriptions):
            name = sub.get('name', '')
            used_lessons = sub.get('used_lessons', {})
            if not isinstance(used_lessons, dict):
                used_lessons = {}
            total = sub.get('total_lessons', 0)
            used_count = len(used_lessons)
            
            text += f"• {name}: {used_count}/{total} дней\n"
            keyboard.append([
                InlineKeyboardButton(
                    f"{name} ({used_count}/{total} дней)",
                    callback_data=f"lesson_{category}_{i}_0"
                )
            ])
        
        keyboard.append([InlineKeyboardButton("🔙 Назад", callback_data=f"category_{category}")])
        
        query.edit_message_text(
            text,
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
        query.answer()

    def handle_lesson_callback(self, update: Update, context: CallbackContext) -> None:
        query = update.callback_query
        chat_id = query.message.chat_id
        _, category, sub_index, lesson_num = query.data.split('_')
        sub_index = int(sub_index)
        lesson_num = int(lesson_num)
        
        # Получаем абонемент
        subscriptions = self.subscription_manager.get_subscriptions(chat_id, category)
        if not subscriptions or sub_index >= len(subscriptions):
            query.answer("Абонемент не найден")
            return
        
        subscription = subscriptions[sub_index]
        
        # Если это первое нажатие (lesson_num == 0), показываем детали абонемента
        if lesson_num == 0:
            keyboard = []
            total = subscription.get('total_lessons', 0)
            used_lessons = subscription.get('used_lessons', {})
            if not isinstance(used_lessons, dict):
                used_lessons = {}
                subscription['used_lessons'] = used_lessons
            
            # Создаем кнопки для каждого дня
            current_row = []
            for i in range(1, total + 1):
                lesson_str = str(i)
                button_text = used_lessons.get(lesson_str, str(i))
                current_row.append(InlineKeyboardButton(
                    button_text,
                    callback_data=f"lesson_{category}_{sub_index}_{i}"
                ))
                
                if len(current_row) == 4:
                    keyboard.append(current_row)
                    current_row = []
            
            if current_row:
                keyboard.append(current_row)
            
            keyboard.append([InlineKeyboardButton("🔙 Назад", callback_data=f"subscription_list_{category}")])
            
            text = f"🎫 Абонемент: {subscription.get('name', '')}\n\n"
            text += f"Использовано дней: {len(used_lessons)}/{total}\n\n"
            text += "Нажмите на день, чтобы отметить его:"
            
            query.edit_message_text(
                text=text,
                reply_markup=InlineKeyboardMarkup(keyboard)
            )
        else:
            # Инициализируем used_lessons если его нет
            if 'used_lessons' not in subscription:
                subscription['used_lessons'] = {}
            
            lesson_str = str(lesson_num)
            current_date = datetime.now().strftime("%d.%m")
            
            # Если день уже отмечен - снимаем отметку
            if lesson_str in subscription['used_lessons']:
                del subscription['used_lessons'][lesson_str]
            else:
                # Иначе отмечаем день текущей датой
                subscription['used_lessons'][lesson_str] = current_date
            
            # Сохраняем изменения
            subscriptions[sub_index] = subscription
            self.subscription_manager.save_subscriptions(chat_id, category, subscriptions)
            
            # Обновляем отображение
            keyboard = []
            total = subscription.get('total_lessons', 0)
            used_lessons = subscription.get('used_lessons', {})
            
            # Создаем кнопки для каждого дня
            current_row = []
            for i in range(1, total + 1):
                lesson_str = str(i)
                button_text = used_lessons.get(lesson_str, str(i))
                current_row.append(InlineKeyboardButton(
                    button_text,
                    callback_data=f"lesson_{category}_{sub_index}_{i}"
                ))
                
                if len(current_row) == 4:
                    keyboard.append(current_row)
                    current_row = []
            
            if current_row:
                keyboard.append(current_row)
            
            keyboard.append([InlineKeyboardButton("🔙 Назад", callback_data=f"subscription_list_{category}")])
            
            text = f"🎫 Абонемент: {subscription.get('name', '')}\n\n"
            text += f"Использовано дней: {len(used_lessons)}/{total}\n\n"
            text += "Нажмите на день, чтобы отметить его:"
            
            query.edit_message_text(
                text=text,
                reply_markup=InlineKeyboardMarkup(keyboard)
            )
        
        query.answer()

    def send_error_message(self, update: Update, text: str = None):
        """Отправка сообщения об ошибке"""
        if not text:
            text = "Произошла ошибка. Пожалуйста, попробуйте еще раз или начните сначала."
        
        if update.callback_query:
            update.callback_query.answer()
            update.callback_query.edit_message_text(
                text=text,
                reply_markup=InlineKeyboardMarkup([[
                    InlineKeyboardButton("🔙 В главное меню", callback_data='back_to_main')
                ]])
            )
        else:
            update.message.reply_text(
                text=text,
                reply_markup=InlineKeyboardMarkup([[
                    InlineKeyboardButton("🔙 В главное меню", callback_data='back_to_main')
                ]])
            ) 