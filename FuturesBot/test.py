import telebot
from telebot import types
import config
API_TOKEN = config.telegram_token
bot = telebot.TeleBot(API_TOKEN)
@bot.message_handler(commands=['help', 'start'])
def send_welcome(message):
    markup = types.ReplyKeyboardMarkup(one_time_keyboard=True)
    markup.add('1', '2') #the names of the buttons
    msg = bot.reply_to(message, 'Test text', reply_markup=markup)
    bot.register_next_step_handler(msg, process_step)

testing = 0
def process_step(message):
    chat_id = config.telegram_chatid
    if message.text=='1':
        print("User entered 1")
        testing = 6
        print(testing)
    else:
        print("User entered 2")



bot.polling()