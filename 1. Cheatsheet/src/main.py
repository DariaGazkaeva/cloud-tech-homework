import requests
import os
import json

"""Telegram Bot on Yandex Cloud Function."""

FUNC_RESPONSE = {
    'statusCode': 200,
    'body': ''
}

GLOBAL_COMMANDS = ["/start", "/help"]

TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
TELEGRAM_API_URL = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}"

WELCOME_MESSAGE = 'Я помогу подготовить ответ на экзаменационный вопрос по дисциплине "Операционные системы".\nПришлите мне фотографию с вопросом или наберите его текстом.'
API_ERROR_MESSAGE = "Я не смог подготовить ответ на экзаменационный вопрос."
PHOTO_ERROR_MESSAGE = "Я не могу обработать эту фотографию."
PHOTOS_ERROR_MESSAGE = "Я могу обработать только одну фотографию."
OTHER_ERROR_MESSAGE = "Я могу обработать только текстовое сообщение или фотографию."

sent_group_error = {}


def send_message(text, message):
    """Отправка сообщения пользователю Telegram."""

    message_id = message['message_id']
    chat_id = message['chat']['id']
    reply_message = {'chat_id': chat_id,
                     'text': text,
                     'reply_to_message_id': message_id}

    requests.post(url=f'{TELEGRAM_API_URL}/sendMessage', json=reply_message)


def handler(event, context):
    """Обработчик облачной функции. Реализует Webhook для Telegram Bot."""

    if TELEGRAM_BOT_TOKEN is None:
        return FUNC_RESPONSE

    update = json.loads(event['body'])

    if 'message' not in update:
        return FUNC_RESPONSE

    message_in = update['message']

    if 'text' not in message_in and 'photo' not in message_in:
        send_message(OTHER_ERROR_MESSAGE, message_in)
        return FUNC_RESPONSE
    
    if 'text' in message_in:
        text = message_in['text']
        if text in GLOBAL_COMMANDS:
            send_message(WELCOME_MESSAGE, message_in)
        else:
            send_message('answer 1', message_in)
        return FUNC_RESPONSE

    if "media_group_id" in message_in:
        media_group_id = message_in['media_group_id']
        if media_group_id not in sent_group_error:
            send_message(PHOTOS_ERROR_MESSAGE, message_in)
            sent_group_error[media_group_id] = True
        return FUNC_RESPONSE 
    elif 'photo' in message_in:
        send_message('answer 2', message_in)
    return FUNC_RESPONSE
