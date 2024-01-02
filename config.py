from discord.ext import commands
import discord
import pymongo
import os
from dotenv import load_dotenv
print('test')

load_dotenv()

MONGO_CLIENT_KEY = os.getenv('MONGO_CLIENT_KEY')
TOKEN = os.getenv('TOKEN','TOKEN')

MongoClient = pymongo.MongoClient(MONGO_CLIENT_KEY)

dbuser = MongoClient.userconfig
dbbot = MongoClient.botconfig
dbserver = MongoClient.serverconfig

bot = commands.Bot(command_prefix="+",intents=discord.Intents.all())
