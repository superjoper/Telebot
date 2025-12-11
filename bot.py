
import telebot
from telebot import types
import requests
from datetime import datetime, timedelta
import logging


TOKEN = "8319307503:AAFL5cbFFSKQ6qogQWzj1Pm8jjHa-Hbij3A"  # Замените на токен вашего бота
API_KEY = "2022f930d9d20d36a90e55d80bcb7bab"  # Замените на ваш API ключ Fixer.io
BASE_URL = "http://api.exchangeratesapi.io/v1/"  # Или Fixer.io URL
BASE_CURRENCY = "EUR" # Базовая валюта (обычно EUR для бесплатных планов)


CURRENCY_OPTIONS = {
    "USD": "Доллар США ",
    "RUB": "Российский рубль ",
    "KZT": "Казахстанский тенге ",
    "GBP": "Фунт стерлингов ",
    "JPY": "Японская иена ",
}

bot = telebot.TeleBot(TOKEN)

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logger = logging.getLogger(__name__)


def get_exchange_rate(date_str: str, base: str, target: str) -> float | None:
    """Получает курс валюты для конкретной даты."""
    url = f"{BASE_URL}{date_str}"
    params = {
        "access_key": API_KEY,
        "base": base,
        "symbols": target,
    }
    
    try:
        response = requests.get(url, params=params)
        response.raise_for_status()
        data = response.json()
        
        if data.get("success"):
            rate = data["rates"].get(target)
            return rate
        else:
            logger.error(f"API Error: {data.get('error')}. API response: {data}")
            return None
            
    except requests.exceptions.RequestException as e:
        logger.error(f"Request Error: {e}")
        return None

def get_rate_change_message(days: int, target_currency: str) -> str:
    """Вычисляет изменение курса и формирует сообщение."""
    
    
    today = datetime.now().strftime("%Y-%m-%d")
    current_rate = get_exchange_rate(today, BASE_CURRENCY, target_currency)
    
  
    past_date = (datetime.now() - timedelta(days=days)).strftime("%Y-%m-%d")
    past_rate = get_exchange_rate(past_date, BASE_CURRENCY, target_currency)
    
    if current_rate is None or past_rate is None:
        return "*Ошибка получения данных!* Проверьте API ключ, лимиты подписки или корректность выбранной валюты."

    
    change = current_rate - past_rate
    percentage_change = (change / past_rate) * 100
    
    period_name = {7: "Неделю", 30: "Месяц", 365: "Год"}.get(days, f"{days} Дней")
    
    change_emoji = "Увеличение" if change > 0 else "Снижение" if change < 0 else "↔Без изменений"
    
    message = (
        f"*Изменение курса {BASE_CURRENCY}/{target_currency} за {period_name}*:\n"
        f"--- \n"
        f"• **Текущий курс** ({today}): `{current_rate:.4f}`\n"
        f"• **Курс {past_date}**: `{past_rate:.4f}`\n"
        f"--- \n"
        f"{change_emoji}: `{change:+.4f}` ({percentage_change:+.2f}%)"
    )
    
    return message



@bot.message_handler(commands=['start', 'help'])
def send_welcome(message):
    """Обрабатывает команду /start и предлагает выбор валюты."""
    
    
    markup = types.InlineKeyboardMarkup()
    
    
    for code, name in CURRENCY_OPTIONS.items():
        
        markup.add(types.InlineKeyboardButton(name, callback_data=f"select_currency_{code}"))

    bot.send_message(
        message.chat.id,
        f"Привет! Я бот для отслеживания курсов. Базовая валюта для расчетов: **{BASE_CURRENCY}**.\n\n"
        "Выберите валюту, курс которой вы хотите отслеживать (Целевая валюта):",
        reply_markup=markup,
        parse_mode='Markdown'
    )

def get_period_keyboard(target_currency_code: str):
    """Генерирует Inline-клавиатуру для выбора периода."""
    
    markup = types.InlineKeyboardMarkup(row_width=3)
    
   
    markup.add(
        types.InlineKeyboardButton("Неделя ", callback_data=f"period_7_{target_currency_code}"),
        types.InlineKeyboardButton("Месяц ", callback_data=f"period_30_{target_currency_code}"),
        types.InlineKeyboardButton("Год ", callback_data=f"period_365_{target_currency_code}")
    )
    return markup


@bot.callback_query_handler(func=lambda call: call.data.startswith('select_currency_'))
def callback_select_currency(call):
    """Обрабатывает выбор целевой валюты."""
    
    bot.answer_callback_query(call.id) 
    
    target_currency_code = call.data.split('_')[-1]
    
    markup = get_period_keyboard(target_currency_code)
    
    bot.edit_message_text(
        f"Валюта **{target_currency_code}** выбрана.\n\n"
        f" Выберите период для отслеживания изменения курса **{BASE_CURRENCY}** к **{target_currency_code}**:",
        call.message.chat.id,
        call.message.message_id,
        reply_markup=markup,
        parse_mode='Markdown'
    )


@bot.callback_query_handler(func=lambda call: call.data.startswith('period_'))
def callback_select_period(call):
    """Обрабатывает выбор периода и выводит результат."""
    
    bot.answer_callback_query(call.id)
    
    parts = call.data.split('_')
    if len(parts) != 3:
        bot.edit_message_text("⚠️ Ошибка данных при выборе периода. Попробуйте /start снова.", 
                              call.message.chat.id, call.message.message_id)
        return

    days = int(parts[1])
    target_currency = parts[2]
    
    response_text = get_rate_change_message(days, target_currency)
    
    bot.edit_message_text(
        response_text,
        call.message.chat.id,
        call.message.message_id,
        parse_mode='Markdown'
    )


def main():
    """Запускает бота в режиме бесконечного цикла (polling)."""
    print("Бот запущен на telebot...")
    try:
        bot.polling(none_stop=True)
    except Exception as e:
        logger.error(f"Ошибка при запуске бота: {e}")

if __name__ == "__main__":

    main()



