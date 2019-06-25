#!/usr/bin/env python3

import logging

# noinspection PyPackageRequirements
from discord.ext import commands
from pony import orm

from config import *

import cogs.santa


logging.basicConfig(level=logging.INFO)

db = orm.Database()
db.bind(**DATABASE)

bot = commands.Bot(command_prefix=COMMAND_PREFIX)
bot.add_cog(cogs.santa.Santa(bot, db))

db.generate_mapping(create_tables=True)

bot.run(DISCORD_TOKEN)
