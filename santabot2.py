#!/usr/bin/env python3

import asyncio
import logging

# noinspection PyPackageRequirements
from discord.ext import commands
from pony import orm

from config import *
import cogs.__shared


logging.basicConfig(level=logging.INFO)

db = orm.Database()
db.bind(**DATABASE)
cogs.__shared.db = db

bot = commands.Bot(command_prefix=COMMAND_PREFIX)
bot.description = (
    'This bot allows to conduct a Secret Santa event in Discord guilds! '
    'It is specifically optimized for digital presents, such as game codes, gift cards etc, '
    'which the bot can send anonymously via DM.'
)
cogs.__shared.bot = bot


@bot.event
async def on_command_error(ctx: commands.Context, error: commands.CommandError):
    msg = str(error)

    if ctx.guild is not None:
        msg = '{} {}'.format(ctx.author.mention, msg)

    await ctx.send(msg)


@bot.command(
    name='eval',
    help='Evaluates the specified Python expression',
    hidden=True
)
@commands.is_owner()
async def _eval(ctx, *, expression: str):
    result = eval(expression)

    if asyncio.iscoroutine(result):
        result = await result

    await ctx.send(result)


# noinspection PyUnresolvedReferences
from cogs import *
db.generate_mapping(check_tables=True, create_tables=True)

bot.run(DISCORD_TOKEN)
