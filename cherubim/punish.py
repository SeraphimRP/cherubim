import discord
import asyncio
from redbot.core import commands, checks, Config
from redbot.core.utils.chat_formatting import pagify, box
import logging
import os
import time
import re

__version__ = '1.6.0'

try:
    from tabulate import tabulate
except Exception as e:
    raise RuntimeError("You must run `pip3 install tabulate`.") from e

log = logging.getLogger('red.punish')

UNIT_TABLE = {'s': 1, 'm': 60, 'h': 60 * 60, 'd': 60 * 60 * 24}
UNIT_SUF_TABLE = {'sec': (1, ''),
                  'min': (60, ''),
                  'hr': (60 * 60, 's'),
                  'day': (60 * 60 * 24, 's')
                  }
DEFAULT_TIMEOUT = '30m'
PURGE_MESSAGES = 1  # for cpunish
DEFAULT_ROLE_NAME = 'Punished'


class BadTimeExpr(Exception):
    pass


def _parse_time(time):
    if any(u in time for u in UNIT_TABLE.keys()):
        delim = '([0-9.]*[{}])'.format(''.join(UNIT_TABLE.keys()))
        time = re.split(delim, time)
        time = sum([_timespec_sec(t) for t in time if t != ''])
    elif not time.isdigit():
        raise BadTimeExpr("invalid expression '%s'" % time)
    return int(time)


def _timespec_sec(t):
    timespec = t[-1]
    if timespec.lower() not in UNIT_TABLE:
        raise BadTimeExpr("unknown unit '%c'" % timespec)
    timeint = float(t[:-1])
    return timeint * UNIT_TABLE[timespec]


def _generate_timespec(sec):
    timespec = []

    def sort_key(kt):
        k, t = kt
        return t[0]
    for unit, kt in sorted(UNIT_SUF_TABLE.items(), key=sort_key, reverse=True):
        secs, suf = kt
        q = sec // secs
        if q:
            if q <= 1:
                suf = ''
            timespec.append('%02.d%s%s' % (q, unit, suf))
        sec = sec % secs
    return ', '.join(timespec)


class Punish(commands.Cog):
    "Put misbehaving users in timeout"
    def __init__(self, bot):
        self.bot = bot
        self.config = Config.get_conf(self, identifier=(3322665 + 4))
        self.handles = {}

        bot.loop.create_task(self.on_load())

        default_guild = {
            "role_id": None,
            "punished_ids": {}
        }

        self.config.register_guild(**default_guild)

    @commands.command(pass_context=True, no_pm=True)
    @checks.mod_or_permissions(manage_messages=True)
    async def cpunish(self, ctx, user: discord.Member, duration: str=None, *, reason: str=None):
        """Same as punish but cleans up after itself and the target"""

        success = await self._punish_cmd_common(ctx, user, duration, reason, quiet=True)

        if not success:
            return

        def check(m):
            return m.id == ctx.message.id or m.author == user

        try:
            await self.bot.purge_from(ctx.message.channel, limit=PURGE_MESSAGES + 1, check=check)
        except discord.errors.Forbidden:
            await ctx.send("Punishment set, but I need permissions to manage messages to clean up.")

    @commands.command(pass_context=True, no_pm=True)
    @checks.mod_or_permissions(manage_messages=True)
    async def punish(self, ctx, user: discord.Member, duration: str=None, *, reason: str=None):
        """Puts a user into timeout for a specified time period, with an optional reason.
        Time specification is any combination of number with the units s,m,h,d.
        Example: !punish @dumbo 1.1h10m To the toll houses with you!"""

        await self._punish_cmd_common(ctx, user, duration, reason)

    @commands.command(pass_context=True, no_pm=True, name='lspunish')
    @checks.mod_or_permissions(manage_messages=True)
    async def list_punished(self, ctx):
        """Shows a table of punished users with time, mod and reason.

        Displays punished users, time remaining, responsible moderator and
        the reason for Punishment, if any."""
        guild = ctx.guild

        guild_group = self.config.guild(guild)

        async with guild_group.punished_ids() as punished_ids:
            if not punished_ids:
                await ctx.send("No users are currently punished.")
                return

            def getmname(mid):
                member = discord.utils.get(guild.members, id=mid)
                if member:
                    if member.nick:
                        return '%s (%s)' % (member.nick, member)
                    else:
                        return str(member)
                else:
                    return '(member not present, id #%d)'

            headers = ['Member', 'Remaining', 'Punished by', 'Reason']
            table = []
            disp_table = []
            now = time.time()
            for member_id, data in punished_ids.items():
                if not member_id.isdigit():
                    continue

                member_name = getmname(member_id)
                punisher_name = getmname(data['by'])
                reason = data['reason']
                t = data['until']
                sort = t if t else float("inf")
                table.append((sort, member_name, t, punisher_name, reason))

            for _, name, rem, mod, reason in sorted(table, key=lambda x: x[0]):
                remaining = _generate_timespec(rem - now) if rem else 'forever'
                if not reason:
                    reason = 'n/a'
                disp_table.append((name, remaining, mod, reason))

            for page in pagify(tabulate(disp_table, headers)):
                await ctx.send(box(page))

    @commands.command(pass_context=True, no_pm=True)
    @checks.mod_or_permissions(manage_messages=True)
    async def pwarn(self, ctx, user: discord.Member, *, reason: str=None):
        """Warns a user with boilerplate about the rules."""
        msg = ['Hey %s, ' % user.mention]
        msg.append("you're doing something that might get you muted if you keep "
                   "doing it.")
        if reason:
            msg.append(" Specifically, %s." % reason)
        msg.append("Be sure to review the guild rules.")
        await ctx.send(' '.join(msg))

    @commands.command(pass_context=True, no_pm=True)
    @checks.mod_or_permissions(manage_messages=True)
    async def unpunish(self, ctx, user: discord.Member):
        """Removes Punishment from a user. Same as removing the role directly"""
        role = await self.get_role(user.guild)

        sid = user.guild.id
        if role and role in user.roles:
            reason = 'Punishment manually ended early by %s. ' % ctx.message.author
            
            guild_group = self.config.guild(user.guild)

            async with guild_group.punished_ids() as punished_ids:
                if punished_ids[str(user.id)]['reason']:
                    reason += punished_ids[str(user.id)]['reason']
            
            await self._unpunish(user, reason)
            await ctx.send('Done.')
        elif role:
            await ctx.send("That user wasn't punished.")
        else:
            await ctx.send("The punish role couldn't be found in this guild.")

    @commands.command(pass_context=True, no_pm=True)
    @checks.mod_or_permissions(manage_messages=True)
    async def fixpunish(self, ctx):
        guild = ctx.guild
        default_name = DEFAULT_ROLE_NAME

        guild_group = self.config.guild(guild)

        role_id = await guild_group.role_id()

        if role_id:
            role = discord.utils.get(guild.roles, id=role_id)
        else:
            role = discord.utils.get(guild.roles, name=default_name)

        perms = guild.me.guild_permissions
        if not perms.manage_roles and perms.manage_channels:
            await ctx.send("The Manage Roles and Manage Channels permissions are required to use this command.")
            return

        if not role:
            msg = "The %s role doesn't exist; Creating it now (please be sure to move it to the top of the roles below any staff or bots)... " % default_name

            msgobj = await ctx.send(msg)

            perms = discord.Permissions.none()
            role = await guild.create_role(name=default_name, permissions=perms)
        else:
            msgobj = await ctx.send('punish role exists... ')

        msgobj = await msgobj.edit(content=msgobj.content + '(re)configuring channels... ')

        for channel in guild.channels:
            await self.setup_channel(channel, role)

        await ctx.send("Done.")

        if role and role.id != role_id:
            role_id = role.id

    async def get_role(self, guild, channel=None, quiet=False, create=False):
        guild_group = self.config.guild(guild)

        role_id = await guild_group.role_id()
        default_name = DEFAULT_ROLE_NAME

        if role_id:
            role = discord.utils.get(guild.roles, id=role_id)
        else:
            role = discord.utils.get(guild.roles, name=default_name)

        if create and not role:
            perms = guild.me.guild_permissions
                
            if not perms.manage_roles and perms.manage_channels and channel:
                await ctx.send("The Manage Roles and Manage Channels permissions are required to use this command.")
                return None
            else:
                msg = "The %s role doesn't exist; Creating it now (please be sure to move it to the top of the roles below any staff or bots)..." % default_name

                if not quiet and channel:
                    msgobj = await channel.send(msg)

                log.debug('Creating punish role in %s' % guild.name)
                perms = discord.Permissions.none()
                role = await guild.create_role(name=default_name, permissions=perms)

                if not quiet and channel:
                    await msgobj.edit(content=msgobj.content + 'configuring channels... ')

                for channel in guild.channels:
                    await self.setup_channel(channel, role)

                if not quiet and channel:
                    await msgobj.edit(content=msgobj.content + 'done.')

        if role and role.id != role_id:
            role_id = role.id

        return role

    async def setup_channel(self, channel, role):
        perms = discord.PermissionOverwrite()

        if isinstance(channel, discord.TextChannel):
            perms.send_messages = False
            perms.send_tts_messages = False
            perms.add_reactions = False
        elif isinstance(channel, discord.VoiceChannel):
            perms.speak = False

        await channel.set_permissions(role, overwrite=perms)

    async def on_load(self):
        await self.bot.wait_until_ready()

        all_guilds = await self.config.all_guilds()

        for guildid, members in all_guilds.copy().items():
            guild = self.bot.get_guild(guildid)

            me = guild.me
            role = await self.get_role(guild, quiet=True, create=True)
            
            if not role:
                log.error("Needed to create punish role in %s, but couldn't."
                          % guild.name)
                continue

            for member_id, data in members.copy().items():
                if not member_id.isdigit():
                    continue

                until = data['until']
                if until:
                    duration = until - time.time()

                member = guild.get_member(member_id)

                guild_group = self.config.guild(guild)

                async with guild_group.punished_ids() as punished_ids:
                    if until and duration < 0:
                        if member:
                            reason = 'punishment removal overdue, maybe bot was offline. '
                            
                            if punished_ids[str(member_id)]['reason']:
                                reason += punished_ids[str(member_id)]['reason']
                            
                            await self._unpunish(member, reason)
                        else:
                            del(punished_ids[str(member_id)])
                    elif member and role not in member.roles:
                        if role >= me.top_role:
                            log.error("Needed to re-add punish role to %s in %s, "
                                      "but couldn't." % (member, guild.name))
                            continue
                        await member.add_roles(role)
                        if until:
                            self.schedule_unpunish(duration, member)

    async def _punish_cmd_common(self, ctx, member, duration, reason, quiet=False):
        guild = ctx.guild
        note = ''

        if ctx.author.top_role <= member.top_role:
            await ctx.send('Permission denied.')
            return

        if duration and duration.lower() in ['forever', 'inf', 'infinite']:
            duration = None
        else:
            if not duration:
                note += ' Using default duration of ' + DEFAULT_TIMEOUT
                duration = DEFAULT_TIMEOUT

            try:
                duration = _parse_time(duration)
                if duration < 1:
                    await ctx.send("Duration must be 1 second or longer.")
                    return False
            except BadTimeExpr as e:
                await ctx.send("Error parsing duration: %s." % e.args)
                return False

        role = await self.get_role(guild, channel=ctx.channel, quiet=quiet, create=True)
        if role is None:
            await ctx.send("There is not a punished role.")
            return

        if role >= guild.me.top_role:
            await ctx.send('The %s role is too high for me to manage.' % role)
            return

        guild_group = self.config.guild(guild)

        async with guild_group.punished_ids() as punished_ids:
            if str(member.id) in punished_ids:
                msg = 'User was already punished; resetting their timer...'
            elif role in member.roles:
                msg = 'User was punished but had no timer, adding it now...'
            else:
                msg = 'Done.'

            if note:
                msg += ' ' + note

            punished_ids[str(member.id)] = {
                'until': (time.time() + duration) if duration else None,
                'by': str(ctx.author.id),
                'reason': reason
            }

        await member.add_roles(role)

        # schedule callback for role removal
        if duration:
            self.schedule_unpunish(duration, member, reason)

        if not quiet:
            await ctx.send(msg)

        return True

    # Functions related to unpunishing

    async def schedule_unpunish(self, delay, member, reason=None):
        """Schedules role removal, canceling and removing existing tasks if present"""
        sid = str(member.guild.id)

        if sid not in self.handles:
            self.handles[sid] = {}

        if member.id in self.handles[sid]:
            self.handles[sid][str(member.id)].cancel()

        coro = self._unpunish(member, reason)

        handle = self.bot.loop.call_later(delay, self.bot.loop.create_task, coro)
        self.handles[sid][str(member.id)] = handle

    async def _unpunish(self, member, reason=None):
        """Remove punish role, delete record and task handle"""
        role = await self.get_role(member.guild)
        if role:
            # Has to be done first to prevent triggering on_member_update listener
            self._unpunish_data(member)
            await member.remove_roles(role)

            msg = 'Your punishion in %s has ended.' % member.guild.name
            if reason:
                msg += "\nReason was: %s" % reason

            await member.send(msg)

    async def _unpunish_data(self, member):
        """Removes punish data entry and cancels any present callback"""
        sid = str(member.guild.id)

        guild_group = self.config.guild(member.guild)

        async with guild_group.punished_ids() as punished_ids:
            if member.id in punished_ids:
                del(punished_ids[str(member.id)])

            if sid in self.handles and member.id in self.handles[sid]:
                self.handles[sid][str(member.id)].cancel()
                del(self.handles[sid][str(member.id)])

    # Listeners

    async def on_channel_create(self, channel):
        """Run when new channels are created and set up role permissions"""
        if channel.is_private:
            return

        role = await self.get_role(channel.guild)
        if not role:
            return

        await self.setup_channel(channel, role)

    async def on_member_update(self, before, after):
        """Remove scheduled unpunish when manually removed"""
        guild_group = self.config.guild(before.guild)

        async with guild_group.punished_ids() as punished_ids:
            if not before.id in punished_ids:
                return

            role = await self.get_role(before.guild)
            
            if role and role in before.roles and role not in after.roles:
                msg = 'Your punishment in %s was ended early by a moderator/admin.' % before.guild.name
                
                if punished_ids[str(before.id)]['reason']:
                    msg += '\nReason was: ' + punished_ids[str(before.id)]['reason']

                await after.send(msg)
                self._unpunish_data(after)

    async def on_member_join(self, member):
        """Restore Punishment if punished user leaves/rejoins"""
        sid = str(member.guild.id)
        role = await self.get_role(member.guild)

        guild_group = self.config.guild(member.guild)

        async with guild_group.punished_ids() as punished_ids:
            if not role or not member.id in punished_ids:
                return

            duration = punished_ids[str(member.id)]['until'] - time.time()
            if duration > 0:
                await member.add_roles(role)

                reason = 'Punishment re-added on rejoin. '
                if punished_ids[str(member.id)]['reason']:
                    reason += punished_ids[str(member.id)]['reason']

                if str(member.id) not in self.handles[sid]:
                    self.schedule_unpunish(duration, member, reason)
