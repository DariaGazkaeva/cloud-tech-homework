import os
import json
import base64
import requests

"""Telegram Bot on Yandex Cloud Function."""

FUNC_RESPONSE = {
    'statusCode': 200,
    'body': '',
}

GLOBAL_COMMANDS = ["/start", "/help"]

BUCKET_NAME = os.environ.get("BUCKET_NAME")
GPT_INSTRUCTION_KEY = os.environ.get("GPT_INSTRUCTION_KEY")
OCR_INSTRUCTION_KEY = os.environ.get("OCR_INSTRUCTION_KEY")
TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
TELEGRAM_API_URL = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}"

WELCOME_MESSAGE = 'Я помогу подготовить ответ на экзаменационный вопрос по дисциплине "Операционные системы".\nПришлите мне фотографию с вопросом или наберите его текстом.'
API_ERROR_MESSAGE = "Я не смог подготовить ответ на экзаменационный вопрос."
PHOTO_ERROR_MESSAGE = "Я не могу обработать эту фотографию."
PHOTOS_ERROR_MESSAGE = "Я могу обработать только одну фотографию."
OTHER_ERROR_MESSAGE = "Я могу обработать только текстовое сообщение или фотографию."

URL_GPT = "https://llm.api.cloud.yandex.net/foundationModels/v1/completion"
URL_OCR = "https://ocr.api.cloud.yandex.net/ocr/v1/recognizeText"

sent_group_error = {}

def send_typing(message):
    if "media_group_id" in message and message['media_group_id'] in sent_group_error:
        return
    url = f'{TELEGRAM_API_URL}/sendChatAction'
    data = {'chat_id': message['chat']['id'], 'action': 'typing'}
    requests.post(url, data=data)


def get_response_from_gpt(question):
    object = open(f'/function/storage/{BUCKET_NAME}/{GPT_INSTRUCTION_KEY}').read()
    request = json.loads(object)

    request['modelUri'] = f"gpt://{os.environ.get('FOLDER_ID')}/yandexgpt"

    request['messages'][1]['text'] = question

    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Api-Key {os.environ.get('SA_API_KEY')}",
        "x-folder-id": os.environ.get('FOLDER_ID'),
    }

    response = requests.post(
        URL_GPT,
        headers=headers,
        json=request,
    )

    return response


def get_response_from_ocr(photo):
    object = open(f'/function/storage/{BUCKET_NAME}/{OCR_INSTRUCTION_KEY}').read()
    request = json.loads(object)

    request['content'] = photo

    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Api-Key {os.environ.get('SA_API_KEY')}",
        "x-folder-id": os.environ.get('FOLDER_ID'),
    }

    response = requests.post(
        URL_OCR,
        headers=headers,
        json=request,
    )

    return response


def get_file_data(id):
    file_info = requests.get(f'https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/getFile', params={'file_id': id})
    file_path = file_info.json()['result']['file_path']
    file_data = requests.get(f'https://api.telegram.org/file/bot{TELEGRAM_BOT_TOKEN}/{file_path}')
    return base64.b64encode(file_data.content).decode("ascii")


def send_message(text, message_id, chat_id):
    """Отправка сообщения пользователю Telegram."""
    reply_message = {'chat_id': chat_id,
                     'text': text,
                     'reply_to_message_id': message_id}

    requests.post(url=f'{TELEGRAM_API_URL}/sendMessage', json=reply_message)


def reply_with_gpt(query, message_id, chat_id):
    response = get_response_from_gpt(query)
    
    if not response.ok:
        send_message(API_ERROR_MESSAGE, message_id, chat_id)
        return FUNC_RESPONSE
    
    answer = response.json()['result']['alternatives'][0]['message']['text']
    send_message(answer, message_id, chat_id)


def handler(event, context):
    """Обработчик облачной функции. Реализует Webhook для Telegram Bot."""

    if TELEGRAM_BOT_TOKEN is None:
        return FUNC_RESPONSE

    update = json.loads(event['body'])

    if 'message' not in update:
        return FUNC_RESPONSE

    message_in = update['message']
    send_typing(message_in)

    message_id = message_in['message_id']
    chat_id = message_in['chat']['id']

    if 'text' not in message_in and 'photo' not in message_in:
        send_message(OTHER_ERROR_MESSAGE, message_id, chat_id)
        return FUNC_RESPONSE
    
    if 'text' in message_in:
        text = message_in['text']
        if text in GLOBAL_COMMANDS:
            send_message(WELCOME_MESSAGE, message_id, chat_id)
        else:
            reply_with_gpt(text, message_id, chat_id)
        return FUNC_RESPONSE

    if "media_group_id" in message_in:
        media_group_id = message_in['media_group_id']
        if media_group_id not in sent_group_error:
            send_message(PHOTOS_ERROR_MESSAGE, message_id, chat_id)
            sent_group_error[media_group_id] = True
        return FUNC_RESPONSE 
    
    if 'photo' in message_in:
        file_id = message_in['photo'][-1]['file_id']
        file = get_file_data(file_id)
        response = get_response_from_ocr(file)

        if not response.ok:
            send_message(PHOTO_ERROR_MESSAGE, message_id, chat_id)
            return FUNC_RESPONSE
        
        text = response.json()['result']['textAnnotation']['fullText']
        reply_with_gpt(text, message_id, chat_id)
    
    return FUNC_RESPONSE
