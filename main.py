import os
import time
from textwrap import dedent

import requests
import telegram
from dotenv import load_dotenv
from urllib.parse import urljoin


def get_long_polling_review(url, token_api_devman, timestamp=None):
    payload = {'timestamp': timestamp}
    headers = {
        "Authorization": f"Token {token_api_devman}"
    }
    response = requests.get(url, headers=headers, params=payload, timeout=5)
    response.raise_for_status()
    return response.json()


def send_message_using_bot(bot, chat_id, response):

    for new_attempt in response['new_attempts']:
        is_negative_review = new_attempt['is_negative']
        lesson_title = new_attempt['lesson_title']
        relative_lesson_url = new_attempt['lesson_url']

    lesson_url = urljoin('https://dvmn.org', relative_lesson_url)
    if is_negative_review:
        text_message = f'''\
            У вас проверили работу "{lesson_title}." 
            К сожалению, в работе нашлись ошибки. 
            Посмотреть их можно по ссылке: {lesson_url}\
        '''
    else:
        text_message = f'''\
            У вас проверили работу "{lesson_title}"  
            Преподавателю все понравилось, можно приступать к следующему уроку. 
            Для этого можно перейти по ссылке: {lesson_url}\
        '''
    bot.send_message(chat_id=chat_id, text=dedent(text_message))


def main():
    load_dotenv()

    TOKEN = os.getenv("TOKEN")
    CHAT_ID = os.getenv("CHAT_ID")
    TOKEN_API_DEVMAN = os.getenv("TOKEN_API_DEVMAN")

    bot = telegram.Bot(token=TOKEN)
    timestamp = None
    failed_connections = 0
    while True:
        try:
            url = 'https://dvmn.org/api/long_polling/'
            response = get_long_polling_review(
                url,
                TOKEN_API_DEVMAN,
                timestamp
            )
            if response['status'] == 'found':
                timestamp = response['last_attempt_timestamp']
            else:
                timestamp = response['timestamp_to_request']
            send_message_using_bot(bot, CHAT_ID, response)
        except requests.exceptions.ReadTimeout:
            pass
        except requests.exceptions.ConnectionError:
            failed_connections += 1
            if failed_connections % 5 == 0:
                time.sleep(60)


if __name__ == '__main__':
    main()
