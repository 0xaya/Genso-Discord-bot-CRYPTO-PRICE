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
SERVER_ID = config.SERVER_ID
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
  # output_log("Get")
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
  # output_log("Load")
  if os.path.isfile("price.json"):
    with open("price.json", "r", encoding="utf-8") as f:
      return json.load(f)
  return None


class CryptoPrice:
  _client: discord.Client
  _token: str
  _id: str
  _token_name: str
  _get_price: bool
  _member: discord.Member

  def __init__(self, token: str, id: str, token_name: str, get_price=False):
    self._token = token
    self._id = id
    self._token_name = token_name
    self._get_price = get_price
    self._member = None
    output_log(f"{self._token_name} Initialized")

  async def main(self):

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
          # name = f"${price:.4f} ({sign}{change:.1f}% 24h)"
          nick = f"{self._token_name}  ${price:.5f}"
          activity = f"{sign_24h}{change_24h:.1f}% 24h, {sign_7d}{change_7d:.1f}% 7D"
          # output_log(f"${self._token_name} {price:.4f} ({sign}{change:.1f}% 24h)")
          activity = discord.Activity(name=activity,
                                      type=discord.ActivityType.watching)
          await self._client.wait_until_ready()
          if self._member is None:
            guild = self._client.get_guild(SERVER_ID)
            # print(f"Guild: {guild.name}")
            self._member = guild.get_member(self._client.user.id)
            print(f"{self._member.name}")
          await self._member.edit(nick=nick)
          await self._client.change_presence(activity=activity)
      except Exception as e:
        output_log(e)
        output_log(traceback.format_exc())

    async with self._client:
      loop.start()
      await self._client.start(self._token)

  def start(self):
    intents = discord.Intents.default()
    intents.message_content = True
    self._client = discord.Client(intents=intents)
    asyncio.run(self.main())


def thread_entry(dict):
  if dict["token_name"] == "BTC":
    cp = CryptoPrice(dict["token"], dict["id"], dict["token_name"], True)
  else:
    cp = CryptoPrice(dict["token"], dict["id"], dict["token_name"])
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
for s in settings:
  thread = threading.Thread(target=thread_entry, args=(s, ))
  thread.start()
  threads.append(thread)
for thread in threads:
  thread.join()
