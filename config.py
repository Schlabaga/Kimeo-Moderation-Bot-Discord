from discord.ext import commands
import discord
import pymongo
import os
bot = commands.Bot(command_prefix="+",intents=discord.Intents.all())


MONGO_CLIENT_KEY = os.environ.get('MONGO_CLIENT_KEY')
TOKEN = os.environ.get('TOKEN')

MongoClient = pymongo.MongoClient(MONGO_CLIENT_KEY)

dbuser = MongoClient.userconfig
dbbot = MongoClient.botconfig
dbserver = MongoClient.serverconfig

bot = commands.Bot(command_prefix="+",intents=discord.Intents.all())
