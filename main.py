# SEEDBOX REVERSE API

import requests
import os
from bs4 import BeautifulSoup
import rich
import telebot
from telebot.types import BotCommand
from fastapi import FastAPI, Request
from fastapi.templating import Jinja2Templates
import uvicorn
from dotenv import load_dotenv, find_dotenv
import time
from fs.memoryfs import MemoryFS
from fs.osfs import OSFS
# import hashlib
# import bencode
# import concurrent.futures
from objprint import objprint
# from hupper import start_reloader
import threading
import json
import sys

main = FastAPI()

templates = Jinja2Templates(directory="templates")

load_dotenv(find_dotenv())

telegram_token = os.getenv("TELEGRAM_TOKEN")
host_url = os.getenv("HOST_URL")
git = os.getenv("GIT_REPO")
user_id = os.getenv("USER_ID")
bot = telebot.TeleBot(telegram_token)

allowed_user_ids = list(map(int, user_id.split(",")))



# Define the webhook route

pending = []


@main.get('/')
def index():
  return {"STATUS": "RUNNING ✨✨"}


def hide_api_key(api_key):
  return "*" * (len(api_key) - 4) + api_key[-4:]


@main.post(f'/{telegram_token}', include_in_schema=False)
async def handle_telegram_webhook(request: Request):
  api_key = telegram_token  # Assuming `telegram_token` contains your actual API key
  hidden_api_key = hide_api_key(api_key)

  body = await request.body()
  print(body)  # Print the received body content
  try:
    data = json.loads(body)
    print(data)  # Print the parsed JSON data
    print(f"API Key: {hidden_api_key}")  # Print the hidden API key
    update = telebot.types.Update.de_json(data)
    bot.process_new_updates([update])
    return 'OK', 201
  except ValueError as e:
    print(f"Error: {e}")
    return 'Bad Request', 400


bot.set_my_commands(
  commands=[BotCommand("help", "Just Send Magnet Link or Torrent File 🧲")])


# Dummy user class to simulate the user ID
class User:

  def __init__(self, chat_id):
    self.id = str(chat_id)


# Dummy chat class to simulate the chat ID
class Chat:

  def __init__(self, chat_id):
    self.id = chat_id


# Dummy message class to pass to torrent_box function
class DummyMessage:

  def __init__(self, user, chat_id):
    self.from_user = user
    self.chat = Chat(chat_id)
    self.message_id = chat_id  # Use chat ID as message ID
    self.text = "Upload My File"


class SimpleFileSystem:

  def __init__(self):
    self.memory_fs = MemoryFS()
    self.real_fs = OSFS("/")

  def write_file(self, path, content):
    with self.memory_fs.open(path, "w") as f:
      f.write(content)

  def read_file(self, path):
    with self.memory_fs.open(path, "r") as f:
      return f.read()

  def delete_file(self, path):
    self.memory_fs.remove(path)

  def list_files(self, path="/"):
    return self.memory_fs.listdir(path)

  def list_files_real_fs(self, path="/"):
    return self.real_fs.listdir(path)

  def get_real_fs(self):
    return self.real_fs


@bot.message_handler(content_types=['text'])
def torrent_box(message):
  if str(message.from_user.id) in allowed_user_ids:
    mag = message.text
    print(mag)

    msgg = None
    try:
      bot.send_chat_action(message.chat.id, "typing")
      msgg = bot.send_message(message.chat.id,
                              text="🧲 Successfully Processed....",
                              reply_to_message_id=message.message_id)
    except Exception as e:
      pass

    url = "https://dash.sonicbit.net/login"

    response = requests.get(url)

    html_content = response.text

    soup = BeautifulSoup(html_content, 'html.parser')

    csrf_token = soup.find('meta', {'name': 'csrf-token'})['content']

    rich.print(csrf_token)

    headers = {
      "User-Agent":
      "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36 Edg/114.0.1823.37"
    }

    login_data = {
      '_token': csrf_token,
      '_method': 'POST',
      'email': '',
      'password': '',
    }

    login_endpoint = 'https://dash.sonicbit.net/login_user'

    response = requests.post(login_endpoint,
                             headers=headers,
                             data=login_data,
                             cookies=response.cookies)

    rich.print(response.json())

    cc = response.cookies

    add_urls = 'https://dash.sonicbit.net/function/add_torrent_url'

    headers = {
      "User-Agent":
      "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36 Edg/114.0.1823.37"
    }

    magnet = {'_token': csrf_token, 'url_list[]': [mag], 'auto_start': 1}

    url_add = requests.post(url=add_urls,
                            headers=headers,
                            data=magnet,
                            cookies=cc)

    rich.print(url_add.json())

    tor_url = 'https://dash.sonicbit.net/function/torrent_list'

    tor_data = {
      '_token': csrf_token,
      '_method': 'POST',
      'action': 'get_torrents_list'
    }

    list_up = requests.post(url=tor_url,
                            headers=headers,
                            data=tor_data,
                            cookies=cc)

    rich.print(list_up.json())

    has_torrents = False
    if list_up.status_code == 200:
      data = list_up.json()

      hash_value = None
      name_value = None
      downloading = 0
      for hash_key, nested_dict in data.items():

        # If the key is not "info", we're dealing with the torrent data
        if hash_key != 'info':
          # Extract values from the nested dictionary
          name_value = nested_dict['name']
          hash_value = nested_dict['hash']
          added = nested_dict['added']
          labels = nested_dict['labels']
          size_bytes = nested_dict['sizeBytes']
          filesize = nested_dict['filesize']

          # Now you can print or use these values
          print(f"Hash Key: {hash_key}")
          print(f"Name: {name_value}")
          print(f"Hash: {hash_value}")
          print(f"Added: {added}")
          print(f"Labels: {labels}")
          print(f"Size Bytes: {size_bytes}")
          size = f"{filesize}"
          print(f"File Size: {size}")

        # If the key is "info", we're dealing with the info data

        if hash_key == 'info':
          # Extract values from the info section
          download_rate = nested_dict['downloadRate']
          upload_rate = nested_dict['uploadRate']
          downloading = nested_dict['downloading']
          #...add here extraction for all the keys in this section you're interested in

          # Now you can print or use these values
          down = f"Download Rate: {download_rate}"
          print(f"Upload Rate: {upload_rate}")
          has_torrents = True
          #...and so on for all the values you've extracted

        if msgg is not None:
          # Rest of the code where 'msgg' is used
          if has_torrents:
            update_text = f"{name_value}\n\n{size}\n\nDownloading 🔰 \n\n{downloading}"
            bot.edit_message_text(
              update_text,
              message.chat.id,
              msgg.message_id,
            )

        else:
          print("NO ANY TORRENTS FOUND")

        if hash_value in pending:
          print(f"PENDING SKIPPED {hash_value}")

        if msgg is not None:
          if has_torrents:
            if not hash_value in pending:
              pending.append(hash_value)
              print(f'ADDED {pending}')

        if downloading == False:
          up_url = 'https://dash.sonicbit.net/function/torrent_list'
          up_data = {
            '_token': csrf_token,
            '_method': 'POST',
            'action': 'get_torrents_list'
          }

          up_2 = requests.post(url=up_url,
                               headers=headers,
                               data=up_data,
                               cookies=cc)

          rich.print(up_2.json())

          up_re = "https://dash.sonicbit.net/function/add_upload_task"

          headers = {
            "User-Agent":
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36 Edg/114.0.1823.37",
          }

          up_data_2 = {
            '_token': csrf_token,
            '_method': 'POST',
            'set_fname': name_value,
            'set_idx': 'NA',
            'set_hash': hash_value,
            'set_remoteid': 23747,
            'set_type': 'dir',
            'platform': 'web',
            'isMyDrive': 0,
          }

          print(up_data_2)

          response_2 = requests.post(url=up_re,
                                     headers=headers,
                                     data=up_data_2,
                                     cookies=cc)
          rich.print(response_2.json())

          if response_2.json()['status'] == 'success':
            print('🎁 success')

  time.sleep(60)


#Define a function to handle incoming documents
@bot.message_handler(content_types=['document'])
def handle_documents(message):
  if str(message.from_user.id) in allowed_user_ids:
    # Get the File object from the message
    document = message.document
    ids = document.file_id
    names = document.file_name
    fs = SimpleFileSystem()

    print(document)
    file_info = bot.get_file(document.file_id)
    file_url = f"https://api.telegram.org/file/bot{bot.token}/{file_info.file_path}"

    with open(names, 'wb') as local_file:
      response = requests.get(file_url, stream=True)
      for chunk in response.iter_content(chunk_size=4096):
        local_file.write(chunk)

    # # Write a file to the in-memory filesystem
    # fs.write_file("/file.txt", "Hello, World!")

    # # Read the file from the in-memory filesystem
    # content = fs.read_file("/file.txt")
    # print(content)

    # # List files in the in-memory filesystem
    # files = fs.list_files("/")
    # print(files)

    # # List files in the real filesystem
    # real_files = fs.list_files_real_fs("/")
    # print(real_files)

    # # Delete the file from the in-memory filesystem
    # fs.delete_file("/file.txt")

    # # Verify deletion in the in-memory filesystem
    # files = fs.list_files("/")
    # print(files)

    # # List files in the real filesystem after deletio
    # real_files = fs.list_files_real_fs("/")
    # print(real_files)

    # Access the real filesystem directly
    real_fs = fs.get_real_fs()
    curr = os.getcwd()
    real_files = real_fs.listdir(curr)
    for torrent in real_files:
      if '.torrent' in torrent:
        filez = torrent

    print(filez)

    # Prompt for torrent file path
    torrent_file_path = filez

    # Open torrent file
    # with open(torrent_file_path, 'rb') as torrent_file:
    #   metainfo = bencode.bdecode(torrent_file.read())

    # info = metainfo['info']
    # info_hash = hashlib.sha1(bencode.bencode(info)).hexdigest()
    # final_res = f'magnet:?xt=urn:btih:{info_hash}'
    # print(final_res)

    url = "https://dash.sonicbit.net/login"

    response = requests.get(url)

    html_content = response.text

    soup = BeautifulSoup(html_content, 'html.parser')

    csrf_token = soup.find('meta', {'name': 'csrf-token'})['content']

    rich.print(csrf_token)

    headers = {
      "User-Agent":
      "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36 Edg/114.0.1823.37"
    }

    login_data = {
      '_token': csrf_token,
      '_method': 'POST',
      'email': 'vibestepler@gmail.com',
      'password': '&8@9qVtZ*jNUGe',
    }

    login_endpoint = 'https://dash.sonicbit.net/login_user'

    response = requests.post(login_endpoint,
                             headers=headers,
                             data=login_data,
                             cookies=response.cookies)

    rich.print(response.json())

    add_urls = 'https://dash.sonicbit.net/function/upload_torrent'

    headers = {
      "User-Agent":
      "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36 Edg/114.0.1823.37"
    }

    mag_file = {
      '_token': csrf_token,
      'auto_start': 1,
    }

    fin = open(torrent_file_path, 'rb')
    files = {'file': fin}

    url_add = requests.post(url=add_urls,
                            headers=headers,
                            data=mag_file,
                            files=files,
                            cookies=response.cookies)

    os.remove(torrent_file_path)
    bot.send_chat_action(message.chat.id, "typing")

    msgg = bot.send_message(message.chat.id,
                            text="🧲 Successfully Processed....",
                            reply_to_message_id=message.message_id)

    rich.print(url_add.json())

    tor_url = 'https://dash.sonicbit.net/function/torrent_list'

    tor_data = {
      '_token': csrf_token,
      '_method': 'POST',
      'action': 'get_torrents_list'
    }

    list_up = requests.post(url=tor_url,
                            headers=headers,
                            data=tor_data,
                            cookies=response.cookies)

    rich.print(list_up.json())

    if list_up.status_code == 200:
      data = list_up.json()

      for hash_key, nested_dict in data.items():
        # If the key is not "info", we're dealing with the torrent data
        if hash_key != 'info':
          # Extract values from the nested dictionary
          name = nested_dict['name']
          hash_value = nested_dict['hash']
          added = nested_dict['added']
          labels = nested_dict['labels']
          size_bytes = nested_dict['sizeBytes']
          filesize = nested_dict['filesize']

          # Now you can print or use these values
          print(f"Hash Key: {hash_key}")
          name = f"{name}"
          print(f"Hash: {hash_value}")
          print(f"Added: {added}")
          print(f"Labels: {labels}")
          print(f"Size Bytes: {size_bytes}")
          size = f"{filesize}"

        # If the key is "info", we're dealing with the info data
        elif hash_key == 'info':
          # Extract values from the info section
          download_rate = nested_dict['downloadRate']
          upload_rate = nested_dict['uploadRate']
          downlaoding = nested_dict['downloading']
          #...add here extraction for all the keys in this section you're interested in

          # Now you can print or use these values
          down = f"Download Rate: {download_rate}"
          print(f"Upload Rate: {upload_rate}")
          #...and so on for all the values you've extracted

          update_text = f" {name}\n\n{size}\n\nDownloading: \n\n{downlaoding}"
          time.sleep(2)
          bot.edit_message_text(
            update_text,
            message.chat.id,
            msgg.message_id,
          )

        else:
          print(f"Request failed with status code {list_up.status_code}")


# # Example usage

#def main():
# # List files in the real filesystem
# real_files = fs.list_files_real_fs("/")
# print(real_files)

# # Delete the file from the in-memory filesystem
# fs.delete_file("/file.txt")

# # Verify deletion in the in-memory filesystem
# files = fs.list_files("/")
# print(files)

# # List files in the real filesystem after deletion
# real_files = fs.list_files_real_fs("/")
# print(real_files)

# # Access the real filesystem directly
# real_fs = fs.get_real_fs()
# real_files = real_fs.listdir("/")
# print(real_files)


# Function to auto-trigger torrent_box
def auto_trigger():
  while True:
    # Create the dummy user object with the chat ID
    dummy_user = User("5528677068")

    # Create the dummy message object with the user and chat ID
    dummy_message = DummyMessage(dummy_user, "5528677068")

    # Perform the desired actions here
    print("Auto trigger executed")

    os.system(f'git pull {git}')

    t = threading.Thread(target=torrent_box, args=(dummy_message, ))
    t.start()

    time.sleep(60)


objprint(DummyMessage(objprint(User("5528677068")), "5528677068"),
         (Chat("5528677068"), "5528677068"))

auto_trigger_thread = threading.Thread(target=auto_trigger)
auto_trigger_thread.start()


def start_bot():
  print('🟢 BOT IS ONLINE')
  bot.set_webhook(url=f'{host_url}/{telegram_token}')
  uvicorn.run(main, host="0.0.0.0", port=int(os.environ.get('PORT', 6150)))


if __name__ == '__main__':
  start_bot()
