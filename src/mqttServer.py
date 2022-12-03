# -*- coding: utf-8 -*-
# install and invoke libraries
from flask import Flask, request, abort
from linebot import (
    LineBotApi, WebhookHandler
)
from linebot.exceptions import (
    InvalidSignatureError, LineBotApiError
)
from linebot.models import (
    MessageEvent, TextMessage, TextSendMessage,
)
from flask_mqtt import Mqtt, MQTT_LOG_ERR, MQTT_LOG_DEBUG
import firebase_admin
from firebase_admin import credentials
from firebase_admin import firestore
from pyngrok import ngrok

# declare all settings
LINE_CH_SECRET = '8af05fe435febd6fcce636550bcd9faa'
LINE_ACCESS_TOKEN = '92dXUt6Gm6UXkF6WpYuIAuCoRc/DWwGLFoVBjiJwwgj5Lj8PIQ96u4wlAwgGOjAh0K9SuY62/7d5w2q2pGsOxUPsD5RJpkLi9alCPra9TYTvGpuhHMbSEn/UUQ+Wi0FTb234BDtz16A1FFKgvu2IEwdB04t89/1O/w1cDnyilFU='

MQTT_BROKER = 'broker.hivemq.com'
NGROK_AUTH_TOKEN = '1hMCWxPuzbSdIHYTuEFKaWdwFOH_6XJdqSE2GapiLWyas6MTu'

cred = credentials.Certificate("serviceAccountKey.json")
firebase_admin.initialize_app(cred)

# initialize web and MQTT
app = Flask(__name__)

app.config['MQTT_BROKER_URL'] = MQTT_BROKER  # use the free broker from NETPIE
app.config['MQTT_BROKER_PORT'] = 1883  # default port for non-tls connection
# set the time interval for sending a ping to the broker to 5 seconds
app.config['MQTT_KEEPALIVE'] = 60
# set TLS to disabled for testing purposes
app.config['MQTT_TLS_ENABLED'] = False
mqtt = Mqtt(app)
mqtt.client._client_id = mqtt.client_id.encode('utf-8')

line_bot_api = LineBotApi(LINE_ACCESS_TOKEN)
handler = WebhookHandler(LINE_CH_SECRET)

mqtt_msg = ''


@app.route("/callback", methods=['POST'])
def callback():
    signature = request.headers['X-Line-Signature']

    # get request body as text
    body = request.get_data(as_text=True)
    app.logger.info("Request body: " + body)

    # handle webhook body
    try:
        handler.handle(body, signature)
    except LineBotApiError as e:
        print("Got exception from LINE Messaging API: %s\n" % e.message)
        for m in e.error.details:
            print("  %s: %s" % (m.property, m.message))
        print("\n")
    except InvalidSignatureError:
        abort(400)

    return 'OK'


@handler.add(MessageEvent, message=TextMessage)
def handle_text_message(event):
    text = event.message.text
    # get user id
    user_id = event.source.user_id
    profile = line_bot_api.get_profile(user_id)
    name = profile.display_name

    if text.startswith('#'):
        if text == '#on':
            mqtt.publish('/ict792/message', '#on')
            db = firestore.client()
            db.collection(u'messages').add(
                {u'timstamp': firestore.SERVER_TIMESTAMP, u'message': name + u'turn on the LED'})

        elif text == '#off':
            mqtt.publish('/ict792/message', '#off')
            db = firestore.client()
            db.collection(u'messages').add(
                {u'timstamp': firestore.SERVER_TIMESTAMP, u'message': name + u'turn off the LED'})

        if text == '1':
            mqtt.publish('/ict792/message', '1')
        elif text == '2':
            mqtt.publish('/ict792/message', '2')


@mqtt.on_connect()
def handle_mqtt_connect(client, userdata, flags, rc):
    if rc == 0:
        print('Connected successfully')
        mqtt.subscribe('/ict792/message')
    else:
        print('Bad connection. Code:', rc)


# @mqtt.on_log()
# def handle_logging(client, userdata, level, buf):
#     if level == MQTT_LOG_ERR:
#         print('Error: {}'.format(buf))

#     elif level == MQTT_LOG_DEBUG:
#         print('Debug: {}'.format(buf))

@mqtt.on_message()
def handle_mqtt_message(client, userdata, message):
    data = dict(
        topic=message.topic,
        payload=message.payload.decode()
    )
    print(
        'Received message on topic: {topic} with payload: {payload}'.format(**data))

    # If press the board's button, send a message to LINE and save the message to firestore
    if (data["payload"] == 'this is 💣Boom pressing!'):
        db = firestore.client()
        db.collection(u'messages').add(
            {u'timstamp': firestore.SERVER_TIMESTAMP, u'message': data["payload"]})


# runtime
http_tunnel = ngrok.connect(5000)
endpoint_url = http_tunnel.public_url.replace('http://', 'https://')
print('LINE bot online at ' + endpoint_url)
line_bot_api.set_webhook_endpoint(endpoint_url + '/callback')
app.run(port=5000, debug=True, use_reloader=False)
