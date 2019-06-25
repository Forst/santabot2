# noinspection PyPackageRequirements
from discord.ext import commands
from pony import orm


class Santa(commands.Cog):
    def __init__(self, bot, db):
        self.bot = bot
        self.db = db

        class SantaGuild(db.Entity):
            guild_id = orm.PrimaryKey(str)  # Discord guild ID
            state = orm.Required(int, size=8, default=0)  # Current state
            budget = orm.Optional(str)  # Total budget per user
            wishes = orm.Set('SantaWish')
            gifts = orm.Set('SantaGift')

        class SantaGift(db.Entity):
            guild_id = orm.Required(str)  # Discord guild ID
            sender_id = orm.Required(str)  # Discord sender user ID
            recipient_id = orm.Optional(str)  # Discord recipient user ID
            gift = orm.Optional(str)  # Gift contents
            guild = orm.Required(SantaGuild)
            orm.PrimaryKey(guild_id, sender_id)

        class SantaWish(db.Entity):
            guild_id = orm.Required(str)  # Discord guild ID
            recipient_id = orm.Required(str)  # Discord recipient user ID
            wish = orm.Optional(str)  # User's wish
            guild = orm.Required(SantaGuild)
            orm.PrimaryKey(guild_id, recipient_id)

    @commands.command()
    async def owo(self, ctx):
        await ctx.send('uwu')
