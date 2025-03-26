from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import CallbackContext, MessageHandler as TelegramMessageHandler, Filters

class MessageHandler:
    def __init__(self, category_manager, subscription_handler):
        self.category_manager = category_manager
        self.subscription_handler = subscription_handler
        self.handlers = [
            TelegramMessageHandler(Filters.text & ~Filters.command, self.handle_message)
        ]

    def handle_message(self, update: Update, context: CallbackContext) -> None:
        chat_id = update.effective_chat.id
        message_text = update.message.text

        # Проверяем, ожидаем ли мы название новой категории
        if context.user_data.get('waiting_for_category_name'):
            self.category_manager.add_category(chat_id, message_text)
            del context.user_data['waiting_for_category_name']
            
            # Показываем обновленное меню настроек
            keyboard = [
                [InlineKeyboardButton("➕ Создать категорию", callback_data="add_category")],
                [InlineKeyboardButton("❌ Удалить категорию", callback_data="delete_category_menu")],
                [InlineKeyboardButton("🔙 Назад", callback_data="back_to_main")]
            ]
            
            update.message.reply_text(
                f"✅ Категория '{message_text}' успешно создана!\n\n"
                "⚙️ Настройки\n"
                "Выберите действие:",
                reply_markup=InlineKeyboardMarkup(keyboard)
            )
            return

        # Проверяем, ожидаем ли мы данные для нового абонемента
        subscription_data = context.user_data.get('waiting_for_subscription')
        if subscription_data:
            if subscription_data['step'] == 'name':
                # Сохраняем название абонемента и запрашиваем количество занятий
                subscription_data['name'] = message_text
                subscription_data['step'] = 'lessons'
                update.message.reply_text(
                    "Введите количество занятий в абонементе (число):",
                    reply_markup=InlineKeyboardMarkup([[
                        InlineKeyboardButton("🔙 Отмена", callback_data=f"category_{subscription_data['category']}")
                    ]])
                )
            elif subscription_data['step'] == 'lessons':
                try:
                    lessons = int(message_text)
                    if lessons <= 0:
                        raise ValueError("Количество занятий должно быть положительным числом")
                    
                    # Создаем новый абонемент
                    self.subscription_handler.save_subscription(
                        chat_id,
                        subscription_data['category'],
                        subscription_data['name'],
                        {
                            'total_lessons': lessons,
                            'used_lessons': 0
                        }
                    )
                    
                    # Показываем обновленное меню категории
                    keyboard = [
                        [InlineKeyboardButton("➕ Создать абонемент", callback_data=f"subscription_create_{subscription_data['category']}")],
                        [InlineKeyboardButton("❌ Удалить абонемент", callback_data=f"subscription_delete_menu_{subscription_data['category']}")],
                        [InlineKeyboardButton("📋 Список абонементов", callback_data=f"subscription_list_{subscription_data['category']}")],
                        [InlineKeyboardButton("🔙 В главное меню", callback_data="back_to_main")]
                    ]
                    
                    update.message.reply_text(
                        f"✅ Абонемент '{subscription_data['name']}' на {lessons} занятий успешно создан!\n\n"
                        f"📁 Категория: {subscription_data['category']}\n"
                        "Выберите действие:",
                        reply_markup=InlineKeyboardMarkup(keyboard)
                    )
                    
                    del context.user_data['waiting_for_subscription']
                except ValueError:
                    update.message.reply_text(
                        "❌ Пожалуйста, введите корректное число занятий (целое положительное число).",
                        reply_markup=InlineKeyboardMarkup([[
                            InlineKeyboardButton("🔙 Отмена", callback_data=f"category_{subscription_data['category']}")
                        ]])
                    ) 