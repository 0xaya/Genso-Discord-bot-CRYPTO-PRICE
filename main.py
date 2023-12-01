from keep_alive import keep_alive

import threading
import json
import requests
import os
import traceback
import asyncio
import discord
from discord.ext import tasks
from common import output_log

import config

API_KEY = config.API_KEY
SERVER_IDS = config.SERVER_IDS
BTC_TOKEN = config.BTC_TOKEN
MATIC_TOKEN = config.MATIC_TOKEN
MV_TOKEN = config.MV_TOKEN
ROND_TOKEN = config.ROND_TOKEN

url = 'https://pro-api.coinmarketcap.com/v2/cryptocurrency/quotes/latest'
headers = {
    'User-Agent':
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36',
    'X-CMC_PRO_API_KEY': API_KEY,
    'Accept': 'application/json'
}

parameters = {
    # MV:17704 ROND:22034 BTC:1 MATIC:3890
    'id': '17704,22034,1,3890',
    'convert': 'USD'
}


def get_price():
  try:
    r = requests.get(url, headers=headers, params=parameters)
    if r.status_code != requests.codes.ok:
      return None
    j = json.loads(r.text)
    if j['status']['error_code'] == 0:
      with open("price.json", "w", encoding="utf-8") as f:
        f.write(r.text)
      return j
  except Exception as e:
    output_log("!!!" + e)
    output_log(traceback.format_exc())
  return None


def load_price():
  if os.path.isfile("price.json"):
    with open("price.json", "r", encoding="utf-8") as f:
      return json.load(f)
  return None


class CryptoPrice:

  def __init__(self,
               token: str,
               id: str,
               token_name: str,
               get_price=False,
               server_id=None):
    self._token = token
    self._id = id
    self._token_name = token_name
    self._get_price = get_price
    self._member = None
    self._server_id = server_id
    output_log(f"{self._token_name} Initialized")

  async def main(self):
    intents = discord.Intents.default()
    intents.message_content = True
    self._client = discord.Client(intents=intents)

    @tasks.loop(minutes=10)
    async def loop():
      try:
        if self._get_price:
          j = get_price()
        else:
          j = load_price()
        if j is not None:
          price = float(j['data'][self._id]['quote']['USD']['price'])
          print(price)
          change_24h = float(
              j['data'][self._id]['quote']['USD']['percent_change_24h'])
          change_7d = float(
              j['data'][self._id]['quote']['USD']['percent_change_7d'])
          sign_24h = "+" if change_24h > 0 else ""
          sign_7d = "+" if change_7d > 0 else ""
          nick = f"{self._token_name}  ${price:.5f}"
          activity = f"{sign_24h}{change_24h:.1f}% 24h, {sign_7d}{change_7d:.1f}% 7D"
          activity = discord.Activity(name=activity,
                                      type=discord.ActivityType.watching)

          await self._client.wait_until_ready()
          guild = self._client.get_guild(self._server_id)

          if guild is not None:
            self._member = guild.get_member(self._client.user.id)

            if self._member is not None:
              await self._member.edit(nick=nick)
              await self._client.change_presence(activity=activity)
            else:
              output_log(f"Bot is not in the guild with ID {self._server_id}")
          else:
            output_log(f"Guild with ID {self._server_id} not found.")
      except Exception as e:
        output_log(e)
        output_log(traceback.format_exc())

    @self._client.event
    async def on_ready():
      loop.start()

    await self._client.start(self._token)

  def start(self):
    loop = asyncio.new_event_loop()  # Create a new event loop
    asyncio.set_event_loop(
        loop)  # Set the created event loop as the current event loop
    try:
      loop.create_task(self.main())  # Create a new task within the event loop
      loop.run_forever(
      )  # Run the event loop indefinitely to manage the created task
    finally:
      loop.close()  # Close the event loop when it's no longer needed


def thread_entry(dict, server_id):
  if dict["token_name"] == "BTC":
    cp = CryptoPrice(dict["token"], dict["id"], dict["token_name"], True,
                     server_id)
  else:
    cp = CryptoPrice(dict["token"], dict["id"], dict["token_name"], True,
                     server_id)
  cp.start()


settings = [
    {
        "token": BTC_TOKEN,
        "id": "1",
        "token_name": "BTC"
    },
    {
        "token": MATIC_TOKEN,
        "id": "3890",
        "token_name": "MATIC"
    },
    {
        "token": MV_TOKEN,
        "id": "17704",
        "token_name": "MV"
    },
    {
        "token": ROND_TOKEN,
        "id": "22034",
        "token_name": "ROND"
    },
]

keep_alive()

threads = []
for server_id in SERVER_IDS:
  for s in settings:
    thread = threading.Thread(target=thread_entry, args=(s, server_id))
    thread.start()
    threads.append(thread)

for thread in threads:
  thread.join()
