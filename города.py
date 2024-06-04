import telebot
import geonamescache
import wikipedia
import os.path as path
import requests
import json
import data_base as db

API_TOKEN = "47ec177a5d90af427c064ece679a1b87"
TOKEN = "6714241697:AAEG8ttYYLtGKAcN1zHAL_IFLMWB_2s2elM"
bot = telebot.TeleBot(TOKEN, parse_mode=None)
gc = geonamescache.GeonamesCache()
all_cities: dict = gc.get_cities()
rus_bkv = ["ь", "ъ"]
good_image = [".jpg", ".png", ".jpeg"]


class User:
    def __init__(self, chat_id, score, cities):
        self.__id = chat_id
        self.__score = score
        self.__cities = json.loads(cities)

    @property
    def id(self):
        return self.__id

    @id.setter
    def id(self, chat_id):
        self.__id = chat_id

    @property
    def score(self):
        return self.__score

    @score.setter
    def score(self, score):
        self.__score = score

    @property
    def cities(self):
        return self.__cities

    @cities.setter
    def cities(self, cities):
        self.__cities = cities

    def save(self):
        db.update_data(self.id, self.score, json.dumps(self.cities))


@bot.message_handler(commands=["start"])
def start(message):
    bot.send_message(message.chat.id, "Привет, АБОБУС 👺. Игра запущена, назови город первым")
    if db.get_data(message.chat.id) is None:
        db.insert_data(message.chat.id, 0, json.dumps(dict()))


@bot.message_handler(commands=['help'])
def help(message):
    bot.send_message(message.chat.id, """список всех доступных команд:
    /start - игра запущена, назови город первым
    /help - помощи не будет
    ну что, помог, АБОБУС?""")


@bot.message_handler(commands=["stop"])
def stop(message):
    bot.send_message(message.chat.id, "Игра завершена")


def search_city(letter, user):
    for city in all_cities.values():
        names = city.get("alternatenames")
        city_id = str(city.get("geonameid"))
        if city_id in user.cities and city_id:
            continue
        for name in names:
            if name:
                if letter.upper() == name[0]:
                    user.cities[city_id] = name
                    user.save()
                    return name, city.get("latitude"), city.get("longitude")


def get_last_letter(city):
    letter = city[-1]
    if letter in rus_bkv:
        letter = city[-2]
    return letter


def wiki_request(func):
    def decorator(city, *args, **kwargs):
        try:
            return func(city)
        except (wikipedia.WikipediaException, wikipedia.PageError, wikipedia.DisambiguationError,
                wikipedia.HTTPTimeoutError, wikipedia.RedirectError):
            return None
    return decorator


def weather(lan, lon):
    response = requests.get(
        f"https://api.openweathermap.org/data/2.5/weather?lat={lan}&lon={lon}&appid={API_TOKEN}&lang=ru&units=metric")
    data = json.loads(response.text)
    description = data.get("weather")[0].get("description")
    temp = data.get("main").get("temp")
    return temp, description


@wiki_request
def get_info_city(city):
    wikipedia.set_lang("ru")
    wiki_response = wikipedia.search(city)
    if wiki_response:
        wiki_city = wiki_response[0]
        info_city = wikipedia.summary(wiki_city)
        return info_city
    return None


@wiki_request
def get_image_city(city):
    wikipedia.set_lang("ru")
    wiki_response = wikipedia.search(city)
    if wiki_response:
        wiki_city = wiki_response[0]
        for image in wikipedia.page(wiki_city).images:
            if path.splitext(image)[1].lower() in good_image:
                return image
    return None


@bot.message_handler(content_types=["text"])
def handler(message):
    user = User(*db.get_data(message.chat.id))
    user_city = message.text
    letter = get_last_letter(user_city)
    city = gc.search_cities(user_city)
    if user.cities:
        bot_letter = get_last_letter(list(user.cities.values())[-1])
        if user_city[0].lower() != bot_letter:
            bot.send_message(message.chat.id, f"нет уж, тебе на букву {bot_letter}")
            return
    if city:
        city_id = str(city[0].get("geonameid"))
        if city_id in user.cities:
            bot.send_message(message.chat.id, f"такой город уже был!")
            return
        bot.send_message(message.chat.id, F"да такой город есть, мне на букву: {letter}")
        user.cities[city_id] = user_city
        user.save()
        found_city, lan, lon = search_city(letter, user)
        bot_letter = get_last_letter(found_city)
        bot.send_message(message.chat.id, f"{found_city}")
        bot.send_location(message.chat.id, lan, lon)
        info_city = get_info_city(found_city)
        if info_city:
            bot.send_message(message.chat.id, info_city)
        else:
            bot.send_message(message.chat.id, f"информация о {found_city} не найдено")
        image_city = get_image_city(found_city)
        if image_city:
            bot.send_photo(message.chat.id, image_city)
        else:
            bot.send_message(message.chat.id, f"картинки о {found_city} не найдено")
        bot.send_message(message.chat.id, f"тебе на букву {bot_letter}")
        weather(lan, lon)


bot.infinity_polling()
