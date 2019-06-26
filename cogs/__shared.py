from typing import Optional

# noinspection PyPackageRequirements
from discord.ext import commands
from pony import orm


db = None   # type: Optional[orm.Database]
bot = None  # type: Optional[commands.Bot]
