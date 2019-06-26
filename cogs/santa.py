import enum
from typing import Optional

# noinspection PyPackageRequirements
from discord.ext import commands
from pony import orm

import cogs.__shared


table_prefix = 'santa_'


# region HELPER CLASSES

class GuildStates(enum.IntFlag):
    NULL = 1
    STARTED = 2
    COLLECTED = 4
    DISTRIBUTED = 8


def check_guild_state(required_states: GuildStates):
    def predicate(ctx):
        with orm.db_session:
            try:
                guild = Guild[str(ctx.guild.id)]
                state = GuildStates(guild.state)
            except orm.ObjectNotFound:
                state = GuildStates.NULL

            if state in required_states:
                return True
            else:
                raise commands.CommandError(
                    'Command cannot be run in the current guild state (required: {}, current: {}).'
                    .format(str(required_states), str(state))
                )

    return commands.check(predicate)

# endregion


# region DATA STRUCTURES

class Guild(cogs.__shared.db.Entity):
    _table_ = table_prefix + 'guilds'

    guild_id = orm.PrimaryKey(str)  # Discord guild ID
    state = orm.Required(int, size=8, unsigned=True, default=GuildStates.NULL)  # Current state
    budget = orm.Optional(str)  # Total budget per user
    wishes = orm.Set('Wish')
    gifts = orm.Set('Gift')


class Gift(cogs.__shared.db.Entity):
    _table_ = table_prefix + 'gifts'

    guild_id = orm.Required(Guild)  # Discord guild ID
    sender_id = orm.Required(str)  # Discord sender user ID
    recipient_id = orm.Optional(str)  # Discord recipient user ID
    gift = orm.Optional(str)  # Gift contents
    orm.PrimaryKey(guild_id, sender_id)


class Wish(cogs.__shared.db.Entity):
    _table_ = table_prefix + 'wishes'

    guild_id = orm.Required(Guild)  # Discord guild ID
    recipient_id = orm.Required(str)  # Discord recipient user ID
    wish = orm.Optional(str)  # User's wish
    orm.PrimaryKey(guild_id, recipient_id)

# endregion


class Santa(commands.Cog, name='Secret Santa'):
    """Conduct Secret Santa events in your guild!"""

    admin_perms = {'manage_guild': True}

    def __init__(self, bot: commands.Bot, db: orm.Database):
        self.bot = bot
        self.db = db

    # region Moderator commands

    @commands.command(
        help='Starts a new Secret Santa event'
    )
    @check_guild_state(GuildStates.NULL)
    @commands.has_permissions(**admin_perms)
    @commands.guild_only()
    async def start(self, ctx: commands.Context, *, budget: str = 'not specified'):
        with orm.db_session:
            Guild(guild_id=str(ctx.guild.id), state=GuildStates.STARTED, budget=budget)

            await ctx.send('launch done')

    @commands.command(
        help='Resets all Secret Santa data'
    )
    @check_guild_state(~GuildStates.NULL)
    @commands.has_permissions(**admin_perms)
    @commands.guild_only()
    async def reset(self, ctx: commands.Context):
        with orm.db_session:
            try:
                Guild[str(ctx.guild.id)].delete()
            except orm.ObjectNotFound:
                pass

            await ctx.send('reset done')

    @commands.command(
        help='Assign everyone their secret gift recipients'
    )
    @check_guild_state(GuildStates.STARTED)
    @commands.has_permissions(**admin_perms)
    @commands.guild_only()
    async def assign(self, ctx: commands.Context):
        ...  # TODO

    @commands.command(
        help='Send everyone (or specified user) their gifts'
    )
    @check_guild_state(GuildStates.COLLECTED)
    @commands.has_permissions(**admin_perms)
    @commands.guild_only()
    async def send(self, ctx: commands.Context, user: Optional[commands.MemberConverter] = None):
        ...  # TODO

    # endregion


cogs.__shared.bot.add_cog(Santa(cogs.__shared.bot, cogs.__shared.db))
