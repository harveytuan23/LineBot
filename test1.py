# -*- coding: utf-8 -*-
import json
import requests

HEADER = {
    'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/111.0.0.0 Safari/537.36'}
form_data = {
    'SearchType': 'S',
    'Lang': 'TW',
    'StartStation': 'NanGang',
    'EndStation': 'ZuoYing',
    'OutWardSearchDate': '2023/03/28',
    'OutWardSearchTime': '16:30',
    'ReturnSearchDate': '2023/03/27',
    'ReturnSearchTime': '22:30',
    'DiscountType': ''
}
response = requests.post(
    'https://www.thsrc.com.tw/TimeTable/Search', data=form_data)
response.encoding = "utf-8"
data = json.loads(response.text)

print(data)
