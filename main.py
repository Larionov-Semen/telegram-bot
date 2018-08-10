from transliterate import translit, detect_language
from telegram.ext import Updater, MessageHandler, Filters
from telegram.error import (TelegramError, Unauthorized, BadRequest,
                            TimedOut, ChatMigrated, NetworkError)
import logging
import requests
from ignore.keys import token, key_translator, api_map
# файл, где должны находиться:
# token - токен для бота телеграм
# key_translator - ключ для переводчика с translate.yandex.ru
# api_map - ключ для определения погоды с api.openweathermap.org

REQUEST_KWARGS = {'proxy_url': 'socks5://45.32.91.85:12345'}

api_key_translator = key_translator
value_com = None

logging.basicConfig(
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        level=logging.INFO)
logger = logging.getLogger(__name__)

def start(bot, update):
    # update.message.reply_text('Привет, {}!'.format(update.message.from_user.first_name))
    text = 'Привет, {}!'.format(update.message.from_user.first_name)
    bot.send_message(chat_id=update.message.chat_id, text=text)

def error_callback(bot, update, error):
    try:
        raise error
    except Unauthorized:
        text = 'remove update.message.chat_id from conversation list'
    except BadRequest:
        text = 'handle malformed requests - read more below!'
    except TimedOut:
        text = 'handle slow connection problems'
    except NetworkError:
        text = 'handle other connection problems'
    except ChatMigrated as e:
        text = 'the chat_id of a group has changed, use e.new_chat_id instead'
    except TelegramError:
        text = 'handle all other telegram related errors'
    finally:
        bot.send_message(chat_id=update.message.chat_id, text=text)


def help(bot, update):
    update.message.reply_text(
        """Перед использованием требуется активировать команду 
    Вот основные команды, :
    /start - начать взаимодествие
    /help  - помощь, основные команды
    /translate  - переводчик англ-рус,рус-англ(translate.yandex.ru)
    /transcript - перевод транслитом англ-рус, рус-англ
    /weather    - погода в введённом городе
    /stop  - остановка команды
    """)


def transliteration(bot, update):  # функция транслитерации
    if detect_language(update.message.text, num_words=7) == 'ru':
        lang_bool = True
    else:
        lang_bool = False
    update.message.reply_text(translit(update.message.text, 'ru', lang_bool))


def translator(message):  # функция переводчика
    if detect_language(message, num_words=7) == 'ru':
        lang = 'ru-en'
    else:
        lang = 'en-ru'

    res = requests.post('https://translate.yandex.net/api/v1.5/tr.json/translate',
                        params={'key': api_key_translator, 'lang': lang, 'text': message})
    message = (str(res.json()['text']))[2: -2]
    return message


def weather(bot, update, message):   # погода
    r = requests.post('http://api.openweathermap.org/data/2.5/weather?q=%s&appid=%s' % (message, api_map))
    if r.json()['cod'] == 200:
        message = '''{city}
    Координаты:     {coord}
    Погода:         {weat}
    Температура:    {temp}С*
    Давление:       {press}гПа
    Влажность:      {hum}%
        '''\
            .format(city=(translator(message)+ '        '+message),
                    coord=r.json()['coord'],
                    weat=translator(r.json()['weather'][0]['description']),
                    temp=int(r.json()['main']['temp'])-273,
                    press=r.json()['main']['pressure'],
                    hum=r.json()['main']['humidity']
                    )
        update.message.reply_text(message)
    else:
        update.message.reply_text('ERROR: возможно не найден город')


def process_command(bot, update):
    global value_com
    message = update.message.text
    if message == '/start':
        start(bot, update)
    elif message == '/help':
        help(bot, update)
    elif message == '/translate':
        value_com = translator
    elif message == '/transcript':
        value_com = transliteration
    elif message == '/weather':
        value_com = weather
    elif message == '/stop':
            update.message.reply_text('Команда остановлена')
            value_com = None
    else:
        update.message.reply_text("""ERROR : команда не поддерживается /help""")


def process(bot, update):
    message = update.message.text
    if value_com == translator:
        message = translator(message)
        update.message.reply_text(message)
    elif value_com == transliteration:
        transliteration(bot, update)
    elif value_com == weather:
        message = translator(message)
        weather(bot, update, message)
    else:
        update.message.reply_text('Активируйте команду      /help')


def main():

    # updater = Updater(token, request_kwargs=REQUEST_KWARGS)
    updater = Updater(token)
    bot = updater.dispatcher
    bot.add_error_handler(error_callback)
    bot.add_handler(MessageHandler(Filters.command, process_command))
    bot.add_handler(MessageHandler(Filters.text, process))
    updater.start_polling()
    updater.idle()



if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        exit()

