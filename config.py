import os
from dotenv import load_dotenv # type: ignore

load_dotenv()

class Config:
    BOT_TOKEN = os.getenv('BOT_TOKEN')
    WEATHER_API_KEY = os.getenv('WEATHER_API_KEY', "")

    # настройка бд
    DATABASE_URL = 'sqlite://bot_database.db'

    # рабочие api endpoints
    EXCHANGE_RATE_URL = "https://api.frankfurter.app/latest"
    WEATHER_URL = "https://api.open-meteo.com/v1/forecast"
    CRYPTO_URL = "https://api.coingecko.com/api/v3/simple/price"
   