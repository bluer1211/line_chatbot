
import requests
import re
import random
import configparser
#==========================
#QnA
import http.client, json
#==========================

from bs4 import BeautifulSoup
from flask import Flask, request, abort

from linebot import (
    LineBotApi, WebhookHandler
)
from linebot.exceptions import (
    InvalidSignatureError
)
from linebot.models import *
from nlp.olami import Olami


app = Flask(__name__)
config = configparser.ConfigParser()
config.read("config.ini")

line_bot_api = LineBotApi(config['line_bot']['Channel_Access_Token'])
handler = WebhookHandler(config['line_bot']['Channel_Secret'])

#==========================
#QnA
host = 'ismartqna.azurewebsites.net'  #主機
endpoint_key = "994c7330-e0fc-4551-aea9-99dc5fdd7fb1"  #授權碼
kb = "7eccce50-f666-4a42-b5b9-69c5860f05d0"  #GUID碼
method = "/qnamaker/knowledgebases/" + kb + "/generateAnswer"
#==========================

@app.route("/callback", methods=['POST'])
def callback():
    # get X-Line-Signature header value
    signature = request.headers['X-Line-Signature']

    # get request body as text
    body = request.get_data(as_text=True)
    # print("body:",body)
    app.logger.info("Request body: " + body)

    # handle webhook body
    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        abort(400)

    return 'ok'




@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):

    #====================
    findQnA=sendQnA(event, event.message.text)
    
    #===================
    if findQnA:
        line_bot_api.reply_message(event.reply_token,TextSendMessage(text=Olami().nli(event.message.text)))




@handler.add(MessageEvent, message=StickerMessage)
def handle_sticker_message(event):
    # ref. https://developers.line.me/media/messaging-api/sticker_list.pdf
    sticker_ids = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 21, 100, 101, 102, 103, 104, 105, 106,
                   107, 108, 109, 110, 111, 112, 113, 114, 115, 116, 117, 118, 119, 120, 121, 122, 123, 124, 125,
                   126, 127, 128, 129, 130, 131, 132, 133, 134, 135, 136, 137, 138, 139, 401, 402]
    index_id = random.randint(0, len(sticker_ids) - 1)
    sticker_id = str(sticker_ids[index_id])

    sticker_message = StickerSendMessage(
        package_id='1',
        sticker_id=sticker_id
    )
    line_bot_api.reply_message(
        event.reply_token,
        sticker_message)


def sendQnA(event, mtext):  #QnA
    question = {
        'question': mtext,
    }
    content = json.dumps(question)
    headers = {
        'Authorization': 'EndpointKey ' + endpoint_key,
        'Content-Type': 'application/json',
        'Content-Length': len(content)
    }
    conn = http.client.HTTPSConnection(host)
    conn.request ("POST", method, content, headers)
    response = conn.getresponse ()
    result = json.loads(response.read())
    result1 = result['answers'][0]['answer']
    if 'No good match' in result1:
        text1 = '很抱歉，資料庫中無適當解答！\n請再輸入問題。'
        return True
        #將沒有解答的問題寫入資料庫
        #userid = event.source.user_id
        #unit = users.objects.create(uid=userid, question=mtext)
        #unit.save()
    else:
        result2 = result1[0:]
        text1 = result2  
    message = TextSendMessage(
        text = text1
    )
    line_bot_api.reply_message(event.reply_token,message)



if __name__ == '__main__':
    app.run()
