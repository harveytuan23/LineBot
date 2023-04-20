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

                if text == "我的名字":
                    payload["messages"] = [getNameEmojiMessage()]
                elif text == "出去玩囉":
                    payload["messages"] = [getPlayStickerMessage()]
                elif text == "高鐵":
                    payload["messages"] = [THSR_choose_start_station()]
                elif text == "台北101":
                    payload["messages"] = [getTaipei101ImageMessage(),
                                           getTaipei101LocationMessage(),
                                           getMRTVideoMessage()
                                           ]
                elif text == "quoda":
                    payload["messages"] = [
                        {
                            "type": "text",
                            "text": getTotalSentMessageCount()
                        }
                    ]
                elif text == "今日確診人數":
                    payload["messages"] = [
                        {
                            "type": "text",
                            "text": getTodayCovid19Message()
                        }
                    ]
                elif text == "主選單":
                    payload["messages"] = [
                        {
                            "type": "template",
                            "altText": "This is a buttons template",
                            "template": {
                                    "type": "buttons",
                                    "title": "Menu",
                                    "text": "Please select",
                                    "actions": [
                                        {
                                            "type": "message",
                                            "label": "我的名字",
                                            "text": "我的名字"
                                        },
                                        {
                                            "type": "message",
                                            "label": "今日確診人數",
                                            "text": "今日確診人數"
                                        },
                                        {
                                            "type": "uri",
                                            "label": "聯絡我",
                                            "uri": f"tel:{my_phone}"
                                        }
                                    ]
                            }
                        }
                    ]
                else:
                    payload["messages"] = [
                        {
                            "type": "text",
                            "text": text
                        }
                    ]
                replyMessage(payload)
            elif events[0]["message"]["type"] == "location":
                logger.info(events[0]["message"])
                title = events[0]["message"]["title"]
                latitude = events[0]["message"]["latitude"]
                longitude = events[0]["message"]["longitude"]
                payload["messages"] = [
                    getLocationConfirmMessage(title, latitude, longitude)]
                logger.info(payload)
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

                    # payload["messages"] = [{
                    #     "type": "text",
                    #     "text": f"出發站為 : {chiStation}",
                    # },
                    #     THSR_choose_end_station()]
                    payload["messages"] = [THSR_choose_end_station()]

                elif firstData == "ES":
                    json_data["end_station"] = engStation
                    json_data["chi_end_station"] = chiStation
                    if json_data["end_station"] == json_data["start_station"]:
                        logger.info("error")
                        payload["messages"] = [{
                            "type": "text",
                            "text": "出發站不能等於到達站"
                        },
                            THSR_choose_end_station()]
                    else:
                        # Save station data to json
                        with open("./json/THSR_station_data.json", "w") as f:
                            json.dump(json_data, f)

                        # payload["messages"] = [{
                        #     "type": "text",
                        #     "text": f"終點站為 : {chiStation}"
                        # },
                        #     THSR_choose_time()]
                        payload["messages"] = [THSR_choose_time()]

                elif events[0]["postback"]["data"] == "chooseTime":
                    searchTime = events[0]["postback"]["params"]["datetime"].replace(
                        "T", " ")
                    logger.info(json_data["start_station"])
                    logger.info(json_data["end_station"])
                    # payload["messages"] = [{
                    #     "type": "text",
                    #     "text": f"查詢時間為 : {searchTime}"
                    # },
                    #     THSR_result(searchTime)]
                    payload["messages"] = [THSR_result(searchTime)]
                replyMessage(payload)

            else:
                data = json.loads(events[0]["postback"]["data"])
                logger.info(data)
                action = data["action"]
                if action == "get_near":
                    data["action"] = "get_detail"
                    payload["messages"] = [getCarouselMessage(data)]
                elif action == "get_detail":
                    del data["action"]
                    payload["messages"] = [getTaipei101ImageMessage(),
                                           getTaipei101LocationMessage(),
                                           getMRTVideoMessage(),
                                           getCallCarMessage(data)]
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


def THSR_choose_start_station():
    with open("./json/THSR_choose_start_station_2.json", 'r', encoding='utf-8') as f:
        message = json.load(f)
    return message


def THSR_choose_end_station():
    with open("./json/THSR_choose_end_station_2.json", 'r', encoding='utf-8') as f:
        message = json.load(f)

    return message


def THSR_choose_time():
    with open("./json/THSR_choose_time.json", 'r', encoding='utf-8') as f:
        message = json.load(f)
    now_time = datetime.now().strftime("%Y-%m-%dt%H:%M")
    message["template"]["actions"][0]["initial"] = now_time
    return message


def THSR_result(searchTime):
    # Read station data
    closest_start_time = 0
    closest_end_time = 0
    trains_list = []
    trains_duration = []
    with open("./json/THSR_station_data.json") as f:
        json_data = json.load(f)
    logger.info(json_data["start_station"])
    logger.info(json_data["end_station"])
    target_date = searchTime[:10].replace("-", "/")
    target_time = searchTime[11:]
    logger.info('Search date : ' + target_date)
    logger.info('Search time : ' + target_time)
    form_data = {
        'SearchType': 'S',
        'Lang': 'TW',
        'StartStation': json_data["start_station"],
        'EndStation': json_data["end_station"],
        'OutWardSearchDate': target_date,
        'OutWardSearchTime': target_time,
        'ReturnSearchDate': '2023/04/07',
        'ReturnSearchTime': '21:00',
        'DiscountType': ''
    }

    response = requests.post(
        'https://www.thsrc.com.tw/TimeTable/Search', data=form_data)
    response.encoding = "utf-8"
    data = json.loads(response.text)
    num_of_train = len(data['data']['DepartureTable']['TrainItem'])
    logger.info(num_of_train)
    # logger.info(data['data']['DepartureTable']['TrainItem'])

    # Choose the time closest to the user selected departure time
    target_time = int(target_time.replace(":", ""))
    for i in range(num_of_train):
        if abs(int(data['data']['DepartureTable']['TrainItem'][i]['DepartureTime'].replace(
                ":", "")) - target_time) < abs(closest_start_time - target_time):
            closest_start_time = int(data['data']['DepartureTable']['TrainItem'][i]['DepartureTime'].replace(
                ":", ""))
            closest_end_time = int(data['data']['DepartureTable']['TrainItem'][i]['DestinationTime'].replace(
                ":", ""))
            closest_i = i

    logger.info(closest_start_time)
    logger.info(closest_end_time)
    logger.info(closest_i)

    # Choose the train that matches the time and append into time_list
    # if num of train < 5, append corresponding amount of trains into time_list
    if num_of_train - closest_i < 5:
        for j in range(0, num_of_train - closest_i):
            trains_list.append([data['data']['DepartureTable']['TrainItem'][closest_i]['TrainNumber'], data['data']['DepartureTable']['TrainItem'][closest_i]['DepartureTime'].replace(
                ":", "").zfill(4)[:2] + ":" + data['data']['DepartureTable']['TrainItem'][closest_i]['DepartureTime'].replace(
                ":", "").zfill(4)[2:], data['data']['DepartureTable']['TrainItem'][closest_i]['DestinationTime'].replace(
                ":", "").zfill(4)[:2] + ":" + data['data']['DepartureTable']['TrainItem'][closest_i]['DestinationTime'].replace(
                ":", "").zfill(4)[2:], data['data']['DepartureTable']['TrainItem'][closest_i]['Duration']])

            trains_duration.append(int(
                data['data']['DepartureTable']['TrainItem'][closest_i]['Duration'].replace(":", "")))

            closest_i += 1
    # if num of train >= 5, append only five closest start time into time_list
    else:
        for j in range(0, 5):
            trains_list.append([data['data']['DepartureTable']['TrainItem'][closest_i]['TrainNumber'], data['data']['DepartureTable']['TrainItem'][closest_i]['DepartureTime'].replace(
                ":", "").zfill(4)[:2] + ":" + data['data']['DepartureTable']['TrainItem'][closest_i]['DepartureTime'].replace(
                ":", "").zfill(4)[2:], data['data']['DepartureTable']['TrainItem'][closest_i]['DestinationTime'].replace(
                ":", "").zfill(4)[:2] + ":" + data['data']['DepartureTable']['TrainItem'][closest_i]['DestinationTime'].replace(
                ":", "").zfill(4)[2:], data['data']['DepartureTable']['TrainItem'][closest_i]['Duration']])

            trains_duration.append(int(
                data['data']['DepartureTable']['TrainItem'][closest_i]['Duration'].replace(":", "")))

            closest_i += 1

    logger.info(trains_duration)
    min_duration = min(trains_duration)
    logger.info(min_duration)

    logger.info(f"total train : {trains_list}")
    logger.info(f"num of train : {len(trains_list)}")
    num_of_train_list = len(trains_list)
    target_time = str(target_time).zfill(4)

    # Read corresponding json carousel template according to the num of train
    with open(f"./json/THSR_result_{num_of_train_list}_data.json", 'r', encoding='utf-8') as f:
        message = json.load(f)

    message["contents"]["header"]["contents"][0]["contents"][0]["contents"][1]["text"] = target_date
    message["contents"]["header"]["contents"][0]["contents"][1]["contents"][1]["text"] = target_time[:2] + ":" + target_time[2:]
    message["contents"]["header"]["contents"][1]["contents"][0]["contents"][1]["text"] = json_data["chi_start_station"]
    message["contents"]["header"]["contents"][1]["contents"][1]["contents"][1]["text"] = json_data["chi_end_station"]

    for i in range(0, len(trains_list)):
        if min_duration == trains_duration[i]:
            message["contents"]["body"]["contents"][3*i][
                "contents"][1]["background"]["startColor"] = "#FF8000"
            message["contents"]["body"]["contents"][3*i][
                "contents"][1]["background"]["endColor"] = "#FFC78E"

        message["contents"]["body"]["contents"][3*i+1][
            "contents"][1]["contents"][1]["text"] = trains_list[i][3]
        message["contents"]["body"]["contents"][3*i][
            "contents"][0]["contents"][0]["text"] = f'車次 {trains_list[i][0]}'
        message["contents"]["body"]["contents"][3*i +
                                                1]["contents"][0]["contents"][0]["text"] = trains_list[i][1]
        message["contents"]["body"]["contents"][3*i +
                                                1]["contents"][2]["contents"][0]["text"] = trains_list[i][2]

    return message


def getNameEmojiMessage():
    lookUpStr = string.ascii_uppercase + string.ascii_lowercase
    productId = "5ac21a8c040ab15980c9b43f"
    name = "Harvey"
    message = dict()
    message['type'] = "text"
    message['text'] = "$" * len(name)
    emojis = list()
    for i, c in enumerate(name):
        emojis.append({
            "index": i,
            "productId": productId,
            "emojiId": f"{lookUpStr.index(c)+ 1}".zfill(3)
        })
    message['emojis'] = emojis
    return message


def getCarouselMessage(data):
    message = {
        "type": "template",
        "altText": "this is a image carousel template",
        "template": {
            "type": "image_carousel",
            "columns": [
              {
                "imageUrl": F"{end_point}/static/taipei_101.jpeg",
                "action": {
                    "type": "postback",
                    "label": "台北101",
                    "data": json.dumps(data)
                }
              },
                {
                  "imageUrl": F"{end_point}/static/02_shan.jpg",
                  "action": {
                      "type": "postback",
                      "label": "象山步道",
                      "data": json.dumps(data)
                  }
              },
                {
                    "imageUrl": F"{end_point}/static/03_yuanshan.jpg",
                    "action": {
                        "type": "postback",
                        "label": "圓山飯店",
                        "data": json.dumps(data)
                    }
              },
                {
                  "imageUrl": F"{end_point}/static/04_taipeizoo.jpg",
                    "action": {
                        "type": "postback",
                        "label": "台北動物園",
                        "data": json.dumps(data)
                    }
              },
                {
                  "imageUrl": F"{end_point}/static/05_nightmarket.jpg",
                  "action": {
                      "type": "postback",
                      "label": "饒河夜市",
                      "data": json.dumps(data)
                  }
              }
            ]
        }
    }
    return message


def getCallCarMessage(data):
    message = {
        "type": "template",
        "altText": "this is a template",
        "template": {
            "type": "buttons",
            "text": f"請選擇至 {data['title']} 預約叫車時間",
            "actions": [
              {
                  "type": "datetimepicker",
                  "label": "預約",
                  "data": json.dumps(data),
                  "mode": "datetime"
              }
            ]
        }
    }
    return message


def getLocationConfirmMessage(title, latitude, longitude):
    data = {"latitude": latitude, "longitude": longitude,
            "title": title, "action": "get_near"}
    message = {
        "type": "template",
        "altText": "this is a confirm template",
        "template": {
                "type": "confirm",
                "text": f"是否要搜尋 {title} 附近的景點？",
                "actions": [
                    {
                        "type": "postback",
                        "label": "是",
                        "data": json.dumps(data),
                        "displayText": "是",
                    },
                    {
                        "type": "message",
                        "label": "否",
                        "text": "否"
                    }
                ]
        }
    }
    return message


def getPlayStickerMessage():
    message = {
        "type": "sticker",
        "packageId": "446",
        "stickerId": "1988"
    }
    return message


def getTaipei101LocationMessage():
    message = {
        "type": "location",
        "title": "Taipei 101",
        "address": "台北市信義區信義路五段7號89樓",
        "latitude": 25.034804599999998,
        "longitude": 121.5655868
    }
    return message


def getMRTVideoMessage(originalContentUrl=F"{end_point}/static/taipei_101_video.mp4"):
    message = {
        "type": "video",
        "originalContentUrl": F"{end_point}/static/taipei_101_video.mp4",
        "previewImageUrl": F"{end_point}/static/taipei_101.jpeg",
        "trackingId": "track-id"
    }
    return message


def getMRTSoundMessage():
    message = dict()
    message["type"] = "audio"
    message["originalContentUrl"] = F"{end_point}/static/mrt_sound.m4a"
    import audioread
    with audioread.audio_open('static/mrt_sound.m4a') as f:
        # totalsec contains the length in float
        totalsec = f.duration
    message["duration"] = totalsec * 1000
    return message


def getTaipei101ImageMessage(originalContentUrl=F"{end_point}/static/taipei_101.jpeg"):

    return getImageMessage(originalContentUrl)


def getImageMessage(originalContentUrl):
    message = {
        "type": "image",
        "originalContentUrl": originalContentUrl,
        "previewImageUrl": originalContentUrl
    }
    return message


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


def getTotalSentMessageCount():
    response = {}
    return 0


def getTodayCovid19Message():
    response = requests.get(
        "https://covid-19.nchc.org.tw/api/covid19?CK=covid-19@nchc.org.tw&querydata=3001&limited=BGD", headers=HEADER)
    data = response.json()[0]
    date = data['a04']
    total_count = data['a05']
    count = data['a06']
    return F"日期：{date}, 人數：{count}, 確診總人數：{total_count}"


def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1] in ALLOWED_EXTENSIONS


@app.route('/upload_file', methods=['POST'])
def upload_file():
    payload = dict()
    if request.method == 'POST':
        file = request.files['file']
        print("json:", request.json)
        form = request.form
        age = form['age']
        gender = ("男" if form['gender'] == "M" else "女") + "性"
        if file:
            filename = file.filename
            img_path = os.path.join(UPLOAD_FOLDER, filename)
            file.save(img_path)
            print(img_path)
            payload["to"] = my_line_id
            payload["messages"] = [getImageMessage(F"{end_point}/{img_path}"),
                                   {
                "type": "text",
                "text": F"年紀：{age}\n性別：{gender}"
            }
            ]
            pushMessage(payload)
    return 'OK'


@app.route('/line_login', methods=['GET'])
def line_login():
    if request.method == 'GET':
        code = request.args.get("code", None)
        state = request.args.get("state", None)

        if code and state:
            HEADERS = {'Content-Type': 'application/x-www-form-urlencoded'}
            url = "https://api.line.me/oauth2/v2.1/token"
            FormData = {"grant_type": 'authorization_code', "code": code, "redirect_uri": F"{end_point}/line_login",
                        "client_id": line_login_id, "client_secret": line_login_secret}
            data = parse.urlencode(FormData)
            content = requests.post(url=url, headers=HEADERS, data=data).text
            content = json.loads(content)
            url = "https://api.line.me/v2/profile"
            HEADERS = {
                'Authorization': content["token_type"]+" "+content["access_token"]}
            content = requests.get(url=url, headers=HEADERS).text
            content = json.loads(content)
            name = content["displayName"]
            userID = content["userId"]
            pictureURL = content["pictureUrl"]
            statusMessage = content["statusMessage"]
            print(content)
            return render_template('profile.html', name=name, pictureURL=pictureURL, userID=userID, statusMessage=statusMessage)
        else:
            return render_template('login.html', client_id=line_login_id,
                                   end_point=end_point)


if __name__ == "__main__":
    app.debug = True
    app.run()
