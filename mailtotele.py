import os
import pickle
import base64
import time
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from telegram import Update
from telegram.ext import Updater, CommandHandler, CallbackContext

# Thông tin đăng nhập Gmail
SCOPES = ['https://www.googleapis.com/auth/gmail.readonly']
TOKEN_PATH = 'token.pickle'
CREDENTIALS_PATH = 'credentials.json'

# Hàm để lấy thông tin đăng nhập Gmail
def get_gmail_service():
    creds = None
    if os.path.exists(TOKEN_PATH):
        with open(TOKEN_PATH, 'rb') as token:
            creds = pickle.load(token)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(CREDENTIALS_PATH, SCOPES)
            creds = flow.run_local_server(port=0)
        with open(TOKEN_PATH, 'wb') as token:
            pickle.dump(creds, token)
    service = build('gmail', 'v1', credentials=creds)
    return service

# Hàm để gửi thông báo về email mới
def check_email(context: CallbackContext):
    service = get_gmail_service()
    results = service.users().messages().list(userId='me', labelIds=['INBOX'], q='is:unread').execute()
    messages = results.get('messages', [])
    for msg in messages:
        msg_data = service.users().messages().get(userId='me', id=msg['id']).execute()
        subject = ''
        for header in msg_data['payload']['headers']:
            if header['name'] == 'Subject':
                subject = header['value']
                break
        context.bot.send_message(chat_id=context.job.context, text=f'New email: {subject}')
        service.users().messages().modify(userId='me', id=msg['id'], body={'removeLabelIds': ['UNREAD']}).execute()

# Lệnh để bắt đầu bot
def start(update: Update, context: CallbackContext) -> None:
    chat_id = update.message.chat_id
    context.job_queue.run_repeating(check_email, interval=60, first=0, context=chat_id)
    update.message.reply_text('Bot started!')

def main():
    # Thay YOUR_TOKEN_HERE bằng token của bot Telegram của bạn
    updater = Updater('123456:ABC-DEF1234ghIkl-zyx57W2v1u123ew11')

    dp = updater.dispatcher

    dp.add_handler(CommandHandler("start", start))

    updater.start_polling()
    updater.idle()

if __name__ == '__main__':
    main()
