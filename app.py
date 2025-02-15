from flask import Flask, request, abort

from linebot.v3 import (
    WebhookHandler
)
from linebot.v3.exceptions import (
    InvalidSignatureError
)
from linebot.v3.webhooks import (
    MessageEvent,
    TextMessageContent
)

from linebot.v3.messaging import (
    Configuration,
    ApiClient,
    MessagingApi,
    ReplyMessageRequest,
    TextMessage,
    ApiClient
)

from linebot.v3.models import *

import os

app = Flask(__name__)

configuration = Configuration(access_token=os.getenv("CHANNEL_ACCESS_TOKEN"))
handler = WebhookHandler(os.getenv("CHANNEL_SECRET"))


@app.route("/callback", methods=['POST'])
def callback():
    # get X-Line-Signature header value
    signature = request.headers['X-Line-Signature']

    # get request body as text
    body = request.get_data(as_text=True)
    app.logger.info("Request body: " + body)

    # handle webhook body
    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        app.logger.info("Invalid signature. Please check your channel access token/channel secret.")
        abort(400)

    return 'OK'

# Added manual format -Garrett, 2021.05.10
def msg_manual_report(user_msg, groupID, userName):
    user_msg = user_msg.replace('自訂回報','').strip()
    ID = str(userName)
    reportData[groupID][ID] = user_msg
    tmp_str = str(ID)+'，回報成功。'  
    return tmp_str      

def msg_report(user_msg, groupID):
    try:
        if ( # 檢查資料是否有填，字數注意有換行符
            len(user_msg.split('姓名')[-1].split('學號')[0])<3 and
            len(user_msg.split("學號")[-1].split('手機')[0])<3 and 
            len(user_msg.split('手機')[-1].split('地點')[0])<12 and 
            len(user_msg.split('地點')[-1].split('收假方式')[0])<3
            ):
            raise Exception
        # 得到學號
        ID = user_msg.split("學號")[-1].split('手機')[0][1:]
        # 直接完整save學號 -Garrett, 2021.01.28  
        ID = str(int(ID)) #先數值再字串，避免換行困擾
        # 學號不再限定只有5碼 -Garrett, 2021.01.28  
        #if len(ID)==6:
        #    ID = int(ID[-4:])
        #elif len(ID)<=4:
        #    ID = int(ID)
    except Exception:
        tmp_str = '姓名、學號、手機、地點，其中一項未填。'       
    else:
        reportData[groupID][ID] = user_msg
        tmp_str = str(ID)+'號弟兄，回報成功。'  
    return tmp_str        

def msg_readme():
    tmp_str = (
        '回報格式有兩種方法\n'
        '[1]固定格式。\n'
        '----------\n'
        '姓名：\n'
        '學號：\n'
        '手機：\n'
        '地點：\n'
        '收假方式：\n'
        '----------\n'
        '\n'
        '[2]開頭帶有自訂回報\n'
        '後帶的訊息皆會直接紀錄\n'
        '----------\n'
        '自訂回報\n'
        '王小明範例訊息\n'
        '----------\n'
        '\n'
        '指令\n' 
        '----------\n'   
        '•格式\n'
        '->預設格式範例。\n'
        '•回報統計\n'
        '->顯示完成回報的號碼。\n'
        '•輸出回報\n'
        '->貼出所有回報，並清空回報紀錄。\n'
        '•清空\n'
        '->可手動清空Data，除錯用。\n'
        '----------\n' 
        '效果可參閱此說明\n'
        'https://github.com/GarrettTW/linebot_reportmessage/blob/master/README.md'
    )
    return tmp_str

def msg_cnt(groupID):
    tmp_str = ''
    try:
        tmp_str = (
            '完成回報的號碼有:\n'
            +str([number for number in sorted(reportData[groupID].keys())]).strip('[]')
        )
    except BaseException as err:
        tmp_str = '錯誤原因: '+str(err)
    return tmp_str

def msg_output(groupID):
    try:
        tmp_str = ''
        for data in [reportData[groupID][number] for number in sorted(reportData[groupID].keys())]:
            tmp_str = tmp_str + data +'\n\n'      
    except BaseException as err:
        tmp_str = '錯誤原因: '+str(err)
    else:
        reportData[groupID].clear()
    return tmp_str
def msg_format():
    tmp_str = '姓名：\n學號：\n手機：\n地點：\n收假方式：'
    return tmp_str
    
def msg_clear(groupID):
    reportData[groupID].clear()
    tmp_str = '資料已重置!'
    return tmp_str


@handler.add(MessageEvent, message=TextMessageContent)
def handle_message(event):
    # 各群組的資訊互相獨立
    # 確認事件來源類型
    source_type = event.source.type
    if source_type == 'group':
        groupID = event.source.group_id
    else:
        messaging_api = MessagingApi(ApiClient(configuration))
        message = TextMessage(text='我只接收群組內訊息，請先把我邀請到群組!')
        messaging_api.reply_message(event.reply_token, [message])
        return
    
    userID = event.source.user_id
    messaging_api = MessagingApi(ApiClient(configuration))
    
    g_profile = messaging_api.get_group_summary(groupID)
    groupName = g_profile.group_name

    u_profile = configuration.get_group_member_profile(groupID,userID)
    userName = u_profile.display_name
    '''userName = str(userName)'''

    if not reportData.get(groupID): # 如果此群組為新加入，會創立一個新的儲存區
        reportData[groupID]={}
    LineMessage = ''
    receivedmsg = event.message.text

    if '姓名' in receivedmsg and '學號' in receivedmsg and '手機' in receivedmsg:
        LineMessage = msg_report(receivedmsg,groupID)
    elif '自訂回報' in receivedmsg[:4]:
        LineMessage = msg_manual_report(receivedmsg,groupID,userName)
    elif '使用說明' in receivedmsg and len(receivedmsg)==4:
        LineMessage = msg_readme()        
    elif '回報統計' in receivedmsg and len(receivedmsg)==4:
        LineMessage = msg_cnt(groupID)
    elif '格式' in receivedmsg and len(receivedmsg)==2:
        LineMessage = msg_format()
    elif '輸出回報' in receivedmsg and len(receivedmsg)==4:
        LineMessage = msg_output(groupID)
    # for Error Debug, Empty all data -Garrett, 2021.01.27        
    elif '清空' in receivedmsg and len(receivedmsg)==2:
        LineMessage = msg_clear(groupID)
        
    if LineMessage :
        message = TextMessage(text=LineMessage)
        messaging_api.reply_message(event.reply_token, [message])
            
if __name__ == "__main__":
    global reportData
    reportData = {}
    app.run(host="0.0.0.0", port=10000)