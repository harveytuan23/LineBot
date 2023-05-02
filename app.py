from __future__ import unicode_literals
from urllib import parse
from flask import Flask, request, abort, render_template
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import MessageEvent, TextMessage, TextSendMessage
from datetime import datetime
import string
import requests
import json
import configparser
import os
import logging
import THSR


# 1.setup log path and create log directory
logName = 'MyProgram.log'
logDir = 'log'
logPath = logDir + '/' + logName

# create log directory
os.makedirs(logDir, exist_ok=True)

# 2.create logger, then setLevel
logger = logging.getLogger('logger')
logger.setLevel(logging.DEBUG)

# 3.create file handler, then setLevel
# create file handler
fileHandler = logging.FileHandler(logPath, mode='w')
fileHandler.setLevel(logging.DEBUG)

# 4.create stram handler, then setLevel
# create stream handler
streamHandler = logging.StreamHandler()
streamHandler.setLevel(logging.INFO)

# 5.create formatter, then handler setFormatter
AllFormatter = logging.Formatter(
    '[%(levelname)s][%(asctime)s][LINE:%(lineno)s][%(module)s]: %(message)s', datefmt='%Y-%m-%d %H:%M:%S')
fileHandler.setFormatter(AllFormatter)
streamHandler.setFormatter(AllFormatter)

# 6.logger addHandler
logger.addHandler(fileHandler)
logger.addHandler(streamHandler)

app = Flask(__name__, static_url_path='/static')
UPLOAD_FOLDER = 'static'
ALLOWED_EXTENSIONS = set(['pdf', 'png', 'jpg', 'jpeg', 'gif'])


config = configparser.ConfigParser()
config.read('config.ini')

line_bot_api = LineBotApi(config.get('line-bot', 'channel_access_token'))
handler = WebhookHandler(config.get('line-bot', 'channel_secret'))
my_line_id = config.get('line-bot', 'my_line_id')
end_point = config.get('line-bot', 'end_point')
line_login_id = config.get('line-bot', 'line_login_id')
line_login_secret = config.get('line-bot', 'line_login_secret')
my_phone = config.get('line-bot', 'my_phone')
HEADER = {
    'Content-type': 'application/json',
    'Authorization': f'Bearer {config.get("line-bot", "channel_access_token")}'
}


@app.route("/", methods=['POST', 'GET'])
def index():
    if request.method == 'GET':
        return 'ok'
    body = request.json
    events = body["events"]
    if request.method == 'POST' and len(events) == 0:
        return 'ok'
    logger.info(body)
    print(body)
    if "replyToken" in events[0]:
        payload = dict()
        replyToken = events[0]["replyToken"]
        payload["replyToken"] = replyToken
        if events[0]["type"] == "message":
            if events[0]["message"]["type"] == "text":
                text = events[0]["message"]["text"]
                if text == "高鐵":
                    payload["messages"] = [
                        THSR.THSR_choose_start_station()]
                replyMessage(payload)

        elif events[0]["type"] == "postback":

            if "data" in events[0]["postback"]:
                with open("./json/THSR_station_data.json", 'r') as f:
                    json_data = json.load(f)
                firstData = events[0]["postback"]["data"][0:2]
                chiStation = events[0]["postback"]["data"][3:6]
                engStation = events[0]["postback"]["data"][7:]

                if firstData == "SS":
                    json_data["start_station"] = engStation
                    json_data["chi_start_station"] = chiStation

                    # Save station data to json
                    with open("./json/THSR_station_data.json", "w") as f:
                        json.dump(json_data, f)
                    payload["messages"] = [THSR.THSR_choose_end_station()]

                elif firstData == "ES":
                    json_data["end_station"] = engStation
                    json_data["chi_end_station"] = chiStation
                    if json_data["end_station"] == json_data["start_station"]:
                        logger.info("error")
                        payload["messages"] = [{
                            "type": "text",
                            "text": "出發站不能等於到達站"
                        },
                            THSR.THSR_choose_end_station()]
                    else:
                        # Save station data to json
                        with open("./json/THSR_station_data.json", "w") as f:
                            json.dump(json_data, f)

                        payload["messages"] = [THSR.THSR_choose_time()]

                elif events[0]["postback"]["data"] == "chooseTime":
                    searchTime = events[0]["postback"]["params"]["datetime"].replace(
                        "T", " ")
                    logger.info(json_data["start_station"])
                    logger.info(json_data["end_station"])

                    payload["messages"] = [THSR.THSR_result(searchTime)]
                replyMessage(payload)

    return 'OK'

# 有人來call這個路徑，就執行def callback


@app.route("/callback", methods=['POST'])
def callback():
    signature = request.headers['X-Line-Signature']
    body = request.get_data(as_text=True)
    app.logger.info("Request body: " + body)

    try:
        handler.handle(body, signature)

    except InvalidSignatureError:
        abort(400)

    return 'OK'

# 若有接收到MessageEvent的話，call這裡


@handler.add(MessageEvent, message=TextMessage)
def pretty_echo(event):
    line_bot_api.reply_message(
        event.reply_token,
        TextSendMessage(text=event.message.text)
    )


@app.route("/sendTextMessageToMe", methods=['POST'])
def sendTextMessageToMe():
    pushMessage({})
    return 'OK'


def replyMessage(payload):
    response = requests.post(
        "https://api.line.me/v2/bot/message/reply", headers=HEADER, json=payload)
    logger.info(response.text)
    print(response.text)
    print('payload =', payload)
    return 'OK'


def pushMessage(payload):
    response = requests.post(
        "https://api.line.me/v2/bot/message/push", headers=HEADER, json=payload)
    print(response.text)
    return 'OK'


if __name__ == "__main__":
    app.debug = True
    app.run()
