from enum import IntFlag
from secrets import choice

# noinspection PyPackageRequirements
import discord
# noinspection PyPackageRequirements
from discord.ext import commands
from pony import orm

import cogs.__shared


table_prefix = 'santa_'


# region ORM DEFINITIONS

class Guild(cogs.__shared.db.Entity):
    """Guild states and comments"""
    _table_ = table_prefix + 'guilds'

    guild_id = orm.PrimaryKey(str, 20)  # Discord guild ID
    state = orm.Required(int, size=8, unsigned=True)  # Event state
    comment = orm.Optional(str, 4000, lazy=True)  # Event comment
    wishes_gifts = orm.Set('WishGift')


class WishGift(cogs.__shared.db.Entity):
    """Wishes and gifts for all guilds"""
    _table_ = table_prefix + 'wishes_gifts'

    guild_id = orm.Required(Guild)
    recipient_id = orm.Required(str, 20)  # Recipient user ID
    wish = orm.Optional(str, 4000, lazy=True)  # Recipient user's wish
    sender_id = orm.Optional(str, 20, index='sender_id')  # Sender user's ID
    gift = orm.Optional(str, 4000, lazy=True)  # Sender user's gift
    orm.PrimaryKey(guild_id, recipient_id)

# endregion


# region HELPER CLASSES/FUNCTIONS

class GuildStates(IntFlag):
    NULL = 1
    STARTED = 2
    ASSIGNED = 4
    DISTRIBUTED = 8


@orm.db_session
def get_guild_state(guild_id: int):
    try:
        guild = Guild[str(guild_id)]
        state = GuildStates(guild.state)
    except orm.ObjectNotFound:
        state = GuildStates.NULL

    return state


def check_guild_state(required_states: GuildStates):
    def predicate(ctx: commands.Context):
        state = get_guild_state(ctx.guild.id)

        if state in required_states:
            return True
        else:
            raise commands.CommandError('Command cannot be run in the current guild state (see the "status" command).')

    return commands.check(predicate)


def check_user_participation(invert=False):
    @orm.db_session
    def predicate(ctx: commands.Context):
        try:
            _ = WishGift[str(ctx.guild.id), str(ctx.author.id)]
            result = True
        except orm.ObjectNotFound:
            result = False

        if invert:
            result = not result

        if not result:
            if invert:
                raise commands.CommandError('You are already taking part in the current event.')
            else:
                raise commands.CommandError('You are not taking part in the current event.')

        return True

    return commands.check(predicate)


@orm.db_session
def get_status_message(ctx: commands.Context):
    guild_id = ctx.guild.id
    state = get_guild_state(guild_id)

    prefix = ctx.bot.command_prefix

    if state != GuildStates.NULL:
        guild = Guild[str(guild_id)]

        if state == GuildStates.STARTED:
            message = (
                "**The Secret Santa event is started in this guild!**\n"
                "You can now join it and submit your wishes.\n\n"
                "To **join** the event, send this command:\n"
                "```{prefix}join```\n"
                "To set or update your **wish**, send this command, specifying your wish:\n"
                "```{prefix}wish I would like a big penguin plushie, please!```"
                "Your original message will be automatically deleted for secrecy reasons."
            ).format(prefix=prefix)
        elif state == GuildStates.ASSIGNED:
            message = (
                "**All secret Santas were assigned their recipients!**\n"
                "You should've received all the information via a private message.\n\n"
                "To submit your **gift** for the secret recipient, send this command, specifying your gift:\n"
                "```{prefix}gift Your redeem code for 5 candies on SuperGameStore is XXXXX-XXXXX-XXXXX```"
                "Your original message will be automatically deleted for secrecy reasons.\n\n"
                "If for some reason you didn't get any information via a private message, send this command:\n"
                "```{prefix}myrecipient```"
                "Information will be sent to you via private messages again."
            ).format(prefix=prefix)
        else:
            message = (
                "**All the gifts were delivered to the event participants!**\n"
                "You should've received your gift via a private message.\n\n"
                "If for some reason you didn't get anything from the bot, send this command:\n"
                "```{prefix}mygift```"
                "Your gift will be sent to you via private messages again."
            ).format(prefix=prefix)

        message += (
            '\n\n'
            '**Event comment:** {comment}\n'
            '**Participants:** {participant_count} (with wishes: {wish_count})'
        ).format(
            comment='not specified' if guild.comment == '' else guild.comment,
            participant_count=len(guild.wishes_gifts),
            wish_count=len(guild.wishes_gifts.filter(lambda wg: wg.wish != ''))
        )

        if state in GuildStates.ASSIGNED | GuildStates.DISTRIBUTED:
            message += (
                '\n'
                '**Gifts submitted:** {gift_count}'
            ).format(
                gift_count=len(guild.wishes_gifts.filter(lambda wg: wg.gift != ''))
            )

    else:
        message = (
            "No Secret Santa event is happening at the moment."
        )

    return message


async def send_recipient(ctx: commands.Context, wg: WishGift):
    recipient = ctx.bot.get_user(int(wg.recipient_id))  # type: discord.User
    prefix = ctx.bot.command_prefix

    message = (
        "Your secret gift recipient for guild {guild} is {recipient_mention} ({recipient}).\n"
        "**Event comment:** {comment}\n"
        "**User's wish:**\n"
        "{wish}\n\n"
        "To submit your **gift**, send the following command in the guild with the gift and some nice words:\n"
        "```{prefix}gift Your redeem code for 5 candies on SuperGameStore is XXXXX-XXXXX-XXXXX```"
        "Your original message will be automatically deleted for secrecy reasons.\n\n"
    ).format(
        guild=ctx.guild.name,
        recipient_mention=recipient.mention,
        recipient=recipient,
        comment=wg.guild_id.comment,
        wish='No wish specified' if wg.wish == '' else wg.wish,
        prefix=prefix
    )

    sender = ctx.bot.get_user(int(wg.sender_id))  # type: discord.User

    try:
        await sender.send(message)
    except (discord.HTTPException, discord.Forbidden):
        pass


async def send_gift(ctx: commands.Context, wg: WishGift):
    recipient = ctx.bot.get_user(int(wg.recipient_id))  # type: discord.User

    message = (
        "Here is your Secret Santa gift for guild {guild}!\n\n"
        "{gift}"
    ).format(
        guild=ctx.guild.name,
        gift='No gift specified :(' if wg.gift == '' else wg.gift
    )

    try:
        await recipient.send(message)
    except (discord.HTTPException, discord.Forbidden):
        pass

# endregion


class Santa(commands.Cog, name='Secret Santa'):
    """Conduct Secret Santa events in your guild!"""

    admin_perms = {'manage_guild': True}

    def __init__(self, bot: commands.Bot, db: orm.Database):
        self.bot = bot
        self.db = db

    # region Moderator commands

    @commands.command(help='Start a new Secret Santa event (and optionally specify a comment)')
    @check_guild_state(GuildStates.NULL)
    @commands.has_permissions(**admin_perms)
    @commands.guild_only()
    async def start(self, ctx: commands.Context, *, comment: str = 'not specified'):
        with orm.db_session:
            Guild(guild_id=str(ctx.guild.id), state=GuildStates.STARTED, comment=comment)

            await ctx.send(get_status_message(ctx))

    @commands.command(help='Reset all Secret Santa data for guild')
    @commands.has_permissions(**admin_perms)
    @commands.guild_only()
    async def reset(self, ctx: commands.Context):
        with orm.db_session:
            try:
                Guild[str(ctx.guild.id)].delete()
            except orm.ObjectNotFound:
                pass

            await ctx.send('{} All Secret Santa data for this guild has been reset.'.format(ctx.author.mention))

    @commands.command(help='Update comment for current event')
    @check_guild_state(~GuildStates.NULL)
    @commands.has_permissions(**admin_perms)
    @commands.guild_only()
    async def comment(self, ctx: commands.Context, *, comment: str = ''):
        with orm.db_session:
            Guild[str(ctx.guild.id)].comment = comment

            await ctx.send('{} Comment for this Secret Santa event has been updated.'.format(ctx.author.mention))

    @commands.command(help='Assign everyone their secret gift recipients')
    @check_guild_state(GuildStates.STARTED)
    @commands.has_permissions(**admin_perms)
    @commands.guild_only()
    async def assign(self, ctx: commands.Context):
        with orm.db_session:
            guild = Guild[str(ctx.guild.id)]

            if len(guild.wishes_gifts) < 2:
                raise commands.CommandError('Not enough people taking part in the event (two required).')

            recipient_list = guild.wishes_gifts
            sender_set = set([wg.recipient_id for wg in recipient_list])

            for recipient in recipient_list:
                recipient_id = recipient.recipient_id

                sender_list = list(sender_set)

                if recipient_id in sender_set:
                    sender_list.remove(recipient_id)

                if len(sender_list) > 0:
                    sender_id = choice(sender_list)
                    sender_set.remove(sender_id)
                else:
                    exchange = choice(recipient_list.select(lambda wg: wg.recipient_id != recipient_id)[:])
                    exchange.sender_id, sender_id = recipient_id, exchange.sender_id

                WishGift[guild.guild_id, recipient_id].sender_id = sender_id

            guild.state = GuildStates.ASSIGNED

            for wg in guild.wishes_gifts:
                await send_recipient(ctx, wg)

            await ctx.send(get_status_message(ctx))

    @commands.command(help='Reset Secret Santa sender-recipient assignments')
    @check_guild_state(GuildStates.ASSIGNED)
    @commands.has_permissions(**admin_perms)
    @commands.guild_only()
    async def unassign(self, ctx: commands.Context):
        with orm.db_session:
            guild = Guild[str(ctx.guild.id)]

            for wg in guild.wishes_gifts:
                wg.sender_id = ''
                wg.gift = ''

            guild.state = GuildStates.STARTED

            await ctx.send('{} All assignments have been reset, more users can now join.'.format(ctx.author.mention))

    @commands.command(help='Send everyone their gifts, concluding the event')
    @check_guild_state(GuildStates.ASSIGNED)
    @commands.has_permissions(**admin_perms)
    @commands.guild_only()
    async def distribute(self, ctx: commands.Context):
        with orm.db_session:
            guild = Guild[str(ctx.guild.id)]

            guild.state = GuildStates.DISTRIBUTED

            for wg in guild.wishes_gifts:
                await send_gift(ctx, wg)

            await ctx.send('{} All gifts have been distributed! Merry Christmas!'.format(ctx.author.mention))

    # endregion

    # region Help commands

    @commands.command(help='Displays a simple how-to for users for the Secret Santa')
    async def howto(self, ctx: commands.Context):
        await ctx.send(
            "**Quick how-to for users**\n\n"
            "1. To **join** the event, type:\n"
            "```{prefix}join```\n"
            "2. To submit your **wish**, type:\n"
            "```{prefix}wish I would like a big penguin plushie, please!```\n"
            "3. To submit the **gift** for your secret recipient, type:\n"
            "```{prefix}gift Your redeem code for 5 candies on SuperGameStore is XXXXX-XXXXX-XXXXX```\n"
            "For more information, type `s!help`."
            .format(prefix=ctx.bot.command_prefix)
        )

    @commands.command(help='Displays a simple how-to for moderators for the Secret Santa')
    async def modhowto(self, ctx: commands.Context):
        await ctx.send(
            "**Quick how-to for moderators**\n\n"
            "1. To **start** the event (with an optional comment), type:\n"
            "```{prefix}start Budget is 10 candies```\n"
            "2. To **assign** everyone their secret recipients, type:\n"
            "```{prefix}assign```\n"
            "3. To **distribute** everyone their gifts, type:\n"
            "```{prefix}distribute```\n"
            "For more information, type `s!help`."
            .format(prefix=ctx.bot.command_prefix)
        )

    # endregion

    # region User commands

    @commands.command(help='Join an ongoing event')
    @check_user_participation(invert=True)
    @check_guild_state(GuildStates.STARTED)
    @commands.guild_only()
    async def join(self, ctx: commands.Context):
        with orm.db_session:
            WishGift(guild_id=str(ctx.guild.id), recipient_id=str(ctx.author.id))

            await ctx.send('{} You have now joined the event!'.format(ctx.author.mention))

    @commands.command(help='Leave an ongoing event')
    @check_user_participation()
    @check_guild_state(GuildStates.STARTED)
    @commands.guild_only()
    async def leave(self, ctx: commands.Context):
        with orm.db_session:
            WishGift[str(ctx.guild.id), str(ctx.author.id)].delete()

            await ctx.send('{} You have left the event.'.format(ctx.author.mention))

    @commands.command(help='Set or update your current wish in the given guild')
    @check_user_participation()
    @check_guild_state(GuildStates.STARTED)
    @commands.guild_only()
    async def wish(self, ctx: commands.Context, *, wish: str = ''):
        await ctx.message.delete()

        with orm.db_session:
            WishGift[str(ctx.guild.id), str(ctx.author.id)].wish = wish

            await ctx.send('{} Your wish has been updated!'.format(ctx.author.mention))

    @commands.command(help='Submit or update your gift for the secret recipient in the given guild')
    @check_user_participation()
    @check_guild_state(GuildStates.ASSIGNED | GuildStates.DISTRIBUTED)
    @commands.guild_only()
    async def gift(self, ctx: commands.Context, *, gift: str = ''):
        await ctx.message.delete()

        with orm.db_session:
            guild = Guild[str(ctx.guild.id)]

            guild.wishes_gifts.select(lambda wg: wg.sender_id == str(ctx.author.id)).first().gift = gift

            await ctx.send('{} Your gift has been submitted!'.format(ctx.author.mention))

    @commands.command(help='Find out who is your secret recipient (answered via private messages)')
    @check_user_participation()
    @check_guild_state(GuildStates.ASSIGNED | GuildStates.DISTRIBUTED)
    @commands.guild_only()
    async def myrecipient(self, ctx: commands.Context):
        with orm.db_session:
            guild = Guild[str(ctx.guild.id)]
            wg = guild.wishes_gifts.select(lambda x: x.sender_id == str(ctx.author.id)).first()

            await send_recipient(ctx, wg)

            await ctx.send(
                '{} Information about your secret gift recipient has been sent via a private message.'
                .format(ctx.author.mention)
            )

    @commands.command(help='Get your gift (answered via private messages)')
    @check_user_participation()
    @check_guild_state(GuildStates.DISTRIBUTED)
    @commands.guild_only()
    async def mygift(self, ctx: commands.Context):
        with orm.db_session:
            wg = WishGift[str(ctx.guild.id), str(ctx.author.id)]

            await send_gift(ctx, wg)

            await ctx.send('{} Your gift has been sent to you via a private message.'.format(ctx.author.mention))

    @commands.command(help='Send a person their gift')
    @check_guild_state(GuildStates.DISTRIBUTED)
    @commands.has_permissions(**admin_perms)
    @commands.guild_only()
    async def othergift(self, ctx: commands.Context, user: str):
        with orm.db_session:
            try:
                wg = WishGift[str(ctx.guild.id), user]

                await send_gift(ctx, wg)

                await ctx.send('{} The gift has been sent.'.format(ctx.author.mention))
            except orm.ObjectNotFound:
                await ctx.send('{} Specified user did not take part in the event.'.format(ctx.author.mention))

    @commands.command(help='Display current Secret Santa status in the guild')
    @commands.guild_only()
    async def status(self, ctx: commands.Context):
        await ctx.send(ctx.author.mention + '\n' + get_status_message(ctx))

    # endregion


cogs.__shared.bot.add_cog(Santa(cogs.__shared.bot, cogs.__shared.db))
