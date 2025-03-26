import random
from typing import Dict, Any
from config import RANDOM_EMOJIS

def get_random_emoji() -> str:
    """Получение случайного эмодзи"""
    return random.choice(RANDOM_EMOJIS)

def escape_markdown_v2(text: str) -> str:
    """Экранирование специальных символов для Markdown V2"""
    special_chars = ['_', '*', '[', ']', '(', ')', '~', '`', '>', '#', '+', '-', '=', '|', '{', '}', '.', '!']
    escaped_text = ''
    for char in text:
        if char in special_chars:
            escaped_text += f'\\{char}'
        else:
            escaped_text += char
    return escaped_text

def format_subscription_info(sub: Dict[str, Any], show_lessons: bool = False) -> str:
    """Форматирование информации об абонементе"""
    emoji = RANDOM_EMOJIS[hash(sub['name'] + sub['surname']) % len(RANDOM_EMOJIS)]
    name = f"{sub['name']} {sub['surname']}"
    text = f"{emoji} {name}"
    
    if show_lessons:
        used = len(sub.get('used_lessons', {}))
        total = sub['lessons']
        text += f" ({used}/{total})"
    
    return text

def format_category_name(category: str) -> str:
    """Форматирование названия категории"""
    category_mapping = {
        'strip': 'Стрип',
        'exotic_sport': 'ЭкзоСпорт',
        'exo0': 'Экзо 0',
        'individual': 'Индив',
        'pole_dance': 'Pole Dance',
        'aerial_silk': 'Воздушное полотно'
    }
    return category_mapping.get(category, category) 