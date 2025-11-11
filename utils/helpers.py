import requests # type: ignore
import logging
from telebot import types # type: ignore
from config import Config

def create_main_keyboard():
    """Создание основной клавиатуры"""
    keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    buttons = [
        types.KeyboardButton("Мои задачи"),
        types.KeyboardButton("Конвертер"),
        types.KeyboardButton("Погода"),
        types.KeyboardButton("Случайность"),
    ]
    keyboard.add(*buttons)
    return keyboard

def get_exchange_rate(from_currency, to_currency, amount=1):
    apis_to_try = [
        # ExchangeRate-API
        {
            'name': 'ExchangeRate-API',
            'url': f'https://api.exchangerate-api.com/v4/latest/{from_currency}',
            'parse_func': lambda data, to_curr: data.get('rates', {}).get(to_curr)
        },
        # CurrencyAPI
        {
            'name': 'CurrencyAPI',
            'url': f'https://cdn.jsdelivr.net/gh/fawazahmed0/currency-api@1/latest/currencies/{from_currency.lower()}/{to_currency.lower()}.json',
            'parse_func': lambda data, to_curr: data.get(to_currency.lower())
        },
        #Open Exchange Rates
        {
            'name': 'OpenExchangeRates',
            'url': f"https://open.er-api.com/v6/latest/{from_currency}",
            'parse_func' : lambda data, to_curr : data.get('rates', {}).get(to_curr)
        }
    ]

    for api in apis_to_try:
        try:
            logging.info(f"Пробует {api['name']} : {api['url']}")
            response = requests.get(api['url'], timeout=10)
            if response.status_code == 200:
                data = response.json()
                rate = api['parse_func'](data,to_currency)

                if rate is not None:
                    converted_amount = float(amount) * rate
                    logging.info(f"{api['name']} успешен")
                    return converted_amount, rate
                else:
                    logging.warning(f"❌ {api['name']}: курс {to_currency} не найден")

            else:
                logging.warning(f"❌ {api['name']}: HTTP {response.status_code}")
            

        except requests.exceptions.RequestException as e:
            logging.warning(f"❌ {api['name']} ошибка: {e}")
        except Exception as e:
            logging.warning(f"❌ {api['name']} ошибка парсинга: {e}") 

        return get_exchange_rate(from_currency, to_currency, amount)
            
def get_weather(city):
    """
    Погода через Open-Meteo API (бесплатный, не требует ключа)
    Возвращает текущую погоду для города
    """
    try:
        geo_url = "https://geocoding-api.open-meteo.com/v1/search"
        geo_params = {
            'name': city,
            'count': 1,
            'language': 'ru',
            'format': 'json'
        }
        
        geo_response = requests.get(geo_url, params=geo_params, timeout=10)
        geo_response.raise_for_status()
        geo_data = geo_response.json()
        
        if not geo_data.get('results'):
            return "city_not_found"
        
        location = geo_data['results'][0]
        latitude = location['latitude']
        longitude = location['longitude']
        city_name = location['name']
        
        weather_url = "https://api.open-meteo.com/v1/forecast"
        weather_params = {
            'latitude': latitude,
            'longitude': longitude,
            'current_weather': 'true',
            'timezone': 'auto'
        }
        
        weather_response = requests.get(weather_url, params=weather_params, timeout=10)
        weather_response.raise_for_status()
        weather_data = weather_response.json()
        
        current_weather = weather_data['current_weather']
        temperature = current_weather['temperature']
        weather_code = current_weather['weathercode']
        
        weather_descriptions = {
            0: "ясно", 1: "преимущественно ясно", 2: "переменная облачность",
            3: "пасмурно", 45: "туман", 48: "туман", 51: "легкая морось",
            53: "умеренная морось", 55: "сильная морось", 56: "легкая ледяная морось",
            57: "сильная ледяная морось", 61: "небольшой дождь", 63: "умеренный дождь",
            65: "сильный дождь", 66: "ледяной дождь", 67: "сильный ледяной дождь",
            71: "небольшой снег", 73: "умеренный снег", 75: "сильный снег",
            77: "снежные зерна", 80: "небольшие ливни", 81: "умеренные ливни",
            82: "сильные ливни", 85: "небольшие снегопады", 86: "сильные снегопады",
            95: "гроза", 96: "гроза с градом", 99: "сильная гроза с градом"
        }
        
        description = weather_descriptions.get(weather_code, "неизвестно")
        
        weather_info = {
            'city': city_name,
            'description': description,
            'temperature': temperature,
            'humidity': 'N/A',
            'feels_like': temperature,
        }
        return weather_info
        
    except requests.exceptions.RequestException as e:
        logging.error(f'Ошибка API погоды: {e}')
        return None