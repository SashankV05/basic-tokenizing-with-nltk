import os
basepath=os.getcwd()

print("initializing modules")
import nltk
from nltk.stem import WordNetLemmatizer
import json
import random
import speech_recognition as sr
import pickle
import numpy as np
import pyttsx3
from keras.models import load_model

lemmatizer = WordNetLemmatizer()
historypath = basepath+"\histsrc\\activity.his"

model = load_model(basepath+'\chatbot_model.h5')

intents = json.loads(open(basepath+'\intents.lon').read())
words = pickle.load(open(basepath+'\words.pkl', 'rb'))
classes = pickle.load(open(basepath+'\classes.pkl', 'rb'))
print("===============File paths=============")
print("History db : "+ historypath)
print("Current installed path : "+basepath)

def speak(text):
    engine = pyttsx3.init()
    engine.setProperty('rate', 150)
    engine.say(text)
    engine.runAndWait()


def clean_up_sentence(sentence):
    sentence_words = nltk.word_tokenize(sentence)

    sentence_words = [lemmatizer.lemmatize(word.lower()) for word in sentence_words]
    return sentence_words


def bag_of_words(sentence, words, show_details=True):
    sentence_words = clean_up_sentence(sentence)

    bag = [0] * len(words)
    for s in sentence_words:
        for i, word in enumerate(words):
            if word == s:

                bag[i] = 1
                if show_details:
                    print("found in bag: %s" % word)
    return (np.array(bag))


def predict_class(sentence):
    p = bag_of_words(sentence, words, show_details=False)
    res = model.predict(np.array([p]))[0]
    ERROR_THRESHOLD = 0.25
    results = [[i, r] for i, r in enumerate(res) if r > ERROR_THRESHOLD]
    # sorting strength probability
    results.sort(key=lambda x: x[1], reverse=True)
    return_list = []
    for r in results:
        return_list.append({"intent": classes[r[0]], "probability": str(r[1])})
    return return_list


def getResponse(ints, intents_json):
    tag = ints[0]['intent']
    list_of_intents = intents_json['intents']
    for i in list_of_intents:
        if i['tag'] == tag:
            result = random.choice(i['responses'])
            break
    return result


def weather():
    from bs4 import BeautifulSoup as bs
    import requests

    USER_AGENT = "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/44.0.2403.157 Safari/537.36"
    # US english
    LANGUAGE = "en-US,en;q=0.5"

    def get_weather_data(url):
        session = requests.Session()
        session.headers['User-Agent'] = USER_AGENT
        session.headers['Accept-Language'] = LANGUAGE
        session.headers['Content-Language'] = LANGUAGE
        html = session.get(url)
        # create a new soup
        soup = bs(html.text, "html.parser")
        # store all results on this dictionary
        result = {}
        # extract region
        result['region'] = soup.find("div", attrs={"id": "wob_loc"}).text
        # extract temperature now
        result['temp_now'] = soup.find("span", attrs={"id": "wob_tm"}).text
        # get the day and hour now
        result['dayhour'] = soup.find("div", attrs={"id": "wob_dts"}).text
        # get the actual weather
        result['weather_now'] = soup.find("span", attrs={"id": "wob_dc"}).text
        # get the precipitation
        result['precipitation'] = soup.find("span", attrs={"id": "wob_pp"}).text
        # get the % of humidity
        result['humidity'] = soup.find("span", attrs={"id": "wob_hm"}).text
        # extract the wind
        result['wind'] = soup.find("span", attrs={"id": "wob_ws"}).text
        # get next few days' weather
        next_days = []
        days = soup.find("div", attrs={"id": "wob_dp"})
        for day in days.findAll("div", attrs={"class": "wob_df"}):
            # extract the name of the day

            # get weather status for that day
            weather = day.find("img").attrs["alt"]
            temp = day.findAll("span", {"class": "wob_t"})
            # maximum temparature in Celsius, use temp[1].text if you want fahrenheit
            max_temp = temp[0].text
            # minimum temparature in Celsius, use temp[3].text if you want fahrenheit
            min_temp = temp[2].text
            next_days.append({"weather": weather, "max_temp": max_temp, "min_temp": min_temp})
        # append to result
        result['next_days'] = next_days
        return result

    if __name__ == "__main__":
        URL = "https://www.google.com/search?lr=lang_en&ie=UTF-8&q=weather"
        import argparse

        parser = argparse.ArgumentParser(description="Quick Script for Extracting Weather data using Google Weather")
        parser.add_argument("region", nargs="?", help="""Region to get weather for, must be available region.
                                            Default is your current location determined by your IP Address""",
                            default="")
        # parse arguments
        args = parser.parse_args()
        region = args.region
        URL += region
        # get data
        data = get_weather_data(URL)
        # print data
        reg = str(data["region"])
        now = str(data["dayhour"])
        temp = str(data['temp_now'])
        des = str(data['weather_now'])
        print("exctracted data\n "+"region :"+reg +"\n time : " +now +"\n temperature :" +temp +"\n description :"+ des)
        speak("the weather in "+reg+" is "+des+" with the temperature of "+temp+" degree celsius ")

    x = open(historypath, "a")
    x.write("\n[i] : Gave weather data as user requested")
    x.close()


def mailto():
    import time
    from selenium import webdriver
    from selenium.webdriver.common.by import By
    from selenium.webdriver.common.keys import Keys
    from selenium.webdriver.support.ui import WebDriverWait
    from selenium.webdriver.support import expected_conditions as EC

    def play():
        driver = webdriver.Chrome()

        wait = WebDriverWait(driver, 3)
        presence = EC.presence_of_element_located
        visible = EC.visibility_of_element_located

        driver.get("mailto:a")
        time.sleep(5)
        driver.close()
        j = open(historypath, "a")
        j.write("\n[i]:Opened Windows mail as per user's request")
        j.close()

    play()


def actions():
    r = sr.Recognizer()
    with sr.Microphone() as source:
        print("MELON listener starts")
        r.adjust_for_ambient_noise(source)
        audio = r.listen(source)

        try:
            msg = r.recognize_google(audio)
            print("You :" + msg)

        except sr.UnknownValueError:
            x = open(historypath, "a")

            speak('Sorry I didn\'t get that!')
            x.write(
                "\n[e] : Melon listner couldn't get that!")
            x.close()

    ints = predict_class(msg)
    res = getResponse(ints, intents)
    print(res)
    x = open(historypath, "a")
    x.write(
        "\n[i] : User said : " + msg + "\nAnswer given : " + res)
    x.close()
    if res == "Today's weather":
        weather()
    elif res == "opening windows mail":
        mailto()
    else:
        speak(res)


def listen():
    r = sr.Recognizer()
    with sr.Microphone() as source:
        r.adjust_for_ambient_noise(source)
        print('Listening')
        audio = r.listen(source)
        try:
            text = r.recognize_google(audio)
            z = open(historypath, "a")
            # TODO: train using voice models of user and upload them to cloud

            z.write("\n[i]: listner : " + text)
            print("You :" + text)
            if text == 'ok melon':
                actions()
            elif text == 'ok Milan': # only temp
                actions()
            elif text== 'OK Main loan' :# only temp
                actions()
            elif text == 'ok Mela':# only temp
                actions()
            z.close()
        except sr.UnknownValueError:
            print('nothing told')
            k = open(historypath, "a")
            k.write("\n[i]: Nothing was said")
            k.close()


y = open(historypath, "a")
y.write("\n[i]:<------------------------------Melon started---------------------------------------------->")
y.close()
print("================================-> Initialisation complete <-=====================================")

# <----------- Never ending listener starts ------------------->
while 1:
    listen()
    
#TODO : create a log function
