import logging
import telebot # type: ignore
from telebot import types # type: ignore
from config import Config
from database import Database
import random
import os
from dotenv import load_dotenv # type: ignore
from utils.helpers import create_main_keyboard, get_exchange_rate, get_weather  

load_dotenv()

logging.basicConfig (
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

# Инициализация бота и базы данных
BOT_TOKEN = os.getenv('BOT_TOKEN') or Config.BOT_TOKEN
if not BOT_TOKEN:
    print("❌ ОШИБКА: BOT_TOKEN не найден!")
    exit(1)

bot = telebot.TeleBot(BOT_TOKEN)
db = Database()

@bot.message_handler(commands=['start'])
def send_welcome(message):
    welcome_text = """
🤖 Добро пожаловать в SmartHelperBot!

Я ваш универсальный помощник в Telegram. Вот что я умею:

📝 *Управление задачами* - создавайте и управляйте списком дел
💱 *Конвертер валют* - актуальные курсы валют
🌤️ *Погода* - текущая погода в любом городе
🎲 *Случайность* - генератор чисел и помощник в выборе

Используйте кнопки меню или команды для навигации!
    """
    
    bot.send_message(
        message.chat.id,
        welcome_text,
        reply_markup=create_main_keyboard(),
        parse_mode='Markdown'
    )

@bot.message_handler(commands=['help'])
def send_help(message):
    help_text = """
    📋 *Доступные команды:*

    *Управление задачами:*
    /todo add [задача] - добавить таск
    /todo list - показать таски  
    /todo delete [номер] - удалить таск

    *Конвертер валют:*
    /currency [сумма] [из] [в]
    Пример: `/currency 100 USD RUB`

    *Погода:*
    /weather [город]
    Пример: `/weather Москва`

    *Случайность:*
    /random number [от] [до]
    Пример: `/random number 1 100` 
    /random choice [варианты] - Случайный выбор
    Пример: `/random choice пицца сыр колбаска`
        """
    
    bot.send_message(
        message.chat.id,
        help_text,
        parse_mode='Markdown'
    )

@bot.message_handler(commands=['todo'])
def handle_todo(message):
    try:
        chat_id = message.chat.id
        command_text = message.text
        
        if command_text.strip() == '/todo':
            show_tasks(chat_id)
            return
            
        command_parts = command_text.split(maxsplit=2)
        
        if len(command_parts) < 2:
            show_tasks(chat_id)
            return
            
        action = command_parts[1].lower()
        
        if action == 'add':
            if len(command_parts) > 2:
                task_text = command_parts[2]
                if task_text.strip():
                    db.add_task(chat_id, task_text)
                    bot.send_message(chat_id, f"✅ Задача добавлена: *{task_text}*", parse_mode='Markdown')
                else:
                    bot.send_message(chat_id, "❌ Текст задачи не может быть пустым")
            else:
                bot.send_message(chat_id, "❌ Укажите задачу: `/todo add Ваша задача`", parse_mode='Markdown')
                
        elif action == 'list':
            show_tasks(chat_id)
            
        elif action == 'delete':
            if len(command_parts) > 2:
                try:
                    task_id = int(command_parts[2])
                    if db.delete_task(chat_id, task_id):
                        bot.send_message(chat_id, "✅ Задача удалена")
                    else:
                        bot.send_message(chat_id, "❌ Задача не найдена")
                except ValueError:
                    bot.send_message(chat_id, "❌ Неверный номер задачи")
            else:
                bot.send_message(chat_id, "❌ Укажите номер задачи: `/todo delete 1`", parse_mode='Markdown')
        else:
            bot.send_message(chat_id, "❌ Неизвестная команда. Используйте: add, list или delete")
            
    except Exception as e:
        logging.error(f"Todo error: {e}")
        bot.send_message(message.chat.id, "❌ Произошла ошибка при обработке запроса")

@bot.message_handler(commands=['currency'])
def handle_currency(message):
    try:
        chat_id = message.chat.id
        parts = message.text.split()

        if len(parts) != 4:
            bot.send_message(
                chat_id,
                "💱 *Конвертер валют*\n\n"
                "❌ *Неверный формат команды*\n\n"
                "Используйте:\n`/currency [сумма] [из] [в]`\n\n"
                "*Пример:*\n`/currency 100 USD RUB`\n"
                "*Поддерживаемые валюты:* USD, EUR, RUB, GBP, JPY, CNY, etc.",
                parse_mode='Markdown'
            )
            return
            
        amount = float(parts[1])
        from_currency = parts[2].upper()
        to_currency = parts[3].upper()
        
        # Логируем запрос
        logging.info(f"=== ЗАПРОС КОНВЕРТАЦИИ ===")
        logging.info(f"Пользователь: {chat_id}")
        logging.info(f"Команда: {amount} {from_currency} -> {to_currency}")
        
        converted_amount, rate = get_exchange_rate(from_currency, to_currency, amount)
        
        # ДЕТАЛЬНАЯ ОТЛАДКА
        logging.info(f"Результат функции: converted_amount={converted_amount}, rate={rate}")
        logging.info(f"Типы: converted_amount type={type(converted_amount)}, rate type={type(rate)}")
        
        if converted_amount is not None and rate is not None:
            result_text = (
                f"💱 *Результат конвертации:*\n\n"
                f"*{amount} {from_currency}* = *{converted_amount:.2f} {to_currency}*\n"
                f"Курс: 1 {from_currency} = {rate:.4f} {to_currency}"
            )
            logging.info(f"✅ Отправляем результат пользователю: {result_text}")
            bot.send_message(chat_id, result_text, parse_mode='Markdown')
        else:
            result_text = (
                f"❌ Не удалось получить курс валют.\n\n"
                f"*Возможные причины:*\n"
                f"• Неправильные коды валют\n"  
                f"• Временные проблемы с API\n"
                f"• Попробуйте другие валюты\n\n"
                f"*Пример:* `/currency 1 USD EUR`"
            )
            logging.error(f"❌ Конвертация не удалась - возвращены None")
            bot.send_message(chat_id, result_text, parse_mode='Markdown')
                
    except ValueError as e:
        logging.error(f"ValueError: {e}")
        bot.send_message(chat_id, "❌ Неверный формат суммы. Используйте числа, например: 100 или 50.5")
    except Exception as e:
        logging.error(f"Currency error: {e}")
        bot.send_message(chat_id, f'❌ Произошла ошибка при конвертации: {str(e)}')

@bot.message_handler(commands=['weather'])
def handle_weather(message):
    try:    
        chat_id = message.chat.id
        parts = message.text.split(maxsplit=1)
        
        if len(parts) < 2:
            bot.send_message(
                chat_id,
                "🌤️ *Погода*\n\n"
                "❌ *Укажите город*\n\n"
                "Пример:\n`/weather Москва`",
                parse_mode='Markdown'
            )
            return
            
        city = parts[1]
        weather_data = get_weather(city) 
        
        if weather_data == "city_not_found":
            bot.send_message(chat_id, f"❌ Город '{city}' не найден")
            return
        elif weather_data:
            weather_emojis = {
                'clear': "☀️",
                'cloud': "☁️",
                'rain': "🌧️",
                'snow': "❄️", 
                'thunderstorm': "⛈️",
                'drizzle': "🌦️",
                'mist': "🌫️",
            }

            description = weather_data['description']
            emoji = '🌤️'
            for key, value in weather_emojis.items():
                if key in description.lower():
                    emoji = value
                    break

            weather_text = (
                f"{emoji} *Погода в {weather_data['city']}*\n\n"
                f"*Описание:* {description.capitalize()}\n"
                f"*Температура:* {weather_data['temperature']:.1f}°C\n"
                f"*Ощущается как:* {weather_data['feels_like']:.1f}°C\n"
                f"*Влажность:* {weather_data['humidity']}%"
            )
        else:
            weather_text = "❌ Не удалось получить данные о погоде. Проверьте название города."

        bot.send_message(chat_id, weather_text, parse_mode='Markdown')

    except Exception as e:
        logging.error(f'Weather error: {e}')
        bot.send_message(chat_id, '❌ Произошла ошибка при получении погоды')

@bot.message_handler(commands=['random'])
def random_handler(message):
    try:    
        chat_id = message.chat.id
        command_text = message.text
        logging.info(f"Random command received: {command_text}")
        if command_text.strip() == '/random':
            show_random_options(chat_id)
            return
        remaining_text = command_text.replace('/random', '').strip()
        parts = remaining_text.split()
        
        logging.info(f"Parts after split: {parts}")
        
        if len(parts) < 1:
            show_random_options(chat_id)
            return
        
        action = parts[0].lower()
        
        if action == 'number':
            if len(parts) == 3:
                try:
                    min_val = int(parts[1])
                    max_val = int(parts[2])
                    if min_val >= max_val:
                        bot.send_message(chat_id, "❌ Первое число должно быть меньше второго")
                    else:
                        result = random.randint(min_val, max_val)
                        bot.send_message(chat_id, f"🎲 Случайное число: *{result}*", parse_mode='Markdown')
                except ValueError:
                    bot.send_message(chat_id, "❌ Неверный формат чисел. Используйте: `/random number 1 100`", parse_mode='Markdown')
            else:
                bot.send_message(chat_id, f"❌ Укажите диапазон: `/random number 1 100`\n\nПолучено: {' '.join(parts)}", parse_mode='Markdown')
        elif action == 'choice':
            if len(parts) >= 2:
                choices = parts[1:]
                if len(choices) >= 2:
                    result = random.choice(choices)
                    bot.send_message(chat_id, f"🎯 Я выбираю: *{result}*", parse_mode='Markdown')
                else:
                    bot.send_message(chat_id, "❌ Укажите хотя бы 2 варианта для выбора")
            else:
                bot.send_message(chat_id, "❌ Укажите варианты: `/random choice пицца суши`", parse_mode='Markdown')
        else:
            show_random_options(chat_id)
    except Exception as e:
        logging.error(f'Random error: {e}')
        bot.send_message(chat_id, '❌ Произошла ошибка')
@bot.message_handler(content_types=['text'])
def handle_text_messages(message):
    chat_id = message.chat.id
    text = message.text.strip()
    if text == 'Мои задачи':
        show_tasks(chat_id) 
    elif text == 'Конвертер':
        bot.send_message(chat_id, '💱 *Конвертер валют* \n\nИспользуйте формат:\n`/currency 100 USD RUB`', parse_mode='Markdown')
    elif text == 'Погода':
        bot.send_message(chat_id, '🌤️ *Погода*\n\nВведите команду:\n`/weather Москва`', parse_mode='Markdown')
    elif text == 'Случайность':
        show_random_options(chat_id) 
    else:
        bot.send_message(chat_id, "Не понимаю команду. Используйте кнопки меню или /help")

def show_tasks(chat_id):
    """Показать задачи пользователю"""
    try:
        tasks = db.get_user_tasks(chat_id)
        if not tasks:
            bot.send_message(chat_id, '📝 *Список задач пуст*\n\nДобавьте задачу: `/todo add Ваша задача`', parse_mode='Markdown')
            return 
        tasks_text = '📝 *Ваши задачи:*\n\n'
        for task in tasks:
            tasks_text += f"{task['id']}. {task['task_text']}\n"
        tasks_text += "\nУдалить задачу: `/todo delete номер`"
        bot.send_message(chat_id, tasks_text, parse_mode='Markdown')
    except Exception as e:
        logging.error(f"Show tasks error: {e}")
        bot.send_message(chat_id, "❌ Ошибка при загрузке задач")
def show_random_options(chat_id):
    options_text = (
        "🎲 *Модуль случайностей*\n\n"
        "*Случайное число:*\n`/random number 1 100`\n\n"
        "*Случайный выбор:*\n`/random choice пицца суши паста`\n\n"
        "*Примеры:*\n"
        "• `/random number 1 50` - число от 1 до 50\n"
        "• `/random choice кофе чай сок` - выбор напитка\n"
        "• `/random choice да нет` - простой выбор"
    )
    bot.send_message(chat_id, options_text, parse_mode='Markdown')

if __name__ == '__main__':
    print("🚀 Запуск бота...")
    print(f"✅ Токен: {'Найден' if BOT_TOKEN else '❌ НЕ НАЙДЕН'}")
    print("🌐 API: Frankfurter, Open-Meteo")
    print("💾 База данных: SQLite")
    print("📱 Бот готов к работе...")
    
    logging.info("Бот запущен")
    bot.infinity_polling()