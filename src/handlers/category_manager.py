from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import CallbackContext, CommandHandler, CallbackQueryHandler, MessageHandler, Filters
import json
import os
from typing import List, Dict
from config import USERS_DATA_DIR, CHOOSING_CATEGORY_NAME

class CategoryManager:
    def __init__(self):
        self.commands = [
            CommandHandler('start', self.show_main_menu)
        ]
        self.callbacks = [
            CallbackQueryHandler(self.handle_category_callback, pattern='^category_'),
            CallbackQueryHandler(self.handle_settings_callback, pattern='^settings'),
            CallbackQueryHandler(self.handle_add_category_callback, pattern='^add_category'),
            CallbackQueryHandler(self.handle_delete_category_menu_callback, pattern='^delete_category_menu'),
            CallbackQueryHandler(self.handle_delete_category_callback, pattern='^delete_category_'),
            CallbackQueryHandler(self.back_to_main_menu_callback, pattern='^back_to_main')
        ]
        self.handlers = [
            MessageHandler(
                Filters.text & ~Filters.command,
                self.handle_category_name_input
            )
        ]

    def show_main_menu(self, update: Update, context: CallbackContext) -> None:
        """Показ главного меню"""
        chat_id = update.effective_chat.id
        categories = self.get_user_categories(chat_id)
        
        keyboard = []
        # Кнопки для категорий
        current_row = []
        for category in categories:
            current_row.append(
                InlineKeyboardButton(f"📁 {category}", callback_data=f"category_{category}")
            )
            if len(current_row) == 2:
                keyboard.append(current_row)
                current_row = []
        
        if current_row:
            keyboard.append(current_row)
        
        # Кнопка настроек
        keyboard.append([
            InlineKeyboardButton("⚙️ Настройки", callback_data="settings")
        ])

        reply_markup = InlineKeyboardMarkup(keyboard)
        if update.message:
            update.message.reply_text(
                "🏠 Главное меню\n\n"
                "Выберите категорию или перейдите в настройки:",
                reply_markup=reply_markup
            )
        else:
            update.callback_query.edit_message_text(
                "🏠 Главное меню\n\n"
                "Выберите категорию или перейдите в настройки:",
                reply_markup=reply_markup
            )

    def handle_settings_callback(self, update: Update, context: CallbackContext) -> None:
        """Обработка кнопки настроек"""
        query = update.callback_query
        query.answer()
        
        keyboard = [
            [InlineKeyboardButton("➕ Создать категорию", callback_data="add_category")],
            [InlineKeyboardButton("❌ Удалить категорию", callback_data="delete_category_menu")],
            [InlineKeyboardButton("🔙 В главное меню", callback_data="back_to_main")]
        ]
        
        query.edit_message_text(
            "⚙️ Настройки\n\n"
            "Выберите действие:",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )

    def handle_add_category_callback(self, update: Update, context: CallbackContext) -> None:
        """Обработка добавления категории"""
        query = update.callback_query
        query.answer()
        
        context.user_data['waiting_for_category_name'] = True
        query.edit_message_text(
            "Введите название новой категории:",
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton("🔙 Отмена", callback_data="settings")
            ]])
        )
        return CHOOSING_CATEGORY_NAME

    def handle_category_name_input(self, update: Update, context: CallbackContext) -> None:
        """Обработка ввода названия категории"""
        if not context.user_data.get('waiting_for_category_name'):
            return
        
        chat_id = update.effective_chat.id
        category_name = update.message.text.strip()
        
        # Проверяем, что категория не пустая
        if not category_name:
            update.message.reply_text(
                "❌ Название категории не может быть пустым. Попробуйте еще раз:",
                reply_markup=InlineKeyboardMarkup([[
                    InlineKeyboardButton("🔙 Отмена", callback_data="settings")
                ]])
            )
            return CHOOSING_CATEGORY_NAME
        
        # Проверяем, что такой категории еще нет
        categories = self.get_user_categories(chat_id)
        if category_name in categories:
            update.message.reply_text(
                "❌ Такая категория уже существует. Введите другое название:",
                reply_markup=InlineKeyboardMarkup([[
                    InlineKeyboardButton("🔙 Отмена", callback_data="settings")
                ]])
            )
            return CHOOSING_CATEGORY_NAME
        
        # Добавляем категорию
        self.add_category(chat_id, category_name)
        context.user_data['waiting_for_category_name'] = False
        
        # Отправляем подтверждение
        keyboard = [
            [InlineKeyboardButton("📁 Перейти в категорию", callback_data=f"category_{category_name}")],
            [InlineKeyboardButton("🔙 В главное меню", callback_data="back_to_main")]
        ]
        update.message.reply_text(
            f"✅ Категория «{category_name}» успешно создана!",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
        return -1

    def handle_delete_category_menu_callback(self, update: Update, context: CallbackContext) -> None:
        """Показ меню удаления категорий"""
        query = update.callback_query
        query.answer()
        
        chat_id = query.message.chat_id
        categories = self.get_user_categories(chat_id)
        
        if not categories:
            query.edit_message_text(
                "❌ У вас пока нет категорий для удаления.",
                reply_markup=InlineKeyboardMarkup([[
                    InlineKeyboardButton("🔙 Назад", callback_data="settings")
                ]])
            )
            return
        
        keyboard = []
        for category in categories:
            keyboard.append([
                InlineKeyboardButton(f"❌ {category}", callback_data=f"delete_category_{category}")
            ])
        
        keyboard.append([InlineKeyboardButton("🔙 Назад", callback_data="settings")])
        
        query.edit_message_text(
            "❌ Удаление категорий\n\n"
            "Выберите категорию для удаления:",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )

    def handle_delete_category_callback(self, update: Update, context: CallbackContext) -> None:
        """Обработка удаления категории"""
        query = update.callback_query
        chat_id = query.message.chat_id
        category = query.data.replace("delete_category_", "")
        
        self.delete_category(chat_id, category)
        query.answer(f"✅ Категория «{category}» удалена")
        
        # Возвращаемся в меню удаления категорий
        self.handle_delete_category_menu_callback(update, context)

    def back_to_main_menu_callback(self, update: Update, context: CallbackContext) -> None:
        """Возврат в главное меню"""
        query = update.callback_query
        query.answer()
        self.show_main_menu(update, context)

    def handle_category_callback(self, update: Update, context: CallbackContext) -> None:
        """Обработка выбора категории"""
        query = update.callback_query
        chat_id = query.message.chat_id
        category = query.data.replace("category_", "")
        
        # Проверяем, что категория существует у пользователя
        categories = self.get_user_categories(chat_id)
        if category not in categories:
            query.answer("❌ Категория не найдена")
            return
        
        keyboard = [
            [InlineKeyboardButton("➕ Создать абонемент", callback_data=f"create_{category}")],
            [InlineKeyboardButton("📋 Список абонементов", callback_data=f"subscription_list_{category}")],
            [InlineKeyboardButton("❌ Удалить абонемент", callback_data=f"subscription_delete_menu_{category}")],
            [InlineKeyboardButton("🔙 В главное меню", callback_data="back_to_main")]
        ]
        
        query.edit_message_text(
            f"📁 Категория: {category}\n\n"
            "Выберите действие:",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )

    def get_user_categories(self, chat_id: int) -> List[str]:
        """Получение списка категорий пользователя"""
        file_path = os.path.join(USERS_DATA_DIR, f"{chat_id}.json")
        if not os.path.exists(file_path):
            return []
        with open(file_path, 'r') as f:
            data = json.load(f)
            return list(data.get('categories', {}).keys())

    def add_category(self, chat_id: int, category_name: str) -> None:
        """Добавление новой категории"""
        file_path = os.path.join(USERS_DATA_DIR, f"{chat_id}.json")
        if os.path.exists(file_path):
            with open(file_path, 'r') as f:
                data = json.load(f)
        else:
            data = {'categories': {}}
        
        if 'categories' not in data:
            data['categories'] = {}
        
        if category_name not in data['categories']:
            data['categories'][category_name] = {
                'name': category_name,
                'subscriptions': []
            }

        with open(file_path, 'w') as f:
            json.dump(data, f, indent=4)

    def delete_category(self, chat_id: int, category_name: str) -> None:
        """Удаление категории"""
        file_path = os.path.join(USERS_DATA_DIR, f"{chat_id}.json")
        if not os.path.exists(file_path):
            return
        
        with open(file_path, 'r') as f:
            data = json.load(f)
        
        if 'categories' in data and category_name in data['categories']:
            del data['categories'][category_name]
            
        with open(file_path, 'w') as f:
            json.dump(data, f, indent=4) 